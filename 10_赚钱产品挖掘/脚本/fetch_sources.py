#!/usr/bin/env python3
"""从多个数据源抓取赚钱产品信号"""
import json, urllib.request, urllib.parse, ssl, sys, os
from datetime import date

ssl_ctx = ssl.create_default_context()
UA = "Mozilla/5.0 (compatible; HermesBot/1.0)"

def fetch_json(url):
    req = urllib.request.Request(url, headers={"User-Agent": UA})
    with urllib.request.urlopen(req, context=ssl_ctx, timeout=15) as resp:
        return json.loads(resp.read())

def search_hn(query, hits=5):
    """Search HN via Algolia API"""
    results = []
    url = f"https://hn.algolia.com/api/v1/search?query={urllib.parse.quote(query)}&tags=story&hitsPerPage={hits}"
    try:
        data = fetch_json(url)
        for h in data.get("hits", []):
            results.append({
                "source": "hackernews",
                "name": h["title"].replace("Show HN: ", "").strip()[:80],
                "url": h.get("url", f"https://news.ycombinator.com/item?id={h['objectID']}"),
                "description": h["title"],
                "topics": [],
                "mrr": 0,
                "profit": 0,
                "asking_price": 0,
                "paying_users": 0,
                "votes": h.get("points", 0),
                "has_revenue": False,
            })
    except Exception as e:
        print(f"  ⚠️ HN search failed: {e}")
    return results

def search_hn_recent(query, hits=5):
    """Search HN by date (recent)"""
    results = []
    url = f"https://hn.algolia.com/api/v1/search_by_date?query={urllib.parse.quote(query)}&tags=story&hitsPerPage={hits}"
    try:
        data = fetch_json(url)
        for h in data.get("hits", []):
            results.append({
                "source": "hackernews",
                "name": h["title"].replace("Show HN: ", "").strip()[:80],
                "url": h.get("url", f"https://news.ycombinator.com/item?id={h['objectID']}"),
                "description": h["title"],
                "topics": [],
                "mrr": 0,
                "profit": 0,
                "asking_price": 0,
                "paying_users": 0,
                "votes": h.get("points", 0),
                "has_revenue": False,
            })
    except Exception as e:
        print(f"  ⚠️ HN recent search failed: {e}")
    return results

def search_reddit_json(subreddit, query, hits=5):
    """Search Reddit via JSON API"""
    results = []
    url = f"https://www.reddit.com/r/{subreddit}/search.json?q={urllib.parse.quote(query)}&sort=new&limit={hits}"
    try:
        req = urllib.request.Request(url, headers={"User-Agent": UA})
        with urllib.request.urlopen(req, context=ssl_ctx, timeout=15) as resp:
            data = json.loads(resp.read())
        for child in data.get("data", {}).get("children", []):
            d = child["data"]
            title = d.get("title", "")
            selftext = d.get("selftext", "")[:300]
            desc = f"{title}. {selftext}" if selftext else title
            # Revenue signal detection
            has_rev = False
            mrr = 0
            full_text = (title + " " + selftext).lower()
            import re
            # Look for MRR patterns
            mrr_match = re.search(r'(?:mrr|MRR).*?\$?([\d,]+)\s*k?', full_text)
            if mrr_match:
                try:
                    val = mrr_match.group(1).replace(",", "")
                    mrr = int(val)
                    has_rev = True
                except: pass
            if not has_rev:
                rev_match = re.search(r'\$([\d,]+)\s*(?:/mo|/month|k/mo|k/month|per month|MRR)', full_text)
                if rev_match:
                    try:
                        val = rev_match.group(1).replace(",", "")
                        mrr = int(val)
                        has_rev = True
                    except: pass
            if not has_rev:
                if any(kw in full_text for kw in ["revenue", "profit", "making $", "earn", "income"]):
                    has_rev = True
            
            results.append({
                "source": "reddit",
                "name": title[:80],
                "url": f"https://www.reddit.com{d.get('permalink', '')}",
                "description": desc[:300],
                "topics": [],
                "mrr": mrr,
                "profit": 0,
                "asking_price": 0,
                "paying_users": 0,
                "votes": d.get("score", 0),
                "has_revenue": has_rev,
            })
    except Exception as e:
        print(f"  ⚠️ Reddit r/{subreddit} search failed: {e}")
    return results

def main():
    today = date.today().isoformat()
    all_results = []
    
    print("=== 赚钱产品每日挖掘 - 数据抓取 ===")
    print(f"日期: {today}")
    print()
    
    # Source 1: Reddit (try multiple subreddits)
    print("[1/5] Reddit — r/SaaS, r/SideProject...")
    for sub, q in [
        ("SaaS", "MRR revenue reached crossed"),
        ("SideProject", "revenue month making"),
        ("indiehackers", "MRR revenue"),
    ]:
        r = search_reddit_json(sub, q, 5)
        all_results.extend(r)
        print(f"  r/{sub}: {len(r)} results")
    
    # Source 2: Indie Hackers (HN mentions)
    print("[2/5] Indie Hackers — via HN + direct...")
    r = search_hn("indiehackers.com revenue MRR product", 5)
    all_results.extend(r)
    print(f"  indiehackers: {len(r)} results")
    
    # Source 3: Product Hunt (HN mentions)
    print("[3/5] Product Hunt — via HN...")
    r = search_hn("producthunt.com launched SaaS AI tool", 5)
    all_results.extend(r)
    print(f"  producthunt: {len(r)} results")
    
    # Source 4: Chrome extensions
    print("[4/5] Chrome Extensions...")
    r = search_hn("chrome extension paid users subscribers", 5)
    all_results.extend(r)
    r2 = search_hn("browser extension profitable making", 5)
    all_results.extend(r2)
    print(f"  chrome-ext: {len(r) + len(r2)} results")
    
    # Source 5: Flippa + HN Show HN
    print("[5/5] Flippa + HN Show HN...")
    r = search_hn("flippa.com SaaS startup revenue profit sale", 5)
    all_results.extend(r)
    r2 = search_hn_recent("Show HN SaaS product launch", 10)
    all_results.extend(r2)
    print(f"  flippa+hn: {len(r) + len(r2)} results")
    
    # Revenue signal boost: scan for revenue keywords in descriptions
    import re
    for item in all_results:
        desc_lower = (item["description"] + " " + item["name"]).lower()
        # Revenue mentions
        rev_match = re.search(r'\$([\d,]+)\s*(?:k|K)?\s*(?:/mo|/month|per month|MRR|mrr|monthly)', desc_lower)
        if rev_match and item["mrr"] == 0:
            try:
                val = rev_match.group(1).replace(",", "")
                item["mrr"] = int(val)
                item["has_revenue"] = True
            except: pass
        if any(kw in desc_lower for kw in ["revenue", "profitable", "making $", "earn", "income", "paid users"]):
            item["has_revenue"] = True
    
    # Save
    os.makedirs("数据抓取", exist_ok=True)
    out_path = f"数据抓取/{today}_raw.json"
    with open(out_path, "w") as f:
        json.dump(all_results, f, ensure_ascii=False, indent=2)
    
    print(f"\n✅ 共抓取 {len(all_results)} 条 → {out_path}")
    print(f"   含收入信号: {sum(1 for x in all_results if x['has_revenue'])}")
    
    # Print summary
    for item in all_results:
        rev_mark = "💰" if item["has_revenue"] else "  "
        print(f"  {rev_mark} [{item['source']}] {item['name'][:60]}")

if __name__ == "__main__":
    os.chdir(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    main()
