#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
线上数据采集 CLI
==================
用法：
    # 1) 预检：看问题清单 + 各平台可达性（不提问、不消耗额度）
    python3 scripts/collect_run.py cases/<name> --dry-run

    # 2) 正式采集（默认国内 6 平台；无登录态的平台会被如实跳过）
    python3 scripts/collect_run.py cases/<name>

    # 3) 只跑指定平台 / 只跑前 3 题（调试）
    python3 scripts/collect_run.py cases/<name> --platforms doubao,kimi --limit 3

    # 4) 采集海外版 5 平台
    python3 scripts/collect_run.py cases/<name> --version overseas

    # 5) 指定登录态文件
    python3 scripts/collect_run.py cases/<name> --state _private/sessions/doubao.json

    # 6) 可见浏览器（人工核对选择器时用）
    python3 scripts/collect_run.py cases/<name> --probe doubao

产物：cases/<name>/evidence/{manifest.json, raw.json, shots/*.png}
"""
import argparse
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "collect"))

from collector import collect, load_questions          # noqa: E402
from platforms import PLATFORMS, get_platform, resolve_keys  # noqa: E402
from session import sessions_root, session_path, describe    # noqa: E402


def cmd_probe(platform, state):
    """打开可见浏览器，人工核对某平台的选择器是否仍然有效。"""
    from playwright.sync_api import sync_playwright
    cfg = get_platform(platform)
    spath = session_path(platform, state)
    print(f"[probe] 平台={cfg['name']} URL={cfg['url']}")
    print(f"[probe] 登录态={spath or '无（游客模式）'}")
    print("[probe] 浏览器已打开，请人工观察输入框/回复区域，确认选择器后关闭窗口。")
    with sync_playwright() as pw:
        b = pw.chromium.launch(headless=False, args=["--no-sandbox", "--disable-dev-shm-usage"])
        kwargs = {"locale": "zh-CN", "viewport": {"width": 1440, "height": 900}}
        if spath and os.path.isfile(spath):
            kwargs["storage_state"] = spath
        ctx = b.new_context(**kwargs)
        pg = ctx.new_page()
        pg.goto(cfg["url"], timeout=60000, wait_until="domcontentloaded")
        print(f"[probe] 候选输入框选择器：{cfg['input']}")
        print(f"[probe] 候选回复容器选择器：{cfg['reply']}")
        for sel in cfg["input"]:
            found = pg.query_selector(sel)
            print(f"   输入 {sel!r} → {'命中' if found else '未命中'}")
        for sel in cfg["reply"]:
            els = pg.query_selector_all(sel)
            print(f"   回复 {sel!r} → 命中 {len(els)} 个")
        input("[probe] 按 Enter 关闭浏览器…")
        b.close()


def main():
    ap = argparse.ArgumentParser(description="GEO 线上数据采集（无头浏览器）")
    ap.add_argument("case_dir", nargs="?", default=None,
                    help="cases/<name>（--list-platforms / --probe 时可省略）")
    ap.add_argument("--platforms", default=None,
                    help="平台 key，逗号分隔（doubao,deepseek,qwen,baidu,yuanbao,kimi）")
    ap.add_argument("--version", default=None, choices=["domestic", "overseas", "both"],
                    help="平台版本；省略则读 case config 的 VERSION")
    ap.add_argument("--dry-run", action="store_true", help="只检问题清单与平台可达性")
    ap.add_argument("--limit", type=int, default=None, help="只跑前 N 题（调试）")
    ap.add_argument("--state", default=None, help="显式指定 storage_state.json 路径")
    ap.add_argument("--headed", action="store_true", help="显示浏览器窗口（默认无头）")
    ap.add_argument("--no-shot", action="store_true", help="不截图，只存文本")
    ap.add_argument("--probe", default=None, help="打开可见浏览器人工核对某平台选择器")
    ap.add_argument("--list-platforms", action="store_true", help="列出全部平台")
    args = ap.parse_args()

    if args.list_platforms:
        for k, v in PLATFORMS.items():
            print(f"{k:12s} {v['version']:9s} {v['name']:10s} {v['url']}")
        return 0

    if args.probe:
        cmd_probe(args.probe, args.state)
        return 0

    if not args.case_dir:
        print("[error] 缺少 case_dir（除非使用 --list-platforms / --probe）", file=sys.stderr)
        return 2

    if not os.path.isdir(args.case_dir):
        print(f"[error] 目录不存在: {args.case_dir}", file=sys.stderr)
        return 2

    print(f"[collect] 案例: {args.case_dir}")
    if not args.dry_run:
        sroot = sessions_root()
        print(f"[collect] 登录态目录: {sroot}")
        avail = [k for k in (resolve_keys(args.platforms, args.version or "domestic")
                             if args.platforms or args.version else resolve_keys(None, "domestic"))
                 if session_path(k, args.state)]
        if avail:
            print(f"[collect] 已检测到登录态的平台: {avail}")
        else:
            print("[collect] 未检测到任何登录态——多数平台会被跳过。"
                  "请按 scripts/collect/README.md 导出登录态。")
        print()

    try:
        manifest = collect(
            args.case_dir,
            platforms=args.platforms,
            version=args.version,
            dry_run=args.dry_run,
            headless=not args.headed,
            screenshot=not args.no_shot,
            limit=args.limit,
            explicit_state=args.state,
            on_progress=lambda m: print("  " + m),
        )
    except Exception as e:
        print(f"[error] {e}", file=sys.stderr)
        return 1

    print()
    if args.dry_run:
        print("=== 预检结果（未提问）===")
        for k, rep in manifest["platform_report"].items():
            print(f"  {rep['name']:10s} 可达={rep['reachable']}  {rep['note']}")
        print(f"\n问题清单 {len(manifest['questions'])} 题：")
        for q in manifest["questions"][:25]:
            print(f"  {q['qid']} [{q['level']}] {q['question']}")
        return 0

    s = manifest["summary"]
    print("=== 采集汇总 ===")
    print(f"  平台 {s['platforms_total']} 个 · 问题 {s['questions_total']} 题 · "
          f"尝试 {s['attempts']} 次 · 成功 {s['ok']} 次（覆盖率 {s['coverage']:.0%}）")
    print(f"  各状态：{s['by_status']}")
    print(f"  品牌缺席但竞品出现：{s['brand_missing_count']} 条")
    print(f"  品牌被提及且情感偏负：{s['brand_negative_count']} 条")
    print(f"\n  产物：{os.path.join(args.case_dir, 'evidence')}")
    if s["ok"] == 0:
        print("\n  ⚠ 未采集到任何数据。请提供登录态后重跑（见 scripts/collect/README.md）。")
        return 3
    return 0


if __name__ == "__main__":
    sys.exit(main())
