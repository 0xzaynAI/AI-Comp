#!/usr/bin/env python3
"""Generate this week's raw data JSON from scraped results"""
import json
from datetime import date

today = date.today().isoformat()

entries = []

# === GITHUB (from star-history.com weekly Jun 27-Jul 3, 2026 + JQ blog) ===
github = [
    ("DietrichGebert/ponytail", "Anti-overengineering guardrail; pushes AI agents toward simplest implementation", 305,
     ["ai-agent", "code-review", "anti-overengineering"]),
    ("msitarzewski/agency-agents", "Framework for building AI agent agencies with structured collaboration", 286,
     ["ai-agent", "multi-agent", "agent-framework"]),
    ("Panniantong/Agent-Reach", "Multi-agent reachability and coordination framework", 205,
     ["ai-agent", "multi-agent", "coordination"]),
    ("mattpocock/skills", "TypeScript and engineering skills for AI coding agents", 205,
     ["ai-skills", "typescript", "agent-skills"]),
    ("simplex-chat/simplex-chat", "Private messenger without phone numbers, usernames, or user IDs; native mobile/desktop apps", 166,
     ["privacy", "messaging", "encryption", "p2p"]),
    ("usestrix/strix", "Open-source AI penetration testing with strict security boundaries", 158,
     ["security", "pentesting", "ai-agent", "open-source"]),
    ("obra/superpowers", "Agentic skills framework & software development methodology for Claude Code", 145,
     ["ai-agent", "agent-skills", "claude-code", "framework"]),
    ("NousResearch/hermes-agent", "Open-source agent framework by Nous Research", 135,
     ["ai-agent", "agent-framework", "llm", "open-source"]),
    ("multica-ai/andrej-karpathy-skills", "AI coding agent skills inspired by Andrej Karpathy's methodologies", 121,
     ["ai-skills", "agent-skills", "coding-agent"]),
    ("JCodesMore/ai-website-cloner-template", "Clone/rebuild existing website into modern codebase with one AI command", 111,
     ["ai-coding", "website-builder", "automation"]),
    ("firecrawl/firecrawl", "API for turning websites into LLM-ready markdown; web scraping for AI agents", 111,
     ["web-scraping", "ai", "api", "llm"]),
    ("farion1231/cc-switch", "Seamlessly switch between Claude Code and Codex in your workflow", 110,
     ["ai-coding", "claude-code", "codex", "developer-tools"]),
    ("JuliusBrussee/caveman", "Minimalist AI agent framework — strip away complexity for reliable agents", 109,
     ["ai-agent", "agent-framework", "minimalist"]),
    ("ZhuLinsen/daily_stock_analysis", "AI-powered daily stock market analysis and trading signals", 109,
     ["fintech", "stock-market", "ai", "trading"]),
    ("headroomlabs-ai/headroom", "AI agent headroom management — prevent context overflow in long agent sessions", 109,
     ["ai-agent", "context-management", "developer-tools"]),
    ("topoteretes/cognee", "Persistent memory and knowledge graphs for AI agents", 109,
     ["ai-agent", "knowledge-graph", "memory", "python"]),
    ("Leonxlnx/taste-skill", "Design taste and UI/UX evaluation skill for AI coding agents", 103,
     ["ai-skills", "design", "ui-ux", "agent-skills"]),
    ("xbtlin/ai-berkshire", "AI investing research framework using Buffett/Munger value-investing lenses with Claude Code/Codex", 0,
     ["fintech", "investing", "ai-agent", "value-investing"]),
    ("calesthio/OpenMontage", "Agentic video production combining agent workflows, stock footage, narration, music, subtitles", 0,
     ["video", "ai-agent", "content-creation", "automation"]),
    ("google-labs-code/design.md", "Design system specification format for describing visual identity and UI rules to AI coding agents", 0,
     ["design", "ai-agent", "specification", "ui"]),
    ("DeusData/codebase-memory-mcp", "Indexes codebases into persistent knowledge graph for AI agent querying via MCP", 0,
     ["mcp", "knowledge-graph", "ai-agent", "codebase"]),
    ("kunchenguid/no-mistakes", "Pre-push AI safety gate — AI review before code reaches team repo", 0,
     ["code-review", "ai-agent", "safety", "git"]),
    ("ripienaar/free-for-dev", "Curated list of free tiers for hosting, databases, auth, email, analytics — essential for bootstrappers", 0,
     ["dev-resources", "free-tier", "bootstrapping", "curated-list"]),
    ("stablyai/orca", "Desktop/mobile environment for running multiple AI coding agents in parallel", 0,
     ["ai-agent", "coding-agent", "parallel", "development"]),
    ("ChromeDevTools/chrome-devtools-mcp", "MCP server for Chrome DevTools — let AI agents inspect and control browser pages", 0,
     ["mcp", "chrome", "browser", "ai-agent", "developer-tools"]),
    ("immich-app/immich", "Self-hosted photo and video management solution — Google Photos alternative", 0,
     ["self-hosted", "photos", "privacy", "saas-alternative"]),
    ("agentskills/agentskills", "Community-driven repository of reusable AI agent skills", 0,
     ["ai-agent", "skills", "community", "agent-skills"]),
    ("elie222/inbox-zero", "Self-hostable AI email assistant to reach and maintain inbox zero", 0,
     ["email", "ai", "productivity", "self-hosted"]),
    ("browser-use/video-use", "Video editing with AI coding agents — automate video production workflows", 0,
     ["video", "ai-agent", "content-creation", "automation"]),
]

