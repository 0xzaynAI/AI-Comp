#!/usr/bin/env python3
"""
开源商机过滤器 + 分析引擎
用法: python filter_analyze.py <raw_data.json> <output_dir>
输入: 从 GitHub Trending / Product Hunt / HN Show HN 抓取的原始 JSON
输出: 过滤后的候选项目 Markdown 文件

过滤规则（排除噪音）:
  - 排除: 编程语言、框架、论文复现、纯 CLI 工具、面向开发者的 infra
  - 保留: 面向非开发者的工具、AI+垂直场景、数据/可视化、内容创作
"""

import json
import sys
import os
from datetime import datetime
from dataclasses import dataclass, field, asdict
from typing import Optional

# ==================== 分类标签 ====================
CATEGORIES = {
    "infra_oss": "基础设施/开源框架",       # ❌ 排除
    "dev_tool": "开发者工具",              # ❌ 排除
    "cli_tool": "CLI 工具",               # ❌ 排除
    "lang_framework": "编程语言/框架",     # ❌ 排除
    "paper_impl": "论文复现",              # ❌ 排除
    "ai_app": "AI 应用层",                # ✅ 保留
    "vertical_ai": "AI+垂直场景",         # ✅ 保留
    "saas_alt": "SaaS 替代品",            # ✅ 保留
    "tool_nondev": "非开发者工具",         # ✅ 保留
    "data_viz": "数据/可视化",            # ✅ 保留
    "content_creation": "内容创作",        # ✅ 保留
    "productivity": "生产力工具",          # ✅ 保留
    "consumer": "消费者工具",             # ✅ 保留
    "fintech": "金融科技",                # ✅ 保留
    "health": "健康/医疗",               # ✅ 保留
    "education": "教育/学习",             # ✅ 保留
}

# ✅ 应该保留的类别
KEEP_CATEGORIES = {
    "ai_app", "vertical_ai", "saas_alt", "tool_nondev",
    "data_viz", "content_creation", "productivity", "consumer",
    "fintech", "health", "education"
}

# ❌ 应该过滤的关键词（标题/描述中包含）
EXCLUDE_KEYWORDS = [
    "cli", "terminal", "framework", "library", "sdk", "api client",
    "npm package", "pip install", "rust crate", "golang", "compiler",
    "programming language", "vim", "neovim", "plugin", "extension",
    "docker", "kubernetes", "devops", "ci/cd", "github action",
    "linter", "formatter", "typescript", "javascript", "python package",
    "css framework", "react component", "vue component",
    "blockchain protocol", "smart contract", "crypto wallet",
    "论文", "paper", "arxiv", "research code", "benchmark",
    "llm training", "fine-tuning", "inference engine",
    "vector database", "embedding model", "tokenizer",
]

# ✅ 应鼓励的关键词
INCLUDE_KEYWORDS = [
    "saas", "nocode", "no-code", "lowcode", "low-code",
    "alternative to", "replacement for", "self-hosted",
    "ai powered", "ai assistant", "ai writer", "ai editor",
    "photo editor", "video editor", "image generator",
    "content creator", "social media", "marketing",
    "analytics", "dashboard", "visualization",
    "productivity", "notes", "writing", "reading",
    "learning", "education", "course", "study",
    "health", "fitness", "wellness",
    "finance", "trading", "investing", "budget",
    "design", "prototype", "mockup", "presentation",
    "file organizer", "automation", "workflow",
    "menu bar", "desktop app", "mac app",
    "browser extension", "chrome extension",
]


@dataclass
class ProjectCandidate:
    """候选项目数据结构"""
    name: str
    source: str  # github / producthunt / hackernews
    url: str
    description: str
    stars: int = 0
    weekly_growth: int = 0
    upvotes: int = 0
    language: str = ""
    topics: list = field(default_factory=list)
    category: str = "unknown"
    keep: bool = False
    keep_reason: str = ""

    # 分析字段
    problem_solved: str = ""
    target_user: str = ""
    willingness_to_pay: str = ""  # $/月 估计
    mvp_feasibility: str = ""  # 1周MVP评估
    competitors: list = field(default_factory=list)
    commercial_license: str = ""  # Apache 2.0 / MIT / GPL 等


