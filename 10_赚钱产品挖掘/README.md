# 10_赚钱产品挖掘

> **核心逻辑**：不猜不测，只挖掘已经在你面前赚到钱的产品。找到 → 分析 → 抄。

## 数据源

| 数据源 | 信号类型 | 信号强度 | 付费墙 |
|--------|---------|---------|--------|
| **Reddit** r/SaaS r/SideProject | 💰 晒 MRR 里程碑 | ⭐⭐⭐⭐⭐ | ❌ 免费 |
| **Indie Hackers** | 💰 MRR 公开 | ⭐⭐⭐⭐⭐ | ❌ 免费 |
| **Product Hunt** | 📈 Launch 热度 | ⭐⭐⭐ | ❌ 免费 |
| **Chrome Web Store** | 💰 付费 × 用户量 | ⭐⭐⭐⭐ | ❌ 免费 |
| **Flippa + HN Show HN** | 💰 在售 + 新品 | ⭐⭐⭐ | ❌ 免费 |

## 打分体系

每个候选产品在 5 个维度上打分（0-5）：

| 维度 | 含义 | 高分标准 |
|------|------|---------|
| **revenue_signal** | 收入信号强度 | 公开 MRR > $10K = 5，未提及收入 = 0 |
| **cloneability** | 可模仿性 | Chrome 插件/简单 web = 5，需硬件/企业销售 = 0 |
| **maintenance_cost** | 维护成本（高=低维护） | 设后不管 = 5，24/7 客服 = 0 |
| **market_niche** | 利基市场适配度 | 小众无巨头 = 5，赢家通吃 = 0 |
| **tech_fit** | 技术栈匹配度 | 纯 Web/AI = 5，需硬件 = 0 |

**综合分** = `revenue_signal × 2 + cloneability × 2 + maintenance_cost + market_niche + tech_fit`

满分 35。

## 分类体系

| 分类 | 标识 | 典型特征 |
|------|------|---------|
| `saas` | 🏢 | 传统 SaaS，订阅制 |
| `ai_tool` | 🤖 | AI/LLM 驱动的工具 |
| `chrome_extension` | 🧩 | 浏览器插件 |
| `mobile_app` | 📱 | iOS/Android 应用 |
| `api_service` | 🔌 | API 即服务 |
| `digital_product` | 📦 | 模板/课程/数字商品 |
| `newsletter` | 📧 | 付费通讯 |
| `community` | 👥 | 付费社群 |

## 过滤规则

### 保留（KEEP）
- `revenue_signal >= 2`（至少有收入迹象）
- `cloneability >= 3`（一人公司可以做）
- 分类属于 `saas / ai_tool / chrome_extension / api_service / digital_product`

### 排除（EXCLUDE）
- `revenue_signal = 0` 且 `cloneability <= 2`
- 需要硬件、线下运营、企业销售团队
- 纯免费开源无商业化路径
- 涉及强监管（金融/医疗合规）

## 日报格式

每天产出：
- `日报_YYYY-MM-DD.md` — 完整日报（所有候选）
- `精选Top3_YYYY-MM-DD.md` — 精选 Top 3 深度分析
- `候选项目_YYYY-MM-DD.json` — 结构化数据

## 工作流

```
每天 9:00 CST Cron 触发
  → 5 路数据抓取
  → Python filter_analyze.py 过滤/分类/打分
  → 生成日报 Markdown
  → 生成候选项目库 .md 笔记（YAML frontmatter）
  → git add/commit/push
  → 飞书推送 Top 3 摘要（如当日候选 < 5 个则标注）
```

## 负责人

- **流水线搭建与维护**：Steve
- **数据抓取（Cron 自动化）**：Steve（Cron）
- **每周精选分析**：Steve
- **最终决策（抄哪个）**：老板
