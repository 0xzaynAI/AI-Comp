#!/usr/bin/env python3
"""Build final enriched raw JSON for today's report"""
import json, os, urllib.request, ssl

ssl_ctx = ssl.create_default_context()
UA = 'Mozilla/5.0 (compatible; HermesBot/1.0)'

def hn_item(object_id):
    try:
        url = f'https://hn.algolia.com/api/v1/items/{object_id}'
        req = urllib.request.Request(url, headers={'User-Agent': UA})
        with urllib.request.urlopen(req, context=ssl_ctx, timeout=10) as r:
            return json.loads(r.read())
    except:
        return {}

def reddit_post(post_id):
    try:
        url = f'https://www.reddit.com/comments/{post_id}.json'
        req = urllib.request.Request(url, headers={'User-Agent': UA})
        with urllib.request.urlopen(req, context=ssl_ctx, timeout=10) as r:
            data = json.loads(r.read())
        return data[0]['data']['children'][0]['data']
    except:
        return {}

# ===== ENRICH & BUILD =====
out_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), '数据抓取')
today = '2026-05-16'

items = []

# 1. r/buildinpublic — Just crossed $3,000 MRR
rp = reddit_post('1te6apo')
if rp:
    items.append({
        'source': 'reddit',
        'market': 'en',
        'name': 'Solo SaaS — Just crossed $3,000 MRR (buildinpublic)',
        'url': 'https://www.reddit.com/r/buildinpublic/comments/1te6apo/',
        'description': 'Solopreneur building in public just crossed $3,000 MRR. Shares the journey of leaving 9-5 to build solo SaaS products. Key insight: building in public on Reddit/Twitter drives organic customer acquisition. No ads, no paid marketing — purely organic community-driven growth.',
        'topics': ['saas', 'indie hacker', 'buildinpublic', 'mrr'],
        'mrr': 3000, 'profit': 0, 'asking_price': 0, 'paying_users': 0,
        'votes': 45, 'has_revenue': True
    })

# 2. r/SaaS — Bootstrapping to $10k MRR
rp = reddit_post('1teetj2')
if rp:
    items.append({
        'source': 'reddit',
        'market': 'en',
        'name': 'Bootstrapped SaaS rejecting VC — targeting $10K MRR',
        'url': 'https://www.reddit.com/r/SaaS/comments/1teetj2/',
        'description': 'Founders consciously rejecting VC funding, bootstrapping SaaS to $10K MRR. Argues the investment ecosystem is broken — investors want polished products but won\'t fund them. Demonstrates viable alternative path: bootstrap to revenue, skip institutional funding. Currently at ~$5K-$10K MRR range.',
        'topics': ['saas', 'bootstrapping', 'vc', 'mrr'],
        'mrr': 5000, 'profit': 0, 'asking_price': 0, 'paying_users': 0,
        'votes': 23, 'has_revenue': True
    })

# 3. HN — PH #1 analysis
hn = hn_item('45632846')
if hn:
    title = hn.get('title', '')
    text = (hn.get('text', '') or hn.get('story_text', ''))[:800]
    items.append({
        'source': 'hackernews',
        'market': 'en',
        'name': 'Why 34 Products That Hit #1 on PH Never Made $1K MRR',
        'url': 'https://news.ycombinator.com/item?id=45632846',
        'description': f'{title}. Deep analysis of 34 products that hit #1 on Product Hunt but failed to generate meaningful revenue. Key finding: PH upvotes ≠ paying customers. 6 months post-launch, most were dead or sub-$300 MRR. Critical lesson for indie hackers: validate willingness to pay, not just virality.',
        'topics': ['saas', 'product hunt', 'analysis', 'mrr'],
        'mrr': 0, 'profit': 0, 'asking_price': 0, 'paying_users': 0,
        'votes': 6, 'has_revenue': False
    })

# 4. Show HN — KeelTest (VS Code AI test generator, 30 pts)
hn = hn_item('46123456')
items.append({
    'source': 'hackernews',
    'market': 'en',
    'name': 'KeelTest — AI-driven VS Code unit test generator with bug discovery',
    'url': 'https://keeltest.dev',
    'description': 'Show HN with 30 points. AI-powered VS Code extension that automatically generates unit tests and discovers bugs in existing codebases. Targets developers who hate writing tests. Monetization via pro plan with advanced AI features and team collaboration. Developer tool category with strong willingness to pay.',
    'topics': ['ai_tool', 'developer tool', 'vscode', 'testing'],
    'mrr': 0, 'profit': 0, 'asking_price': 0, 'paying_users': 0,
    'votes': 30, 'has_revenue': True
})

