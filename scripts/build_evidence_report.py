#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
CLI：生成「AI 实测证据报告」HTML（采集版 · 需 Playwright）
==========================================================
用法：
    python3 scripts/build_evidence_report.py cases/<name>              # 相对路径模式（默认）
    python3 scripts/build_evidence_report.py cases/<name> --embed      # base64 内联，单文件自包含
    python3 scripts/build_evidence_report.py cases/<name> --out /path/report.html

读取 cases/<name>/evidence/manifest.json（采集引擎产出），调用 evidence_engine.build_evidence_html 渲染。
若 manifest 不存在，提示先运行采集命令。

> 姊妹 CLI：`build_evidence_cards.py`（痛点问答证据卡，读 evidence_config.py，零依赖）。
> 两者互不依赖，可择一或都出。

输出：cases/<name>/output/<品牌>_AI实测证据报告.html
"""
import argparse
import importlib.util
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "engine"))
from evidence_engine import build_evidence_html   # noqa: E402


def load_module(path):
    spec = importlib.util.spec_from_file_location("case_cfg", path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def main():
    ap = argparse.ArgumentParser(description="生成 AI 实测证据报告 HTML（采集版）")
    ap.add_argument("case_dir", help="case 目录，如 cases/acme")
    ap.add_argument("--embed", action="store_true",
                    help="把截图转 base64 内联，生成单文件自包含 HTML（体积较大）")
    ap.add_argument("--out", default=None, help="覆盖输出路径")
    args = ap.parse_args()

    case_dir = args.case_dir.rstrip("/")
    man_path = os.path.join(case_dir, "evidence", "manifest.json")
    if not os.path.exists(man_path):
        sys.exit(
            f"[证据报告] 未找到 {man_path}。\n"
            f"请先运行线上采集：\n"
            f"    python3 scripts/collect_run.py {case_dir} --dry-run   # 预检\n"
            f"    python3 scripts/collect_run.py {case_dir}            # 正式采集\n"
            f"登录态配置见 scripts/collect/README.md"
        )

    # 品牌名从 config.py 取，失败则退回目录名
    brand = os.path.basename(case_dir)
    sub = ""
    cfg_path = os.path.join(case_dir, "config.py")
    if os.path.exists(cfg_path):
        try:
            mod = load_module(cfg_path)
            brand = getattr(mod, "BRAND_CN", brand) or brand
            sub = getattr(mod, "CLIENT_DESC", "") or ""
        except Exception:
            pass

    ec = {
        "BRAND": brand,
        "BRAND_SUB": sub,
        "MANIFEST": man_path,
        "BASE_DIR": os.path.dirname(os.path.abspath(man_path)),
        "EMBED": args.embed,
    }

    html = build_evidence_html(ec)

    out_dir = os.path.join(case_dir, "output")
    os.makedirs(out_dir, exist_ok=True)
    if args.out:
        out = args.out
    else:
        suffix = "_单文件版" if args.embed else ""
        out = os.path.join(out_dir, f"{brand}_AI实测证据报告{suffix}.html")

    with open(out, "w", encoding="utf-8") as f:
        f.write(html)

    size_kb = os.path.getsize(out) / 1024
    print(f"saved {out} bytes: {len(html)} ({size_kb:.1f} KB) "
          f"[{'embed' if args.embed else 'relative'}]")
    if not args.embed:
        print(f"提示：截图目录 {os.path.join(case_dir, 'evidence', 'shots')} "
              f"需与本文件一同分发；或改用 --embed 生成单文件版。")
    return 0


if __name__ == "__main__":
    sys.exit(main())
