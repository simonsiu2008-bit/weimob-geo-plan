#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
CLI：生成「痛點問答證據卡」HTML
================================
用法： python3 scripts/build_evidence.py cases/<name>
       （可选） python3 scripts/build_evidence.py cases/<name> --out /path/custom.html

读取 cases/<name>/evidence_config.py 的 EVIDENCE_CONFIG，调用共享引擎 evidence_engine.build_evidence_cards，
输出到 cases/<name>/output/<OUT_FILENAME>。
"""
import argparse
import importlib.util
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "engine"))
from evidence_engine import build_evidence_cards


def load_module(path):
    spec = importlib.util.spec_from_file_location("case_ev_cfg", path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("case_dir", help="case 目录，如 cases/meiriki")
    ap.add_argument("--out", default=None, help="覆盖输出路径")
    args = ap.parse_args()

    case_dir = args.case_dir.rstrip("/")
    ec_path = os.path.join(case_dir, "evidence_config.py")
    if not os.path.exists(ec_path):
        sys.exit(f"[证据卡] 缺少 {ec_path}。请先按 references/evidence_capture.md 填写痛点卡数据。")

    cfg = load_module(ec_path).EVIDENCE_CONFIG
    out_dir = os.path.join(case_dir, "output")
    os.makedirs(out_dir, exist_ok=True)
    out = args.out or os.path.join(out_dir, cfg["OUT_FILENAME"])

    html = build_evidence_cards(cfg)
    with open(out, "w", encoding="utf-8") as f:
        f.write(html)
    print("saved", out, "bytes:", len(html))


if __name__ == "__main__":
    main()
