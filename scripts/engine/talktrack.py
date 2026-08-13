#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
共享引擎：销售话术 / 讲稿文档（双轨输出的 B 轨）
================================================
客户版 PPT 保持纯净；本引擎生成仅供销售内部使用的「话术 + 讲稿」Markdown，
由 CONFIG（PPT 数据）与 TOPIC_CONFIG（话题词方案数据）共同驱动。

build_talktrack(config, topic_config, palette, output_path)  →  生成 .md

双轨原则（references/dual_track.md）：
  · 客户版（A 轨）= PPT + 话题词方案 HTML，不含现场话术。
  · 销售版（B 轨）= 本 talktrack.md，含逐页讲稿、现场话术、可引用的硬数据、合规红线。
二者由同一 config 数据源生成，但字段不同，天然避免「话术泄露给客户」。

本引擎按 CONFIG 自动推断：
  · 20 页逐页讲稿骨架（每页该讲什么、重点强调哪个数）
  · 销售开场 / 报价 / 异议处理 / 收尾话术
  · 可引用的硬数据清单（AIVO、被引用率、竞品池、排名锚点、信源榜）
  · 合规红线（COMPLIANCE.applicable=True 时）
依赖：无第三方库。
"""
import os


# ---- 每页讲稿骨架（映射 CONFIG 数据，自动填数）----
def _page_script(c, topic_cfg):
    """返回 20 页讲稿的 (页码, 标题, 讲稿正文, 重点数据) 列表。"""
    diag = c["DIAG"]
    comp = c["COMPLIANCE"] or {}
    comp_applicable = comp.get("applicable", False)
    rows = []

    rows.append((
        1, "封面",
        f"开场一句带出定位：{c['BRAND_CN']} · {c['PRODUCT_TYPE']}。"
        "今天这份《微盟星启 GEO 优化方案》帮客户回答三件事：客户品牌现在在 AI 里排第几、为什么、以及 90–180 天能追到哪。",
        ["品牌定位一句话", "今天讲三件事"]))
    rows.append((
        2, "執行摘要",
        f"直接抛 AIVO 总分 {c['AIVO_TOTAL']}（{c['AIVO_RATE']}）。"
        f"四个维度拆开看：AI 可见度 {c['AIVO_VIS']}、基建 {c['AIVO_INFRA']}、竞争 {c['AIVO_COMP']}、舆情 {c['AIVO_SENT']}。"
        f"关键发现共 {len(c['KEY_FINDINGS'])} 条，重点讲『被引用率 {c['CITE_RATE']}，行业头部 0.70，差距明确』这一条最有体感。",
        [f"AIVO {c['AIVO_TOTAL']}", f"被引用率 {c['CITE_RATE']}", "关键发现"]))
    rows.append((
        3, "方法論",
        "讲方法论是为建立专业感：AIVO 四维等权（各 25%）、4 阶段流水线、国内 6 平台（主）+ 海外 5 平台（辅）。"
        "强调『每个数字都是诊断模型估算，可复测』，打消客户对数据可信度的疑虑。",
        ["AIVO 四维", "4 阶段", "国内 6 + 海外 5 平台"]))
    rows.append((
        4, "行業 AI 搜索現狀",
        f"用 {len(c['STAT_CARDS'])} 张行业现状卡带出市场机会。"
        f"收尾读 INDUSTRY_NOTE：行业竞争白热化、用户靠 AI 决策，客户品牌是利基定位、有基础露出但距优秀线差距明确。",
        ["行业现状卡", "距优秀线 0.70"]))
    rows.append((
        5, "AI 平臺曝光度 · 體檢",
        f"这是客户最关心的数字页。国内 6 平台平均被引用率 {c['CITE_RATE']}（{c['CITED']}/{c['TOTAL_SCEN']} 场景），曝光缺口 {c['GAP_PCT']}%。"
        + (f"双指标：品牌词 {c['VIS_DUAL']['brand_word']:.0%} / 品类词 {c['VIS_DUAL']['category_word']:.0%}。"
           "点名『指名你在、陌生人不认识你』这个反差。" if c.get("VIS_DUAL") else "")
        + f"平台影响力：{c['PLATFORM_INFLUENCE'][1][0]} 贡献最高，是最高效杠杆。",
        [f"被引用率 {c['CITE_RATE']}", f"缺口 {c['GAP_PCT']}%",
         (f"双指标 {c['VIS_DUAL']['brand_word']:.0%}/{c['VIS_DUAL']['category_word']:.0%}" if c.get("VIS_DUAL") else None)]))
    rows.append((
        6, "常見問答圖譜",
        "讲客户行业里用户到底在问什么。按意图聚类（选购/比价/正品/门市/成分/海外），"
        "强调『这些问题的答案，现在 AI 给的不是你』，是内容优化的直接依据。",
        ["问答复意图聚类", "内容缺口"]))
    rows.append((
        7, "高頻問題被提及次數",
        f"共 {len(c['FREQ_ROWS'])} 类高频问题。最高提及的是「{c['FREQ_ROWS'][0][0]}」类，"
        f"但命中率低——这是内容补强第一顺位。读 FREQ_HL 收尾。",
        ["高频问题提及率", "补强第一顺位"]))
    rows.append((
        8, "常見引用文章 / 信源清單",
        f"信源类型 4 类，重点是『缺失项』= 内容改造机会。"
        + (f"信源引用次数榜：{' / '.join(f'{n} {c2}' for n, c2 in (c.get('SOURCE_CITE') or [])[:5])}。"
           "上榜信源就是 AI 的取材来源，投放优先级按此排序。" if c.get("SOURCE_CITE") else ""),
        ["信源类型", "缺失项（机会）",
         ("信源引用榜" if c.get("SOURCE_CITE") else None)]))
    rows.append((
        9, "引用偏好框架（7 維度）",
        "讲 AI 喜欢什么样的内容：权威信源、知识图谱、结构化 FAQ、数据证据、新鲜度、多语言、多模态。"
        "『结构化 FAQ 与简中多语是最优先补强项』——直接对应对客户的优化模块。",
        ["7 维度", "优先补强：结构化FAQ"]))
    rows.append((
        10, "AIVO 四維評分卡",
        f"总分 {c['AIVO_TOTAL']}。雷达图对比行业基准 {c['AIVO_BENCH']}。"
        "讲法：总分看着一般，但拆分后能精准定位『哪一维在拖后腿、哪一维已是亮点』——这正是优化起点。",
        [f"AIVO {c['AIVO_TOTAL']}", "vs 行业基准"]))
    rows.append((
        11, "品牌基建診斷",
        f"三张基建卡：{c['INFRA_CARDS'][0][0]} {c['INFRA_CARDS'][0][1]} / {c['INFRA_CARDS'][1][0]} {c['INFRA_CARDS'][1][1]} / {c['INFRA_CARDS'][2][0]} {c['INFRA_CARDS'][2][1]}。"
        "讲法：官方站+权威媒体已有基础，但『国内自媒体缺位 + 简中结构化深度不足』是切入机会。",
        ["官网站点评分", "自媒体缺口（最大短板）"]))
    rows.append((
        12, "輿情風險監控",
        f"舆情健康度 {c['AIVO_SENT']}，低风险。读 SENTIMENT_BULLETS：未检索到品牌专属恶评，负面多为行业层级。"
        "给客户吃定心丸，同时提示可上舆情监测服务。",
        [f"舆情健康度 {c['AIVO_SENT']}", "低风险"]))
    rows.append((
        13, "橫縱分析 · 企業現狀",
        f"{len(c['CURRENT_FACTS'])} 条客观事实，只摆证据不评判。"
        "重点讲资质状态（若合规适用）与数字资产现状，让客户看到『我们已读懂你的业务』。",
        ["客观事实", "数字资产现状"]))
    rows.append((
        14, "橫縱分析 · 行業與競品",
        f"竞品池 {len(c['COMPETITORS'])} 个品牌。"
        + (f"本品牌在品类话题排 #{c['RANK_POOL']['rank']}（池 {c['RANK_POOL']['total']}）。" if c.get("RANK_POOL") else "")
        + "用 ECO_MAP 讲清楚各品牌在 AI 生态的位置，让客户看见差距与可追的空间。",
        ["竞品对比",
         (f"排名 #{c['RANK_POOL']['rank']}/{c['RANK_POOL']['total']}" if c.get("RANK_POOL") else None)]))
    rows.append((
        15, "對手在 AI 平臺的做法",
        "讲对手靠『品牌权威 + 聚合占位 + 自媒体声量』三件套占住 AI 回答。"
        "本品牌补齐同构三件套即可追平——这是给客户的信心。",
        ["对手三件套", "本品牌可借镜"]))
    rows.append((
        16, "GEO 優化問題清單",
        f"{len(c['GAP_ROWS'])} 条数据驱动的问题清单，每一条都带证据与优先级。"
        "讲法：这不是拍脑袋，是 15 问 × 6 平台测出来的。",
        ["问题清单", "优先级排序"]))
    rows.append((
        17, "微盟星启 GEO 能力映射",
        "把问题映射到微盟星启四大能力模块（AI 可见性监测 / 舆情指数 / 内容创作优化 / 智能媒体分发），"
        "每一条都配可追踪指标——证明服务不是『卖概念』而是『卖可量化的闭环』。",
        ["四大能力模块", "指标闭环"]))
    rows.append((
        18, "數據追蹤方案",
        f"核心话题词 {len(c['TOPIC_WORDS'])} 条 + 平台双版本 + KPI 基线→目标（被引用率 {c['KPI_ROWS'][1][1]}→{c['KPI_ROWS'][1][3]}）。"
        + (f"合规红线：受限行业仅做成分/正品/品质/选购科普，不作功效声称。" if comp_applicable else ""),
        ["话题词", "KPI 目标", ("合规红线" if comp_applicable else None)]))
    rows.append((
        19, "實施節奏與追蹤指標",
        "五步标准服务流程：诊断评估→优化策略→执行上线→效果监控→持续优化。"
        "配 ROADMAP_TABLE 讲清 P1/P2/P3 每阶段的动作与追踪指标。",
        ["五步流程", "P1/P2/P3 节奏"]))
    rows.append((
        20, "結尾",
        "收尾给联系方式 + 行动号召：约下一次诊断基线跑测。"
        f"联系方式：{c['CONTACT'][0]}。",
        ["联系方式", "行动号召"]))

    return rows


# ---- 销售话术（开场/报价/异议/收尾）----
def _sales_lines(c, topic_cfg):
    comp = c["COMPLIANCE"] or {}
    lines = []
    lines.append(("开场钩子",
        f"『我在 {c['BRAND_CN']} 这个品类下，用国内 6 个 AI 问了 {c['TOTAL_SCEN']} 个问题，"
        f"发现 AI 平均只在你 {c['CITE_RATE']:.0%} 次会提到你。剩下 {int((1 - c['CITE_RATE']) * 100)}% 的新客，"
        "根本不知道你的存在。这不是产品问题，是 AI 内容在场率问题——今天我就告诉你答案在哪里。』"))
    if c.get("RANK_POOL"):
        lines.append(("报价锚点（最有感的一个数）",
            f"『品类话题竞品池 {c['RANK_POOL']['total']} 个品牌，你排 #{c['RANK_POOL']['rank']}。"
            "这个排名每个月都能复测——它涨了，说明钱花对了。』"))
    lines.append(("异议处理 · 预算",
        "『这笔投入不是广告费，是内容资产。广告停了就没有了，而这篇内容只要被 AI 收录，就会持续被引用。"
        f"现在你每 100 次相关提问只有 {int(c['CITE_RATE']*100)} 次被看见，补到位后这个数字是可量化提升的。』"))
    lines.append(("异议处理 · 周期",
        "『第一阶段 1–2 周先建基线，把『现在排第几』这个数字测出来；90 天看第一次进榜，180 天看排名进入行业前十。每一步都有可复测的指标，不是空头支票。』"))
    if comp.get("applicable"):
        lines.append(("合规口径（受监管品类必读）",
            f"『客户是受限行业（{comp.get('industry','')}），内容只能做成分事实、正品辨别、品质认证、选购方法四件事，"
            "全程不碰功效声称。这不是限制，反而是差异化——竞品只能打功效牌，我们用原装与品质的硬事实建立信任，且完全合法。』"))
    lines.append(("收尾行动号召",
        "『下一步我安排一次 20 问 × 6 平台的诊断基线跑测，出一份带行业排名的话题基线报告。"
        f"拿到基线后我们再定 90 天目标。联系方式：{c['CONTACT'][0]}。』"))
    return lines


def build_talktrack(config, topic_config=None, palette_name="weimob_blue", output_path="talktrack.md"):
    """config: 该 case 的 CONFIG dict；topic_config: 可选，话题词方案数据。"""
    c = config
    tc = topic_config or {}
    comp = c.get("COMPLIANCE") or {}
    comp_applicable = comp.get("applicable", False)

    md = []
    md.append(f"# {c['BRAND_CN']} · 微盟星启 GEO 销售话术 / 讲稿")
    md.append("")
    md.append(f"> **内部资料，仅限销售使用 · 不进入客户版 PPT**　·　口径：{c['DIAG']}")
    md.append("")
    md.append(f"- 客户定位：{c['CLIENT_DESC']}")
    md.append(f"- 主营品类：{c['PRODUCT_TYPE']}")
    md.append(f"- 主题 palette：`{palette_name}`")
    md.append("")

    # 合规横幅
    if comp_applicable:
        md.append("## 合规红线（硬性）")
        md.append("")
        md.append(f"- 行业：{comp.get('industry', '')}")
        md.append(f"- 禁用词：{', '.join(comp.get('forbidden', []))}")
        md.append(f"- 仅可做：{', '.join(comp.get('allowed', []))}")
        md.append(f"- 说明：{comp.get('note', '')}")
        md.append("")

    # 一、可引用的硬数据清单
    md.append("## 一、可引用的硬数据清单（说服客户用）")
    md.append("")
    md.append("| 数据 | 数值 | 话术要点 |")
    md.append("| --- | --- | --- |")
    md.append(f"| AIVO 总分 | {c['AIVO_TOTAL']}（{c['AIVO_RATE']}） | 四维等权，可拆分定位短板 |")
    md.append(f"| 国内 6 平台被引用率 | {c['CITE_RATE']}（{c['CITED']}/{c['TOTAL_SCEN']}） | 距头部 0.70 差距明确 |")
    md.append(f"| 曝光缺口 | {c['GAP_PCT']}% | 每 100 次提问仅 {int(c['CITE_RATE']*100)} 次被看见 |")
    md.append(f"| 舆情健康度 | {c['AIVO_SENT']} | 低风险，无品牌专属恶评 |")
    if c.get("VIS_DUAL"):
        md.append(f"| 可见度双指标 | 品牌词 {c['VIS_DUAL']['brand_word']:.0%} / 品类词 {c['VIS_DUAL']['category_word']:.0%} | 指名你在、陌生人不认识你 |")
    if c.get("RANK_POOL"):
        md.append(f"| 品类排名锚点 | #{c['RANK_POOL']['rank']} / {c['RANK_POOL']['total']} | 每月可复测，涨了=钱花对 |")
    if c.get("SOURCE_CITE"):
        md.append(f"| 信源引用榜 | {' / '.join(f'{n} {s}' for n, s in c['SOURCE_CITE'][:3])} | 上榜信源=AI 取材来源 |")
    md.append("")

    # 二、销售话术
    md.append("## 二、销售话术（开场 / 报价 / 异议 / 收尾）")
    md.append("")
    for title, line in _sales_lines(c, tc):
        md.append(f"### {title}")
        md.append("")
        md.append(f"> {line}")
        md.append("")

    # 三、逐页讲稿
    md.append("## 三、逐页讲稿（对应客户版 PPT 20 页）")
    md.append("")
    for no, title, body, datas in _page_script(c, tc):
        md.append(f"### 第 {no} 页 · {title}")
        md.append("")
        md.append(body)
        valid = [f"`{d}`" for d in datas if d]
        if valid:
            md.append("")
            md.append(f"重点数据：{', '.join(valid)}")
        md.append("")

    # 四、话题词话题（若有）
    if tc and tc.get("TOPICS"):
        md.append("## 四、话题词逐题话术（来自话题词方案）")
        md.append("")
        for t in tc["TOPICS"]:
            md.append(f"### {t['no']} · {t['title']}")
            md.append("")
            md.append(f"- 意图：{t['intent']}")
            md.append(f"- 现场话术：{t['script_v']}")
            if t.get("comp_note"):
                md.append(f"- 合规提示：{t['comp_note']}")
            md.append("")

    # 五、结尾联系方式
    md.append("---")
    md.append("")
    md.append("微盟星启 GEO 运营团队　·　" + c["CONTACT"][0])
    md.append("")
    return "\n".join(md)


if __name__ == "__main__":
    print("本模块是共享引擎，请通过 scripts/build_talktrack.py CLI 调用。")