def classify_project(proj: dict) -> str:
    """根据项目名称、描述、主题标签自动分类"""
    name = (proj.get("name") or proj.get("title") or "").lower()
    desc = (proj.get("description") or proj.get("tagline") or "").lower()
    topics_str = " ".join(proj.get("topics", [])).lower()
    all_text = f"{name} {desc} {topics_str}"

    # 从 topics 快速判断
    if "fintech" in topics_str or "trading" in topics_str:
        return "fintech"
    if any(t in topics_str for t in ["education", "learning", "study"]):
        return "education"
    if any(t in topics_str for t in ["health", "fitness", "medical"]):
        return "health"
    if any(t in topics_str for t in ["design", "photo", "video", "content-creation", "presentation"]):
        return "content_creation"
    if any(t in topics_str for t in ["consumer", "social", "dating", "travel"]):
        return "consumer"
    if any(t in topics_str for t in ["productivity", "file-management", "bookmark", "notes"]):
        return "tool_nondev"
    if any(t in topics_str for t in ["saas", "nocode", "no-code", "messaging", "business"]):
        return "saas_alt"
    if "privacy" in topics_str and "api" in topics_str:
        return "saas_alt"  # privacy tools as potential SaaS

    # 文本分析
    # AI+垂直场景（priority: check before generic AI）
    if any(kw in all_text for kw in ["trading agent", "financial trading", "stock market"]):
        return "fintech"
    if any(kw in all_text for kw in ["health data", "personal health", "patient", "medical record"]):
        return "health"
    if any(kw in all_text for kw in ["personalized learning", "ai learning", "study tool", "flashcard",
                                       "online course", "udemy", "hotmart"]):
        return "education"
    if any(kw in all_text for kw in ["photo editor", "video editor", "image generator", "presentation tool",
                                       "design tool", "prototype builder", "promo screenshots"]):
        return "content_creation"
    if any(kw in all_text for kw in ["build business", "by texting", "nocode business", "no-code business"]):
        return "saas_alt"

    # AI 应用层（generic AI tools for non-devs）
    if any(kw in all_text for kw in ["ai powered", "with ai", "ai assistant", "ai writer", "ai tool",
                                       "personal ai", "ai agent that", "copilot"]):
        if not any(kw in all_text for kw in ["coding", "developer", "programming", "cli", "terminal", "framework"]):
            return "ai_app"

    # SaaS 替代品
    if any(kw in all_text for kw in ["alternative to", "replacement for", "self-hosted"]):
        if not any(kw in all_text for kw in ["coding", "developer", "cli", "terminal"]):
            return "saas_alt"

    # 非开发者工具
    if any(kw in all_text for kw in ["menu bar", "desktop app", "mac app",
                                       "browser extension", "chrome extension",
                                       "screenshot tool", "file organizer", "file sharing",
                                       "bookmark", "pomodoro", "timer"]):
        return "tool_nondev"

    # 生产力
    if any(kw in all_text for kw in ["productivity tool", "workflow", "automation platform"]):
        return "productivity"

    # 数据/可视化
    if any(kw in all_text for kw in ["dashboard", "analytics", "visualization", "chart", "graph",
                                       "calculator"]):
        return "data_viz"

    # 消费者工具
    if any(kw in all_text for kw in ["matchmaking", "dating", "relationship", "track relation",
                                       "social", "travel", "trip", "reading", "e-ink"]):
        return "consumer"

    # 排除类（最后检查，不覆盖上面的分类）
    if any(kw in all_text for kw in ["web scraping framework", "scraping framework"]):
        return "dev_tool"
    if any(kw in all_text for kw in ["cli", "command line", "terminal emulator"]):
        return "cli_tool"
    if any(kw in all_text for kw in ["programming language", "compiler", "runtime"]):
        return "lang_framework"
    if any(kw in all_text for kw in ["developer tool", "coding interview", "build your own",
                                       "issue tracker", "git"]):
        return "dev_tool"
    if any(kw in all_text for kw in ["docker", "kubernetes", "devops", "server orchestration"]):
        return "infra_oss"
    if any(kw in all_text for kw in ["paper", "arxiv", "research code", "benchmark", "llm training"]):
        return "paper_impl"
    if any(kw in all_text for kw in ["agentic skills framework", "agent orchestration", "agent swarm",
                                       "software development methodology", "improve claude code",
                                       "coding pitfalls", "claude.md", "skills for real engineers"]):
        return "dev_tool"

    return "unknown"


def should_keep(proj: dict, category: str) -> tuple[bool, str]:
    """判断是否保留项目"""
    name = (proj.get("name") or proj.get("title") or "").lower()
    desc = (proj.get("description") or proj.get("tagline") or "").lower()
    all_text = f"{name} {desc}"

    # 类别过滤
    if category in KEEP_CATEGORIES:
        # 二次关键词过滤（但"framework"在 fintech/ai_app 等上下文中不排除）
        context_sensitive_exclude = [kw for kw in EXCLUDE_KEYWORDS if kw != "framework"]
        for kw in context_sensitive_exclude:
            if kw in all_text:
                return False, f"排除关键词匹配: '{kw}'"
        # "framework" 只在非商业类别中排除
        if "framework" in all_text and category not in ["fintech", "ai_app", "saas_alt", "vertical_ai"]:
            return False, "排除关键词匹配: 'framework'"

        for kw in INCLUDE_KEYWORDS:
            if kw in all_text:
                return True, f"包含鼓励关键词: '{kw}'"
        return True, f"类别符合: {CATEGORIES.get(category, category)}"

    return False, f"排除类别: {CATEGORIES.get(category, category)}"


