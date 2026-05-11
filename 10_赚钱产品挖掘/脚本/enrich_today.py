#!/usr/bin/env python3
"""Enrichment script — additional HN + Reddit targeted searches for revenue signals"""
import json, urllib.request, urllib.parse, ssl, sys, os, re
from datetime import date

ssl_ctx = ssl.create_default_context()
UA = "Mozilla/5.0 (compatible; HermesBot/1.0)"

def fetch_json(url):
    req = urllib.request.Request(url, headers={"User-Agent": UA})
    with urllib.request.urlopen(req, context=ssl_ctx, timeout=15) as resp:
        return json.loads(resp.read())

def search_hn(query, hits=8):
    results = []
    url = f"https://hn.algolia.com/api/v1/search?query={urllib.parse.quote(query)}&tags=story&hitsPerPage={hits}"
    try:
        data = fetch_json(url)
        for h in data.get("hits", []):
            title = h.get("title", "")
            url_str = h.get("url") or f"https://news.ycombinator.com/item?id={h['objectID']}"
            pts = h.get("points", 0)
            # Detect revenue
            has_rev = False
            mrr = 0
            full = title.lower()
            m = re.search(r'\$([\d,]+)\s*k?\s*(?:/mo|/month|mrr|per month)', full)
            if m:
                try: mrr = int(m.group(1).replace(",","")); has_rev = True
                except: pass
            if not has_rev:
                if any(kw in full for kw in ["revenue", "profitable", "making $", "earn", "income", "paid users", "subscription"]):
                    has_rev = True
            results.append({
                "source": "hackernews",
                "market": "global",
                "name": title[:100],
                "url": url_str,
                "description": title[:300],
                "topics": [],
                "mrr": mrr,
                "profit": 0,
                "asking_price": 0,
                "paying_users": 0,
                "votes": pts,
                "has_revenue": has_rev,
            })
    except Exception as e:
        print(f"  ⚠️ HN '{query[:30]}' failed: {e}")
    return results

def search_hn_recent(query, hits=8):
    results = []
    url = f"https://hn.algolia.com/api/v1/search_by_date?query={urllib.parse.quote(query)}&tags=story&hitsPerPage={hits}"
    try:
        data = fetch_json(url)
        for h in data.get("hits", []):
            title = h.get("title", "")
            url_str = h.get("url") or f"https://news.ycombinator.com/item?id={h['objectID']}"
            pts = h.get("points", 0)
            has_rev = False
            mrr = 0
            full = title.lower()
            m = re.search(r'\$([\d,]+)\s*k?\s*(?:/mo|/month|mrr|per month)', full)
            if m:
                try: mrr = int(m.group(1).replace(",","")); has_rev = True
                except: pass
            if not has_rev:
                if any(kw in full for kw in ["revenue", "profitable", "making $", "earn", "income", "paid", "subscription"]):
                    has_rev = True
            results.append({
                "source": "hackernews",
                "market": "global",
                "name": title[:100],
                "url": url_str,
                "description": title[:300],
                "topics": [],
                "mrr": mrr,
                "profit": 0,
                "asking_price": 0,
                "paying_users": 0,
                "votes": pts,
                "has_revenue": has_rev,
            })
    except Exception as e:
        print(f"  ⚠️ HN-recent '{query[:30]}' failed: {e}")
    return results

