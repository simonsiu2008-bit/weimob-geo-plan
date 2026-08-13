#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Palette 数据模型 + 预设主题
============================
设计风格由 case 的 PALETTE 决定（作为 config 数据传入引擎），引擎不硬编码任何颜色/字体。
引擎内部只使用 11 个「逻辑色名」BLUE/NAVY/CYAN/CLOUD/INK/GRAY/WHITE/GREEN/AMBER/RED/LIGHTBLUE，
每个 palette 必须为这 11 个逻辑名提供实际 hex 值——这样 slide 绘制代码无需任何修改。

预设：
- weimob_blue   : 微盟商务蓝（默认 / 通用 B2B / 科技 / 零售）
- meiriki_teal  : 日式健康青（保健品 / 健康食品 / 中老年营养 / 母婴）
扩展：新品类按 references/design_system.md 决策规则创建自定义 palette。
"""
from pptx.dml.color import RGBColor


# 引擎固定使用的 11 个逻辑色名（slide 绘制代码直接引用这些名字）
LOGICAL_NAMES = ["BLUE", "NAVY", "CYAN", "CLOUD", "INK", "GRAY",
                 "WHITE", "GREEN", "AMBER", "RED", "LIGHTBLUE"]


PALETTES = {
    "weimob_blue": {
        "name": "微盟商务蓝",
        "colors": {
            "BLUE": "#2A5BEA", "NAVY": "#0B1F4D", "CYAN": "#18C8FF",
            "CLOUD": "#F5F7FC", "INK": "#16213A", "GRAY": "#6E7689",
            "WHITE": "#FFFFFF", "GREEN": "#059669", "AMBER": "#D97706",
            "RED": "#DC2626", "LIGHTBLUE": "#E8EEFD",
        },
        "font": "微軟雅黑",
        "font_numeral": "Arial",
        "chart_series": ["#2A5BEA", "#9DB6F5"],  # 雷达图两条序列
    },
    "meiriki_teal": {
        "name": "日式健康青",
        "colors": {
            # 微盟蓝逻辑名 → 日式健康青等价色（slide 绘制代码零修改）
            "BLUE": "#16706A", "NAVY": "#0F4A46", "CYAN": "#2E7D5B",
            "CLOUD": "#FAFAF8", "INK": "#18201D", "GRAY": "#5C6661",
            "WHITE": "#FFFFFF", "GREEN": "#2E7D5B", "AMBER": "#B5793A",
            "RED": "#C0473A", "LIGHTBLUE": "#D9E6E3",
        },
        "font": "Noto Sans CJK SC",
        "font_numeral": "JetBrains Mono",
        "chart_series": ["#16706A", "#0F4A46"],
    },
    "heritage_green": {
        "name": "自然保育綠",
        "colors": {
            # 文化遺產 / 生態旅遊 / 歷史活化 → 自然綠 + 礦石棕（文物遺產調性）
            "BLUE": "#3E7C4F", "NAVY": "#1E3D2B", "CYAN": "#6BA368",
            "CLOUD": "#F4F7F2", "INK": "#223024", "GRAY": "#6B7A6E",
            "WHITE": "#FFFFFF", "GREEN": "#3E7C4F", "AMBER": "#B07B4A",
            "RED": "#B0453A", "LIGHTBLUE": "#E4EDE2",
        },
        "font": "Noto Sans CJK SC",
        "font_numeral": "Arial",
        "chart_series": ["#3E7C4F", "#B07B4A"],
    },
}


def hex_to_rgb(hex_str):
    """'#RRGGBB' → RGBColor 对象。"""
    h = hex_str.lstrip("#")
    return RGBColor(int(h[0:2], 16), int(h[2:4], 16), int(h[4:6], 16))


def build_rgb(palette):
    """把 palette 的 colors dict（hex 字符串）转为 RGBColor 字典。"""
    return {k: hex_to_rgb(v) for k, v in palette["colors"].items()}


def validate_palette(palette):
    """校验 palette 完整性：必须提供全部 11 个逻辑色名 + font + font_numeral。"""
    missing = [n for n in LOGICAL_NAMES if n not in palette.get("colors", {})]
    if missing:
        raise ValueError(f"[palette 不完整] 缺少逻辑色名: {missing}")
    for k in ("font", "font_numeral"):
        if not palette.get(k):
            raise ValueError(f"[palette 不完整] 缺少 {k}")
    return True


def get_palette(name_or_dict):
    """按名称取预设，或直接返回自定义 palette dict。"""
    if isinstance(name_or_dict, dict):
        validate_palette(name_or_dict)
        return name_or_dict
    if name_or_dict in PALETTES:
        return PALETTES[name_or_dict]
    raise KeyError(f"[palette] 未知预设主题 '{name_or_dict}'，可选: {list(PALETTES)}")