def analyze_candidate(candidate: ProjectCandidate):
    """填充分析字段"""
    desc = (candidate.description or "").lower()
    name = candidate.name.lower()

    # 问题与用户推断
    problem_map = {
        "photo": ("非专业用户需要简单易用的图片处理工具", "普通用户/内容创作者"),
        "video": ("视频创作者需要高效的剪辑工具", "视频创作者/自媒体"),
        "design": ("非设计师需要快速出图/出原型的工具", "创业者/产品经理/营销人员"),
        "learn": ("学习者需要个性化的学习辅助", "学生/自学者"),
        "study": ("学习者需要高效的学习工具", "学生/自学者"),
        "trading": ("个人投资者需要专业的交易分析工具", "个人投资者/交易员"),
        "finance": ("用户需要更好的个人财务管理", "普通用户"),
        "health": ("用户需要追踪和管理个人健康数据", "普通用户/健康关注者"),
        "file": ("用户文件越来越多，需要智能整理", "普通用户/办公人员"),
        "note": ("用户需要更好的笔记和知识管理", "知识工作者/学生"),
        "productivity": ("用户需要提升工作效率的工具", "知识工作者/自由职业者"),
        "pomodoro": ("用户需要专注时间管理工具", "所有电脑用户"),
        "presentation": ("用户需要快速制作演示文稿", "职场人士/教育者"),
        "write": ("内容创作者需要AI辅助写作", "内容创作者/营销人员"),
        "read": ("用户需要更好的阅读体验", "读者/研究者"),
        "organize": ("用户需要智能整理数字资产", "普通用户/创作者"),
        "social": ("用户需要管理社交关系", "普通用户"),
        "bookmark": ("团队需要更好的书签和链接管理", "团队/知识工作者"),
        "text": ("用户需要基于文本完成商业操作", "小商家/创业者"),
        "analy": ("用户需要更简单的数据分析工具", "业务人员/分析师"),
    }

    candidate.problem_solved = ""
    candidate.target_user = ""
    for kw, (problem, user) in problem_map.items():
        if kw in desc or kw in name:
            candidate.problem_solved = problem
            candidate.target_user = user
            break

    if not candidate.problem_solved:
        candidate.problem_solved = "待进一步调研确定"
        candidate.target_user = "待进一步调研确定"

    # 付费意愿估计
    pay_map = {
        "trading": "$20-50/月（金融工具付费意愿强）",
        "finance": "$10-30/月",
        "health": "$10-25/月",
        "design": "$10-30/月",
        "photo": "$5-15/月",
        "video": "$10-30/月",
        "learn": "$10-25/月",
        "study": "$5-15/月",
        "productivity": "$5-15/月",
        "presentation": "$10-25/月",
        "write": "$5-20/月",
        "file": "$3-10/月",
        "organize": "$3-10/月",
        "social": "$5-15/月",
    }
    candidate.willingness_to_pay = "待评估"
    for kw, estimate in pay_map.items():
        if kw in desc or kw in name:
            candidate.willingness_to_pay = estimate
            break

    # MVP 可行性
    candidate.mvp_feasibility = "✅ 1周内可实现核心功能 MVP" if candidate.target_user != "待进一步调研确定" else "⚠️ 需进一步调研后评估"


def process_raw_data(raw_projects: list) -> list[ProjectCandidate]:
    """主处理流程"""
    candidates = []

    for proj in raw_projects:
        source = proj.get("source", "unknown")
        url = proj.get("url", "")
        name = proj.get("name") or proj.get("title") or "unknown"

        candidate = ProjectCandidate(
            name=name,
            source=source,
            url=url,
            description=proj.get("description") or proj.get("tagline") or "",
            stars=proj.get("stars", 0),
            weekly_growth=proj.get("weekly_growth", 0),
            upvotes=proj.get("upvotes", 0),
            language=proj.get("language", ""),
            topics=proj.get("topics", []),
        )

        # 1. 分类
        candidate.category = classify_project(proj)

        # 2. 过滤
        candidate.keep, candidate.keep_reason = should_keep(proj, candidate.category)

        if candidate.keep:
            # 3. 分析
            analyze_candidate(candidate)

        candidates.append(candidate)

    return candidates