for name, desc, wg, topics in github:
    entries.append({
        "source": "github",
        "name": name,
        "url": f"https://github.com/{name}",
        "description": desc,
        "stars": 0,
        "weekly_growth": wg,
        "topics": topics
    })

# === PRODUCT HUNT (Week 27, Jun 29 – Jul 5, 2026) ===
producthunt = [
    ("Glaze by Raycast", "https://glaze.app", "Create your own Mac apps by chatting with AI — real apps in dock, instant launch, offline", 466,
     ["mac", "productivity", "artificial-intelligence", "no-code"]),
    ("Context.dev", "https://context.dev", "One API to scrape, enrich, and extract the internet for AI agents", 0,
     ["api", "ai", "data", "web-scraping"]),
    ("Acti", "https://acti.ai", "Agentic keyboard for mobile commands and search — AI-powered mobile productivity", 0,
     ["productivity", "custom-keyboards", "artificial-intelligence", "mobile"]),
    ("Fypro", "https://fypro.com", "Convert your TikTok followers into paying customers", 0,
     ["social-media", "e-commerce", "shopping", "tiktok"]),
    ("Cursor for iOS", "https://cursor.com/ios", "Build with AI coding agents from anywhere — mobile AI development", 0,
     ["ai", "development", "vibe-coding", "mobile"]),
    ("Agent Mode by Receiptor AI", "https://receiptor.ai", "Bookkeeping assistant that runs receipt workflows end-to-end with AI agents", 0,
     ["fintech", "ai", "accounting", "automation"]),
    ("Spira for Product Hunt Makers", "https://spira.ai", "Social media growth agents that build your launch momentum", 0,
     ["social-media", "marketing", "ai", "growth"]),
    ("Humalike", "https://humalike.com", "Give your AI agents the social intelligence they're missing — API for agent social skills", 0,
     ["api", "developer-tools", "artificial-intelligence", "ai-agent"]),
    ("Skills Marketplace by Databox", "https://databox.com", "Ready-made AI analytics skills for your business data", 0,
     ["analytics", "marketing", "ai", "business-intelligence"]),
    ("Tabstack Browser Automation", "https://tabstack.com", "Automate the web in your app or agent — no browser to host", 0,
     ["api", "developer-tools", "ai", "automation", "browser"]),
    ("Claude Sonnet 5", "https://anthropic.com", "AI that plans, acts, and gets work done — latest from Anthropic", 0,
     ["ai", "llm", "saas", "agentic-ai"]),
    ("Goals from Loops", "https://loops.so", "Measure whether your email campaign drove the desired outcome", 286,
     ["email", "email-marketing", "marketing", "analytics"]),
    ("ClinePass", "https://clinepass.com", "Run the best open-weights models in Cline — open-source AI copilot", 0,
     ["developer-tools", "ai", "open-source", "coding"]),
    ("Adam CAD Copilot", "https://adamcad.com", "AI CAD copilot inside Onshape and Fusion — AI-assisted mechanical design", 0,
     ["design-tools", "productivity", "ai", "cad"]),
    ("Tamamon", "https://tamamons.com", "Desktop pet that grows as you code with Claude Code — 20 species, evolves, reacts to weather", 244,
     ["mac", "productivity", "developer-tools", "games", "claude-code"]),
    ("Osloq", "https://osloq.com", "AI dev tool that actually runs your code — spins up sandbox, reproduces bugs with real evidence", 199,
     ["developer-tools", "ai", "testing", "qa", "github"]),
    ("Archify", "https://archify.salahxd.dev", "See components, APIs, libraries — understand application behavior directly in browser", 178,
     ["chrome-extensions", "developer-tools", "architecture", "visualization"]),
    ("nxt", "https://nxt.do", "AI task manager you talk to like a human assistant — brain-dump in plain language", 145,
     ["productivity", "task-management", "ai", "personal-assistant"]),
    ("Vox", "https://aasis21.github.io/vox", "Voice in, voice out with GitHub Copilot — speak to your AI coding agent", 139,
     ["developer-tools", "ai", "voice", "github-copilot"]),
    ("Sequence Agentic", "https://sequence.ai", "Money movement for AI agents — fintech API for agentic payments", 0,
     ["fintech", "api", "artificial-intelligence", "payments"]),
    ("OASIS 1 Ring", "https://oasisring.com", "Whisper to write and touch to edit — voice-first wearable productivity", 0,
     ["productivity", "ai", "voice", "wearable"]),
]

