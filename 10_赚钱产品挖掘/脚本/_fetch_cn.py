#!/usr/bin/env python3
"""Fetch Chinese/Japanese indie dev signals from V2EX, Okjike, HN Algolia CN, etc."""
import json, urllib.request, ssl, re, os

ssl_ctx = ssl.create_default_context()
UA = 'Mozilla/5.0 (compatible; HermesBot/1.0)'

def fetch_json(url):
    req = urllib.request.Request(url, headers={'User-Agent': UA})
    with urllib.request.urlopen(req, context=ssl_ctx, timeout=15) as resp:
        return json.loads(resp.read())

results = []

# V2EX nodes: create, share, idev, programmer
for node in ['create', 'share', 'idev', 'programmer']:
    try:
        url = f'https://www.v2ex.com/api/topics/show.json?node_name={node}'
        data = fetch_json(url)
        for t in data[:8]:
            title = t.get('title', '')
            content = t.get('content', '')[:300]
            desc = f"{title}. {content}" if content else title
            full = title + ' ' + content
            has_rev = any(kw in full.lower() for kw in [
                '收入', '赚钱', '付费', '订阅', '盈利', '$', 'MRR', 'mrr',
                '营收', '变现', '收费', '月付', '年付', '订阅制',
                'app store', '内购', '广告收入', '打赏'
            ])
            mrr = 0
            m = re.search(r'[\$¥]([\d,]+)\s*(?:/月|/mo|万|k)', full)
            if m:
                try: mrr = int(m.group(1).replace(',','')); has_rev = True
                except: pass
            results.append({
                'source': 'v2ex',
                'market': 'zh',
                'name': title[:120],
                'url': f"https://www.v2ex.com/t/{t['id']}",
                'description': desc[:500],
                'topics': [node],
                'mrr': mrr, 'profit': 0, 'asking_price': 0,
                'paying_users': 0,
                'votes': t.get('replies', 0),
                'has_revenue': has_rev
            })
        print(f'  V2EX/{node}: {len(data[:8])} items')
    except Exception as e:
        print(f'  V2EX/{node}: ERR {e}')

# HN Algolia for CN/JP keywords
hn_cn_queries = [
    ('独立开发者 SaaS 收入', 'story'),
    ('chrome extension 付费 收入', 'story'),
    ('producthunt 中国 indie', 'story'),
    ('日本 SaaS 収益 アプリ', 'story'),
]
for query, tag in hn_cn_queries:
    try:
        q = urllib.parse.quote(query)
        url = f'https://hn.algolia.com/api/v1/search?query={q}&tags={tag}&hitsPerPage=5'
        data = fetch_json(url)
        for h in data.get('hits', []):
            title = h.get('title', '')
            pts = h.get('points', 0)
            obj_id = h.get('objectID', '')
            url_h = h.get('url') or f'https://news.ycombinator.com/item?id={obj_id}'
            st = h.get('story_text', '')[:400]
            desc = title + (' — ' + st[:200] if st else '')
            full = title + ' ' + st
            has_rev = any(kw in full.lower() for kw in ['revenue','mrr','profit','paid','subscription','定价','收入','付费','収益'])
            results.append({
                'source': 'hackernews',
                'market': 'global',
                'name': title[:120],
                'url': url_h,
                'description': desc[:500],
                'topics': [],
                'mrr': 0, 'profit': 0, 'asking_price': 0,
                'paying_users': 0,
                'votes': pts,
                'has_revenue': has_rev
            })
        print(f'  HN: "{query[:40]}" -> {len(data.get("hits", []))} items')
    except Exception as e:
        print(f'  HN: "{query[:30]}" -> ERR {e}')

# Save
out_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), '数据抓取')
os.makedirs(out_dir, exist_ok=True)
from datetime import date
today = date.today().isoformat()
out_path = os.path.join(out_dir, f'{today}_cn_raw.json')
with open(out_path, 'w') as f:
    json.dump(results, f, ensure_ascii=False, indent=2)

print(f'\n✅ CN/JP supplement: {len(results)} items | Revenue: {sum(1 for x in results if x["has_revenue"])}')
print(f'   Saved: {out_path}')
