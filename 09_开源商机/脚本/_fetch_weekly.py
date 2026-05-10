#!/usr/bin/env python3
"""Weekly data fetcher v2 — fixed parsers for GitHub, PH, HN"""
import json, os, sys, datetime, re
import urllib.request

today = datetime.date.today().isoformat()
results = []

# ---- 1. GitHub Trending (weekly) — improved parser ----
print("[1/3] Fetching GitHub Trending...")
try:
    gh_url = "https://github.com/trending?since=weekly"
    req = urllib.request.Request(gh_url, headers={
        "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36"
    })
    html = urllib.request.urlopen(req, timeout=25).read().decode(errors='replace')
    articles = re.findall(r'<article[^>]*class="Box-row".*?</article>', html, re.DOTALL)
    gh_count = 0
    for art in articles:
        # Get all hrefs, find the one with /owner/repo (skip login, stargazers, forks)
        hrefs = re.findall(r'href="(/[^"]+)"', art)
        repo_href = None
        for h in hrefs:
            parts = h.strip('/').split('/')
            if len(parts) == 2 and h not in ['/login', '/settings'] and not any(x in h for x in ['stargazers','forks','login','return_to']):
                repo_href = h
                break
        if not repo_href:
            continue
        full_name = repo_href.strip('/')

        # Description: try to find the long text in the p tag
        desc = ""
        p_blocks = re.findall(r'<p[^>]*>(.*?)</p>', art, re.DOTALL)
        for p in p_blocks:
            text = re.sub(r'<[^>]+>', ' ', p).strip()
            text = re.sub(r'\s+', ' ', text)
            # Skip short/star blocks
            if len(text) > 20 and 'Star' not in text[:20]:
                # Clean repeated owner/repo prefix
                text = re.sub(r'^\S+/\S+\s+', '', text).strip()
                if len(text) > 10:
                    desc = text
                    break

        # Stars this week
        stars_m = re.search(r'(\d[\d,]*)\s*stars?\s*(this week|today)', art)
        weekly_stars = int(stars_m.group(1).replace(',','')) if stars_m else 0

        # Language
        lang_m = re.search(r'programmingLanguage">([^<]+)<', art)
        topics = [lang_m.group(1)] if lang_m else []

        results.append({
            "source": "github",
            "name": full_name,
            "url": f"https://github.com/{full_name}",
            "description": desc[:300],
            "stars": 0,
            "weekly_growth": weekly_stars,
            "topics": topics
        })
        gh_count += 1
    print(f"   GitHub: {gh_count} repos parsed from {len(articles)} articles")
except Exception as e:
    print(f"   GitHub ERROR: {e}")

# ---- 2. Product Hunt — try multiple approaches ----
print("[2/3] Fetching Product Hunt...")
ph_count = 0
ph_approaches = []

# Approach A: RSS feed
try:
    rss_url = "https://www.producthunt.com/feed?category=undefined"
    req = urllib.request.Request(rss_url, headers={
        "User-Agent": "Mozilla/5.0 (compatible; PhantomBot/1.0)"
    })
    rss = urllib.request.urlopen(req, timeout=20).read().decode(errors='replace')
    items = re.findall(r'<item>(.*?)</item>', rss, re.DOTALL)
    for item in items[:20]:
        title_m = re.search(r'<title>(.*?)</title>', item)
        desc_m = re.search(r'<description>(.*?)</description>', item)
        link_m = re.search(r'<link>(.*?)</link>', item)
        if title_m and link_m:
            title = re.sub(r'<[^>]+>', '', title_m.group(1)).strip()
            desc = re.sub(r'<[^>]+>', '', desc_m.group(1)).strip() if desc_m else ""
            results.append({
                "source": "producthunt",
                "name": title[:150],
                "url": link_m.group(1).strip(),
                "description": desc[:300],
                "stars": 0,
                "upvotes": 0,
                "topics": []
            })
            ph_count += 1
    ph_approaches.append(f"RSS: {len(items)} items, {ph_count} parsed")
