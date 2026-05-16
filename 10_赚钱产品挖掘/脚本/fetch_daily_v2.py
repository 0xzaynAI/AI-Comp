#!/usr/bin/env python3
"""Daily revenue product scraper v2 — HN Algolia + Reddit JSON"""
import json, urllib.request, urllib.parse, ssl, re, os, sys

ssl_ctx = ssl.create_default_context()
UA = 'Mozilla/5.0 (compatible; HermesBot/1.0)'

def fetch(url):
    req = urllib.request.Request(url, headers={'User-Agent': UA})
    with urllib.request.urlopen(req, context=ssl_ctx, timeout=15) as r:
        return json.loads(r.read())

def extract_mrr(text):
    if not text: return 0, False
    tl = text.lower()
    m = re.search(r'\$([\d,]+)\s*k?\s*(?:/mo|/month|per month|MRR|mrr|monthly)', tl)
    if m:
        try: return int(m.group(1).replace(',','')), True
        except: pass
    m = re.search(r'(?:making|earning|earned|generates?)\s+\$([\d,]+)\s*k?', tl)
    if m:
        try:
            val = int(m.group(1).replace(',',''))
            return (val * 1000 if 'k' in m.group(0).lower() else val), True
        except: pass
    has_rev = any(kw in tl for kw in [
        'revenue','profit','paid user','subscription','making $',
        'earn','income','MRR','mrr','pricing','pro plan','付费','订阅'
    ])
    return 0, has_rev

def extract_users(text):
    if not text: return 0
    m = re.search(r'(\d+)\s*(?:paying|paid)\s*(?:users|customers|subscribers)', text.lower())
    return int(m.group(1)) if m else 0

# ===== CONFIG =====
CUTOFF_TS = 1759276800  # 2025-10-01
OUT_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), '数据抓取')
os.makedirs(OUT_DIR, exist_ok=True)

all_items = []

# ===== HN ALGOLIA SEARCHES =====
hn_searches = [
    ('MRR revenue making monthly', 'story', 15),
    ('just hit reached crossed MRR startup', 'story', 12),
    ('chrome extension paid users subscribers', 'story', 10),
    ('micro SaaS side project revenue profit', 'story', 12),
    ('indie hacker bootstrapped profitable', 'story', 10),
    ('flippa for sale SaaS startup', 'story', 8),
    ('open source monetized enterprise pricing', 'story', 10),
    ('buildinpublic buildinginpublic', 'story', 8),
    ('Show HN SaaS AI tool', 'show_hn', 10),
    ('Show HN extension app product', 'show_hn', 10),
]

for query, tag, hits in hn_searches:
    try:
        q_enc = urllib.parse.quote(query)
        url = f'https://hn.algolia.com/api/v1/search?query={q_enc}&tags={tag}&hitsPerPage={hits}&numericFilters=created_at_i%3E{CUTOFF_TS}'
        data = fetch(url)
        count = 0
        for h in data.get('hits', []):
            title = h.get('title', '')
            pts = h.get('points', 0)
            comments = h.get('num_comments', 0)
            if pts < 1 and comments < 1:
                continue
            obj_id = h.get('objectID', '')
            url_h = h.get('url') or f'https://news.ycombinator.com/item?id={obj_id}'
            st = h.get('story_text', '')[:500]
            full_desc = title + ' ' + st
            desc_text = title
            if st:
                desc_text += ' — ' + st[:200]
            mrr, has_rev = extract_mrr(full_desc)
            users = extract_users(full_desc)
            all_items.append({
                'source': 'hackernews',
                'market': 'en',
                'name': title[:120],
                'url': url_h,
                'description': desc_text[:500],
                'topics': [],
                'mrr': mrr, 'profit': 0, 'asking_price': 0,
                'paying_users': users, 'votes': pts, 'has_revenue': has_rev
            })
            count += 1
        print(f'  HN [{tag}] "{query[:40]}" -> {count} items')
    except Exception as e:
        print(f'  HN [{tag}] "{query[:30]}" -> ERR: {e}')

# ===== REDDIT JSON API =====
reddit_subs = [
    ('SaaS', 'MRR revenue'),
    ('SaaS', 'just hit'),
    ('SideProject', 'revenue making'),
    ('SideProject', 'MRR'),
    ('chrome_extensions', 'paid subscribers'),
    ('microsaas', 'revenue'),
]

for sub, query in reddit_subs:
    try:
        q_enc = urllib.parse.quote(query)
        url = f'https://www.reddit.com/r/{sub}/search.json?q={q_enc}&sort=new&limit=10&raw_json=1'
        data = fetch(url)
        count = 0
        for child in data.get('data', {}).get('children', []):
            d = child['data']
            title = d.get('title', '')
            selftext = d.get('selftext', '')[:400]
            full_text = title + ' ' + selftext
            mrr, has_rev = extract_mrr(full_text)
            users = extract_users(full_text)
            permalink = d.get('permalink', '')
            reddit_url = 'https://www.reddit.com' + permalink
            desc_text = title
            if selftext:
                desc_text += '. ' + selftext
            all_items.append({
                'source': 'reddit',
                'market': 'en',
                'name': title[:120],
                'url': reddit_url,
                'description': desc_text[:500],
                'topics': [],
                'mrr': mrr, 'profit': 0, 'asking_price': 0,
                'paying_users': users,
                'votes': d.get('score', 0),
                'has_revenue': has_rev
            })
            count += 1
        print(f'  Reddit r/{sub} q="{query}" -> {count} items')
    except Exception as e:
        print(f'  Reddit r/{sub} q="{query}" -> ERR: {e}')

# ===== DEDUPLICATE =====
seen = set()
unique = []
for item in all_items:
    key = item['url'].split('?')[0].rstrip('/')
    if key not in seen:
        seen.add(key)
        unique.append(item)

# ===== POST-PROCESS: BOOST SIGNALS =====
for item in unique:
    desc = (item.get('description', '') + ' ' + item.get('name', '')).lower()
    mrr2, has_rev2 = extract_mrr(desc)
    if mrr2 > item['mrr']:
        item['mrr'] = mrr2
    if has_rev2 and not item['has_revenue']:
        item['has_revenue'] = True

# ===== SAVE =====
from datetime import date
today = date.today().isoformat()
out_path = os.path.join(OUT_DIR, f'{today}_raw.json')
with open(out_path, 'w') as f:
    json.dump(unique, f, ensure_ascii=False, indent=2)

has_rev = sum(1 for x in unique if x['has_revenue'])
has_mrr = sum(1 for x in unique if x['mrr'] > 0)
print(f'\n✅ Total: {len(unique)} items | Revenue: {has_rev} | MRR>0: {has_mrr}')
print(f'   Saved: {out_path}')

# Print top revenue items
for item in sorted(unique, key=lambda x: x['mrr'], reverse=True)[:10]:
    if item['mrr'] > 0 or item['has_revenue']:
        rev = '💰' if item['has_revenue'] else '  '
        mrr_s = f'${item["mrr"]}' if item['mrr'] > 0 else ''
        print(f'  {rev} [{item["source"]:12}] {item["name"][:70]} {mrr_s}')
