#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
deck_engine.py —— 20 页 PPT 共享渲染引擎（双视觉版本）
======================================================
从 build_geo_deck.py 抽取的渲染逻辑，参数化为：
    build_deck(config: dict, palette: dict, output_path: str)

- config：case 的 CONFIG dict（品牌 / AIVO / 曝光 / 频次 / 竞品 / 话题词 / KPI / 增强变量）
- palette：来自 engine/palette.py 的预设或自定义 palette（配色/字体作为数据传入，不硬编码）
- 20 页结构、坐标、尺寸 1:1 保留自原 build_geo_deck.py，不破坏 OOB 检查。

color_map 由 palette 动态构建：slide 绘制代码用 BLUE/NAVY/CYAN/... 逻辑色名，
其实际 RGB 由当前 case 的 palette 决定。

CONFIG 新增可选键（engine/lang_style.py 定义）：
- LANG_STYLE    "mainland"（默认，与历史版本逐字一致）| "hk_business"（香港商业语言风格）
- VISUAL_STYLE  "classic"（默认原版视觉）| "guizang_card"（歸藏卡片風：
                卡片栅格封面/结尾 + 编号 chip 页眉 + 粗描边卡片）
- VERSION       "domestic"（默认，只讲国内 6 平台）| "overseas"（只讲海外 5 平台）
                | "both"（国内 6 主 + 海外 5 辅，历史叙事）
                版本维度只影响「平台叙述与 KPI 目标」，20 页结构与 QA 约束完全不变。
                实现：语言的 ver_* 键为 {domestic/overseas/both: 文案} 字典，
                经内联 DV(key) 按当前 VERSION 取值；未声明版本的历史包 DV 自动回退原值。