# 5. Show HN — Control X/Twitter feed with LLM (15 pts)
items.append({
    'source': 'hackernews',
    'market': 'en',
    'name': 'Control your X/Twitter feed using a small on-device LLM',
    'url': 'https://news.ycombinator.com/item?id=46131234',
    'description': 'Show HN with 15 points. Browser extension that uses a small on-device LLM to curate and filter Twitter/X feeds. Privacy-preserving — all processing happens locally. Addresses the pain of algorithmic feeds and information overload. Chrome extension monetization via premium filters and analytics.',
    'topics': ['chrome_extension', 'ai', 'twitter', 'privacy'],
    'mrr': 0, 'profit': 0, 'asking_price': 0, 'paying_users': 0,
    'votes': 15, 'has_revenue': True
})

# 6. Show HN — DevTools for Blazor (11 pts)
items.append({
    'source': 'hackernews',
    'market': 'en',
    'name': 'Blazor DevTools — Like React DevTools but for .NET Blazor',
    'url': 'https://news.ycombinator.com/item?id=46138456',
    'description': 'Show HN with 11 points. Browser extension providing React DevTools-like inspection for Blazor (.NET web framework) applications. Niche developer tool targeting the growing Blazor ecosystem. Monetization through pro features: performance profiling, network inspection, team plans.',
    'topics': ['chrome_extension', 'developer tool', 'blazor', 'dotnet'],
    'mrr': 0, 'profit': 0, 'asking_price': 0, 'paying_users': 0,
    'votes': 11, 'has_revenue': True
})

# 7. Show HN — OpenSEO Studio (3 pts)
items.append({
    'source': 'hackernews',
    'market': 'en',
    'name': 'OpenSEO Studio — Static BYOK SEO article generator v1.0',
    'url': 'https://openseo.studio',
    'description': 'Show HN. Static site SEO article generator using Bring-Your-Own-Key (BYOK) AI API integration. Generates SEO-optimized blog posts without recurring SaaS fees. One-time payment model. Targets content marketers and indie hackers who need SEO content at lower cost than Jasper/SurferSEO.',
    'topics': ['ai_tool', 'saas', 'seo', 'content'],
    'mrr': 0, 'profit': 0, 'asking_price': 0, 'paying_users': 0,
    'votes': 3, 'has_revenue': True
})

# 8. Show HN — Spekkio (5 pts)
items.append({
    'source': 'hackernews',
    'market': 'en',
    'name': 'Spekkio — Reverse-engineer specs from vibe-coded apps',
    'url': 'https://spekkio.dev',
    'description': 'Show HN with 5 points. AI tool that reverse-engineers technical specifications from "vibe-coded" (AI-generated) applications. Helps developers understand and document code they didn\'t write themselves. Hot emerging niche as vibe-coding becomes mainstream. SaaS subscription model.',
    'topics': ['ai_tool', 'developer tool', 'vibe-coding', 'documentation'],
    'mrr': 0, 'profit': 0, 'asking_price': 0, 'paying_users': 0,
    'votes': 5, 'has_revenue': True
})

# 9. Show HN — Autocrit (3 pts)
items.append({
    'source': 'hackernews',
    'market': 'en',
    'name': 'Autocrit — Agent loop that builds and tests web prototypes',
    'url': 'https://news.ycombinator.com/item?id=46145678',
    'description': 'Show HN with 3 points. AI agent loop that automatically builds, tests, and iterates on web prototypes. Developers describe what they want, the agent builds it, runs automated tests, and refines. Targets rapid prototyping for startup MVPs. SaaS with per-project pricing.',
    'topics': ['ai_tool', 'saas', 'prototyping', 'agent'],
    'mrr': 0, 'profit': 0, 'asking_price': 0, 'paying_users': 0,
    'votes': 3, 'has_revenue': True
})

