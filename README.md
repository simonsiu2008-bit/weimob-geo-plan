# weimob-geo-plan

微盟星启 GEO 优化方案生成器 — 一个可复用的 Agent Skill，为品牌客户产出 **固定 20 页 GEO 优化方案 PPT** + 话题词方案 HTML + **独立销售话术/讲稿** + 可选 PDF。

采用 **共享引擎 + 每案例隔离配置** 架构：**数据在案例之间不穿透，每一案例可单独、有针对性呈现。**

## 这个 Skill 解决什么问题

品牌在 DeepSeek、豆包、Kimi、元宝、百度AI、阿里千问等 AI 搜索平台上的「被推荐率」正在成为新的流量入口。客户最关心三件事：

1. **我现在在 AI 平台的曝光度有多少？**
2. **哪些问题被提及了多少次？哪个平台最有影响力？**
3. **竞争对手在 AI 平台是怎么做的？**

本 Skill 把这三个问题用数据在方案中体现并重点标注（第 5 / 7 / 15 页），并给出可落地的 KPI 路径。

## 三项整合能力（三版合一）

| 整合 | 体现 | 参考文档 |
|---|---|---|
| ① 双轨输出 | 客户版（PPT/HTML）纯净 + 独立销售话术文件 | `references/dual_track.md` |
| ② 自动风格 | 配色/字体作为 palette 数据按行业/客户匹配 | `references/design_system.md` |
| ③ 三阶段工作流 | 诊断 → 话题词 → 报价后最终版 | `references/workflow_stages.md` |

基础 20 页框架之上内建四项增强能力：

| 能力 | 解决的问题 | 参考文档 |
|---|---|---|
| ① 话题词框架 | 话题词拍脑袋定，语义场错配 | `references/topic_framework.md` |
| ② 合规红线 | 海外保健品无蓝帽子却写功效，客户担责 | `references/compliance_guide.md` |
| ③ 销售转化增强 | 方案讲得对但客户不着急签 | `references/sales_power.md` |
| ④ 可见度双指标 | 只报一个数被客户误读 | `references/visibility_dual.md` |

> 20 页是硬约束。四项能力以「CONFIG 条件插字」或「独立 HTML 交付物」实现，不新增页面。

## 快速开始

### 依赖

```bash
pip install python-pptx
# 话题词 HTML 生成器无外部依赖（纯标准库）
# PDF 渲染（可选）需要 LibreOffice（soffice 命令）
```

### 生成一份方案（从脱敏模板）

> ⚠️ **隐私说明**：本 skill 发布版**不携带任何真实客户案例**。`cases/` 仅含脱敏模板 `_template/`。
> 真实客户案例需用家从模板复制生成，真实数据独立存储、不随 skill 分发。

```bash
cd /root/.codebuddy/skills/weimob-geo-plan   # 先 cd 到 skill 根目录

# 0. 从脱敏模板生成客户案例
cp -r cases/_template cases/<客户代号>      # 如 cases/acme

# 1. 编辑 cases/<客户代号>/config.py（替换占位数据）

# 2. 20 页客户版 PPT（Stage 3）
python3 scripts/build_deck.py cases/<客户代号>

# 3. 话题词方案 HTML（Stage 2，可选）
python3 scripts/build_topic.py cases/<客户代号>

# 4. 销售话术/讲稿（双轨 B 轨，内部）
python3 scripts/build_talktrack.py cases/<客户代号>

# 5. QA（含跨 case 污染反查）
python3 scripts/qa_check.py <客户代号>
```

### 案例目录

| case | 说明 |
|---|---|
| `_template` | **脱敏结构模板**（无真实数据），新客户案例的起点 |

> 真实案例由用家按需从 `_template` 生成，不随 skill 分发，保护客户隐私。

### 套用新客户

```bash
# 从脱敏模板复制生成客户案例（含 config.py / topic_config.py / pollute_words.txt 结构）
cp -r cases/_template cases/<name>
```

