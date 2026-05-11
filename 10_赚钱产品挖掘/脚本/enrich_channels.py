#!/usr/bin/env python3
"""Additional channel enrichment: Reddit revenue posts, Flippa, GitHub, Chrome Store"""
import json, urllib.request, urllib.parse, ssl, sys, os, re
from datetime import date

ssl_ctx = ssl.create_default_context()
UA = "Mozilla/5.0 (compatible; HermesBot/1.0)"

def fetch_json(url):
    req = urllib.request.Request(url, headers={"User-Agent": UA})
    with urllib.request.urlopen(req, context=ssl_ctx, timeout=15) as resp:
        return json.loads(resp.read())

def search_reddit(subreddit, query, hits=5):
    results = []
    url = f"https://www.reddit.com/r/{subreddit}/search.json?q={urllib.parse.quote(query)}&sort=new&limit={hits}"
    try:
        data = fetch_json(url)
        for child in data.get("data", {}).get("children", []):
            d = child["data"]
            title = d.get("title", "")
            selftext = d.get("selftext", "")[:500]
            desc = f"{title}. {selftext}" if selftext else title
            has_rev = False
            mrr = 0
            full_text = (title + " " + selftext).lower()
            # MRR patterns
            mrr_m = re.search(r'(?:mrr|monthly.recurring).*?\$?([\d,]+)\s*k?', full_text)
            if mrr_m:
                try: mrr = int(mrr_m.group(1).replace(",","")); has_rev = True
                except: pass
            if not has_rev:
                rev_m = re.search(r'\$([\d,]+)\s*(?:/mo|/month|per month|k/mo|k/month)', full_text)
                if rev_m:
                    try: mrr = int(rev_m.group(1).replace(",","")); has_rev = True
                    except: pass
            if not has_rev:
                if any(kw in full_text for kw in ["revenue", "profit", "making $", "earn", "income", "paying"]):
                    has_rev = True
            results.append({
                "source": "reddit",
                "market": "global",
                "name": title[:100],
                "url": f"https://www.reddit.com{d.get('permalink', '')}",
                "description": desc[:400],
                "topics": [],
                "mrr": mrr,
                "profit": 0,
                "asking_price": 0,
                "paying_users": 0,
                "votes": d.get("score", 0),
                "has_revenue": has_rev,
            })
    except Exception as e:
        print(f"  ⚠️ Reddit r/{subreddit} '{query[:30]}' failed: {e}")
    return results