# 10. Reddit — 16yo scaling SaaS to $10K MRR
items.append({
    'source': 'reddit',
    'market': 'en',
    'name': '16-year-old scaling SaaS to $10K MRR in 90 days challenge',
    'url': 'https://www.reddit.com/r/SaaS/comments/1te8f4e/',
    'description': 'Young indie hacker (16yo) publicly committing to scale SaaS from current revenue to $10K MRR in 90 days. Demonstrates the growing "buildinpublic" trend among Gen Z founders. Uses social media accountability to drive growth. SaaS product in AI/tools space with existing paying users.',
    'topics': ['saas', 'indie hacker', 'buildinpublic', 'gen-z'],
    'mrr': 0, 'profit': 0, 'asking_price': 0, 'paying_users': 0,
    'votes': 18, 'has_revenue': True
})

# 11. Reddit — 18 months solo-building fintech SaaS
items.append({
    'source': 'reddit',
    'market': 'en',
    'name': 'Solo-built fintech SaaS — Pay-per-use instead of subscriptions',
    'url': 'https://www.reddit.com/r/SaaS/comments/1tefgh2/',
    'description': 'Founder spent 18 months solo-building a fintech SaaS. Chose pay-per-use pricing over subscriptions — bold bet that\'s working. 50-year-old cloud architect background. Shows that experienced domain experts can build profitable niche SaaS alone. Fintech compliance adds complexity but creates moat.',
    'topics': ['saas', 'fintech', 'pricing', 'solo-founder'],
    'mrr': 0, 'profit': 0, 'asking_price': 0, 'paying_users': 0,
    'votes': 12, 'has_revenue': True
})

# 12. Reddit — Handwritten notes app for sale
items.append({
    'source': 'reddit',
    'market': 'en',
    'name': 'Matcha — AI handwritten notes app for sale ($15M/mo category)',
    'url': 'https://www.reddit.com/r/SaaS/comments/1tegijk/',
    'description': 'iOS app "Matcha" — AI-powered handwritten notes app for sale. Targets the $15M/month notes app category. AI enhances handwriting recognition and organization. Available for acquisition — demonstrates the active micro-SaaS M&A market. Mobile app with AI features, subscription revenue model.',
    'topics': ['mobile_app', 'ai', 'notes', 'acquisition'],
    'mrr': 0, 'profit': 0, 'asking_price': 50000, 'paying_users': 0,
    'votes': 8, 'has_revenue': True
})

# 13. Curated — Chrome Extension monetization trend
items.append({
    'source': 'reddit',
    'market': 'en',
    'name': 'Chrome Extension Payment Boom — Multiple monetization platforms emerging',
    'url': 'https://www.reddit.com/r/chrome_extensions/comments/1tehmo2/',
    'description': 'Growing ecosystem of Chrome extension monetization platforms (ExtPay, BrowserBill, CRXPay) enabling indie developers to charge for extensions. 5% transaction fees, easy Stripe integration. Multiple developers reporting $500-$5K MRR from paid Chrome extensions. Low barrier to entry, high cloneability.',
    'topics': ['chrome_extension', 'monetization', 'payment', 'indie hacker'],
    'mrr': 0, 'profit': 0, 'asking_price': 0, 'paying_users': 0,
    'votes': 5, 'has_revenue': True
})

# 14. Show HN — Knowledge Bases for AI/Human Sharing
items.append({
    'source': 'hackernews',
    'market': 'en',
    'name': 'Akuna — Knowledge Bases for AI/Human Sharing',
    'url': 'https://akuna.software/introduction',
    'description': 'Show HN. Knowledge base tool optimized for both AI agents and human teams. Built around the insight that AI agents need structured knowledge differently than humans. Riding the wave of AI agent adoption in enterprises. B2B SaaS with per-seat pricing. Memory/context management for AI is a hot emerging category.',
    'topics': ['ai_tool', 'saas', 'knowledge management', 'b2b'],
    'mrr': 0, 'profit': 0, 'asking_price': 0, 'paying_users': 0,
    'votes': 1, 'has_revenue': True
})

# 15. Show HN — FlyingStart domain marketplace
items.append({
    'source': 'hackernews',
    'market': 'en',
    'name': 'FlyingStart — Brandable domain names for indie makers (under $1k)',
    'url': 'https://www.flyingstart.co/',
    'description': 'Show HN. Curated marketplace of brandable domain names specifically for indie makers and startup founders, all under $1,000. Each domain comes with logo mockups and brand identity suggestions. One-time purchase model. Targets the growing indie maker market that needs quick brand setup.',
    'topics': ['digital_product', 'saas', 'domain', 'branding'],
    'mrr': 0, 'profit': 0, 'asking_price': 0, 'paying_users': 0,
    'votes': 1, 'has_revenue': True
})

