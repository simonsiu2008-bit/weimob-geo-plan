#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
check_lang_parity.py —— 语言包键集一致性校验（QA 前置门）
=========================================================
lang_style.py 的三个注册表 TOPIC_LANG / DECK_LANG / TT_LANG，
每个包含若干语言包（mainland / hk_business / …）。任意两个语言包之间：

  · 键集（key set）必须完全一致
  · 版本分支键（值本身是 {domestic/overseas/both: …} 的字典）的
    分支键集也必须一致
  · DECK_LANG 的所有键必须能被 deck_engine 用到（存在性由 registry 保证）

不一致意味着「某语言包缺一句文案」——渲染时会 KeyError 或静默回退，
是新增语言包 / 语言包改版时最隐蔽的坑。本脚本把它变成一道硬门。

用法：
    python3 scripts/check_lang_parity.py            # 校验，全部一致退出码 0
    python3 scripts/check_lang_parity.py -v         # 打印每个包的键数
退出码：0 = ALL OK；1 = 存在差异（打印差异明细）。
"""
import argparse
import importlib.util
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
LANG_PATH = os.path.join(HERE, "engine", "lang_style.py")

VERSION_BRANCH_KEYS = ("domestic", "overseas", "both")


def load_lang():
    spec = importlib.util.spec_from_file_location("lang_style", LANG_PATH)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def check_registry(name, table, verbose=False):
    """返回 (fail_count, lines)。"""
    lines = []
    fail = 0
    pkgs = list(table.keys())
    if len(pkgs) < 2:
        lines.append(f"  {name}: 仅 {len(pkgs)} 个语言包，跳过比对")
        return (fail, lines)

    sets = {k: set(table[k].keys()) for k in pkgs}
    base_name = pkgs[0]
    base = sets[base_name]
    lines.append(f"  {name}: 语言包 {pkgs}（基准 {base_name}，{len(base)} 键）")

    for k in pkgs[1:]:
        only_base = base - sets[k]
        only_k = sets[k] - base
        if only_base or only_k:
            fail += 1
            lines.append(f"    ✗ {k} 键集不一致：")
            if only_base:
                lines.append(f"        仅在 {base_name}：{sorted(only_base)}")
            if only_k:
                lines.append(f"        仅在 {k}：{sorted(only_k)}")
        elif verbose:
            lines.append(f"    ✓ {k} 键集一致（{len(sets[k])} 键）")

    # 版本分支键的分支集一致性
    def branch_map(table_pkg):
        out = {}
        for key, val in table_pkg.items():
            if isinstance(val, dict):
                out[key] = tuple(sorted(val.keys()))
        return out

    bmaps = {k: branch_map(table[k]) for k in pkgs}
    base_b = bmaps[base_name]
    for k in pkgs[1:]:
        cur = bmaps[k]
        only_base = set(base_b) - set(cur)
        only_k = set(cur) - set(base_b)
        if only_base or only_k:
            fail += 1
            lines.append(f"    ✗ {k} 版本分支键集合不一致："
                         f"仅 {base_name}={sorted(only_base)}，仅 {k}={sorted(only_k)}")
        # 分支值集（domestic/overseas/both）也必须齐全
        for key, branches in cur.items():
            missing = [b for b in VERSION_BRANCH_KEYS if b not in branches]
            if missing:
                fail += 1
                lines.append(f"    ✗ {k}.{key} 版本分支缺失：{missing}")
    return (fail, lines)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("-v", "--verbose", action="store_true")
    args = ap.parse_args()

    if not os.path.exists(LANG_PATH):
        print(f"✗ 未找到 {LANG_PATH}")
        raise SystemExit(1)
    m = load_lang()

    total_fail = 0
    print("[语言包键集一致性校验]")
    for reg in ("TOPIC_LANG", "DECK_LANG", "TT_LANG"):
        table = getattr(m, reg)
        f, lines = check_registry(reg, table, verbose=args.verbose)
        total_fail += f
        for l in lines:
            print(l)

    # 版本注册表自检
    print("  VERSION_KEYS:", getattr(m, "VERSION_KEYS", "N/A"),
          "| 默认:", getattr(m, "VERSION_DEFAULT", "N/A"))

    print("\n===> %s" % ("ALL OK" if total_fail == 0 else f"FAIL {total_fail} 项"))
    raise SystemExit(0 if total_fail == 0 else 1)


if __name__ == "__main__":
    main()
