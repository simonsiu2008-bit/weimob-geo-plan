#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
脱敏案例模板（_template）
=======================
本文件是 skill 自带的结构骨架模板，用于生成新客户案例。
**不含任何真实客户数据**。所有行业、品牌、竞品均为通用占位。

使用方法：
  1. 复制本目录为 cases/<客户代号>/（如 cases/acme）
  2. 把下方所有「示例/占位」内容替换为该客户的真实诊断数据
  3. 在 cases/<客户代号>/ 下运行各构建脚本

字段说明见 references/style_guide.md 第二节（20 页结构）。
风格（PALETTE）决策规则见 references/design_system.md。
"""

# ---- 品牌基本信息（占位示例：钟表零售）----
BRAND_CN   = "示例客户"
BRAND_EN   = "Sample Client"
CLIENT_DESC = "示例客户业务描述（钟表零售行业，占位）"
PRODUCT_TYPE = "示例品类 / 门店零售"

# 联系卡片（占位）
CONTACT = [
    "示例客户（占位）",
    "Tel: 0000 0000 · Email: sample@example.com",
    "地址占位（填客户真实联系方式）",
]

# 诊断口径标注（固定文案）
DIAG = "微盟星启 GEO 診斷模型估算（國內 6 平臺 × 15 問模擬收錄）"

# ---- AIVO 四维评分（占位数值）----
AIVO_TOTAL = 50
AIVO_RATE  = "一般"
AIVO_VIS, AIVO_INFRA, AIVO_COMP, AIVO_SENT = 40, 55, 45, 60
AIVO_BENCH = [55, 60, 55, 65]

# ---- 曝光度体检（第 5 页，占位）----
CITE_RATE   = 0.20
CITED       = 18
TOTAL_SCEN  = 90
GAP_PCT     = 80
PLATFORM_INFLUENCE = [
    ["平臺", "貢獻次數", "佔比", "影響等級"],
    ["示例平臺A", "5", "28%", "高影響"],
    ["示例平臺B", "4", "22%", "高影響"],
]
INFLUENCE_NOTE = "示例：描述各平台对曝光贡献与优化杠杆（替换为真实诊断）。"

# ---- 高频问题被提及次数（第 7 页，占位）----
FREQ_ROWS = [
    ["選購 / 信任", "4", "6", "6.7%", "示例平臺"],
    ["比價 / 門店", "3", "4", "4.4%", "示例平臺"],
]
FREQ_HL = "示例：最高提及意图与内容补强优先级（替换为真实诊断）。"

# ---- 竞品基准（第 14-15 页，占位）----
COMPETITORS = [
    ["示例競品A", "55", "行业定位描述（占位）"],
    ["示例競品B", "48", "行业定位描述（占位）"],
]
ECO_MAP = [
    ["本品牌（本）", "長尾 · 利基定位", "示例被引用形式", "官網 / 示例渠道"],
    ["示例競品A", "腰部", "示例被引用形式", "官網 / 示例渠道"],
]
COMPETITOR_TACTICS = [
    "品牌權威：示例策略",
    "聚合佔位：示例策略",
    "自媒體聲量：示例策略",
]
COMPETITOR_HL = "示例：竞品策略分析与本品牌借镜点（替换为真实诊断）。"

# ---- 行业现状卡（第 4 页，占位）----
STAT_CARDS = [
    ("0.20", "示例指標一\n占位描述", "BLUE", "來源：" + DIAG),
    ("50", "示例指標二\n占位描述", "CYAN", "來源：示例"),
    ("3", "示例指標三\n占位描述", "AMBER", "來源：示例"),
]
INDUSTRY_NOTE = "示例：行业现状与机会叙事（替换为该客户所在行业的真实判断）。"

# ---- 基建三卡（第 11 页，占位）----
INFRA_CARDS = [
    ("官網 / 渠道", "55", "占位：官网/渠道基建现状与缺口。", "BLUE"),
    ("自媒體矩陣", "10", "占位：自媒体矩阵现状与缺口。", "CYAN"),
    ("權威媒體", "15", "占位：权威媒体/背书现状。", "GREEN"),
]

# ---- KPI 基线→目标（第 18 页，占位）----
KPI_ROWS = [
    ["指標", "基線（現）", "90 天目標", "180 天目標"],
    ["被引用率", "0.20", "0.30", "0.45"],
    ["FAQ 覆蓋率", "低", "55%", "85%"],
]

# ---- 常见问答图谱（第 6 页，占位）----
QA_GRAPH = [
    ["意圖", "高頻問句（示例）", "平臺版本", "典型信源"],
    ["選購 / 信任", "示例客戶 值得買嗎", "國內版", "官網 / 示例"],
    ["比價 / 門店", "示例客戶 門店 價格", "國內版", "官網 / 示例"],
]

# ---- 信源清单（第 8 页，占位）----
SOURCE_OFFICIAL = "官網 + 示例權威來源"
SOURCE_TABLE = [
    ["官方 / 權威", SOURCE_OFFICIAL, "高", "占位：缺口"],
    ["UGC / 社區", "占位：自有聲量", "中低", "占位：缺口"],
    ["缺失項（機會）", "占位：内容改造重点", "——", "微盟星启 內容改造重點"],
]
SOURCE_FOOTNOTE = "占位：信源覆盖与缺口说明。"

# ---- 核心话题词（第 18 页，占位）----
TOPIC_WORDS = [
    "示例客戶 值得買嗎",
    "示例客戶 門店 價格",
]

# ---- 执行摘要关键发现（slide 2，占位）----
KEY_FINDINGS = [
    "示例：被引用率与平台差异（替换为真实诊断）。",
    "示例：基建现状与最大短板。",
    "示例：舆情健康度与风险。",
    "示例：竞争优势与差距。",
    "示例：优化主线。",
]

# ---- 舆情监控（slide 12，占位）----
SENTIMENT_BULLETS = [
    "示例：未检索到针对本品牌专属恶评。",
    "示例：平台分布与种草表述。",
    "示例：正向驱动因素。",
]
SENTIMENT_ACTIONS = [
    "示例：品牌舆情指数监测。",
    "示例：内容整改动作。",
]

# ---- 企业现状（slide 13，占位）----
CURRENT_FACTS = [
    ["業務基本面", "示例：客户业务描述。"],
    ["數字資產現狀", "示例：官网/自媒体/权威媒体现状。"],
    ["GEO 可見度（估算）", "示例：被引用率与出现形式。"],
    ["內容缺口", "示例：对应对答图谱的覆盖不足。"],
]

# ---- GEO 优化问题清单（slide 16，占位）----
GAP_ROWS = [
    ["1", "示例缺口一", "示例類型", "示例現狀", "高"],
    ["2", "示例缺口二", "示例類型", "示例現狀", "中"],
]

# ---- 能力映射（slide 17，占位）----
CAPABILITY_MAP = [
    ["示例問題", "示例模塊", "示例指標", "高"],
    ["示例問題", "示例模塊", "示例指標", "中"],
]

# ---- 实施节奏（slide 19，占位）----
ROADMAP_TABLE = [
    ["階段", "重點動作", "追蹤指標", "頻率"],
    ["P1 即時（1–2週）", "示例動作", "示例指標", "每週"],
    ["P2 短期（1–3月）", "示例動作", "示例指標", "每月"],
    ["P3 長期（3–6月）", "示例動作", "示例指標", "每月 + 複盤"],
]

# ---- 增强变量（可选；不填则 20 页结构不变）----
VIS_DUAL = None          # {"brand_word":0.5,"category_word":0.2,"industry_top":0.3}
RANK_POOL = None         # {"total":20,"rank":8}
SOURCE_CITE = None       # [("示例信源",50),...]
COMPLIANCE = {"applicable": False}   # 受监管品类改为 True，并按 compliance_guide.md 填禁止词等

# ---- 输出文件名（填客户名）----
OUT_FILENAME = "示例客户_微盟星启GEO优化方案.pptx"

# ---- 主题 palette（design_system.md 决策规则）----
# 钟表/金融 → weimob_blue；保健品/日系健康 → meiriki_teal；文化遗产/生态 → heritage_green
PALETTE = "weimob_blue"

# ---- 汇聚成 CONFIG dict ----
CONFIG = dict(
    BRAND_CN=BRAND_CN, BRAND_EN=BRAND_EN, CLIENT_DESC=CLIENT_DESC, PRODUCT_TYPE=PRODUCT_TYPE,
    CONTACT=CONTACT, DIAG=DIAG,
    AIVO_TOTAL=AIVO_TOTAL, AIVO_RATE=AIVO_RATE,
    AIVO_VIS=AIVO_VIS, AIVO_INFRA=AIVO_INFRA, AIVO_COMP=AIVO_COMP, AIVO_SENT=AIVO_SENT,
    AIVO_BENCH=AIVO_BENCH,
    CITE_RATE=CITE_RATE, CITED=CITED, TOTAL_SCEN=TOTAL_SCEN, GAP_PCT=GAP_PCT,
    PLATFORM_INFLUENCE=PLATFORM_INFLUENCE, INFLUENCE_NOTE=INFLUENCE_NOTE,
    FREQ_ROWS=FREQ_ROWS, FREQ_HL=FREQ_HL,
    COMPETITORS=COMPETITORS, ECO_MAP=ECO_MAP,
    COMPETITOR_TACTICS=COMPETITOR_TACTICS, COMPETITOR_HL=COMPETITOR_HL,
    STAT_CARDS=STAT_CARDS, INDUSTRY_NOTE=INDUSTRY_NOTE,
    INFRA_CARDS=INFRA_CARDS, KPI_ROWS=KPI_ROWS, QA_GRAPH=QA_GRAPH,
    SOURCE_OFFICIAL=SOURCE_OFFICIAL, SOURCE_TABLE=SOURCE_TABLE, SOURCE_FOOTNOTE=SOURCE_FOOTNOTE,
    TOPIC_WORDS=TOPIC_WORDS, KEY_FINDINGS=KEY_FINDINGS,
    SENTIMENT_BULLETS=SENTIMENT_BULLETS, SENTIMENT_ACTIONS=SENTIMENT_ACTIONS,
    CURRENT_FACTS=CURRENT_FACTS, GAP_ROWS=GAP_ROWS,
    CAPABILITY_MAP=CAPABILITY_MAP, ROADMAP_TABLE=ROADMAP_TABLE,
    VIS_DUAL=VIS_DUAL, RANK_POOL=RANK_POOL, SOURCE_CITE=SOURCE_CITE, COMPLIANCE=COMPLIANCE,
    OUT_FILENAME=OUT_FILENAME,
)
