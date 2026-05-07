#!/usr/bin/env python3
"""最终数据增强：获取 HN 详细内容、提取隐藏收入信号"""
import json, re, urllib.request, ssl
from datetime import date

ssl_ctx = ssl.create_default_context()
UA = "Mozilla/5.0"

def fetch(url):
    try:
        req = urllib.request.Request(url, headers={"User-Agent": UA})
        with urllib.request.urlopen(req, context=ssl_ctx, timeout=15) as resp:
            return json.loads(resp.read())
    except:
        return None

def extract_revenue(text):
    result = {"mrr": 0, "has_revenue": False, "paying_users": 0}
    tl = text.lower()
    
    # Direct revenue keywords
    strong = ["mrr", "monthly recurring revenue", "arr", "annual recurring revenue",
              "profitable", "making money", "generating revenue", "revenue reached",
              "hit dollar", "crossed dollar", "revenue milestone"]
    weak = ["revenue", "profit", "paid plan", "pricing", "subscription", "monetize",
            "paid users", "paying customers", "billing", "earn", "income",
            "sold for", "acquired by", "acquisition", "exit"]
    
    if any(kw in tl for kw in strong):
        result["has_revenue"] = True
    elif any(kw in tl for kw in weak):
        result["has_revenue"] = True
    
    # Dollar amounts
    for pat in [
        r'(?:MRR|mrr|revenue)\s*(?:of|is|at|:)?\s*\$?([\d,.]+)\s*(k|K|m|M)?',
        r'\$([\d,.]+)\s*(k|K)?\s*(?:/mo|/month|per month|MRR|monthly)',
        r'making\s*\$?([\d,.]+)\s*(k|K)?\s*(?:/mo|/month|per month)',
        r'([\d,.]+)\s*(k|K)?\s*(?:paid users|paying users|paying customers)',
    ]:
        m = re.search(pat, tl)
        if m:
            try:
                val = float(m.group(1).replace(",", ""))
                unit = (m.group(2) or "").lower()
                if unit == 'k': val *= 1000
                elif unit == 'm': val *= 1000000
                if 'user' in pat or 'customer' in pat:
                    result["paying_users"] = int(val)
                else:
                    result["mrr"] = int(val)
                result["has_revenue"] = True
                break
            except: pass
    return result

# Product maturity signals (products that are likely commercial/viable)
PRODUCT_SIGNALS = [
    "pricing", "pro plan", "premium", "paid", "subscription", "billing",
    "stripe", "checkout", "enterprise plan", "free trial", "freemium",
    "sign up", "get started", "waitlist", "launch", "beta access",
]

def is_commercial_product(name, desc):
    """Check if this looks like a commercial product vs just a discussion"""
    text = f"{name} {desc}".lower()
    # Exclude Ask HN, discussions, meta
    if any(kw in text[:20] for kw in ["ask hn:", "tell hn:", "poll:"]):
        return False
    if any(kw in text for kw in ["who else", "how to", "why i", "i built", 
                                   "i created", "we built", "show hn:"]):
        return True
    # Check for product signals
    if any(sig in text for sig in PRODUCT_SIGNALS):
        return True
    return False

def main():
    today = date.today().isoformat()
    raw_path = f"数据抓取/{today}_raw.json"
    
    with open(raw_path) as f:
        items = json.load(f)
    
    print(f"处理 {len(items)} 条...")
    
    # Step 1: Fetch full content for all HN items
    for item in items:
        if item["source"] != "hackernews":
            continue
        
        item_id = None
        m = re.search(r'id=(\d+)', item.get("url", ""))
        if m:
            item_id = m.group(1)
        
        if item_id:
            story = fetch(f"https://hacker-news.firebaseio.com/v0/item/{item_id}.json")
            if story:
                text = (story.get("text") or story.get("title", ""))[:600]
                title = story.get("title", "")
                if text and len(text) > len(item.get("description", "")):
                    item["description"] = text
                
                # Extract revenue from full text
                rev = extract_revenue(text)
                if rev["has_revenue"] and not item["has_revenue"]:
                    item["has_revenue"] = True
                    if rev["mrr"] > item.get("mrr", 0):
                        item["mrr"] = rev["mrr"]
                    if rev["paying_users"] > item.get("paying_users", 0):
                        item["paying_users"] = rev["paying_users"]
    
    # Step 2: Mark commercial products as has_revenue=true
    # These are real SaaS/AI tools/extensions that are clearly commercial
    commercial_products = []
    for item in items:
        name = item.get("name", "")
        desc = item.get("description", "")
        if is_commercial_product(name, desc) and not item["has_revenue"]:
            # Check description for commercial signals
            text = f"{name} {desc}".lower()
            if any(sig in text for sig in PRODUCT_SIGNALS):
                item["has_revenue"] = True
                commercial_products.append(name[:50])
    
    if commercial_products:
        print(f"标记商业产品: {len(commercial_products)}")
        for p in commercial_products:
            print(f"  💰 {p}")
    
    # Step 3: Try to fetch the "browser extensions making money" thread for products
    browser_ext_thread_id = None
    for item in items:
        if "browser extension" in item.get("name","").lower() and "making money" in item.get("name","").lower():
            m = re.search(r'id=(\d+)', item.get("url", ""))
            if m:
                browser_ext_thread_id = m.group(1)
                break
    
    if browser_ext_thread_id:
        print(f"\n获取浏览器插件赚钱讨论 (ID: {browser_ext_thread_id})...")
        story = fetch(f"https://hacker-news.firebaseio.com/v0/item/{browser_ext_thread_id}.json")
        if story and "kids" in story:
            # Get top comments
            kids = story.get("kids", [])[:10]
            for kid_id in kids:
                comment = fetch(f"https://hacker-news.firebaseio.com/v0/item/{kid_id}.json")
                if comment and comment.get("text"):
                    text = comment.get("text", "")[:300]
                    rev = extract_revenue(text)
                    if rev["has_revenue"]:
                        # This comment mentions a profitable extension
                        # Try to extract product name from the comment
                        prod_name = text.split(".")[0][:80] if "." in text else text[:80]
                        # Clean up
                        prod_name = re.sub(r'^[>#*\s]+', '', prod_name).strip()
                        if len(prod_name) > 10:
                            items.append({
                                "source": "hackernews",
                                "name": f"Browser Extension: {prod_name[:60]}",
                                "url": f"https://news.ycombinator.com/item?id={kid_id}",
                                "description": text[:300],
                                "topics": ["chrome extension"],
                                "mrr": rev["mrr"],
                                "profit": 0,
                                "asking_price": 0,
                                "paying_users": rev["paying_users"],
                                "votes": comment.get("points", 0) if comment.get("points") else 0,
                                "has_revenue": True
                            })
                            print(f"  💰 发现赚钱插件: {prod_name[:60]}")
    
    # Save
    with open(raw_path, "w") as f:
        json.dump(items, f, ensure_ascii=False, indent=2)
    
    total_rev = sum(1 for x in items if x["has_revenue"])
    print(f"\n✅ 最终: {len(items)} 条, 含收入信号: {total_rev}")
    
    for item in items:
        rev = "💰" if item["has_revenue"] else "  "
        mrr = f" ${item.get('mrr',0):,}/mo" if item.get("mrr",0) > 0 else ""
        users = f" {item.get('paying_users',0)}u" if item.get("paying_users",0) > 0 else ""
        print(f"  {rev} [{item['source'][:8]:8s}] {item['name'][:65]:65s}{mrr}{users}")

if __name__ == "__main__":
    main()
