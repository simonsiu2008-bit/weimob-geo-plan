#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
CLI：生成「国内版 GEO 话题词方案」HTML（支持多视觉版本并行输出）
================================================================
用法： python3 scripts/build_topic.py cases/<name>
       python3 scripts/build_topic.py cases/<name> --style guizang_card   （只构建指定版本）
       （可选） python3 scripts/build_topic.py cases/<name> --out /path/custom.html

读取 cases/<name>/topic_config.py 的 TOPIC_CONFIG，调用共享引擎 topic_engine.build_topic_html。
视觉版本由 topic_config.py 的 VISUAL_STYLES 决定（默认 ["classic"]，历史行为不变）：
- classic       → output/<OUT_FILENAME>              （原版，文件名与历史完全一致）
- guizang_card  → output/<OUT_FILENAME 去扩展名>_歸藏卡片版.html
语言风格由 LANG_STYLE 决定（默认 "mainland"；"hk_business" 为香港商业语言风格）。
"""
import argparse
import importlib.util
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "engine"))
from topic_engine import build_topic_html
from lang_style import resolve_styles, versioned_filename, resolve_version


def load_module(path):
    spec = importlib.util.spec_from_file_location("case_cfg", path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("case_dir", help="case 目录，如 cases/meiriki")
    ap.add_argument("--style", default=None, help="只构建指定视觉版本（如 guizang_card）")
    ap.add_argument("--out", default=None, help="覆盖输出路径（仅单版本时有效）")
    args = ap.parse_args()

    case_dir = args.case_dir.rstrip("/")
    tc_path = os.path.join(case_dir, "topic_config.py")
    if not os.path.exists(tc_path):
        sys.exit(f"[话题词] 缺少 {tc_path}。该 case 尚未创建话题词数据。")

    mod = load_module(tc_path)
    cfg = mod.TOPIC_CONFIG
    out_dir = os.path.join(case_dir, "output")
    os.makedirs(out_dir, exist_ok=True)

    styles = resolve_styles(mod)
    if args.style:
        styles = [args.style]
    version = resolve_version(mod)

    for style in styles:
        cfg2 = dict(cfg)
        cfg2["VISUAL_STYLE"] = style
        cfg2["VERSION"] = version
        out = args.out if (args.out and len(styles) == 1) else \
            os.path.join(out_dir, versioned_filename(cfg["OUT_FILENAME"], style))
        html = build_topic_html(cfg2)
        with open(out, "w", encoding="utf-8") as f:
            f.write(html)
        print("saved", out, f"[{cfg2.get('LANG_STYLE', 'mainland')}/{style}/{version}]", "bytes:", len(html))


if __name__ == "__main__":
    main()
