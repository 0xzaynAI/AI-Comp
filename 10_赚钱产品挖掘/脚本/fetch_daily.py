#!/usr/bin/env python3
"""Daily product scraper — HN Algolia + Reddit JSON APIs"""
import json, urllib.request, urllib.parse, ssl, os, re, sys
from datetime import date

ssl_ctx = ssl.create_default_context()
UA = 'Mozilla/5.0 (compatible; HermesBot/1.0)'

def fetch_json(url):
    req = urllib.request.Request(url, headers={'User-Agent': UA})
    with urllib.request.urlopen(req, context=ssl_ctx, timeout=15) as resp:
        return json.loads(resp.read())

def extract_mrr(text):
    """Extract MRR/revenue numbers from text"""
    if not text:
        return 0, False
    text_l = text.lower()
    # Pattern: $Xk/mo, $X/mo, MRR $X, etc
    m = re.search(r'\$([\d,]+)\s*k?\s*(?:/mo|/month|per month|MRR|mrr)', text_l)
    if m:
        try:
            val = int(m.group(1).replace(',', ''))
            return val, True
        except:
            pass
    # Pattern: making $X
    m = re.search(r'(?:making|earning|earned)\s+\$([\d,]+)', text_l)
    if m:
        try:
            return int(m.group(1).replace(',', '')), True
        except:
            pass
    # Pattern: revenue $X
    m = re.search(r'revenue\s*:?\s*\$([\d,]+)', text_l)
    if m:
        try:
            return int(m.group(1).replace(',', '')), True
        except:
            pass
    # Has revenue keyword
    if any(kw in text_l for kw in ['revenue', 'profit', 'paid user', 'subscription',
                                      'making $', 'earn', 'income', 'MRR', 'mrr']):
        return 0, True
    return 0, False

def extract_paying_users(text):
    """Extract paying user counts"""
    if not text:
        return 0
    m = re.search(r'(\d+)\s*(?:paying|paid)\s*(?:users|customers|subscribers)', text.lower())
    if m:
        return int(m.group(1))
    return 0

