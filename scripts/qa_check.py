#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
CLI wrapper：交付物 QA 检查器（薄封装，转发到 engine/qa_engine.py）
================================================================
用法： python3 scripts/qa_check.py <case名> [--no-compliance]
退出码：0=全部通过；非0=失败项数。
"""
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "engine"))
from qa_engine import run_qa

if __name__ == "__main__":
    import argparse
    ap = argparse.ArgumentParser()
    ap.add_argument("case", help="case 名，如 meiriki")
    ap.add_argument("--cases-dir", default=os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "cases"))
    ap.add_argument("--no-compliance", action="store_true")
    args = ap.parse_args()
    f, lines = run_qa(args.case, cases_dir=args.cases_dir,
                      compliance=not args.no_compliance)
    for l in lines:
        print(l)
    raise SystemExit(f)