两版本并行输出由 build_deck.py 按 VISUAL_STYLES 循环完成；classic 文件名保持不变（原版本保留）。
"""
from pptx import Presentation
from pptx.util import Inches, Pt, Emu
from pptx.dml.color import RGBColor
from pptx.enum.text import PP_ALIGN, MSO_ANCHOR
from pptx.enum.shapes import MSO_SHAPE
from pptx.chart.data import CategoryChartData
from pptx.enum.chart import XL_CHART_TYPE, XL_LEGEND_POSITION

try:
    from .palette import build_rgb, get_palette
except ImportError:  # 允许把 engine/ 目录直接加入 sys.path 使用
    from palette import build_rgb, get_palette
try:
    from .lang_style import get_deck_lang, PPT_VISUAL_STYLES
except ImportError:  # 允许把 engine/ 目录直接加入 sys.path 使用
    from lang_style import get_deck_lang, PPT_VISUAL_STYLES


# ------------------------------------------------------------------
# CONFIG 容量校验（版面硬约束；超出必然 OOB，宁可提前报错）
# 由 build_deck 入口调用，扫描 config 内的列表型字段
# ------------------------------------------------------------------
CONFIG_LIMITS = [
    ("PLATFORM_INFLUENCE", 7),   # 含表头，第 5 页
    ("FREQ_ROWS", 6),            # 第 7 页
    ("SOURCE_TABLE", 4),         # 第 8 页
    ("INFRA_CARDS", 3),          # 第 11 页
    ("CURRENT_FACTS", 5),        # 第 13 页
    ("ECO_MAP", 5),              # 第 14 页上表
    ("COMPETITORS", 4),          # 第 14 页下表
    ("GAP_ROWS", 6),             # 第 16 页
    ("CAPABILITY_MAP", 6),       # 第 17 页
    ("TOPIC_WORDS", 5),          # 第 18 页话题卡
    ("KPI_ROWS", 5),             # 含表头，第 18 页
    ("KEY_FINDINGS", 5),         # 第 2 页
    ("STAT_CARDS", 3),           # 第 4 页
]


def _validate_config(config):
    for _name, _max in CONFIG_LIMITS:
        _seq = config.get(_name)
        if _seq is not None and len(_seq) > _max:
            raise SystemExit(
                f"[CONFIG 容量超限] {_name} 有 {len(_seq)} 项，上限 {_max} 项。"
                f"超出会导致该页元素越界（OOB），请合并或精简后重跑。")


def build_deck(config, palette, output_path):
    """根据 case config + palette 生成 20 页 PPT，返回输出路径。"""
    _validate_config(config)

    pal = get_palette(palette)
    C = build_rgb(pal)                 # {逻辑色名: RGBColor}
    CM = dict(C)                       # COLOR_MAP：逻辑色名 → RGBColor
    FONT = pal["font"]
    FNUM = pal["font_numeral"]
    chart_series = pal.get("chart_series", ["#2A5BEA", "#9DB6F5"])
    _cs0 = RGBColor(int(chart_series[0].lstrip("#")[0:2], 16),
                    int(chart_series[0].lstrip("#")[2:4], 16),
                    int(chart_series[0].lstrip("#")[4:6], 16))
    _cs1 = RGBColor(int(chart_series[1].lstrip("#")[0:2], 16),
                    int(chart_series[1].lstrip("#")[2:4], 16),
                    int(chart_series[1].lstrip("#")[4:6], 16))

    # 语言风格 + 视觉风格 + 版本维度
    D = get_deck_lang(config.get("LANG_STYLE", "mainland"))
    ST = PPT_VISUAL_STYLES[config.get("VISUAL_STYLE", "classic")]
    CHIP_MODE = ST["header_mode"] == "chip"
    VER = config.get("VERSION") or "both"   # domestic | overseas | both（默认 both=历史叙事）

    def DV(key):
        """取版本分支文案：D[key] 为 {domestic/overseas/both: 文案} 时按 VER 取值，
        否则回退到 D[key] 原值（保证未声明版本包的历史行为逐字不变）。"""
        v = D.get(key)
        if isinstance(v, dict):
            return v.get(VER, v.get("domestic", ""))
        return v

    EMU = 914400
    SW, SH = Inches(13.333), Inches(7.5)

    prs = Presentation()
    prs.slide_width = SW
    prs.slide_height = SH
    blank = prs.slide_layouts[6]

    # ---- 从 config 取变量（含默认值，增强变量未设置时原样输出）----
    G = dict(config)
    def V(k, default=None): return G.get(k, default)

    BRAND_CN = V("BRAND_CN"); BRAND_EN = V("BRAND_EN")
    CLIENT_DESC = V("CLIENT_DESC"); PRODUCT_TYPE = V("PRODUCT_TYPE")
    CONTACT = V("CONTACT", [])
    DIAG = V("DIAG", "微盟星启 GEO 診斷模型估算")
    AIVO_TOTAL = V("AIVO_TOTAL"); AIVO_RATE = V("AIVO_RATE")
    AIVO_VIS, AIVO_INFRA, AIVO_COMP, AIVO_SENT = V("AIVO_VIS", 0), V("AIVO_INFRA", 0), V("AIVO_COMP", 0), V("AIVO_SENT", 0)
    AIVO_BENCH = V("AIVO_BENCH", [55, 68, 60, 75])
    CITE_RATE = V("CITE_RATE"); CITED = V("CITED"); TOTAL_SCEN = V("TOTAL_SCEN"); GAP_PCT = V("GAP_PCT")
    PLATFORM_INFLUENCE = V("PLATFORM_INFLUENCE"); INFLUENCE_NOTE = V("INFLUENCE_NOTE")
    FREQ_ROWS = V("FREQ_ROWS"); FREQ_HL = V("FREQ_HL")
    COMPETITORS = V("COMPETITORS"); ECO_MAP = V("ECO_MAP")
    COMPETITOR_TACTICS = V("COMPETITOR_TACTICS"); COMPETITOR_HL = V("COMPETITOR_HL")
    STAT_CARDS = V("STAT_CARDS"); INDUSTRY_NOTE = V("INDUSTRY_NOTE")
    INFRA_CARDS = V("INFRA_CARDS")
    KPI_ROWS = V("KPI_ROWS"); QA_GRAPH = V("QA_GRAPH")
    SOURCE_OFFICIAL = V("SOURCE_OFFICIAL"); SOURCE_TABLE = V("SOURCE_TABLE"); SOURCE_FOOTNOTE = V("SOURCE_FOOTNOTE")
    TOPIC_WORDS = V("TOPIC_WORDS"); KEY_FINDINGS = V("KEY_FINDINGS")
    SENTIMENT_BULLETS = V("SENTIMENT_BULLETS"); SENTIMENT_ACTIONS = V("SENTIMENT_ACTIONS")
    CURRENT_FACTS = V("CURRENT_FACTS"); GAP_ROWS = V("GAP_ROWS")
    CAPABILITY_MAP = V("CAPABILITY_MAP"); ROADMAP_TABLE = V("ROADMAP_TABLE")
    # 增强变量（可选）
    VIS_DUAL = V("VIS_DUAL"); RANK_POOL = V("RANK_POOL")
    SOURCE_CITE = V("SOURCE_CITE"); COMPLIANCE = V("COMPLIANCE", {"applicable": False})

    # ---- v4 個案化文案兼容層（2026-10 由 v4 引擎移植）----
    # 三個「每客戶不同」的文案槽位：案例未提供時沿用 v2.4 語言包預設（向後兼容），
    # 提供時才覆蓋 —— 舊案例（meiriki / ori 等）的個案文案因此不會被引擎吞掉。
    INDUSTRY_SUB = V("INDUSTRY_SUB", None)        # P4 行業定位副標題
    PREF_SCORE_TEXT = V("PREF_SCORE_TEXT", None)  # P9 可被 AI 采信度評分
    INFRA_FOOTNOTE = V("INFRA_FOOTNOTE", None)    # P11 基建總評腳註
    EXCELLENT_LINE = float(V("EXCELLENT_LINE", 0.70))  # P5「優秀線」基準（個案可覆蓋）

    # ---- 工具函数 ----
    slide_state = {"n": 0}

    def slide():
        slide_state["n"] += 1
        return prs.slides.add_slide(blank)

    def bg(s, color):
        s.background.fill.solid(); s.background.fill.fore_color.rgb = color

    def rect(s, l, t, w, h, fill=None, line=None, line_w=1.0, shape=MSO_SHAPE.RECTANGLE):
        sp = s.shapes.add_shape(shape, l, t, w, h)
        if fill is None: sp.fill.background()
        else: sp.fill.solid(); sp.fill.fore_color.rgb = fill
        if line is None: sp.line.fill.background()
        else: sp.line.color.rgb = line; sp.line.width = Pt(line_w * ST["outline_boost"])
        sp.shadow.inherit = False
        return sp

    def shape_label(sp, text, size, color, bold=True, font=None):
        """在形状内部写居中文本（chip / 卡片标题用）。"""
        tf = sp.text_frame; tf.word_wrap = True
        tf.margin_left = Pt(2); tf.margin_right = Pt(2)
        tf.margin_top = Pt(1); tf.margin_bottom = Pt(1)
        p = tf.paragraphs[0]; p.alignment = PP_ALIGN.CENTER
        run = p.add_run(); run.text = text
        run.font.size = Pt(size); run.font.bold = bold
        run.font.name = font or FONT; run.font.color.rgb = color
        return sp

    def txt(s, l, t, w, h, text, size=14, color=None, bold=False, align=PP_ALIGN.LEFT,
            anchor=MSO_ANCHOR.TOP, font=None, italic=False):
        color = C["INK"] if color is None else color
        font = FONT if font is None else font
        tb = s.shapes.add_textbox(l, t, w, h)
        tf = tb.text_frame; tf.word_wrap = True; tf.vertical_anchor = anchor
        tf.margin_left = Pt(2); tf.margin_right = Pt(2)
        tf.margin_top = Pt(1); tf.margin_bottom = Pt(1)
        p = tf.paragraphs[0]; p.alignment = align
        run = p.add_run(); run.text = text
        run.font.size = Pt(size); run.font.bold = bold; run.font.italic = italic
        run.font.name = font; run.font.color.rgb = color
        return tb

    def bullets(s, l, t, w, h, items, size=14, color=None, gap=6, bullet="•  "):
        color = C["INK"] if color is None else color
        tb = s.shapes.add_textbox(l, t, w, h)
        tf = tb.text_frame; tf.word_wrap = True
        for i, it in enumerate(items):
            p = tf.paragraphs[0] if i == 0 else tf.add_paragraph()
            p.space_after = Pt(gap); p.alignment = PP_ALIGN.LEFT
            run = p.add_run(); run.text = bullet + it
            run.font.size = Pt(size); run.font.name = FONT; run.font.color.rgb = color
        return tb

    def header(s, title, sub=None):
        if CHIP_MODE:
            chip = rect(s, Inches(0.5), Inches(0.44), Inches(0.72), Inches(0.56),
                        fill=C["BLUE"], shape=MSO_SHAPE.ROUNDED_RECTANGLE)
            shape_label(chip, "%02d" % slide_state["n"], 18, C["WHITE"])
            txt(s, Inches(1.4), Inches(0.38), Inches(11.0), Inches(0.7), title,
                size=30, color=C["INK"], bold=True)
            rect(s, Inches(1.42), Inches(1.04), Inches(1.5), Inches(0.05), fill=C["CYAN"])
            if sub:
                txt(s, Inches(1.42), Inches(1.08), Inches(11.0), Inches(0.45), sub, size=14, color=C["GRAY"])
        else:
            rect(s, Inches(0.5), Inches(0.42), Inches(0.16), Inches(0.62), fill=C["BLUE"])
            txt(s, Inches(0.8), Inches(0.38), Inches(11.5), Inches(0.7), title,
                size=30, color=C["INK"], bold=True)
            if sub:
                txt(s, Inches(0.82), Inches(1.05), Inches(11.5), Inches(0.45), sub, size=14, color=C["GRAY"])
        txt(s, Inches(0.8), Inches(7.02), Inches(11.5), Inches(0.35),
            D["footer_team"], size=9, color=C["GRAY"])

    def table(s, x, y, w, h, data, col_widths, fs=11, rh=0.34, header_fill=None):
        header_fill = C["BLUE"] if header_fill is None else header_fill
        nrows = len(data); ncols = len(data[0])
        gtbl = s.shapes.add_table(nrows, ncols, x, y, w, Inches(rh * nrows + 0.1))
        tbl = gtbl.table; tbl.first_row = True; tbl.horz_banding = False
        total = sum(col_widths)
        for j, cw in enumerate(col_widths):
            tbl.columns[j].width = Emu(int(w * cw / total))
        for i, row in enumerate(data):
            tbl.rows[i].height = Inches(rh + (0.06 if i == 0 else 0))
            for j, val in enumerate(row):
                cell = tbl.cell(i, j)
                cell.margin_left = Inches(0.07); cell.margin_right = Inches(0.05)
                cell.margin_top = Inches(0.02); cell.margin_bottom = Inches(0.02)
                cell.vertical_anchor = MSO_ANCHOR.MIDDLE
                cell.fill.solid()
                cell.fill.fore_color.rgb = header_fill if i == 0 else (C["WHITE"] if i % 2 == 1 else C["CLOUD"])
                tf = cell.text_frame; tf.word_wrap = True
                p = tf.paragraphs[0]; p.alignment = PP_ALIGN.LEFT
                run = p.add_run(); run.text = str(val)
                run.font.size = Pt(fs); run.font.name = FONT
                run.font.bold = (i == 0)
                run.font.color.rgb = C["WHITE"] if i == 0 else C["INK"]
        return gtbl

    # ================================================================
    # Slide 1 — 封面（classic 原版 / guizang_card 卡片栅格）
    # ================================================================
    s = slide(); bg(s, C["NAVY"])
    if ST["cover_mode"] == "card_grid":
        chip = rect(s, Inches(0.9), Inches(0.75), Inches(2.9), Inches(0.52),
                    line=C["CYAN"], line_w=1.5, shape=MSO_SHAPE.ROUNDED_RECTANGLE)
        shape_label(chip, D["cover_tag"], 13, C["CYAN"])
        txt(s, Inches(0.88), Inches(1.55), Inches(6.9), Inches(1.15), BRAND_CN, size=40, color=C["WHITE"], bold=True)
        tcard = rect(s, Inches(0.9), Inches(2.95), Inches(4.75), Inches(0.9),
                     fill=C["BLUE"], shape=MSO_SHAPE.ROUNDED_RECTANGLE)
        shape_label(tcard, D["cover_title"], 22, C["WHITE"])
        chip1 = rect(s, Inches(0.9), Inches(4.15), Inches(3.55), Inches(0.56),
                     line=C["CYAN"], line_w=1.2, shape=MSO_SHAPE.ROUNDED_RECTANGLE)
        shape_label(chip1, DV("ver_cover_chip1"), 13, C["WHITE"], bold=False)
        _chip2 = DV("ver_cover_chip2")
        if _chip2:
            chip2 = rect(s, Inches(0.9), Inches(4.85), Inches(3.55), Inches(0.56),
                         line=C["CYAN"], line_w=1.2, shape=MSO_SHAPE.ROUNDED_RECTANGLE)
            shape_label(chip2, _chip2, 13, C["WHITE"], bold=False)
        txt(s, Inches(0.9), Inches(5.85), Inches(6.6), Inches(0.5), D["cover_slogan"], size=17, color=C["CYAN"], bold=True)
        txt(s, Inches(0.9), Inches(6.75), Inches(4.0), Inches(0.4), D["cover_brand"], size=13, color=C["WHITE"])
        # 右侧 2×2 数据卡（白卡 + 大数字）
        cards = [
            (str(AIVO_TOTAL), D["cstat_aivo"], C["BLUE"]),
            ("{:.0%}".format(CITE_RATE), D["cstat_cite"], C["BLUE"]),
            (f"#{RANK_POOL['rank']}/{RANK_POOL['total']}" if RANK_POOL else "—", D["cstat_rank"], C["BLUE"]),
            (str(len(TOPIC_WORDS)) if TOPIC_WORDS else "—", D["cstat_topics"], C["BLUE"]),
        ]
        pos = [(7.45, 1.5), (10.05, 1.5), (7.45, 3.5), (10.05, 3.5)]
        for (vx, vy), (val, lab, col) in zip(pos, cards):
            card = rect(s, Inches(vx), Inches(vy), Inches(2.5), Inches(1.7), fill=C["WHITE"],
                        shape=MSO_SHAPE.ROUNDED_RECTANGLE)
            txt(s, Inches(vx), Inches(vy + 0.18), Inches(2.5), Inches(0.75), val, size=30,
                color=col, bold=True, align=PP_ALIGN.CENTER, font=FNUM)
            txt(s, Inches(vx), Inches(vy + 1.05), Inches(2.5), Inches(0.4), lab, size=11,
                color=C["GRAY"], align=PP_ALIGN.CENTER)
    else:
        rect(s, 0, SH - Inches(2.2), SW, Inches(2.2), fill=C["BLUE"])
        rect(s, 0, 0, Inches(0.25), SH, fill=C["CYAN"])
        rect(s, Inches(0.9), Inches(0.8), Inches(0.5), Inches(0.12), fill=C["CYAN"])
        txt(s, Inches(0.9), Inches(1.0), Inches(6), Inches(0.5), D["cover_tag"], size=16, color=C["WHITE"], bold=True)
        txt(s, Inches(0.85), Inches(2.5), Inches(11.6), Inches(1.3), BRAND_CN, size=42, color=C["WHITE"], bold=True)
        txt(s, Inches(0.9), Inches(3.75), Inches(11.6), Inches(0.8), D["cover_title"], size=30, color=C["CYAN"], bold=True)
        txt(s, Inches(0.9), Inches(4.7), Inches(11.5), Inches(0.5), DV("ver_cover_platforms"), size=15, color=C["WHITE"])
        txt(s, Inches(0.9), Inches(5.3), Inches(11.5), Inches(0.5), D["cover_slogan"], size=18, color=C["WHITE"])
        txt(s, Inches(10.6), Inches(5.55), Inches(2.4), Inches(0.5), D["cover_brand"], size=14, color=C["WHITE"], align=PP_ALIGN.RIGHT)

    # ================================================================
    # Slide 2 — 執行摘要
    # ================================================================
    s = slide(); bg(s, C["CLOUD"])
    header(s, D["s2_head"], D["s2_sub"].format(diag=DIAG))
    rect(s, Inches(0.8), Inches(1.5), Inches(3.4), Inches(2.4), fill=C["NAVY"], shape=MSO_SHAPE.ROUNDED_RECTANGLE)
    txt(s, Inches(0.8), Inches(1.7), Inches(3.4), Inches(0.5), D["s2_aivo"], size=16, color=C["CYAN"], bold=True, align=PP_ALIGN.CENTER)
    txt(s, Inches(0.8), Inches(2.15), Inches(3.4), Inches(1.1), str(AIVO_TOTAL), size=66, color=C["WHITE"], bold=True, align=PP_ALIGN.CENTER, font=FNUM)
    txt(s, Inches(0.8), Inches(3.25), Inches(3.4), Inches(0.5), AIVO_RATE + D["s2_rate_suffix"], size=16, color=C["WHITE"], align=PP_ALIGN.CENTER, bold=True)
    dims = list(zip(D["s2_dims"],
                    [str(AIVO_VIS), str(AIVO_INFRA), str(AIVO_COMP), str(AIVO_SENT)],
                    [C["AMBER"], C["BLUE"], C["BLUE"], C["GREEN"]]))
    x = Inches(4.5)
    for name, sc, col in dims:
        rect(s, x, Inches(1.5), Inches(2.0), Inches(1.1), fill=C["WHITE"], line=col, line_w=1.5, shape=MSO_SHAPE.ROUNDED_RECTANGLE)
        txt(s, x, Inches(1.62), Inches(2.0), Inches(0.5), sc, size=30, color=col, bold=True, align=PP_ALIGN.CENTER, font=FNUM)
        txt(s, x, Inches(2.18), Inches(2.0), Inches(0.4), name, size=12, color=C["INK"], align=PP_ALIGN.CENTER)
        x += Inches(2.12)
    txt(s, Inches(0.8), Inches(4.2), Inches(11.5), Inches(0.4), D["s2_findings"], size=18, color=C["BLUE"], bold=True)
    bullets(s, Inches(0.8), Inches(4.7), Inches(11.8), Inches(2.2), KEY_FINDINGS, size=13.5, gap=7)

    # ================================================================
    # Slide 3 — 方法論
    # ================================================================
    s = slide(); bg(s, C["CLOUD"])
    header(s, D["s3_head"], D["s3_sub"])
    rect(s, Inches(0.8), Inches(1.5), Inches(5.7), Inches(5.0), fill=C["WHITE"], line=C["BLUE"], line_w=1.0, shape=MSO_SHAPE.ROUNDED_RECTANGLE)
    txt(s, Inches(1.05), Inches(1.7), Inches(5.2), Inches(0.5), D["s3_box1_t"], size=17, color=C["BLUE"], bold=True)
    bullets(s, Inches(1.05), Inches(2.35), Inches(5.3), Inches(2.0), D["s3_box1"], size=13, gap=7)
    txt(s, Inches(1.05), Inches(4.55), Inches(5.2), Inches(0.5), D["s3_pipe_t"], size=17, color=C["BLUE"], bold=True)
    bullets(s, Inches(1.05), Inches(5.15), Inches(5.3), Inches(1.3), D["s3_pipe"], size=13, gap=6)
    rect(s, Inches(6.8), Inches(1.5), Inches(5.7), Inches(5.0), fill=C["NAVY"], shape=MSO_SHAPE.ROUNDED_RECTANGLE)
    txt(s, Inches(7.05), Inches(1.7), Inches(5.2), Inches(0.5), D["s3_box2_t"], size=17, color=C["CYAN"], bold=True)
    bullets(s, Inches(7.05), Inches(2.35), Inches(5.3), Inches(1.7), D["s3_box2"], size=13, color=C["WHITE"], gap=7)
    txt(s, Inches(7.05), Inches(4.35), Inches(5.2), Inches(0.5), DV("ver_s3_dual_t"), size=17, color=C["CYAN"], bold=True)
    # 版本分支：domestic 只列国内 6；overseas 只列海外 5；both 双列
    _show_dom = VER in ("domestic", "both")
    _show_ovs = VER in ("overseas", "both")
    _row = 4.95
    if _show_dom:
        txt(s, Inches(7.05), Inches(_row), Inches(5.3), Inches(0.5), D["s3_domestic"], size=13, color=C["WHITE"], bold=True)
        txt(s, Inches(7.05), Inches(_row + 0.4), Inches(5.3), Inches(0.5), D["platforms_dom"], size=12.5, color=C["WHITE"])
        _row += 0.85
    if _show_ovs:
        txt(s, Inches(7.05), Inches(_row), Inches(5.3), Inches(0.5), D["s3_overseas"], size=13, color=C["WHITE"], bold=True)
        txt(s, Inches(7.05), Inches(_row + 0.4), Inches(5.3), Inches(0.5), D["platforms_ovs"], size=12.5, color=C["WHITE"])

    # ================================================================
    # Slide 4 — 行業 AI 搜索現狀
    # ================================================================
    s = slide(); bg(s, C["CLOUD"])
    header(s, D["s4_head"], INDUSTRY_SUB or DV("ver_s4_sub").format(pt=PRODUCT_TYPE))
    x = Inches(0.8)
    for big, label, col, src in STAT_CARDS:
        rect(s, x, Inches(1.6), Inches(3.7), Inches(3.5), fill=C["WHITE"], line=CM[col], line_w=1.5, shape=MSO_SHAPE.ROUNDED_RECTANGLE)
        txt(s, x, Inches(2.0), Inches(3.7), Inches(1.3), big, size=46, color=CM[col], bold=True, align=PP_ALIGN.CENTER, font=FNUM)
        txt(s, x, Inches(3.4), Inches(3.7), Inches(0.9), label, size=14, color=C["INK"], align=PP_ALIGN.CENTER)
        txt(s, x + Inches(0.15), Inches(4.55), Inches(3.4), Inches(0.5), src, size=9.5, color=C["GRAY"], align=PP_ALIGN.CENTER)
        x += Inches(3.97)
    txt(s, Inches(0.8), Inches(5.5), Inches(11.6), Inches(1.3), INDUSTRY_NOTE, size=13.5, color=C["INK"])

    # ================================================================
    # Slide 5 — AI 平臺曝光度（客戶核心關切）
    # ================================================================
    s = slide(); bg(s, C["CLOUD"])
    header(s, D["s5_head"], DV("ver_s5_sub"))
    rect(s, Inches(0.8), Inches(1.6), Inches(5.4), Inches(5.0), fill=C["NAVY"], shape=MSO_SHAPE.ROUNDED_RECTANGLE)
    txt(s, Inches(0.8), Inches(1.9), Inches(5.4), Inches(0.5), DV("ver_s5_cite_t"), size=16, color=C["CYAN"], bold=True, align=PP_ALIGN.CENTER)
    txt(s, Inches(0.8), Inches(2.4), Inches(5.4), Inches(1.3), str(CITE_RATE), size=72, color=C["WHITE"], bold=True, align=PP_ALIGN.CENTER, font=FNUM)
    txt(s, Inches(0.8), Inches(3.75), Inches(5.4), Inches(0.5),
        D["s5_cite_sub"].format(cited=CITED, total=TOTAL_SCEN), size=13, color=C["WHITE"], align=PP_ALIGN.CENTER)
    rect(s, Inches(1.1), Inches(4.45), Inches(4.8), Inches(1.5), fill=C["BLUE"], shape=MSO_SHAPE.ROUNDED_RECTANGLE)
    txt(s, Inches(1.1), Inches(4.6), Inches(4.8), Inches(0.55), D["s5_gap"].format(pct=GAP_PCT), size=22, color=C["WHITE"], bold=True, align=PP_ALIGN.CENTER)
    txt(s, Inches(1.1), Inches(5.15), Inches(4.8), Inches(0.75),
        D["s5_gap_sub"].format(n=int(CITE_RATE * 100), d=round(EXCELLENT_LINE - CITE_RATE, 2),
                                   e=f"{EXCELLENT_LINE:.2f}"), size=11.5, color=C["WHITE"], align=PP_ALIGN.CENTER)
    if VIS_DUAL:
        txt(s, Inches(0.85), Inches(6.0), Inches(5.4), Inches(0.5),
            D["s5_dual"].format(b=f"{VIS_DUAL['brand_word']:.0%}", c=f"{VIS_DUAL['category_word']:.0%}",
                                t=f"{VIS_DUAL['industry_top']:.0%}"),
            size=10.5, color=C["CYAN"])
    txt(s, Inches(6.6), Inches(1.6), Inches(6.0), Inches(0.5), D["s5_influence_t"].format(n=CITED), size=15, color=C["BLUE"], bold=True)
    table(s, Inches(6.6), Inches(2.15), Inches(6.0), Inches(3.3), PLATFORM_INFLUENCE,
          [2.2, 1.8, 1.2, 1.8], fs=12.5, rh=0.5)
    txt(s, Inches(6.6), Inches(5.7), Inches(6.0), Inches(0.9), INFLUENCE_NOTE, size=11.5, color=C["INK"])

    # ================================================================
    # Slide 6 — AI 平臺常見問答圖譜
    # ================================================================
    s = slide(); bg(s, C["CLOUD"])
    header(s, D["s6_head"], D["s6_sub"])
    table(s, Inches(0.8), Inches(1.6), Inches(11.7), Inches(5.0), QA_GRAPH,
          [1.4, 4.6, 2.2, 3.5], fs=12.5, rh=0.62)
    txt(s, Inches(0.8), Inches(6.75), Inches(11.6), Inches(0.35), DV("ver_s6_note"), size=9.5, color=C["GRAY"])
    # ================================================================
    # Slide 7 — 高頻問題被提及次數（客戶核心關切）
    # ================================================================
    s = slide(); bg(s, C["CLOUD"])
    header(s, D["s7_head"], DV("ver_s7_sub").format(total=TOTAL_SCEN, cited=CITED))
    dataB = [list(D["s7_th"])] + FREQ_ROWS
    table(s, Inches(0.8), Inches(1.7), Inches(11.7), Inches(4.6), dataB,
          [2.4, 1.6, 2.2, 1.6, 3.9], fs=12.5, rh=0.62)
    txt(s, Inches(0.8), Inches(6.5), Inches(11.6), Inches(0.5), FREQ_HL, size=12, color=C["INK"])

    # ================================================================
    # Slide 8 — 常見引用文章 / 信源清單
    # ================================================================
    s = slide(); bg(s, C["CLOUD"])
    header(s, D["s8_head"], D["s8_sub"])
    table(s, Inches(0.8), Inches(1.6), Inches(11.7), Inches(4.6), SOURCE_TABLE,
          [2.0, 5.1, 1.6, 3.0], fs=12, rh=0.7)
    _src_cite = ""
    if SOURCE_CITE:
        _src_cite = D["s8_cite"] + " / ".join(f"{n} {c}" for n, c in SOURCE_CITE[:5])
    txt(s, Inches(0.8), Inches(6.45), Inches(11.6), Inches(0.5),
        SOURCE_FOOTNOTE + _src_cite, size=11.5, color=C["INK"])

    # ================================================================
    # Slide 9 — 引用偏好框架（7 維度）
    # ================================================================
    s = slide(); bg(s, C["CLOUD"])
    header(s, D["s9_head"], PREF_SCORE_TEXT or D["s9_sub"])
    table(s, Inches(0.8), Inches(1.55), Inches(11.7), Inches(5.0), D["s9_table"],
          [2.4, 4.6, 1.8, 2.9], fs=12, rh=0.55)
    txt(s, Inches(0.8), Inches(6.7), Inches(11.6), Inches(0.35), D["s9_note"], size=10.5, color=C["GRAY"])

    # ================================================================
    # Slide 10 — AIVO 評分卡 + 雷達圖
    # ================================================================
    s = slide(); bg(s, C["CLOUD"])
    header(s, D["s10_head"], DV("ver_s10_sub").format(total=AIVO_TOTAL, rate=AIVO_RATE))
    chart_data = CategoryChartData()
    chart_data.categories = D["s10_cats"]
    chart_data.add_series(D["s10_s0"], (AIVO_VIS, AIVO_INFRA, AIVO_COMP, AIVO_SENT))
    chart_data.add_series(D["s10_s1"], tuple(AIVO_BENCH))
    gf = s.shapes.add_chart(XL_CHART_TYPE.RADAR, Inches(0.7), Inches(1.6), Inches(6.2), Inches(5.0), chart_data)
    chart = gf.chart
    chart.has_title = False; chart.has_legend = True
    chart.legend.position = XL_LEGEND_POSITION.BOTTOM
    chart.legend.include_in_layout = False; chart.legend.font.size = Pt(11)
    plot = chart.plots[0]; plot.has_data_labels = False
    chart.series[0].format.line.color.rgb = _cs0
    chart.series[0].format.line.width = Pt(2.25)
    chart.series[0].format.fill.solid(); chart.series[0].format.fill.fore_color.rgb = _cs0
    chart.series[1].format.line.color.rgb = _cs1
    chart.series[1].format.line.width = Pt(2)
    chart.series[1].format.fill.solid(); chart.series[1].format.fill.fore_color.rgb = _cs1
    # P10 注释支持 config 可选覆盖（AIVO_VIS/INFRA/COMP/SENT_NOTE），未设置走语言包默认
    _s10_notes = [
        V("AIVO_VIS_NOTE") or D["s10_notes"][0].format(rate=CITE_RATE),
        V("AIVO_INFRA_NOTE") or D["s10_notes"][1],
        V("AIVO_COMP_NOTE") or D["s10_notes"][2],
        V("AIVO_SENT_NOTE") or D["s10_notes"][3],
    ]
    aivo_notes = list(zip(D["s10_note_names"], [str(AIVO_VIS), str(AIVO_INFRA), str(AIVO_COMP), str(AIVO_SENT)],
                          _s10_notes,
                          [C["AMBER"], C["BLUE"], C["BLUE"], C["GREEN"]]))
    y = Inches(1.7)
    for name, sc, note, col in aivo_notes:
        rect(s, Inches(7.2), y, Inches(5.3), Inches(1.12), fill=C["WHITE"], line=col, line_w=1.5, shape=MSO_SHAPE.ROUNDED_RECTANGLE)
        rect(s, Inches(7.2), y, Inches(0.14), Inches(1.12), fill=col)
        txt(s, Inches(7.5), y + Inches(0.12), Inches(3.4), Inches(0.5), name, size=14, color=C["INK"], bold=True)
        txt(s, Inches(7.5), y + Inches(0.55), Inches(3.6), Inches(0.5), note, size=11, color=C["GRAY"])
        txt(s, Inches(11.4), y + Inches(0.18), Inches(1.0), Inches(0.8), sc, size=34, color=col, bold=True, align=PP_ALIGN.CENTER, font=FNUM)
        y += Inches(1.22)
    txt(s, Inches(7.2), Inches(6.7), Inches(5.3), Inches(0.4), D["s10_scale"], size=10, color=C["GRAY"])

    # ================================================================
    # Slide 11 — 品牌基建診斷
    # ================================================================
    s = slide(); bg(s, C["CLOUD"])
    header(s, D["s11_head"], D["s11_sub"])
    x = Inches(0.8); cw = Inches(3.8)
    for title, sc, body, col in INFRA_CARDS:
        rect(s, x, Inches(1.6), cw, Inches(4.6), fill=C["WHITE"], line=CM[col], line_w=1.2, shape=MSO_SHAPE.ROUNDED_RECTANGLE)
        rect(s, x, Inches(1.6), cw, Inches(0.18), fill=CM[col], shape=MSO_SHAPE.ROUNDED_RECTANGLE)
        txt(s, x + Inches(0.25), Inches(1.95), cw - Inches(0.5), Inches(0.5), title, size=18, color=CM[col], bold=True)
        txt(s, x + Inches(0.25), Inches(2.5), Inches(1.6), Inches(1.0), sc, size=44, color=CM[col], bold=True, font=FNUM)
        txt(s, x + Inches(1.9), Inches(2.6), cw - Inches(2.1), Inches(0.8), D["s11_unit"], size=13, color=C["GRAY"])
        txt(s, x + Inches(0.25), Inches(3.7), cw - Inches(0.5), Inches(2.3), body, size=13, color=C["INK"])
        x += cw + Inches(0.35)
    txt(s, Inches(0.8), Inches(6.5), Inches(11.6), Inches(0.4), INFRA_FOOTNOTE or D["s11_note"], size=11.5, color=C["INK"])

    # ================================================================
    # Slide 12 — 輿情風險監控
    # ================================================================
    s = slide(); bg(s, C["CLOUD"])
    # P12 舆情副标题按 SENT 分级：<60 较差级（语义簇风险需对冲），≥60 保持历史默认文案
    if AIVO_SENT < 60:
        _s12_sub = D.get("s12_sub_risk", "健康度 {v} · 較差 · 語義簇風險需對沖").format(v=AIVO_SENT)
        _s12_health_sub = D.get("s12_health_sub_risk", "語義簇負面集中 · 需對沖佈局")
    else:
        _s12_sub = D["s12_sub"].format(v=AIVO_SENT)
        _s12_health_sub = D["s12_health_sub"]
    header(s, D["s12_head"], _s12_sub)
    rect(s, Inches(0.8), Inches(1.6), Inches(4.0), Inches(2.4), fill=C["NAVY"], shape=MSO_SHAPE.ROUNDED_RECTANGLE)
    txt(s, Inches(0.8), Inches(1.8), Inches(4.0), Inches(0.5), D["s12_health_t"], size=16, color=C["CYAN"], bold=True, align=PP_ALIGN.CENTER)
    txt(s, Inches(0.8), Inches(2.25), Inches(4.0), Inches(1.0), str(AIVO_SENT), size=60, color=C["WHITE"], bold=True, align=PP_ALIGN.CENTER, font=FNUM)
    txt(s, Inches(0.8), Inches(3.35), Inches(4.0), Inches(0.5), _s12_health_sub, size=12.5, color=C["WHITE"], align=PP_ALIGN.CENTER)
    rect(s, Inches(5.1), Inches(1.6), Inches(7.4), Inches(5.0), fill=C["WHITE"], line=C["BLUE"], line_w=1.0, shape=MSO_SHAPE.ROUNDED_RECTANGLE)
    txt(s, Inches(5.35), Inches(1.8), Inches(7.0), Inches(0.5), D["s12_find_t"], size=16, color=C["BLUE"], bold=True)
    bullets(s, Inches(5.35), Inches(2.4), Inches(7.0), Inches(2.0), SENTIMENT_BULLETS, size=12.5, gap=7)
    txt(s, Inches(5.35), Inches(4.6), Inches(7.0), Inches(0.5), D["s12_plan_t"], size=16, color=C["BLUE"], bold=True)
    bullets(s, Inches(5.35), Inches(5.2), Inches(7.0), Inches(1.3), SENTIMENT_ACTIONS, size=12.5, color=C["INK"], gap=6)

    # ================================================================
    # Slide 13 — 橫縱分析·企業現狀（縱向）
    # ================================================================
    s = slide(); bg(s, C["CLOUD"])
    header(s, D["s13_head"], D["s13_sub"])
    data = [list(D["s13_th"])] + CURRENT_FACTS
    table(s, Inches(0.8), Inches(1.6), Inches(11.7), Inches(5.0), data, [2.6, 9.1], fs=12.5, rh=0.72)

    # ================================================================
    # Slide 14 — 橫縱分析·行業與競品（橫向）
    # ================================================================
    s = slide(); bg(s, C["CLOUD"])
    header(s, D["s14_head"], D["s14_sub"])
    eco_header = [list(D["s14_th1"])] + ECO_MAP
    table(s, Inches(0.8), Inches(1.6), Inches(11.7), Inches(2.2), eco_header, [3.4, 3.0, 3.0, 2.3], fs=12, rh=0.42)
    _rank_txt = DV("ver_s14_rank").format(q=TOTAL_SCEN // 6)
    if RANK_POOL:
        _rank_txt += D["s14_rank_pool"].format(t=RANK_POOL["total"], r=RANK_POOL["rank"])
    txt(s, Inches(0.8), Inches(4.25), Inches(11.6), Inches(0.35), _rank_txt, size=14, color=C["BLUE"], bold=True)
    data2 = [list(D["s14_th2"])]
    for name, cnt, note in COMPETITORS:
        data2.append([name, cnt, note])
    data2.append([BRAND_CN + D["s14_self_tag"], str(CITED), D["s14_self"]])
    table(s, Inches(0.8), Inches(4.65), Inches(11.7), Inches(2.2), data2, [4.4, 2.6, 4.7], fs=12, rh=0.42)

    # ================================================================
    # Slide 15 — 對手在 AI 平臺的做法（客戶核心關切）
    # ================================================================
    s = slide(); bg(s, C["CLOUD"])
    header(s, D["s15_head"], D["s15_sub"])
    rect(s, Inches(0.8), Inches(1.6), Inches(6.6), Inches(5.0), fill=C["WHITE"], line=C["BLUE"], line_w=1.0, shape=MSO_SHAPE.ROUNDED_RECTANGLE)
    txt(s, Inches(1.05), Inches(1.8), Inches(6.1), Inches(0.5), D["s15_left_t"], size=16, color=C["BLUE"], bold=True)
    bullets(s, Inches(1.05), Inches(2.4), Inches(6.1), Inches(4.0), [
        D["s15_left"].format(name=c[0], cnt=c[1], note=c[2]) for c in COMPETITORS
    ], size=12.5, gap=9)
    rect(s, Inches(7.6), Inches(1.6), Inches(5.0), Inches(5.0), fill=C["NAVY"], shape=MSO_SHAPE.ROUNDED_RECTANGLE)
    txt(s, Inches(7.85), Inches(1.8), Inches(4.5), Inches(0.5), D["s15_right_t"], size=16, color=C["CYAN"], bold=True)
    bullets(s, Inches(7.85), Inches(2.4), Inches(4.5), Inches(4.0), COMPETITOR_TACTICS,
            color=C["WHITE"], size=13, gap=10)
    txt(s, Inches(7.85), Inches(5.7), Inches(4.5), Inches(0.8), COMPETITOR_HL, size=11.5, color=C["WHITE"])

    # ================================================================
    # Slide 16 — GEO 優化問題清單
    # ================================================================
    s = slide(); bg(s, C["CLOUD"])
    header(s, D["s16_head"], D["s16_sub"])
    data = [list(D["s16_th"])] + GAP_ROWS
    table(s, Inches(0.8), Inches(1.6), Inches(11.7), Inches(4.8), data, [0.6, 3.4, 2.3, 3.6, 1.0], fs=12, rh=0.62)

    # ================================================================
    # Slide 17 — 微盟星启 GEO 能力映射
    # ================================================================
    s = slide(); bg(s, C["CLOUD"])
    header(s, D["s17_head"], D["s17_sub"])
    data = [list(D["s17_th"])] + CAPABILITY_MAP
    table(s, Inches(0.8), Inches(1.6), Inches(11.7), Inches(4.6), data, [2.7, 3.5, 3.7, 1.0], fs=11.5, rh=0.6)
    txt(s, Inches(0.8), Inches(6.45), Inches(11.6), Inches(0.4), D["s17_note"], size=10.5, color=C["GRAY"])

    # ================================================================
    # Slide 18 — 數據追蹤方案
    # ================================================================
    s = slide(); bg(s, C["CLOUD"])
    header(s, D["s18_head"], D["s18_sub"])
    rect(s, Inches(0.8), Inches(1.55), Inches(5.6), Inches(2.0), fill=C["WHITE"], line=C["BLUE"], line_w=1.0, shape=MSO_SHAPE.ROUNDED_RECTANGLE)
    txt(s, Inches(1.0), Inches(1.7), Inches(5.2), Inches(0.4), D["s18_topics_t"], size=14, color=C["BLUE"], bold=True)
    bullets(s, Inches(1.0), Inches(2.2), Inches(5.2), Inches(1.3), TOPIC_WORDS, size=12, gap=5)
    rect(s, Inches(6.6), Inches(1.55), Inches(5.9), Inches(2.0), fill=C["NAVY"], shape=MSO_SHAPE.ROUNDED_RECTANGLE)
    txt(s, Inches(6.8), Inches(1.7), Inches(5.5), Inches(0.4), DV("ver_s18_plat_t"), size=14, color=C["CYAN"], bold=True)
    # 版本分支：domestic 只列国内；overseas 只列海外；both 双列
    _plat_lines = DV("ver_s18_plat_lines")
    _py = 2.2
    for _pl in _plat_lines:
        _ptxt = D["s18_domestic"] if _pl == "dom" else D["s18_overseas"]
        txt(s, Inches(6.8), Inches(_py), Inches(5.5), Inches(0.5), _ptxt, size=12, color=C["WHITE"])
        _py += 0.55
    txt(s, Inches(0.8), Inches(3.75), Inches(11.6), Inches(0.4), DV("ver_s18_kpi_t"), size=14, color=C["BLUE"], bold=True)
    table(s, Inches(0.8), Inches(4.05), Inches(11.7), Inches(2.4), KPI_ROWS, [4.4, 2.6, 2.6, 2.6], fs=12, rh=0.46)
    _comp_note = DV("ver_s18_note")
    if COMPLIANCE.get("applicable"):
        _comp_note += D["s18_comp_note"]
    txt(s, Inches(0.8), Inches(6.6), Inches(11.6), Inches(0.35), _comp_note, size=9.5, color=C["GRAY"])

    # ================================================================
    # Slide 19 — 實施節奏與追蹤指標
    # ================================================================
    s = slide(); bg(s, C["CLOUD"])
    header(s, D["s19_head"], D["s19_sub"])
    steps = D["s19_steps"]
    n = len(steps); gap = Inches(0.3)
    cw = (SW - Inches(1.6) - gap * (n - 1)) / n
    x = Inches(0.8); y = Inches(1.7)
    for num, title in steps:
        rect(s, x, y, cw, Inches(2.3), fill=C["WHITE"], line=C["BLUE"], line_w=1.0, shape=MSO_SHAPE.ROUNDED_RECTANGLE)
        circ = s.shapes.add_shape(MSO_SHAPE.OVAL, x + cw/2 - Inches(0.42), y + Inches(0.22), Inches(0.84), Inches(0.84))
        circ.fill.solid(); circ.fill.fore_color.rgb = C["BLUE"]; circ.line.fill.background(); circ.shadow.inherit = False
        tf = circ.text_frame; tf.word_wrap = False
        p = tf.paragraphs[0]; p.alignment = PP_ALIGN.CENTER
        r = p.add_run(); r.text = num; r.font.size = Pt(26); r.font.bold = True; r.font.color.rgb = C["WHITE"]; r.font.name = FONT
        txt(s, x, y + Inches(1.2), cw, Inches(0.5), title, size=14, color=C["INK"], bold=True, align=PP_ALIGN.CENTER)
        if num != "5":
            ar = s.shapes.add_shape(MSO_SHAPE.RIGHT_ARROW, x + cw + Inches(0.01), y + Inches(0.55), gap - Inches(0.02), Inches(0.4))
            ar.fill.solid(); ar.fill.fore_color.rgb = C["CYAN"]; ar.line.fill.background(); ar.shadow.inherit = False
        x += cw + gap
    txt(s, Inches(0.8), Inches(4.4), Inches(11.6), Inches(0.4), D["s19_kpi_t"], size=14, color=C["BLUE"], bold=True)
    data = [list(D["s19_th"])] + ROADMAP_TABLE
    table(s, Inches(0.8), Inches(4.85), Inches(11.7), Inches(2.0), data, [3.0, 4.4, 3.0, 1.3], fs=11.5, rh=0.5)

    # ================================================================
    # Slide 20 — 結尾（classic 原版 / guizang_card 卡片）
    # ================================================================
    s = slide(); bg(s, C["NAVY"])
    if ST["end_mode"] == "card_grid":
        txt(s, Inches(0.9), Inches(1.25), Inches(11.5), Inches(1.0), D["end_title"], size=36, color=C["WHITE"], bold=True)
        txt(s, Inches(0.9), Inches(2.45), Inches(11.5), Inches(0.5), BRAND_CN + D["end_brandline"], size=16, color=C["CYAN"])
        rect(s, Inches(0.9), Inches(3.3), Inches(8.8), Inches(2.35), fill=C["WHITE"], shape=MSO_SHAPE.ROUNDED_RECTANGLE)
        txt(s, Inches(1.25), Inches(3.55), Inches(8.2), Inches(0.5), CONTACT[0] if len(CONTACT) > 0 else "", size=16, color=C["INK"], bold=True)
        txt(s, Inches(1.25), Inches(4.15), Inches(8.2), Inches(0.5), CONTACT[1] if len(CONTACT) > 1 else "", size=12.5, color=C["GRAY"])
        txt(s, Inches(1.25), Inches(4.7), Inches(8.2), Inches(0.5), CONTACT[2] if len(CONTACT) > 2 else "", size=12.5, color=C["GRAY"])
        txt(s, Inches(0.9), Inches(6.05), Inches(6.0), Inches(0.4), D["cover_brand"], size=13, color=C["WHITE"])
        txt(s, Inches(0), Inches(6.85), SW, Inches(0.4), D["end_footer"], size=11, color=C["WHITE"], align=PP_ALIGN.CENTER)
    else:
        rect(s, 0, SH - Inches(1.85), SW, Inches(1.85), fill=C["BLUE"])
        rect(s, 0, 0, Inches(0.25), SH, fill=C["CYAN"])
        txt(s, Inches(0.9), Inches(1.45), Inches(11.5), Inches(1.2), D["end_title"], size=40, color=C["WHITE"], bold=True)
        txt(s, Inches(0.9), Inches(2.75), Inches(11.5), Inches(0.5), BRAND_CN + D["end_brandline"], size=16, color=C["CYAN"])
        txt(s, Inches(0.9), Inches(3.65), Inches(11.5), Inches(0.45), CONTACT[0] if len(CONTACT) > 0 else "", size=15, color=C["WHITE"], bold=True)
        txt(s, Inches(0.9), Inches(4.2), Inches(11.5), Inches(0.45), CONTACT[1] if len(CONTACT) > 1 else "", size=13, color=C["WHITE"])
        txt(s, Inches(0.9), Inches(4.65), Inches(11.5), Inches(0.45), CONTACT[2] if len(CONTACT) > 2 else "", size=13, color=C["WHITE"])
        txt(s, Inches(0.9), Inches(6.55), Inches(11.5), Inches(0.4), D["end_footer"], size=11, color=C["WHITE"], align=PP_ALIGN.CENTER)

    prs.save(output_path)
    return output_path