1. **先判合规品类**（海外保健品 / 医疗器械 / 化妆品功效 / 金融）→ 命中则读 `compliance_guide.md`
2. **定风格**：按 `design_system.md` 决策规则设 `config.py` 的 `PALETTE`
3. **填数据**：把诊断数据填入 `cases/<name>/config.py`（替换模板中所有占位，所有客户变量集中于此）
4. **定话题词**：按 `topic_framework.md` 填 `cases/<name>/topic_config.py`，跑 `build_topic.py`
5. **生成**：跑 `build_deck.py` + `build_talktrack.py`
6. **QA**：跑 `qa_check.py <name>`（自动扫描其他 case 的 `pollute_words.txt` 反查污染）
7. **补隔离词**：把本案例的品牌/竞品/行业词写入 `cases/<name>/pollute_words.txt`（供后续案例反查）
8. **对话内嵌展示 + 询问**：在对话内嵌交互式双 Tab（PPT 可翻页 + 话题词方案），并**询问用户是否生成正式 PPT 文件**，确认后才落成 .pptx（见 `style_guide.md` 第十节）

> 🔒 **隐私**：客户案例数据属客户机密，建议存于独立目录（如 `_private_cases/`，已加入 `.gitignore`），勿随 skill 分发。

## 固定框架（不可改动）

| 项目 | 内容 |
|---|---|
| **国内版 6 平台（主）** | 豆包 / DeepSeek / 阿里千问 / 百度AI / 元宝 / Kimi |
| **海外版 5 平台（辅）** | ChatGPT / Perplexity / Claude / Gemini / Copilot |
| **配色（逻辑色名）** | 引擎用 11 个逻辑色名，hex 由 `config.py` 的 `PALETTE` 决定 |
| **AIVO 四维等权（各 25%）** | AI搜索可见性 / 基建完善度 / 竞争优势 / 舆情健康度 |
| **AIVO 评级** | ≥90 优秀 · ≥75 良好 · ≥60 一般 · <60 较差 |
| **数据标注纪律** | 估算类一律标「診斷模型估算」；禁用 實測 / 虛擬 / ⚠️ / website / `{{` |

## 20 页结构

| 页 | 标题 | 说明 |
|---|---|---|
| 1 | 封面 | 品牌名 + 双版本布局 |
| 2 | 执行摘要 · 结论先行 | AIVO 总评 + 四维卡 + 关键发现 |
| 3 | 方法论 | AIVO 四维 + 4 阶段流水线 + 平台双版本 |
| 4 | 行业 AI 搜索现状 | 三张行业统计卡 + 行业叙事 |
| 5 | ⭐ **AI 平台曝光度 · 当前体检与平台影响力** | 客户核心关切 ① |
| 6 | AI 平台常见问答图谱 | 按用户意图聚类 |
| 7 | ⭐ **高频问题被提及次数** | 客户核心关切 ② |
| 8 | 常见引用文章 / 信源清单 | 信源 typology 与覆盖缺口 |
| 9 | 引用偏好框架（7 维度） | 可被 AI 采信度评分 |
| 10 | AIVO 四维评分卡 + 雷达图 | 对比行业基准 |
| 11 | 品牌基建诊断 | 官网 / 自媒体 / 权威媒体三卡 |
| 12 | 舆情风险监控 | 健康度 + 风险清单 + 监控方案 |
| 13 | 横纵分析 · 企业现状（纵向） | 客观事实 |
| 14 | 横纵分析 · 行业与竞品（横向） | 生态位 + 竞品同题提及 |
| 15 | ⭐ **对手在 AI 平台的做法 · 竞品基准** | 客户核心关切 ③ |
| 16 | GEO 优化问题清单 | 缺口 + 证据 + 优先级 |
| 17 | 微盟星启 GEO 能力映射 | 问题 → 模块 → 指标 |
| 18 | 数据追踪方案 | 话题词 + 双版本 + 基线→目标 |
| 19 | 实施节奏与追踪指标 | 五步流程 + P1/P2/P3 |
| 20 | 结尾 | 联络卡片 |

## 增强变量（config.py，可选）

| CONFIG 变量 | 对应页 | 示例值 | 作用 |
|---|---|---|---|
| `VIS_DUAL` | 5 | `{"brand_word":0.88,"category_word":0.17,"industry_top":0.14}` | 品牌词/品类词双指标 |
| `SOURCE_CITE` | 8 | `[("百家号",84),("微信公众号",67)]` | 信源引用次数 Top 榜 |
| `RANK_POOL` | 14 | `{"total":41,"rank":16}` | 竞品池规模 + 排名锚点 |
| `COMPLIANCE` | 18 | `{"applicable":True}` | 合规红线声明 |