for name, url, desc, upvotes, topics in producthunt:
    entries.append({
        "source": "producthunt",
        "name": name,
        "url": url,
        "description": desc,
        "stars": 0,
        "weekly_growth": 0,
        "upvotes": upvotes,
        "topics": topics
    })

# === HACKER NEWS Show HN (current page + bestofshowhn.com recent) ===
hackernews = [
    ("Mcpsnoop", "https://github.com/kerlenton/mcpsnoop", "Wireshark for MCP — transparent proxy and live TUI for debugging MCP communications", 61,
     ["mcp", "debugging", "developer-tools", "proxy", "tui"]),
    ("Bramble", "https://bramble.app", "Local-first password manager — privacy-first credential management", 129,
     ["security", "password-manager", "privacy", "local-first"]),
    ("Graph Paper Generator", "https://graphpaper.app", "Vector PDF graph paper generator — create custom grids directly in browser", 106,
     ["design", "productivity", "pdf", "browser"]),
    ("Slopo", "https://slopo.dev", "CLI for non-exact code duplication detection using embedding models", 91,
     ["code-analysis", "cli", "embeddings", "developer-tools"]),
    ("Inkwell", "https://inkwell.app", "RSS reader designed for e-ink devices — distraction-free reading", 75,
     ["rss", "e-ink", "reading", "minimalist"]),
    ("zkGolf", "https://zkgolf.com", "Competitive optimization of formally verified circuits — puzzle game for cryptographers", 69,
     ["cryptography", "zero-knowledge", "game", "optimization"]),
    ("ctx", "https://ctx.dev", "Search your AI coding agent's history — find past conversations and generated code", 42,
     ["ai-coding", "search", "productivity", "developer-tools"]),
    ("Claudoro", "https://github.com/claudoro", "Pomodoro timer embedded in Claude Code statusline — timebox your AI coding sessions", 35,
     ["productivity", "pomodoro", "claude-code", "time-management"]),
    ("File Organizer 2000", "https://fileorganizer2000.com", "AI-powered local file organizer — automatically sort, tag, and rename files", 0,
     ["productivity", "file-management", "ai", "local-first"]),
    ("Tolaria", "https://tolaria.app", "Open-source macOS app for Markdown knowledge bases — Obsidian alternative built in Rust", 318,
     ["knowledge-management", "markdown", "macos", "open-source", "note-taking"]),
    ("Files.md", "https://files.md", "Open-source alternative to Obsidian — Markdown-based knowledge management", 730,
     ["knowledge-management", "markdown", "open-source", "note-taking"]),
    ("HackerNewsTrends", "https://hntrends.com", "Google Trends for Hacker News — indexed 18 years of comments to surface trending topics", 812,
     ["data", "analytics", "hacker-news", "trends", "visualization"]),
]

for name, url, desc, upvotes, topics in hackernews:
    entries.append({
        "source": "hackernews",
        "name": name,
        "url": url,
        "description": desc,
        "stars": 0,
        "weekly_growth": 0,
        "upvotes": upvotes,
        "topics": topics
    })

path = f"/Users/lennyz/github/AI-Comp/09_开源商机/数据抓取/{today}_raw.json"
with open(path, "w") as f:
    json.dump(entries, f, ensure_ascii=False, indent=2)

print(f"✅ Saved {len(entries)} entries to {path}")
print(f"   GitHub: {sum(1 for e in entries if e['source']=='github')}")
print(f"   Product Hunt: {sum(1 for e in entries if e['source']=='producthunt')}")
print(f"   Hacker News: {sum(1 for e in entries if e['source']=='hackernews')}")