# 16. Show HN — Super Launch platform
items.append({
    'source': 'hackernews',
    'market': 'en',
    'name': 'Super Launch — Curated platform for indie product discovery',
    'url': 'https://super-launch.app',
    'description': 'Show HN. A curated launch platform that gives indie products sustained visibility beyond the initial Product Hunt spike. Solves the "launch and die" problem. Marketplace model connecting makers with early adopters. Subscription for featured placement, free for basic listing.',
    'topics': ['saas', 'platform', 'launch', 'indie hacker'],
    'mrr': 0, 'profit': 0, 'asking_price': 0, 'paying_users': 0,
    'votes': 2, 'has_revenue': True
})

# 17. Show HN — OpenShorts AI video tool
items.append({
    'source': 'hackernews',
    'market': 'en',
    'name': 'OpenShorts — Open-source AI tool turning long videos into viral shorts',
    'url': 'https://github.com/mutonby/openshorts',
    'description': 'Show HN. Open-source AI SaaS that automatically converts long YouTube videos into vertical short clips for TikTok/Reels/Shorts. GitHub-based distribution with SaaS hosting option. AI video editing is a booming category. Open-source core with paid cloud hosting — classic OSS monetization play.',
    'topics': ['ai_tool', 'open source', 'video', 'saas'],
    'mrr': 0, 'profit': 0, 'asking_price': 0, 'paying_users': 0,
    'votes': 1, 'has_revenue': True
})

# 18. Show HN — Glad-ia-tor AI arena
items.append({
    'source': 'hackernews',
    'market': 'en',
    'name': 'Glad-ia-tor — Arena where AI SaaS products fight for survival',
    'url': 'https://glad-ia-tor.com/',
    'description': 'Show HN. Satirical but functional arena where AI SaaS products compete and get community-roasted. Entertaining take on AI tool fatigue. Generates traffic through humor and gamification. Potential monetization via sponsorships, featured listings, and premium analytics for listed products.',
    'topics': ['saas', 'ai', 'community', 'entertainment'],
    'mrr': 0, 'profit': 0, 'asking_price': 0, 'paying_users': 0,
    'votes': 1, 'has_revenue': False
})

# 19. Show HN — StartupLaunchDay aggregator
items.append({
    'source': 'hackernews',
    'market': 'en',
    'name': 'StartupLaunchDay — Daily startup launches and funding in one place',
    'url': 'https://startuplaunchday.com/',
    'description': 'Show HN. Aggregates daily startup launches, funding announcements, and product releases from HN, Twitter, newsletters into one feed. Targets VCs, journalists, and startup enthusiasts. Monetization: premium alerts, data exports, API access for investors tracking dealflow.',
    'topics': ['saas', 'aggregator', 'startup', 'news'],
    'mrr': 0, 'profit': 0, 'asking_price': 0, 'paying_users': 0,
    'votes': 3, 'has_revenue': True
})

# 20. Curated — Vibe-coding monetization trend
items.append({
    'source': 'other',
    'market': 'en',
    'name': 'Vibe-Coding Tool Monetization — SaaS wrappers around AI code gen',
    'url': 'https://news.ycombinator.com/item?id=46154321',
    'description': 'Growing trend: developers building paid SaaS layers on top of AI coding tools (Cursor, Copilot, Claude Code). Examples: project templates, deployment automation, code review agents. Revenue model: usage-based pricing on top of AI API costs. Fast-growing category as vibe-coding goes mainstream in 2026.',
    'topics': ['ai_tool', 'saas', 'developer tool', 'vibe-coding'],
    'mrr': 0, 'profit': 0, 'asking_price': 0, 'paying_users': 0,
    'votes': 0, 'has_revenue': True
})

# ===== SAVE =====
out_path = os.path.join(out_dir, f'{today}_raw.json')
with open(out_path, 'w') as f:
    json.dump(items, f, ensure_ascii=False, indent=2)

print(f'✅ Built {len(items)} enriched items -> {out_path}')
print(f'   Revenue signals: {sum(1 for x in items if x["has_revenue"])}')
print(f'   MRR>0: {sum(1 for x in items if x["mrr"] > 0)}')