> **硬性规则**：`ECO_MAP` 必须填真实竞品名称，禁止「頭部競品 A / 頭部競品 B」占位符。

## QA（交付前必做）

```bash
python3 scripts/qa_check.py <case名>
```

检查器自动覆盖：页数=20 / 禁忌标记=0 / 占位符=0 / OOB=0 / `診斷模型估算`≥2 /
**跨 case 污染反查（扫描全部其他 case 的 pollute_words）/ 话题词 HTML 反查 / 合规功效词否定语境**。退出码 0 为通过。

> **口径一致性也要查**：`VIS_DUAL` 与第 18 页 KPI、话题词 HTML 三处一致；PPT `TOPIC_WORDS` ↔ HTML `TOPICS` ↔ **报价表** 一字不差。

## 目录结构

```
weimob-geo-plan/
├── SKILL.md                          # Skill 元数据与工作流（含合规红线硬规则）
├── README.md                         # 本文件
├── scripts/
│   ├── engine/                       # 共享引擎（无案例数据，颜色只走逻辑色名）
│   │   ├── palette.py                # 配色数据模型 + 预设
│   │   ├── deck_engine.py            # 20 页客户版 PPT
│   │   ├── topic_engine.py           # 话题词方案 HTML
│   │   ├── talktrack.py              # 销售话术/讲稿
│   │   └── qa_engine.py              # QA（含跨 case 反查）
│   ├── build_deck.py                 # CLI → engine/deck_engine.py
│   ├── build_topic.py                # CLI → engine/topic_engine.py
│   ├── build_talktrack.py            # CLI → engine/talktrack.py
│   ├── qa_check.py                   # CLI → engine/qa_engine.py
├── cases/<name>/                     # 每案例隔离目录
│   ├── config.py                     # PPT 数据 + PALETTE
│   ├── topic_config.py               # 话题词数据（可选）
│   ├── pollute_words.txt             # 本案例行业词（供反查）
│   └── output/                       # 本案例输出，独立隔离
└── references/
    ├── style_guide.md                # 架构、双轨交付物、20 页、QA 清单、渲染坑
    ├── design_system.md              # 风格按行业/客户自动匹配决策规则
    ├── dual_track.md                 # 客户版 vs 销售版分离规范
    ├── workflow_stages.md            # 三阶段工作流
    ├── weimob_geo_service.md         # 平台双版本、四大模块、KPI
    ├── topic_framework.md            # ① 话题分层、五问测试、监测池
    ├── compliance_guide.md           # ② SAMR 24 项、蓝帽子、禁用词、改写剧本
    ├── sales_power.md                # ③ 成交焦虑要素与页面映射
    └── visibility_dual.md            # ④ 品牌词/品类词双指标
```

## 已知风险

- **数据隔离是本 Skill 最高优先硬性要求**。换新客户 = 新建 `cases/<name>/`，QA 自动跨 case 反查兜底。曾出现家族办公室方案残留「瑞士奢华 / 腕表之家 / Chrono24」等钟表用语——新架构用 `pollute_words.txt` + 自动反查根治。
- **模板污染是第二高风险**。换客户时务必逐项替换 CONFIG 的 `ECO_MAP` / `SOURCE_TABLE` / `SENTIMENT_BULLETS` / `GAP_ROWS` / `CAPABILITY_MAP` / `ROADMAP_TABLE`。
- **合规污染是第三高风险**。海外保健品无「蓝帽子」时，出现任何功效表述都让客户担责。受监管品类须 PPT / 话题词 HTML / 讲稿 / 话术四处同查。
- **语义场错配风险**。话题词召回的竞品必须与品牌同场——「香港保健品推荐」召回港式中药赛道，对日系原装品牌是无效话题词。
- 估算数据为模型模拟收录，非真实 API 调用。如需「真实收录证据」应另做一轮实检。
- 不对诊断结果做法律或商业决策背书；合规结论以客户法务与监管机关口径为准。

## License

MIT
