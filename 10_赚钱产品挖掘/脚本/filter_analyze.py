#!/usr/bin/env python3
"""
赚钱产品挖掘 — 过滤器 & 分析引擎
用法: python filter_analyze.py <raw_data.json> <output_dir>
"""

import json, sys, os
from datetime import datetime, date
from dataclasses import dataclass, field, asdict
from typing import Optional

# ============================================================
# 分类体系
# ============================================================
CATEGORIES = {
    "saas": {"emoji": "🏢", "label": "SaaS", "keywords": ["saas", "subscription", "b2b", "crm", "analytics", "dashboard", "cms"]},
    "ai_tool": {"emoji": "🤖", "label": "AI工具", "keywords": ["ai", "llm", "gpt", "chatgpt", "openai", "claude", "generative", "copilot", "agent", "machine learning", "nlp"]},
    "chrome_extension": {"emoji": "🧩", "label": "浏览器插件", "keywords": ["chrome extension", "browser extension", "chrome", "firefox extension"]},
    "mobile_app": {"emoji": "📱", "label": "移动应用", "keywords": ["ios", "android", "mobile app", "app store", "play store"]},
    "api_service": {"emoji": "🔌", "label": "API服务", "keywords": ["api", "sdk", "developer tool", "platform", "integration"]},
    "digital_product": {"emoji": "📦", "label": "数字产品", "keywords": ["template", "course", "ebook", "notion template", "figma", "ui kit"]},
    "newsletter": {"emoji": "📧", "label": "付费通讯", "keywords": ["newsletter", "substack", "beehiiv"]},
    "community": {"emoji": "👥", "label": "付费社群", "keywords": ["community", "membership", "discord", "slack", "circle"]},
}

# ============================================================
# 排除关键词（命中任一条即排除）
# ============================================================
EXCLUDE_KEYWORDS = [
    "blockchain", "crypto", "nft", "web3", "defi",  # 币圈
    "hardware", "iot", "device", "robot",             # 需硬件
    "enterprise sales", "sales team required",        # 需销售团队
    "marketplace", "two-sided",                       # 双边市场冷启动难
    "healthcare hipaa", "medical device",             # 强监管
    "gambling", "casino", "betting",                  # 灰色
    "adult", "nsfw",                                   # 灰色
]

# ============================================================
# 保留分类
# ============================================================
KEEP_CATEGORIES = {"saas", "ai_tool", "chrome_extension", "api_service", "digital_product"}


@dataclass
class Candidate:
    """候选产品"""
    # 原始数据
    source: str
    name: str
    url: str
    description: str
    market: str = "global"   # en | zh | ja | sea | global
    raw_signals: dict = field(default_factory=dict)  # {mrr, profit, price, users, votes, ...}

    # 分类打分
    category: str = "unknown"
    revenue_signal: int = 0       # 0-5
    cloneability: int = 0         # 0-5
    maintenance_cost: int = 0     # 0-5 (高=低维护)
    market_niche: int = 0         # 0-5
    tech_fit: int = 0             # 0-5
    score: int = 0                # 综合分

    # 分析字段
    problem: str = ""
    target_user: str = ""
    willingness_to_pay: str = ""
    mvp_feasibility: str = ""
    competitors: str = ""
    how_to_clone: str = ""

    # 决策
    keep: bool = True
    reject_reason: str = ""


def classify(item: dict) -> str:
    """基于描述+标签+名称分类"""
    text = f"{item.get('description', '')} {item.get('name', '')} {' '.join(item.get('topics', []))}".lower()

    # 先检查精确分类信号
    for cat, info in CATEGORIES.items():
        for kw in info["keywords"]:
            if kw in text:
                return cat

    # 启发式
    if any(kw in text for kw in ["extension", "chrome", "browser"]):
        return "chrome_extension"
    if any(kw in text for kw in ["ai ", "llm", "gpt", "openai"]):
        return "ai_tool"
    if any(kw in text for kw in ["api", "sdk"]):
        return "api_service"

    return "saas"  # 默认


