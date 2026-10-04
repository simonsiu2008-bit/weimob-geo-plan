#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
共享引擎：销售话术 / 讲稿文档（双轨输出的 B 轨）
================================================
客户版 PPT 保持纯净；本引擎生成仅供销售内部使用的「话术 + 讲稿」Markdown，
由 CONFIG（PPT 数据）与 TOPIC_CONFIG（话题词方案数据）共同驱动。

build_talktrack(config, topic_config, palette, output_path, lang_style)  →  生成 .md

双轨原则（references/dual_track.md）：
  · 客户版（A 轨）= PPT + 话题词方案 HTML，不含现场话术。
  · 销售版（B 轨）= 本 talktrack.md，含逐页讲稿、现场话术、可引用的硬数据、合规红线。
二者由同一 config 数据源生成，但字段不同，天然避免「话术泄露给客户」。

语言风格（lang_style，来自 CONFIG["LANG_STYLE"]，默认 "mainland"）：
  · "mainland"    —— 历史简体文案，逐字与旧版一致。
  · "hk_business" —— 香港商业语言风格（繁體書面語為主，銷售話術可帶粵語口語色彩）。
两套文案由 engine/lang_style.py 的 TT_LANG 提供，占位符一一对应。

本引擎按 CONFIG 自动推断：
  · 20 页逐页讲稿骨架（每页该讲什么、重点强调哪个数）
  · 销售开场 / 报价 / 异议处理 / 收尾话术
  · 可引用的硬数据清单（AIVO、被引用率、竞品池、排名锚点、信源榜）
  · 合规红线（COMPLIANCE.applicable=True 时）