def main():
    today = date.today().isoformat()
    all_results = []
    
    # Load existing
    existing_path = f"数据抓取/{today}_raw.json"
    if os.path.exists(existing_path):
        with open(existing_path) as f:
            existing = json.load(f)
        print(f"📂 Loaded {len(existing)} existing entries")
    else:
        existing = []
    
    seen_urls = set()
    for item in existing:
        seen_urls.add(item.get("url",""))
    all_results = list(existing)
    
    print("=== Enrichment: Additional HN + Reddit searches ===\n")
    
    # --- HN Targeted Searches ---
    hn_queries = [
        "launched today SaaS AI tool making money",
        "just hit MRR revenue month",
        "side project making revenue profitable",
        "chrome extension paid users subscribers revenue",
        "sold startup flippa acquire",
        "product hunt trending SaaS extension AI today",
        "micro SaaS for sale revenue MRR",
        "indie hacker making monthly recurring revenue",
    ]
    
    for q in hn_queries:
        print(f"[HN] {q[:60]}...")
        r = search_hn(q, 5)
        new = 0
        for item in r:
            if item["url"] not in seen_urls:
                seen_urls.add(item["url"])
                all_results.append(item)
                new += 1
        print(f"  → {len(r)} fetched, {new} new")
    
    # --- HN Recent ---
    recent_queries = [
        "Show HN SaaS AI product launch",
        "Show HN side project",
        "revenue MRR profitable",
    ]
    for q in recent_queries:
        print(f"[HN-recent] {q[:60]}...")
        r = search_hn_recent(q, 5)
        new = 0
        for item in r:
            if item["url"] not in seen_urls:
                seen_urls.add(item["url"])
                all_results.append(item)
                new += 1
        print(f"  → {len(r)} fetched, {new} new")
    
    # --- Deduplicate & clean ---
    # Remove obvious noise (non-product posts)
    noise_patterns = [
        r'budget bombshell', r'encounters-per-day', r'Queen of the Squirrels',
        r'resume evaluation', r'carpal.?tunnel', r'LDA Roundabout',
        r'MBC GROUP', r'FRESH Remote Jobs', r'design flaw',
        r'DELIVERS RESILIENT', r'secret meetings',
    ]
    cleaned = []
    for item in all_results:
        name = item.get("name","")
        desc = item.get("description","")
        combined = (name + " " + desc).lower()
        if any(re.search(p, combined) for p in noise_patterns):
            continue
        # Add market classification
        if not item.get("market"):
            item["market"] = "global"
        # Topic extraction
        topics = []
        combined_l = combined
        if any(kw in combined_l for kw in ["saas", "sass", "b2b"]): topics.append("saas")
        if any(kw in combined_l for kw in ["ai ", "ai-", "gpt", "llm", "copilot", "artificial intelligence"]): topics.append("ai_tool")
        if any(kw in combined_l for kw in ["chrome extension", "browser extension", "chrome web store"]): topics.append("chrome_extension")
        if any(kw in combined_l for kw in ["payment", "stripe", "subscription", "billing"]): topics.append("fintech")
        if any(kw in combined_l for kw in ["open source", "github", "oss"]): topics.append("open_source")
        if any(kw in combined_l for kw in ["marketplace", "platform"]): topics.append("marketplace")
        if any(kw in combined_l for kw in ["analytics", "data", "dashboard"]): topics.append("analytics")
        if any(kw in combined_l for kw in ["ecommerce", "shopify", "woocommerce"]): topics.append("ecommerce")
        if any(kw in combined_l for kw in ["no code", "nocode", "low code", "no-code"]): topics.append("no_code")
        if any(kw in combined_l for kw in ["boilerplate", "template", "starter"]): topics.append("boilerplate")
        if any(kw in combined_l for kw in ["productivity", "automation", "workflow"]): topics.append("productivity")
        item["topics"] = topics
        cleaned.append(item)
    
    # Sort: revenue signals first, then by votes
    cleaned.sort(key=lambda x: (not x["has_revenue"], -x.get("votes", 0)))
    
    # Save
    out_path = f"数据抓取/{today}_raw.json"
    with open(out_path, "w") as f:
        json.dump(cleaned, f, ensure_ascii=False, indent=2)
    
    rev_count = sum(1 for x in cleaned if x["has_revenue"])
    print(f"\n✅ Final: {len(cleaned)} entries → {out_path}")
    print(f"   💰 Revenue signals: {rev_count}")
    
    # Print top entries
    print("\n--- Top Entries ---")
    for i, item in enumerate(cleaned[:20]):
        rev = "💰" if item["has_revenue"] else "  "
        print(f"  {rev} [{item['source'][:2]:2s}] {item['name'][:80]}")

if __name__ == "__main__":
    os.chdir(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    main()