def score_revenue(item: dict) -> int:
    """收入信号强度 0-5"""
    mrr = item.get("mrr", 0)
    profit = item.get("profit", 0)
    price = item.get("asking_price", 0)
    users = item.get("paying_users", 0)
    has_revenue = item.get("has_revenue", False)

    if isinstance(mrr, str):
        mrr = parse_money(mrr)
    if isinstance(profit, str):
        profit = parse_money(profit)

    # 直接 MRR 披露（最硬）
    if mrr > 10000:
        return 5
    if mrr > 5000:
        return 4
    if mrr > 1000:
        return 3
    if mrr > 0:
        return 2

    # 在售项目，有要价（次硬）
    if price > 50000:
        return 4
    if price > 10000:
        return 3
    if price > 0:
        return 2

    # 有付费用户数
    if users > 1000:
        return 3
    if users > 100:
        return 2

    # 间接信号
    if has_revenue:
        return 1
    if profit > 0:
        return 2

    return 0


def score_cloneability(item: dict, category: str) -> int:
    """可模仿性 0-5"""
    desc = item.get("description", "").lower()
    name = item.get("name", "").lower()

    # Chrome 插件最容易抄
    if category == "chrome_extension":
        return 5

    # AI wrapper 也容易
    if category == "ai_tool":
        if any(kw in desc for kw in ["wrapper", "chat", "prompt", "template"]):
            return 5
        return 4

    # 数字产品
    if category == "digital_product":
        return 5

    # API 服务
    if category == "api_service":
        return 3

    # SaaS — 看复杂度
    if any(kw in desc for kw in ["real-time", "infrastructure", "database", "distributed"]):
        return 2
    if any(kw in desc for kw in ["video", "streaming", "cdn"]):
        return 2
    if any(kw in desc for kw in ["security", "compliance", "soc2"]):
        return 2

    return 4  # 一般 SaaS，能抄


def score_maintenance(item: dict) -> int:
    """维护成本（高=低维护）0-5"""
    desc = item.get("description", "").lower()

    # 零维护产品
    if any(kw in desc for kw in ["template", "digital download", "one-time"]):
        return 5

    # 低维护
    if any(kw in desc for kw in ["automated", "self-serve", "no-code"]):
        return 4

    # 中等
    if any(kw in desc for kw in ["support", "onboarding"]):
        return 2

    return 4  # 默认偏低维护


def score_niche(item: dict) -> int:
    """利基市场适配度 0-5"""
    desc = item.get("description", "").lower()

    # Niche 信号
    if any(kw in desc for kw in ["niche", "specific", "specialized", "focused"]):
        return 5
    if any(kw in desc for kw in ["for", "tailored", "exclusive"]):
        return 4

    # 通用市场
    if any(kw in desc for kw in ["everyone", "all-in-one", "universal"]):
        return 1

    return 3  # 默认中等


def score_tech_fit(item: dict) -> int:
    """技术栈匹配度 0-5"""
    desc = item.get("description", "").lower()

    # Web 原生（我们最擅长）
    if any(kw in desc for kw in ["web", "browser", "extension", "website"]):
        return 5
    if any(kw in desc for kw in ["api", "rest", "graphql"]):
        return 5
    if any(kw in desc for kw in ["ai", "llm", "gpt", "claude", "openai"]):
        return 5
    if any(kw in desc for kw in ["saas", "cloud", "subscription"]):
        return 5

    # 移动端
    if any(kw in desc for kw in ["ios", "android", "mobile", "app"]):
        return 3

    return 4  # 默认还不错


def should_exclude(item: dict, category: str, desc_lower: str) -> tuple[bool, str]:
    """检查是否应排除"""
    # 分类不在保留列表
    if category not in KEEP_CATEGORIES:
        return True, f"分类 {category} 不在保留列表"

    # 排除关键词
    for kw in EXCLUDE_KEYWORDS:
        if kw in desc_lower:
            return True, f"命中排除关键词: {kw}"

    return False, ""


def parse_money(s: str) -> float:
    """解析 '$5,000/mo' → 5000.0"""
    try:
        s = s.replace("$", "").replace(",", "").replace("/mo", "").replace("/month", "").replace("/yr", "").replace("/year", "").strip()
        if "k" in s.lower():
            return float(s.lower().replace("k", "")) * 1000
        if "m" in s.lower():
            return float(s.lower().replace("m", "")) * 1000000
        return float(s)
    except (ValueError, AttributeError):
        return 0.0


