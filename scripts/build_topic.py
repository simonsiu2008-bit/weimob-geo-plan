#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
CLI：生成「国内版 GEO 话题词方案」HTML
======================================
用法： python3 scripts/build_topic.py cases/<name>
       （可选） python3 scripts/build_topic.py cases/<name> --out /path/custom.html

读取 cases/<name>/topic_config.py 的 TOPIC_CONFIG，调用共享引擎 topic_engine.build_topic_html，
输出到 cases/<name>/output/<OUT_FILENAME>。
"""
import argparse
import importlib.util
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "engine"))
from topic_engine import build_topic_html


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
    tc_path = os.path.join(case_dir, "topic_config.py")
    if not os.path.exists(tc_path):
        sys.exit(f"[话题词] 缺少 {tc_path}。该 case 尚未创建话题词数据。")

    cfg = load_module(tc_path).TOPIC_CONFIG
    out_dir = os.path.join(case_dir, "output")
    os.makedirs(out_dir, exist_ok=True)
    out = args.out or os.path.join(out_dir, cfg["OUT_FILENAME"])

    html = build_topic_html(cfg)
    with open(out, "w", encoding="utf-8") as f:
        f.write(html)
    print("saved", out, "bytes:", len(html))


if __name__ == "__main__":
    main()