依赖：无第三方库。
"""
import os

try:
    from .lang_style import get_tt_lang
except ImportError:  # 允许把 engine/ 目录直接加入 sys.path 使用
    from lang_style import get_tt_lang


# ---- 逐页讲稿（模板由语言包 pages 提供，数据插值在此组装）----
def _page_script(c, tc, T):
    """返回 20 页讲稿的 (页码, 标题, 讲稿正文, 重点数据) 列表。"""
    comp = c["COMPLIANCE"] or {}
    comp_applicable = comp.get("applicable", False)
    vd = c.get("VIS_DUAL")
    rp = c.get("RANK_POOL")
    sc = c.get("SOURCE_CITE")

    # 条件插入句（留空表示该数据不存在）
    dual = T["p5_dual"].format(
        b=f"{vd['brand_word']:.0%}", c=f"{vd['category_word']:.0%}") if vd else ""
    p8cite = T["p8_cite"].format(
        list=" / ".join(f"{n} {c2}" for n, c2 in sc[:5])) if sc else ""
    p14rank = T["p14_rank"].format(r=rp["rank"], t=rp["total"]) if rp else ""
    p18comp = T["p18_comp"] if comp_applicable else ""

    # 公共插值字段（focus 短语与正文共用）
    common = dict(
        total=c["AIVO_TOTAL"], cite=c["CITE_RATE"], gap=c["GAP_PCT"],
        sent=c["AIVO_SENT"],
    )

    kw = {
        1: dict(brand=c["BRAND_CN"], ptype=c["PRODUCT_TYPE"]),
        2: dict(rate=c["AIVO_RATE"], vis=c["AIVO_VIS"], infra=c["AIVO_INFRA"],
                comp=c["AIVO_COMP"], nf=len(c["KEY_FINDINGS"]), **common),
        4: dict(ncards=len(c["STAT_CARDS"])),
        5: {**common, **dict(cited=c["CITED"], total=c["TOTAL_SCEN"], dual=dual,
                             top1=c["PLATFORM_INFLUENCE"][1][0])},
        7: dict(nfreq=len(c["FREQ_ROWS"]), top=c["FREQ_ROWS"][0][0]),
        8: dict(cite=p8cite),
        10: dict(bench=c["AIVO_BENCH"], **common),
        11: dict(c1=c["INFRA_CARDS"][0][0], s1=c["INFRA_CARDS"][0][1],
                 c2=c["INFRA_CARDS"][1][0], s2=c["INFRA_CARDS"][1][1],
                 c3=c["INFRA_CARDS"][2][0], s3=c["INFRA_CARDS"][2][1]),
        12: common,
        13: dict(nf=len(c["CURRENT_FACTS"])),
        14: dict(ncomp=len(c["COMPETITORS"]), rank=p14rank),
        16: dict(n=len(c["GAP_ROWS"])),
        18: dict(ntopic=len(c["TOPIC_WORDS"]),
                 base=c["KPI_ROWS"][1][1], goal=c["KPI_ROWS"][1][3],
                 comp=p18comp),
        20: dict(contact=c["CONTACT"][0]),
    }

    rows = []
    for no, (title, body_t) in enumerate(T["pages"], 1):
        body = body_t.format(**{**common, **kw.get(no, {})})
        datas = [d.format(**{**common, **kw.get(no, {})})
                 for d in T["focus_pages"][no - 1]]
        # 条件性重点数据
        if no == 5 and vd:
            datas.append(T["focus_p5_dual"].format(
                b=f"{vd['brand_word']:.0%}", c=f"{vd['category_word']:.0%}"))
        if no == 8 and sc:
            datas.append(T["focus_p8_src"])
        if no == 14 and rp:
            datas.append(T["focus_p14_rank"].format(r=rp["rank"], t=rp["total"]))
        if no == 18 and comp_applicable:
            datas.append(T["focus_p18_comp"])
        rows.append((no, title, body, datas))
    return rows


# ---- 销售话术（开场/报价/异议/收尾；模板由语言包 sales 提供）----
def _sales_lines(c, topic_cfg, T):
    comp = c["COMPLIANCE"] or {}
    rp = c.get("RANK_POOL")
    out = []
    # 语言包 sales 固定 6 条，按数据条件过滤出实际条目：
    # 0 开场钩子 / 1 报价锚点（需 RANK_POOL）/ 2 预算 / 3 周期 /
    # 4 合规口径（需 applicable）/ 5 收尾行动号召
    for idx, (title, body_t) in enumerate(T["sales"]):
        if idx == 1 and not rp:
            continue
        if idx == 4 and not comp.get("applicable"):
            continue
        body = body_t.format(
            brand=c["BRAND_CN"], total=c["TOTAL_SCEN"],
            pct=f"{c['CITE_RATE']:.0%}",
            rest=int((1 - c["CITE_RATE"]) * 100),
            n=int(c["CITE_RATE"] * 100),
            t=(rp or {}).get("total", ""), r=(rp or {}).get("rank", ""),
            industry=comp.get("industry", ""),
            contact=c["CONTACT"][0],
        )
        out.append((title, body))
    return out


def build_talktrack(config, topic_config=None, palette_name="weimob_blue",
                    output_path="talktrack.md", lang_style="mainland"):
    """config: 该 case 的 CONFIG dict；topic_config: 可选，话题词方案数据。"""
    c = config
    tc = topic_config or {}
    comp = c.get("COMPLIANCE") or {}
    comp_applicable = comp.get("applicable", False)
    T = get_tt_lang(lang_style)
    VER = c.get("VERSION") or "both"

    def DV(key, default=None):
        """版本分支文案：T[key] 为 {domestic/overseas/both: 值} 时按 VER 取值。"""
        v = T.get(key)
        if isinstance(v, dict):
            return v.get(VER, v.get("both", default))
        return v

    md = []
    md.append(T["title"].format(brand=c["BRAND_CN"]))
    md.append("")
    md.append(T["banner"].format(diag=c["DIAG"]))
    md.append("")
    md.append(T["client"].format(v=c["CLIENT_DESC"]))
    md.append(T["category"].format(v=c["PRODUCT_TYPE"]))
    md.append(T["palette_line"].format(v=palette_name))
    md.append("")

    # 合规横幅
    if comp_applicable:
        md.append(T["comp_title"])
        md.append("")
        md.append(T["comp_industry"].format(v=comp.get("industry", "")))
        md.append(T["comp_forbid"].format(v=", ".join(comp.get("forbidden", []))))
        md.append(T["comp_allowed"].format(v=", ".join(comp.get("allowed", []))))
        md.append(T["comp_note"].format(v=comp.get("note", "")))
        md.append("")

    # 一、可引用的硬数据清单
    md.append(T["sec1"])
    md.append("")
    md.append("| " + " | ".join(T["sec1_th"]) + " |")
    md.append("| --- | --- | --- |")
    md.append("| " + " | ".join([
        T["row_aivo"][0],
        T["row_aivo"][1].format(total=c["AIVO_TOTAL"], rate=c["AIVO_RATE"]),
        T["row_aivo"][2]]) + " |")
    md.append("| " + " | ".join([
        DV("ver_row_cite")[0],
        DV("ver_row_cite")[1].format(rate=c["CITE_RATE"], cited=c["CITED"], total=c["TOTAL_SCEN"]),
        DV("ver_row_cite")[2]]) + " |")
    md.append("| " + " | ".join([
        T["row_gap"][0],
        T["row_gap"][1].format(pct=c["GAP_PCT"]),
        T["row_gap"][2].format(n=int(c["CITE_RATE"] * 100))]) + " |")
    md.append("| " + " | ".join([
        T["row_sent"][0],
        T["row_sent"][1].format(v=c["AIVO_SENT"]),
        T["row_sent"][2]]) + " |")
    if c.get("VIS_DUAL"):
        md.append("| " + " | ".join([
            T["row_dual"][0],
            T["row_dual"][1].format(b=f"{c['VIS_DUAL']['brand_word']:.0%}",
                                    c=f"{c['VIS_DUAL']['category_word']:.0%}"),
            T["row_dual"][2]]) + " |")
    if c.get("RANK_POOL"):
        md.append("| " + " | ".join([
            T["row_rank"][0],
            T["row_rank"][1].format(r=c["RANK_POOL"]["rank"], t=c["RANK_POOL"]["total"]),
            T["row_rank"][2]]) + " |")
    if c.get("SOURCE_CITE"):
        md.append("| " + " | ".join([
            T["row_src"][0],
            T["row_src"][1].format(list=" / ".join(f"{n} {s}" for n, s in c["SOURCE_CITE"][:3])),
            T["row_src"][2]]) + " |")
    md.append("")

    # 二、销售话术
    md.append(T["sec2"])
    md.append("")
    for title, line in _sales_lines(c, tc, T):
        md.append(f"### {title}")
        md.append("")
        md.append(f"> {line}")
        md.append("")

    # 三、逐页讲稿
    md.append(T["sec3"])
    md.append("")
    for no, title, body, datas in _page_script(c, tc, T):
        md.append(T["page_head"].format(no=no, title=title))
        md.append("")
        md.append(body)
        valid = [f"`{d}`" for d in datas if d]
        if valid:
            md.append("")
            md.append(T["focus"].format(items=", ".join(valid)))
        md.append("")

    # 四、话题词话题（若有）
    if tc and tc.get("TOPICS"):
        md.append(T["sec4"])
        md.append("")
        for t in tc["TOPICS"]:
            md.append(f"### {t['no']} · {t['title']}")
            md.append("")
            md.append(T["t_intent"].format(v=t["intent"]))
            md.append(T["t_script"].format(v=t["script_v"]))
            if t.get("comp_note"):
                md.append(T["t_comp"].format(v=t["comp_note"]))
            md.append("")

    # 五、结尾联系方式
    md.append("---")
    md.append("")
    md.append(T["ending"].format(contact=c["CONTACT"][0]))
    md.append("")
    return "\n".join(md)


if __name__ == "__main__":
    print("本模块是共享引擎，请通过 scripts/build_talktrack.py CLI 调用。")