# ============== MAIN ==============
os.chdir(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
today = date.today().isoformat()
all_results = []

# --- Group A: HN Algolia — buildinpublic / MRR / revenue signals ---
queries_a = [
    ('buildinpublic MRR revenue', 8),
    ('launched SaaS AI tool making money', 8),
    ('just hit just crossed MRR startup', 8),
    ('side project revenue dollars', 8),
    ('indie hacker MRR income', 8),
]
print("=== Group A: HN buildinpublic/MRR ===")
for q, hits in queries_a:
    try:
        url = 'https://hn.algolia.com/api/v1/search_by_date?' + \
              f'query={urllib.parse.quote(q)}&tags=story&hitsPerPage={hits}'
        data = fetch_json(url)
        for h in data.get('hits', []):
            title = h.get('title', '')
            pts = h.get('points', 0)
            comments = h.get('num_comments', 0)
            # Skip very low engagement
            if pts < 2 and comments < 2:
                continue
            url_h = h.get('url', f'https://news.ycombinator.com/item?id={h["objectID"]}')
            mrr, has_rev = extract_mrr(title)
            all_results.append({
                'source': 'hackernews',
                'market': 'en',
                'name': title[:120],
                'url': url_h,
                'description': title,
                'topics': [],
                'mrr': mrr, 'profit': 0, 'asking_price': 0,
                'paying_users': 0, 'votes': pts, 'has_revenue': has_rev
            })
        print(f'  q="{q[:40]}" -> {len(data.get("hits",[]))} hits')
    except Exception as e:
        print(f'  q="{q[:40]}" -> ERR: {e}')

# --- Group B: HN Algolia — Chrome extensions / GitHub / ProductHunt ---
queries_b = [
    ('chrome extension paid users subscribers', 6),
    ('github pricing pro plan enterprise SaaS', 6),
    ('monetized open source SaaS revenue', 6),
    ('producthunt trending SaaS AI', 6),
    ('flippa SaaS for sale revenue', 6),
]
print("\n=== Group B: Chrome/GitHub/PH/Flippa ===")
for q, hits in queries_b:
    try:
        url = 'https://hn.algolia.com/api/v1/search_by_date?' + \
              f'query={urllib.parse.quote(q)}&tags=story&hitsPerPage={hits}'
        data = fetch_json(url)
        for h in data.get('hits', []):
            title = h.get('title', '')
            pts = h.get('points', 0)
            comments = h.get('num_comments', 0)
            if pts < 2 and comments < 2:
                continue
            url_h = h.get('url', f'https://news.ycombinator.com/item?id={h["objectID"]}')
            mrr, has_rev = extract_mrr(title)
            # Also check story_text if available
            st = h.get('story_text', '')
            if st:
                mrr2, has_rev2 = extract_mrr(st)
                if mrr2 > mrr:
                    mrr = mrr2
                has_rev = has_rev or has_rev2
            all_results.append({
                'source': 'hackernews',
                'market': 'en',
                'name': title[:120],
                'url': url_h,
                'description': title + (f' — {st[:200]}' if st else ''),
                'topics': [],
                'mrr': mrr, 'profit': 0, 'asking_price': 0,
                'paying_users': 0, 'votes': pts, 'has_revenue': has_rev
            })
        print(f'  q="{q[:40]}" -> {len(data.get("hits",[]))} hits')
    except Exception as e:
        print(f'  q="{q[:40]}" -> ERR: {e}')

# --- Group C: Japanese/East Asian keywords ---
queries_c = [
    ('日本のスタートアップ SaaS 収益', 5),
    ('個人開発 アプリ 収益 月額', 5),
    ('indie hacker 収入 アプリ', 5),
    ('中国 独立开发者 收入 产品', 5),
]
print("\n=== Group C: Japan/China ===")
for q, hits in queries_c:
    try:
        url = 'https://hn.algolia.com/api/v1/search?' + \
              f'query={urllib.parse.quote(q)}&tags=story&hitsPerPage={hits}'
        data = fetch_json(url)
        for h in data.get('hits', []):
            title = h.get('title', '')
            url_h = h.get('url', f'https://news.ycombinator.com/item?id={h["objectID"]}')
            pts = h.get('points', 0)
            mrr, has_rev = extract_mrr(title)
            market = 'ja' if any(c in title for c in '日本語収益開発アプリ') else 'zh'
            all_results.append({
                'source': 'hackernews',
                'market': market,
                'name': title[:120],
                'url': url_h,
                'description': title,
                'topics': [],
                'mrr': mrr, 'profit': 0, 'asking_price': 0,
                'paying_users': 0, 'votes': pts, 'has_revenue': has_rev
            })
        print(f'  q="{q[:40]}" -> {len(data.get("hits",[]))} hits')
    except Exception as e:
        print(f'  q="{q[:40]}" -> ERR: {e}')

# --- Reddit ---
print("\n=== Reddit: r/SaaS, r/SideProject, r/chrome_extensions ===")
for sub in ['SaaS', 'SideProject', 'chrome_extensions']:
    try:
        url = f'https://www.reddit.com/r/{sub}/search.json?q=revenue+MRR+profit+making&sort=new&limit=8&raw_json=1'
        data = fetch_json(url)
        for child in data.get('data', {}).get('children', []):
            d = child['data']
            title = d.get('title', '')
            selftext = d.get('selftext', '')[:400]
            desc = f'{title}. {selftext}' if selftext else title
            full_text = (title + ' ' + selftext).lower()
            mrr, has_rev = extract_mrr(full_text)
            users = extract_paying_users(full_text)
            all_results.append({
                'source': 'reddit',
                'market': 'en',
                'name': title[:120],
                'url': f'https://www.reddit.com{d.get("permalink","")}',
                'description': desc[:500],
                'topics': [],
                'mrr': mrr, 'profit': 0, 'asking_price': 0,
                'paying_users': users,
                'votes': d.get('score', 0), 'has_revenue': has_rev
            })
        print(f'  r/{sub} -> fetched')
    except Exception as e:
        print(f'  r/{sub} -> ERR: {e}')

# --- Deduplicate ---
seen_urls = set()
unique = []
for r in all_results:
    url_key = r['url'].split('?')[0]  # normalize
    if url_key not in seen_urls:
        seen_urls.add(url_key)
        unique.append(r)

# --- Boost: scan all descriptions for revenue signals ---
for item in unique:
    desc = (item.get('description', '') + ' ' + item.get('name', '')).lower()
    mrr2, has_rev2 = extract_mrr(desc)
    if mrr2 > item['mrr']:
        item['mrr'] = mrr2
    if has_rev2:
        item['has_revenue'] = True

# --- Save ---
os.makedirs('数据抓取', exist_ok=True)
out_path = f'数据抓取/{today}_raw.json'
with open(out_path, 'w') as f:
    json.dump(unique, f, ensure_ascii=False, indent=2)

has_rev_count = sum(1 for x in unique if x['has_revenue'])
has_mrr_count = sum(1 for x in unique if x['mrr'] > 0)
print(f'\n✅ Saved {len(unique)} items ({has_rev_count} with revenue signals, {has_mrr_count} with MRR) -> {out_path}')

# Print summary
for item in unique:
    rev = '💰' if item['has_revenue'] else '  '
    mrr_str = f'(${item["mrr"]})' if item['mrr'] > 0 else ''
    print(f'  {rev} [{item["source"]:12}] [{item["market"]}] {item["name"][:70]} {mrr_str}')
