#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
CLI：生成销售话术 / 讲稿文档（双轨 B 轨）
========================================
用法： python3 scripts/build_talktrack.py cases/<name>

读取 cases/<name>/config.py 的 CONFIG（+ 可选 topic_config.py 的 TOPIC_CONFIG），
调用共享引擎 talktrack.build_talktrack，输出到 cases/<name>/output/<name>_销售话术讲稿.md。
"""
import argparse
import importlib.util
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "engine"))
from talktrack import build_talktrack


def load_module(path):
    spec = importlib.util.spec_from_file_location("case_cfg", path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("case_dir", help="case 目录，如 cases/meiriki")
    ap.add_argument("--out", default=None, help="覆盖输出路径")
    args = ap.parse_args()

    case_dir = args.case_dir.rstrip("/")
    cfg_path = os.path.join(case_dir, "config.py")
    if not os.path.exists(cfg_path):
        sys.exit(f"[话术] 缺少 {cfg_path}")

    cfg_mod = load_module(cfg_path)
    config = cfg_mod.CONFIG

    # 可选加载话题词方案数据（提供逐题话术）
    topic_config = None
    tc_path = os.path.join(case_dir, "topic_config.py")
    if os.path.exists(tc_path):
        topic_config = load_module(tc_path).TOPIC_CONFIG

    out_dir = os.path.join(case_dir, "output")
    os.makedirs(out_dir, exist_ok=True)
    out = args.out or os.path.join(out_dir, f"{config['BRAND_CN'].replace(' ', '_')}_销售话术讲稿.md")

    palette_name = getattr(cfg_mod, "PALETTE", "weimob_blue")
    md = build_talktrack(config, topic_config, palette_name=palette_name)
    with open(out, "w", encoding="utf-8") as f:
        f.write(md)
    print("saved", out, "chars:", len(md))


if __name__ == "__main__":
    main()
