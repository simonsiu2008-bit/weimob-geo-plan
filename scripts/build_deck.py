#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
CLI 入口：生成 20 页 GEO 方案 PPT（支持多视觉版本并行输出）
================================================================
用法： python3 scripts/build_deck.py cases/<case_name> [--palette <预设名>] [--style <视觉版本>]
       python3 scripts/build_deck.py cases/acme
       python3 scripts/build_deck.py cases/acme --palette weimob_blue
       python3 scripts/build_deck.py cases/acme --style guizang_card   （只构建指定版本）

从 cases/<name>/config.py 读取 CONFIG（+ PALETTE），调用共享引擎生成 PPT。
视觉版本由 config.py 的 VISUAL_STYLES 决定（默认 ["classic"]，历史行为不变）：
- classic       → output/<OUT_FILENAME>              （原版，文件名与历史完全一致）
- guizang_card  → output/<OUT_FILENAME 去扩展名>_歸藏卡片版.pptx
语言风格由 config.py 的 LANG_STYLE 决定（默认 "mainland"；"hk_business" 为香港商业语言风格）。
"""
import argparse
import importlib.util
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
sys.path.insert(0, os.path.join(HERE, "engine"))

from deck_engine import build_deck
from palette import get_palette
from lang_style import resolve_styles, versioned_filename, resolve_version


def load_config(case_dir):
    cfg_path = os.path.join(case_dir, "config.py")
    if not os.path.exists(cfg_path):
        raise SystemExit(f"[build_deck] 未找到 {cfg_path}")
    spec = importlib.util.spec_from_file_location("case_config", cfg_path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod.CONFIG, getattr(mod, "PALETTE", "weimob_blue"), mod


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("case_dir", help="case 目录，如 cases/acme")
    ap.add_argument("--palette", default=None, help="覆盖配色预设名")
    ap.add_argument("--style", default=None, help="只构建指定视觉版本（如 guizang_card）")
    ap.add_argument("--out", default=None, help="覆盖输出路径（仅单版本时有效）")
    args = ap.parse_args()

    case_dir = os.path.abspath(args.case_dir)
    config, palette, mod = load_config(case_dir)
    if args.palette:
        palette = args.palette
    pal = get_palette(palette)

    out_dir = os.path.join(case_dir, "output")
    os.makedirs(out_dir, exist_ok=True)

    styles = resolve_styles(mod)
    if args.style:
        styles = [args.style]
    version = resolve_version(mod)

    for style in styles:
        cfg2 = dict(config)
        cfg2["VISUAL_STYLE"] = style
        cfg2.setdefault("LANG_STYLE", "mainland")
        cfg2["VERSION"] = version
        out = args.out if (args.out and len(styles) == 1) else \
            os.path.join(out_dir, versioned_filename(config["OUT_FILENAME"], style))
        build_deck(cfg2, pal, out)
        print("saved", out, f"[{cfg2['LANG_STYLE']}/{style}/{version}]")


if __name__ == "__main__":
    main()