def analyze_business(c: Candidate):
    """填充业务分析字段"""
    desc = c.description.lower()

    # 解决的问题
    problem_keywords = {
        "productivity": "提高工作效率",
        "automation": "自动化重复任务",
        "analytics": "数据分析和洞察",
        "content": "内容创作和分发",
        "communication": "团队沟通协作",
        "marketing": "营销获客",
        "sales": "销售转化",
        "developer": "开发者工具和效率",
        "design": "设计协作",
        "finance": "财务管理",
    }
    for kw, problem in problem_keywords.items():
        if kw in desc:
            c.problem = problem
            break
    if not c.problem:
        c.problem = "具体问题待深入调研"

    # 目标用户
    user_keywords = {
        "developer": "开发者",
        "designer": "设计师",
        "marketer": "市场营销人员",
        "founder": "创业者/独立开发者",
        "writer": "内容创作者/作家",
        "sales": "销售团队",
        "hr": "HR/招聘",
        "student": "学生",
        "small business": "小企业主",
    }
    for kw, user in user_keywords.items():
        if kw in desc:
            c.target_user = user
            break
    if not c.target_user:
        c.target_user = "待调研"

    # 付费意愿
    if c.revenue_signal >= 4:
        c.willingness_to_pay = "💰 强 — 已有可观MRR"
    elif c.revenue_signal >= 2:
        c.willingness_to_pay = "✅ 确认 — 有付费用户"
    elif c.revenue_signal >= 1:
        c.willingness_to_pay = "⚠️ 待验证 — 有收入但无细节"
    else:
        c.willingness_to_pay = "❓ 未知"

    # MVP 可行性和抄袭路径
    if c.cloneability >= 4 and c.tech_fit >= 4:
        c.mvp_feasibility = f"✅ 高 — {c.category} 类产品，1-2 周可出 MVP"
        c.how_to_clone = f"1. 研究 {c.name} 的核心功能\n2. 用 AI 辅助写核心代码\n3. 简化功能，只保留 20% 核心\n4. 差异化定位（价格/地区/垂直行业）\n5. 1 周内上线 MVP"
    elif c.cloneability >= 3:
        c.mvp_feasibility = f"⚠️ 中 — 需要 2-4 周，有中等复杂度"
        c.how_to_clone = f"1. 先做最小核心功能\n2. 利用开源方案加速\n3. 2-4 周 MVP"
    else:
        c.mvp_feasibility = f"🔴 低 — 复杂度过高，不适合快速抄袭"
        c.how_to_clone = "建议放弃或大幅简化后再评估"


def process_item(item: dict) -> Candidate:
    """处理单个候选项目"""
    c = Candidate(
        source=item.get("source", "unknown"),
        market=item.get("market", "global"),
        name=item.get("name", ""),
        url=item.get("url", ""),
        description=item.get("description", ""),
        raw_signals={k: item.get(k) for k in ["mrr", "profit", "asking_price", "paying_users", "votes", "stars"] if k in item},
    )

    # 分类
    c.category = classify(item)

    # 排除检查
    desc_lower = c.description.lower()
    should_ex, reason = should_exclude(item, c.category, desc_lower)
    if should_ex:
        c.keep = False
        c.reject_reason = reason
        return c

    # 打分
    c.revenue_signal = score_revenue(item)
    c.cloneability = score_cloneability(item, c.category)
    c.maintenance_cost = score_maintenance(item)
    c.market_niche = score_niche(item)
    c.tech_fit = score_tech_fit(item)

    # 综合分
    c.score = c.revenue_signal * 2 + c.cloneability * 2 + c.maintenance_cost + c.market_niche + c.tech_fit

    # 收入信号为 0 的排除（我们是找赚钱产品）
    if c.revenue_signal < 1:
        c.keep = False
        c.reject_reason = "无收入信号"
        return c

    # 收入信号太弱且可模仿性低的过滤
    if c.revenue_signal < 2 and c.cloneability < 3:
        c.keep = False
        c.reject_reason = "收入信号弱且难以模仿"

    # 分析
    if c.keep:
        analyze_business(c)

    return c


