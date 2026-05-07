#!/usr/bin/env python3
"""Merge raw data from multiple sources and enrich revenue signals"""
import json, re, sys, os

os.chdir(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Load existing raw data
with open('数据抓取/2026-05-07_raw.json') as f:
    existing = json.load(f)

# sspai entries (from direct API)
sspai_entries = [
    {
        "source": "sspai", "market": "zh",
        "name": "BuhoLaunchpad - Mac Launchpad Replacement",
        "url": "https://sspai.com/post/109471",
        "description": "BuhoLaunchpad replaces the removed macOS 26 Launchpad. Mac app that restores app launcher with custom groups and fullscreen mode. Developer shares build journey.",
        "topics": ["mac", "launcher", "utility"],
        "mrr": 0, "profit": 0, "asking_price": 0, "paying_users": 0, "votes": 0, "has_revenue": True
    },
    {
        "source": "sspai", "market": "zh",
        "name": "DesignExtractor - One-click website design spec to Design.md",
        "url": "https://sspai.com/post/109463",
        "description": "Chrome extension that extracts design specs from any website into design.md. Built by indie dev with AI Skills integration. Helps developers and designers capture page design tokens quickly.",
        "topics": ["chrome extension", "design", "developer tool"],
        "mrr": 0, "profit": 0, "asking_price": 0, "paying_users": 0, "votes": 0, "has_revenue": True
    },
    {
        "source": "sspai", "market": "zh",
        "name": "SOLO Indie Developer Community",
        "url": "https://solo.xin",
        "description": "SOLO is a Chinese indie developer community at solo.xin. Author wiwi observes growing trend of developers building their own products, moving from side projects to full-time indie making.",
        "topics": ["indie hacker", "community", "china"],
        "mrr": 0, "profit": 0, "asking_price": 0, "paying_users": 0, "votes": 0, "has_revenue": True
    }
]

# HN Algolia results with parsed revenue signals
hn_revenue = [
    {
        "source": "hackernews", "market": "en",
        "name": "My First $500 MRR - My thoughts and learnings",
        "url": "https://news.ycombinator.com/item?id=44935238",
        "description": "First $500 monthly recurring revenue with a SaaS product. Lessons learned, marketing strategies, and technical decisions shared transparently.",
        "topics": ["saas", "indie hacker", "mrr"],
        "mrr": 500, "profit": 0, "asking_price": 0, "paying_users": 0, "votes": 44, "has_revenue": True
    },
    {
        "source": "hackernews", "market": "en",
        "name": "$2,600 MRR business in 6 months (two brothers)",
        "url": "https://news.ycombinator.com/item?id=43015308",
        "description": "Two brothers built a SaaS to $2,600 monthly recurring revenue within 6 months. Covers ideation, dev, launch, and growth tactics. Bootstrapped.",
        "topics": ["saas", "indie hacker", "mrr", "bootstrapped"],
        "mrr": 2600, "profit": 0, "asking_price": 0, "paying_users": 0, "votes": 1, "has_revenue": True
    },
    {
        "source": "hackernews", "market": "en",
        "name": "$18,000 in 7 months - what I did differently",
        "url": "https://news.ycombinator.com/item?id=44663347",
        "description": "Indie hacker made $18k revenue over 7 months (~$2,571/mo avg). Shares strategies that worked vs previous failed attempts.",
        "topics": ["indie hacker", "revenue", "saas"],
        "mrr": 2571, "profit": 0, "asking_price": 0, "paying_users": 0, "votes": 5, "has_revenue": True
    },
    {
        "source": "hackernews", "market": "en",
        "name": "6 months of my SaaS - real numbers, real mistakes",
        "url": "https://news.ycombinator.com/item?id=46523039",
        "description": "Transparent breakdown of 6 months running a SaaS: real revenue numbers, mistakes, churn rate, CAC. No sugarcoating.",
        "topics": ["saas", "revenue", "indie hacker"],
        "mrr": 0, "profit": 0, "asking_price": 0, "paying_users": 0, "votes": 2, "has_revenue": True
    },
    {
        "source": "hackernews", "market": "en",
        "name": "My first $10k internet dollars",
        "url": "https://news.ycombinator.com/item?id=36786480",
        "description": "Retrospective on earning first $10,000 from internet projects. Multiple products and revenue streams documented.",
        "topics": ["indie hacker", "revenue"],
        "mrr": 0, "profit": 10000, "asking_price": 0, "paying_users": 0, "votes": 97, "has_revenue": True
    },
    {
        "source": "hackernews", "market": "en",
        "name": "Selling Content Platform/SaaS at ~$50K MRR",
        "url": "https://news.ycombinator.com/item?id=34154870",
        "description": "Founder seeks advice on selling a content platform SaaS generating ~$50,000/month recurring revenue. High-value exit discussion.",
        "topics": ["saas", "exit", "mrr", "content platform"],
        "mrr": 50000, "profit": 0, "asking_price": 0, "paying_users": 0, "votes": 1, "has_revenue": True
    },
    {
        "source": "hackernews", "market": "en",
        "name": "Pixaras.com - Turnkey AI Image Generator SaaS (Flippa)",
        "url": "https://flippa.com/12017488-turnkey-ai-image-generator-saas-for-sale",
        "description": "Ready-to-launch AI image generator SaaS for sale on Flippa. Monetizable via ads or subscriptions. Full support and transfer included.",
        "topics": ["ai_tool", "saas", "flippa", "image generator"],
        "mrr": 0, "profit": 0, "asking_price": 0, "paying_users": 0, "votes": 2, "has_revenue": True
    },
    {
        "source": "hackernews", "market": "en",
        "name": "Muscula - JS Error Monitoring SaaS For Sale (Flippa)",
        "url": "https://flippa.com/3902524-muscula-saas-webapp-log-javascript-errors",
        "description": "Muscula SaaS for sale on Flippa. JavaScript error logging, used on millions of page views daily. Established developer tool with user base.",
        "topics": ["saas", "flippa", "developer tool", "error monitoring"],
        "mrr": 0, "profit": 0, "asking_price": 0, "paying_users": 0, "votes": 1, "has_revenue": True
    },
    {
        "source": "hackernews", "market": "en",
        "name": "Airbyte Agents - AI agent context across data sources",
        "url": "https://news.ycombinator.com/item?id=48023496",
        "description": "Airbyte launches agent framework for context across multiple data sources. 142 HN upvotes. AI tool for data-aware agents.",
        "topics": ["ai_tool", "api", "data", "agent"],
        "mrr": 0, "profit": 0, "asking_price": 0, "paying_users": 0, "votes": 142, "has_revenue": True
    },
    {
        "source": "hackernews", "market": "en",
        "name": "Spec27 - Spec-driven validation for AI agents",
        "url": "https://www.spec27.ai/launch",
        "description": "Tool for validating AI agent behavior against specifications. Developer tool for AI reliability testing. 13 HN upvotes.",
        "topics": ["ai_tool", "developer tool", "agent", "testing"],
        "mrr": 0, "profit": 0, "asking_price": 0, "paying_users": 0, "votes": 13, "has_revenue": True
    },
    {
        "source": "hackernews", "market": "en",
        "name": "Agent-desktop - Native desktop automation for AI agents",
        "url": "https://github.com/lahfir/agent-desktop",
        "description": "Open source CLI tool for AI agents to automate desktop tasks natively. 98 HN upvotes. GitHub open source project.",
        "topics": ["ai_tool", "open source", "automation", "agent"],
        "mrr": 0, "profit": 0, "asking_price": 0, "paying_users": 0, "votes": 98, "has_revenue": False
    },
    {
        "source": "hackernews", "market": "en",
        "name": "Yumi - AI workspace for chat, notes, and research",
        "url": "https://askyumi.app",
        "description": "All-in-one AI workspace combining chat, note-taking, and research capabilities. Productivity SaaS tool.",
        "topics": ["ai_tool", "productivity", "saas"],
        "mrr": 0, "profit": 0, "asking_price": 0, "paying_users": 0, "votes": 2, "has_revenue": False
    },
]

# Merge with dedup by URL
seen_urls = set()
merged = []

for item in existing:
    url = item.get('url', '')
    if url and url not in seen_urls:
        seen_urls.add(url)
        merged.append(item)

for item in hn_revenue + sspai_entries:
    url = item.get('url', '')
    if url and url not in seen_urls:
        seen_urls.add(url)
        merged.append(item)

# Parse revenue signals from descriptions
for item in merged:
    desc = (item.get('description', '') + ' ' + item.get('name', '')).lower()
    if item['mrr'] == 0:
        m = re.search(r'\$([\d,]+)k?\s*(?:/mo|/month|mrr|monthly|per month)', desc)
        if m:
            try:
                val = m.group(1).replace(',','')
                item['mrr'] = int(val) * (1000 if 'k' in m.group(0).lower() else 1)
                item['has_revenue'] = True
            except:
                pass
    if not item['has_revenue']:
        if any(kw in desc for kw in ['revenue', 'mrr', 'profitable', 'making $', 'earn $', 'income', 'for sale']):
            item['has_revenue'] = True

# Save
with open('数据抓取/2026-05-07_raw.json', 'w') as f:
    json.dump(merged, f, ensure_ascii=False, indent=2)

print(f"Merged: {len(merged)} items (was {len(existing)} + {len(hn_revenue) + len(sspai_entries)} new)")
print(f"Revenue signals: {sum(1 for x in merged if x['has_revenue'])}")
print(f"MRR > 0: {sum(1 for x in merged if x['mrr'] > 0)}")
for item in sorted(merged, key=lambda x: x['mrr'], reverse=True)[:5]:
    print(f"  ${item['mrr']:,}/mo - {item['name'][:70]}")