def generate_markdown(candidates: list[ProjectCandidate], output_path: str):
    """生成 Markdown 格式的候选项目报告"""
    kept = [c for c in candidates if c.keep]
    excluded = [c for c in candidates if not c.keep]

    now = datetime.now().strftime("%Y-%m-%d")

    lines = [
        f"# 开源商机周报 — {now}",
        "",
        f"> 自动抓取 | 数据源: GitHub Trending + Product Hunt + Hacker News Show HN",
        f"> 候选项目: {len(kept)} | 已过滤: {len(excluded)}",
        "",
        "---",
        "",
        "## 📊 概览",
        "",
        f"| 指标 | 数值 |",
        f"|------|------|",
        f"| 原始项目数 | {len(candidates)} |",
        f"| 保留候选 | {len(kept)} |",
        f"| 排除项目 | {len(excluded)} |",
        f"| 保留率 | {len(kept)/max(len(candidates),1)*100:.1f}% |",
        "",
        "---",
        "",
        "## 🌟 候选项目 Top 3（推荐优先关注）",
        "",
    ]

    # 按信号强度排序：stars + weekly_growth + upvotes
    kept_sorted = sorted(kept, key=lambda c: c.stars + c.weekly_growth + c.upvotes, reverse=True)
    top3 = kept_sorted[:3]

    for i, c in enumerate(top3, 1):
        source_emoji = {"github": "🐙", "producthunt": "🦊", "hackernews": "🔶"}.get(c.source, "📌")
        lines.extend([
            f"### {i}. {c.name}",
            "",
            f"| 维度 | 详情 |",
            f"|------|------|",
            f"| 来源 | {source_emoji} {c.source} |",
            f"| 链接 | {c.url} |",
            f"| Stars/增长 | ⭐ {c.stars} / 周+{c.weekly_growth} |",
            f"| 分类 | {CATEGORIES.get(c.category, c.category)} |",
            f"| 描述 | {c.description} |",
            "",
            "**分析:**",
            f"- ❓ 解决什么问题: {c.problem_solved}",
            f"- 👤 目标用户: {c.target_user}",
            f"- 💰 付费意愿: {c.willingness_to_pay}",
            f"- 🚀 MVP 可行性: {c.mvp_feasibility}",
            "",
        ])

    lines.extend([
        "",
        "---",
        "",
        "## 📋 全部候选项目",
        "",
        "| # | 项目 | 来源 | Stars | 分类 | 付费意愿 | MVP |",
        "|---|------|------|-------|------|----------|-----|",
    ])

    for i, c in enumerate(kept_sorted, 1):
        mvp_icon = "✅" if "1周" in c.mvp_feasibility else "⚠️"
        lines.append(f"| {i} | [{c.name}]({c.url}) | {c.source} | ⭐{c.stars} | {CATEGORIES.get(c.category, c.category)} | {c.willingness_to_pay[:15]}... | {mvp_icon} |")

    lines.extend([
        "",
        "---",
        "",
        "## ❌ 已过滤项目（部分示例）",
        "",
        "| 项目 | 来源 | 排除原因 |",
        "|------|------|----------|",
    ])
    for c in excluded[:20]:
        lines.append(f"| {c.name} | {c.source} | {c.keep_reason} |")

    lines.extend([
        "",
        "---",
        "",
        "## 🔗 相关笔记",
        "",
        "- [[开源商机数据库]] — 所有候选项目汇总",
        f"- [[数据抓取/{now}_raw.json]] — 原始抓取数据",
        "",
    ])

    with open(output_path, "w") as f:
        f.write("\n".join(lines))

    return output_path


def main():
    if len(sys.argv) < 2:
        print("用法: python filter_analyze.py <raw_data.json> [output_dir]")
        sys.exit(1)

    raw_path = sys.argv[1]
    output_dir = sys.argv[2] if len(sys.argv) > 2 else "."

    with open(raw_path) as f:
        raw_data = json.load(f)

    candidates = process_raw_data(raw_data)

    # 保存周报
    now = datetime.now().strftime("%Y-%m-%d")
    report_path = os.path.join(output_dir, f"周报_{now}.md")
    generate_markdown(candidates, report_path)

    # 保存候选项目 JSON（用于数据库）
    kept = [asdict(c) for c in candidates if c.keep]
    db_path = os.path.join(output_dir, f"候选项目_{now}.json")
    with open(db_path, "w") as f:
        json.dump(kept, f, ensure_ascii=False, indent=2)

    print(f"✅ 周报: {report_path}")
    print(f"✅ 数据: {db_path}")
    print(f"📊 {len(candidates)} → {len(kept)} 候选 (保留 {len(kept)} 个)")


if __name__ == "__main__":
    main()