except Exception as e:
    ph_approaches.append(f"RSS: {e}")

# Approach B: If RSS failed, try PH homepage with proper headers
if ph_count < 5:
    try:
        ph_url = "https://www.producthunt.com/"
        req = urllib.request.Request(ph_url, headers={
            "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            "Accept": "text/html,application/xhtml+xml",
            "Accept-Language": "en-US,en;q=0.9"
        })
        html = urllib.request.urlopen(req, timeout=20).read().decode(errors='replace')
        # Look for __NEXT_DATA__ or product cards
        next_data = re.search(r'<script id="__NEXT_DATA__"[^>]*>(.*?)</script>', html, re.DOTALL)
        if next_data:
            nd = json.loads(next_data.group(1))
            apollo = nd.get('props',{}).get('apolloState',{})
            ph_b = 0
            for k, v in apollo.items():
                if isinstance(v, dict) and v.get('__typename') == 'Post':
                    name = v.get('name','')
                    tagline = v.get('tagline','')
                    votes = v.get('votesCount', 0) or 0
                    slug = v.get('slug','')
                    if name and ph_b < 15:
                        results.append({
                            "source": "producthunt",
                            "name": name,
                            "url": f"https://www.producthunt.com/posts/{slug}" if slug else f"https://www.producthunt.com/search?q={name.replace(' ','+')}",
                            "description": (tagline or '')[:300],
                            "stars": 0,
                            "upvotes": votes,
                            "topics": []
                        })
                        ph_b += 1
            ph_count += ph_b
            ph_approaches.append(f"NextJS: {ph_b} posts")
    except Exception as e:
        ph_approaches.append(f"NextJS: {e}")

print(f"   ProductHunt: {ph_count} products ({'; '.join(ph_approaches)})")

# ---- 3. Hacker News Show HN (via Algolia API) ----
print("[3/3] Fetching Hacker News Show HN...")
try:
    week_ago = int((datetime.datetime.now() - datetime.timedelta(days=7)).timestamp())
    hn_url = (
        f"https://hn.algolia.com/api/v1/search_by_date"
        f"?tags=show_hn&hitsPerPage=30&numericFilters=created_at_i>{week_ago}"
    )
    req = urllib.request.Request(hn_url, headers={"User-Agent": "PhantomBot/1.0"})
    data = json.loads(urllib.request.urlopen(req, timeout=25).read())
    hn_count = 0
    for hit in data.get("hits", [])[:20]:
        title = hit.get("title", "")
        title = re.sub(r'^Show HN:\s*', '', title).strip()
        url = hit.get("url", "") or f"https://news.ycombinator.com/item?id={hit['objectID']}"
        points = hit.get("points", 0) or 0
        num_comments = hit.get("num_comments", 0) or 0
        results.append({
            "source": "hackernews",
            "name": title[:150],
            "url": url,
            "description": f"{num_comments} comments · {points} points",
            "stars": 0,
            "upvotes": points,
            "topics": []
        })
        hn_count += 1
    print(f"   HN: {hn_count} posts parsed")
except Exception as e:
    print(f"   HN ERROR: {e}")

# ---- Save ----
out_dir = "/Users/lennyz/github/AI-Comp/09_开源商机/数据抓取"
os.makedirs(out_dir, exist_ok=True)
out_path = os.path.join(out_dir, f"{today}_raw.json")
with open(out_path, 'w', encoding='utf-8') as f:
    json.dump(results, f, ensure_ascii=False, indent=2)

print(f"\n✅ Total: {len(results)} projects saved to {out_path}")
print(f"   GitHub: {sum(1 for r in results if r['source']=='github')}")
print(f"   ProductHunt: {sum(1 for r in results if r['source']=='producthunt')}")
print(f"   HN: {sum(1 for r in results if r['source']=='hackernews')}")