def generate_daily_report(candidates: list[Candidate], output_path: str, date_str: str):
    """生成日报 Markdown"""
    kept = [c for c in candidates if c.keep]
    rejected = [c for c in candidates if not c.keep]

    # 按得分排序
    kept.sort(key=lambda c: c.score, reverse=True)

    lines = []
    lines.append(f"# 🕵️ 赚钱产品挖掘日报 — {date_str}")
    lines.append("")
    lines.append(f"> 📊 今日抓取: {len(candidates)} | ✅ 保留: {len(kept)} | ❌ 排除: {len(rejected)}")
    lines.append(f"> 🕐 生成时间: {datetime.now().strftime('%Y-%m-%d %H:%M')}")
    lines.append("")

    # Top 候选表格
    lines.append("## 🏆 候选排名")
    lines.append("")
    lines.append("| # | 产品 | 来源 | 分类 | 收入信号 | 可抄性 | 综合分 |")
    lines.append("|---|------|------|------|---------|--------|--------|")
    for i, c in enumerate(kept[:20], 1):
        cat_emoji = CATEGORIES.get(c.category, {}).get("emoji", "❓")
        stars = "⭐" * min(c.revenue_signal, 5)
        clone_stars = "⭐" * min(c.cloneability, 5)
        lines.append(f"| {i} | [{c.name}]({c.url}) | {c.source} | {cat_emoji} {c.category} | {stars} | {clone_stars} | **{c.score}** |")
    lines.append("")

    # Top 3 深度分析
    lines.append("## 🔥 Top 3 精选深度分析")
    lines.append("")
    for i, c in enumerate(kept[:3], 1):
        lines.append(f"### No.{i} — {c.name}")
        lines.append("")
        lines.append(f"- **URL**: {c.url}")
        lines.append(f"- **来源**: {c.source}")
        lines.append(f"- **分类**: {CATEGORIES.get(c.category, {}).get('emoji', '❓')} {CATEGORIES.get(c.category, {}).get('label', c.category)}")
        lines.append(f"- **描述**: {c.description}")
        lines.append("")
        lines.append("| 维度 | 评分 |")
        lines.append("|------|------|")
        lines.append(f"| 💰 收入信号 | {'⭐' * c.revenue_signal} ({c.revenue_signal}/5) |")
        lines.append(f"| 🔧 可模仿性 | {'⭐' * c.cloneability} ({c.cloneability}/5) |")
        lines.append(f"| 🛠️ 维护成本 | {'⭐' * c.maintenance_cost} ({c.maintenance_cost}/5) |")
        lines.append(f"| 🎯 利基市场 | {'⭐' * c.market_niche} ({c.market_niche}/5) |")
        lines.append(f"| 💻 技术匹配 | {'⭐' * c.tech_fit} ({c.tech_fit}/5) |")
        lines.append(f"| 📊 **综合分** | **{c.score}/35** |")
        lines.append("")
        lines.append(f"- **解决的问题**: {c.problem}")
        lines.append(f"- **目标用户**: {c.target_user}")
        lines.append(f"- **付费意愿**: {c.willingness_to_pay}")
        lines.append(f"- **MVP 可行性**: {c.mvp_feasibility}")
        lines.append(f"- **抄袭路径**: {c.how_to_clone}")
        lines.append("")
        if c.raw_signals:
            lines.append(f"- **原始信号**: {json.dumps(c.raw_signals)}")
        lines.append("")

    # 排除项目摘要
    if rejected:
        lines.append("## ❌ 本日排除项目")
        lines.append("")
        lines.append("| 产品 | 原因 |")
        lines.append("|------|------|")
        for c in rejected:
            lines.append(f"| {c.name} | {c.reject_reason} |")
        lines.append("")

    with open(output_path, "w") as f:
        f.write("\n".join(lines))

    print(f"✅ 日报已生成: {output_path}")