def main():
    today = date.today().isoformat()
    existing_path = f"数据抓取/{today}_raw.json"
    with open(existing_path) as f:
        existing = json.load(f)
    print(f"📂 Loaded {len(existing)} existing")
    seen_urls = set(item.get("url","") for item in existing)
    all_results = list(existing)
    
    # --- Reddit: revenue-specific subreddits ---
    print("\n=== Reddit Revenue Channels ===")
    reddit_searches = [
        ("SaaS", "revenue MRR month profit last month"),
        ("SideProject", "revenue month making money"),
        ("indiehackers", "MRR revenue profit this month"),
        ("microsaas", "revenue MRR sale"),
        ("webdev", "side project revenue making money"),
    ]
    for sub, q in reddit_searches:
        print(f"  r/{sub}: {q[:50]}...")
        r = search_reddit(sub, q, 5)
        new = 0
        for item in r:
            if item["url"] not in seen_urls:
                seen_urls.add(item["url"])
                all_results.append(item)
                new += 1
        print(f"    → {len(r)} fetched, {new} new")
    
    # --- Try GitHub Trending via HN mentions ---
    print("\n=== GitHub Monetization Signals ===")
    gh_url = "https://hn.algolia.com/api/v1/search?query=github.com+pricing+pro+plan+enterprise+stars+SaaS&tags=story&hitsPerPage=5"
    try:
        data = fetch_json(gh_url)
        for h in data.get("hits", []):
            title = h.get("title", "")
            url_str = h.get("url", "")
            if "github.com" not in url_str.lower():
                continue
            if url_str in seen_urls:
                continue
            seen_urls.add(url_str)
            all_results.append({
                "source": "github_hackernews",
                "market": "global",
                "name": title[:100],
                "url": url_str,
                "description": title[:300],
                "topics": ["open_source", "saas"],
                "mrr": 0, "profit": 0, "asking_price": 0,
                "paying_users": 0, "votes": h.get("points", 0),
                "has_revenue": any(k in title.lower() for k in ["pricing","pro","enterprise","paid"]),
            })
        print(f"  → Added GitHub mentions")
    except Exception as e:
        print(f"  ⚠️ GitHub HN: {e}")
    
    # --- Try Flippa mentions on HN/Reddit ---
    print("\n=== Flippa/交易市场信号 ===")
    fl_url = "https://hn.algolia.com/api/v1/search?query=flippa.com+SaaS+sale+revenue+profit+sold&tags=story&hitsPerPage=5"
    try:
        data = fetch_json(fl_url)
        for h in data.get("hits", []):
            title = h.get("title", "")
            url_str = h.get("url", "")
            if url_str in seen_urls:
                continue
            seen_urls.add(url_str)
            has_rev = any(k in title.lower() for k in ["sold","sale","revenue","profit","mrr","flippa"])
            all_results.append({
                "source": "flippa_hackernews",
                "market": "global",
                "name": title[:100],
                "url": url_str,
                "description": title[:300],
                "topics": ["saas", "acquisition"],
                "mrr": 0, "profit": 0, "asking_price": 0,
                "paying_users": 0, "votes": h.get("points", 0),
                "has_revenue": has_rev,
            })
        print(f"  → Added Flippa mentions")
    except Exception as e:
        print(f"  ⚠️ Flippa HN: {e}")
    
    # --- Chrome Web Store mentions ---
    print("\n=== Chrome Extension Revenue ===")
    ce_url = "https://hn.algolia.com/api/v1/search?query=chrome+extension+paid+users+subscribers+revenue&tags=story&hitsPerPage=5"
    try:
        data = fetch_json(ce_url)
        for h in data.get("hits", []):
            title = h.get("title", "")
            url_str = h.get("url", "")
            if url_str in seen_urls:
                continue
            seen_urls.add(url_str)
            all_results.append({
                "source": "chrome_extension_hackernews",
                "market": "global",
                "name": title[:100],
                "url": url_str,
                "description": title[:300],
                "topics": ["chrome_extension"],
                "mrr": 0, "profit": 0, "asking_price": 0,
                "paying_users": 0, "votes": h.get("points", 0),
                "has_revenue": any(k in title.lower() for k in ["paid","revenue","profit","subscriber","monetiz"]),
            })
        print(f"  → Added Chrome extension mentions")
    except Exception as e:
        print(f"  ⚠️ Chrome HN: {e}")
    
    # --- Topic tagging ---
    for item in all_results:
        combined = (item.get("name","") + " " + item.get("description","")).lower()
        topics = list(item.get("topics", []))
        if any(kw in combined for kw in ["saas", "sass", "b2b", "subscription", "stripe"]): 
            if "saas" not in topics: topics.append("saas")
        if any(kw in combined for kw in ["ai ", "ai-", "gpt", "llm", "copilot", "artificial intelligence", "chatgpt"]):
            if "ai_tool" not in topics: topics.append("ai_tool")
        if any(kw in combined for kw in ["chrome extension", "browser extension", "chromewebstore"]):
            if "chrome_extension" not in topics: topics.append("chrome_extension")
        if any(kw in combined for kw in ["open source", "github", "oss", "open-source"]):
            if "open_source" not in topics: topics.append("open_source")
        if any(kw in combined for kw in ["marketplace", "platform", "two-sided"]):
            if "marketplace" not in topics: topics.append("marketplace")
        if any(kw in combined for kw in ["analytics", "dashboard", "metrics"]):
            if "analytics" not in topics: topics.append("analytics")
        if any(kw in combined for kw in ["ecommerce", "shopify"]):
            if "ecommerce" not in topics: topics.append("ecommerce")
        if any(kw in combined for kw in ["no code", "nocode", "no-code", "low code"]):
            if "no_code" not in topics: topics.append("no_code")
        if any(kw in combined for kw in ["boilerplate", "template", "starter"]):
            if "boilerplate" not in topics: topics.append("boilerplate")
        if any(kw in combined for kw in ["productivity", "automation", "workflow"]):
            if "productivity" not in topics: topics.append("productivity")
        if any(kw in combined for kw in ["chrome extension", "extension monetiz", "browser extension"]):
            if "chrome_extension" not in topics: topics.append("chrome_extension")
        if any(kw in combined for kw in ["payment", "billing", "invoice"]):
            if "fintech" not in topics: topics.append("fintech")
        item["topics"] = topics
    
    # Sort: revenue first, then votes
    all_results.sort(key=lambda x: (not x["has_revenue"], -x.get("votes", 0)))
    
    out_path = f"数据抓取/{today}_raw.json"
    with open(out_path, "w") as f:
        json.dump(all_results, f, ensure_ascii=False, indent=2)
    
    rev_count = sum(1 for x in all_results if x["has_revenue"])
    print(f"\n✅ Final: {len(all_results)} entries → {out_path}")
    print(f"   💰 Revenue signals: {rev_count}")
    print(f"   Sources: {set(x['source'] for x in all_results)}")

if __name__ == "__main__":
    os.chdir(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    main()
