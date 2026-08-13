#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
CLI 入口：生成 20 页 GEO 方案 PPT
用法： python3 build_deck.py cases/<case_name> [--palette <预设名>]
     python3 build_deck.py cases/primo
     python3 build_deck.py cases/meiriki --palette meiriki_teal
从 cases/<name>/config.py 读取 CONFIG（+ PALETTE），调用共享引擎生成 PPT。
"""
import sys, os, importlib.util

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)

from engine.deck_engine import build_deck
from engine.palette import get_palette


def load_config(case_dir):
    cfg_path = os.path.join(case_dir, "config.py")
    if not os.path.exists(cfg_path):
        raise SystemExit(f"[build_deck] 未找到 {cfg_path}")
    spec = importlib.util.spec_from_file_location("case_config", cfg_path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod.CONFIG, getattr(mod, "PALETTE", "weimob_blue")


def main():
    if len(sys.argv) < 2:
        raise SystemExit(__doc__)
    case_dir = os.path.abspath(sys.argv[1])
    palette_override = None
    if "--palette" in sys.argv:
        palette_override = sys.argv[sys.argv.index("--palette") + 1]

    config, palette = load_config(case_dir)
    if palette_override:
        palette = palette_override
    pal = get_palette(palette)

    out = os.path.join(case_dir, "output", config["OUT_FILENAME"])
    os.makedirs(os.path.dirname(out), exist_ok=True)
    build_deck(config, palette, out)
    print("saved", out)


if __name__ == "__main__":
    main()