def generate_candidate_notes(candidates: list[Candidate], notes_dir: str, date_str: str):
    """为每个候选项目生成 Obsidian 笔记（YAML frontmatter）"""
    os.makedirs(notes_dir, exist_ok=True)

    for c in candidates:
        safe_name = c.name.replace("/", "-").replace(" ", "_")[:100]
        note_path = os.path.join(notes_dir, f"{safe_name}.md")

        # 如果笔记已存在，跳过（保留人工编辑）
        if os.path.exists(note_path):
            continue

        cat_label = CATEGORIES.get(c.category, {}).get("label", c.category)

        frontmatter = f"""---
name: "{c.name}"
source: "{c.source}"
url: "{c.url}"
category: "{c.category}"
category_label: "{cat_label}"
function: "{c.description[:100]}"
date: "{date_str}"
status: "{'candidate' if c.keep else 'rejected'}"
revenue_signal: {c.revenue_signal}
cloneability: {c.cloneability}
maintenance_cost: {c.maintenance_cost}
market_niche: {c.market_niche}
tech_fit: {c.tech_fit}
score: {c.score}
select_reason: ""
reject_reason: "{c.reject_reason}"
problem: "{c.problem}"
target_user: "{c.target_user}"
willingness_to_pay: "{c.willingness_to_pay}"
mvp_feasibility: "{c.mvp_feasibility}"
reviewed: false
prd_started: false
research_done: false
---

# {c.name}

> 来源: {c.source} | 分类: {cat_label} | 得分: {c.score}/35
> URL: {c.url}

## 描述
{c.description}

## 分析

- **解决的问题**: {c.problem}
- **目标用户**: {c.target_user}
- **付费意愿**: {c.willingness_to_pay}
- **MVP 可行性**: {c.mvp_feasibility}

## 抄袭路径
{c.how_to_clone}

## 原始信号
```json
{json.dumps(c.raw_signals, indent=2)}
```
"""

        with open(note_path, "w") as f:
            f.write(frontmatter)

    print(f"✅ 已生成 {len(candidates)} 个候选项目笔记 → {notes_dir}")


def main():
    if len(sys.argv) < 3:
        print("用法: python filter_analyze.py <raw_data.json> <output_dir>")
        print("示例: python filter_analyze.py 数据抓取/2026-05-07_raw.json 日报归档/")
        sys.exit(1)

    raw_path = sys.argv[1]
    output_dir = sys.argv[2]
    date_str = os.path.basename(raw_path).replace("_raw.json", "")

    # 读取原始数据
    with open(raw_path) as f:
        raw_items = json.load(f)

    print(f"📥 读取 {len(raw_items)} 条原始数据")

    # 处理
    candidates = [process_item(item) for item in raw_items]

    # 统计
    kept = [c for c in candidates if c.keep]
    rejected = [c for c in candidates if not c.keep]
    print(f"📊 保留 {len(kept)} | 排除 {len(rejected)}")

    # 生成日报
    os.makedirs(output_dir, exist_ok=True)
    report_path = os.path.join(output_dir, f"日报_{date_str}.md")
    generate_daily_report(candidates, report_path, date_str)

    # 生成候选 JSON
    json_path = os.path.join(output_dir, f"候选项目_{date_str}.json")
    with open(json_path, "w") as f:
        json.dump([asdict(c) for c in kept], f, ensure_ascii=False, indent=2)
    print(f"✅ 候选 JSON: {json_path}")

    # 生成候选笔记
    notes_dir = os.path.join(os.path.dirname(output_dir), "候选项目库")
    generate_candidate_notes(candidates, notes_dir, date_str)

    # 打印 Top 3 摘要（供飞书推送用）
    print("\n" + "=" * 50)
    print("🔥 TOP 3 摘要")
    print("=" * 50)
    for i, c in enumerate(kept[:3], 1):
        print(f"\nNo.{i} — {c.name} (得分: {c.score}/35)")
        print(f"  来源: {c.source} | 分类: {c.category}")
        print(f"  收入信号: {c.revenue_signal}/5 | 可抄性: {c.cloneability}/5")
        print(f"  {c.how_to_clone[:150]}...")


if __name__ == "__main__":
    main()
