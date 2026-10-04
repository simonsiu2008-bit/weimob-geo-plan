#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
线上数据采集核心
==================
用无头浏览器（Playwright）对每个「监测池问题」逐平台提问，抓取 AI 回答文本 +
回答区域截图，产出 manifest.json 供证据报告消费。

铁律（数据诚信）：
    采集不到就如实标记 status，**绝不伪造**、绝不用模型估算冒充真实采集。
    manifest.json 的 status 字段是唯一真相源。

status 取值：
    ok              成功取到回答
    login_required  需要登录态但未提供/已失效
    selector_not_found  输入框或回复容器选择器失效（平台改版）
    timeout         等待回答超时
    failed          其他异常（附 error 摘要）

用法（由 collect_run.py 调用）：
    from collect.collector import collect
    manifest = collect(case_dir, platforms=["doubao"], version="domestic", dry_run=False)
"""
import json
import os
import random
import re
import sys
import time
from datetime import datetime, timezone, timedelta

try:
    from .platforms import PLATFORMS, get_platform, resolve_keys
    from .session import build_context, detect_login_wall, describe, session_path
except ImportError:  # 以顶层脚本方式运行时的兼容
    sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
    from platforms import PLATFORMS, get_platform, resolve_keys
    from session import build_context, detect_login_wall, describe, session_path

CN_TZ = timezone(timedelta(hours=8))


def _now():
    return datetime.now(CN_TZ).isoformat(timespec="seconds")


# ---------------------------------------------------------------- 问题清单

def load_questions(case_dir):
    """
    从 case 的 topic_config.py 读 20 题监测池。

    QUESTION_POOL 字段约定（与 topic_framework.md 一致）：
        (编号, 层级, 问题文本, 意图, 说明, 状态)
    额外兼容：若 case 提供 evidence_config.py 的 QUESTIONS 覆盖，则优先使用。
    """
    ev = os.path.join(case_dir, "evidence_config.py")
    if os.path.isfile(ev):
        mod = _load_module(ev)
        qs = getattr(mod, "QUESTIONS", None)
        if qs:
            return _norm_questions(qs)

    tc = os.path.join(case_dir, "topic_config.py")
    if os.path.isfile(tc):
        mod = _load_module(tc)
        pool = getattr(mod, "QUESTION_POOL", None)
        if pool:
            return _norm_questions(pool)

    raise FileNotFoundError(
        f"[collector] 在 {case_dir} 找不到 QUESTION_POOL（topic_config.py）或 QUESTIONS（evidence_config.py）"
    )


def _load_module(path):
    import importlib.util
    spec = importlib.util.spec_from_file_location("_case_mod_" + str(abs(hash(path))), path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def _norm_questions(raw):
    """归一化为 [{"qid","level","question","intent","note"}]。"""
    out = []
    for i, row in enumerate(raw):
        if isinstance(row, dict):
            out.append({
                "qid": row.get("qid") or f"q{i+1:02d}",
                "level": row.get("level", ""),
                "question": row.get("question", ""),
                "intent": row.get("intent", ""),
                "note": row.get("note", ""),
            })
        elif isinstance(row, (list, tuple)):
            r = list(row) + [""] * 6
            out.append({
                "qid": f"q{i+1:02d}",
                "level": str(r[1]),
                "question": str(r[2]),
                "intent": str(r[3]),
                "note": str(r[4]),
            })
    return [q for q in out if q["question"]]


# ---------------------------------------------------------------- 品牌识别

def _load_brand_terms(case_dir):
    """
    品牌词 + 竞品词，用于在回答文本里判断「谁出现了」。
    来源：todo_config BRAND / config COMPETITORS，最后叠加 pollute_words（粗兜底）。
    """
    brands, rivals = set(), set()
    for fname, keys in (("config.py", ("BRAND_CN", "BRAND_EN")),
                        ("topic_config.py", ("BRAND",))):
        p = os.path.join(case_dir, fname)
        if not os.path.isfile(p):
            continue
        try:
            mod = _load_module(p)
        except Exception:
            continue
        for k in keys:
            v = getattr(mod, k, None)
            if isinstance(v, str) and v.strip():
                brands.add(v.strip())
                # "示例鐘錶 Sample Watch" → 拆出空格分隔的独立词
                for part in re.split(r"[\s/]+", v.strip()):
                    if len(part) >= 2:
                        brands.add(part)
        comps = getattr(mod, "COMPETITORS", None)
        if comps:
            for row in comps:
                if isinstance(row, (list, tuple)) and row:
                    name = str(row[0]).strip()
                    if name:
                        rivals.add(name)
                        rivals.add(re.sub(r"[（(].*?[)）]", "", name).strip())
    return sorted(brands - {""}), sorted(rivals - {""})


def _mentions(text, terms):
    """返回文本中命中的词列表（去重，保序）。"""
    if not text:
        return []
    hits = []
    for t in terms:
        if t and t in text and t not in hits:
            hits.append(t)
    return hits


def judge_sentiment(text, brand_hits):
    """
    粗粒度情感判断（启发式，供证据报告分区用，不作为结论）。
    负向关键词命中 → negative；正向 → positive；否则 neutral。
    判定依据会随结果一起输出，人工可复核。
    """
    if not text:
        return "unknown", []
    neg = ["投诉", "质量问题", "翻车", "事故", "缺陷", "召回", "维权", "差评", "不值得", "劝退",
           "broken", "recall", "lawsuit", "complaint", "defect", "crash"]
    pos = ["推荐", "优秀", "领先", "值得", "好评", "优势", "标杆",
           "recommend", "best", "leading", "excellent"]
    found_neg = [w for w in neg if w in text]
    found_pos = [w for w in pos if w in text]
    if found_neg and not found_pos:
        return "negative", found_neg
    if found_pos and not found_neg:
        return "positive", found_pos
    if found_neg and found_pos:
        return "mixed", found_neg + found_pos
    return "neutral", []


# ---------------------------------------------------------------- 单平台采集

def _find_first(page, selectors, timeout=1500):
    """按候选选择器顺序找第一个可见元素。"""
    for sel in selectors:
        try:
            el = page.query_selector(sel)
            if el and el.is_visible():
                return el, sel
        except Exception:
            continue
    return None, None


def _reply_text(page, selectors):
    """取回复容器文本（取命中里最长的那个，通常是完整回答）。"""
    best, best_sel = "", None
    for sel in selectors:
        try:
            els = page.query_selector_all(sel)
        except Exception:
            continue
        for el in els:
            try:
                t = (el.inner_text() or "").strip()
            except Exception:
                continue
            if len(t) > len(best):
                best, best_sel = t, sel
    return best, best_sel


def _wait_stable(page, selectors, max_wait, min_len=30, stable_rounds=2, interval=2.0):
    """
    等回答稳定：连续 stable_rounds 次采样文本长度不变且 > min_len，或超时。
    返回 (text, waited_seconds)。
    """
    start = time.time()
    last_len, stable, text = -1, 0, ""
    while time.time() - start < max_wait:
        time.sleep(interval)
        text, _ = _reply_text(page, selectors)
        cur = len(text)
        if cur > min_len and cur == last_len:
            stable += 1
            if stable >= stable_rounds:
                break
        else:
            stable = 0
        last_len = cur
    return text, round(time.time() - start, 1)


def collect_one(page, pkey, q, out_shots, brand_terms, rival_terms, screenshot=True):
    """对单个问题采集一次，返回 result dict（含 status）。"""
    cfg = get_platform(pkey)
    qid = q["qid"]
    res = {
        "status": "failed",
        "shot": None,
        "text": "",
        "brand_mentioned": False,
        "brand_hits": [],
        "rivals_mentioned": [],
        "sentiment": "unknown",
        "sentiment_evidence": [],
        "selector": {"input": None, "reply": None},
        "waited": None,
        "error": None,
        "collected_at": _now(),
    }

    # 1) 输入框
    box, input_sel = _find_first(page, cfg["input"], timeout=8000)
    if not box:
        res["status"] = "selector_not_found"
        res["error"] = "输入框未找到（平台可能已改版或未登录）"
        if detect_login_wall(page, cfg):
            res["status"] = "login_required"
            res["error"] = "检测到登录墙"
        return res
    res["selector"]["input"] = input_sel

    # 2) 输入 + 发送
    try:
        box.click(timeout=8000)
        page.wait_for_timeout(300)
        box.fill("")
        page.keyboard.type(q["question"], delay=18)
        page.wait_for_timeout(400)
        if cfg["send_mode"] == "click":
            btn, _ = _find_first(page, cfg["send"], timeout=3000)
            if btn:
                btn.click(timeout=5000)
            else:
                page.keyboard.press("Enter")
        else:
            page.keyboard.press("Enter")
    except Exception as e:
        res["status"] = "failed"
        res["error"] = f"输入/发送失败: {type(e).__name__}: {str(e)[:160]}"
        if detect_login_wall(page, cfg):
            res["status"] = "login_required"
            res["error"] = "发送时弹出登录墙"
        return res

    # 3) 等回答稳定
    text, waited = _wait_stable(page, cfg["reply"], max_wait=cfg["wait"])
    res["waited"] = waited

    if len(text) < 30:
        if detect_login_wall(page, cfg):
            res["status"] = "login_required"
            res["error"] = "发送后出现登录墙，未取得回答"
        else:
            res["status"] = "timeout"
            res["error"] = f"等待 {waited}s 未取得有效回答"
    else:
        res["status"] = "ok"
        res["text"] = text
        res["brand_hits"] = _mentions(text, brand_terms)
        res["brand_mentioned"] = bool(res["brand_hits"])
        res["rivals_mentioned"] = _mentions(text, rival_terms)
        res["sentiment"], res["sentiment_evidence"] = judge_sentiment(text, res["brand_hits"])

    # 4) 截图（无论成功与否都留证 —— 失败画面本身就是证据）
    if screenshot:
        try:
            shot_name = f"{pkey}_{qid}.png"
            shot_path = os.path.join(out_shots, shot_name)
            target = None
            for sel in cfg["reply"]:
                el = page.query_selector(sel)
                if el and el.is_visible():
                    target = el
                    break
            if target:
                target.screenshot(path=shot_path)
            else:
                page.screenshot(path=shot_path, full_page=False)
            res["shot"] = f"shots/{shot_name}"
        except Exception as e:
            res["error"] = (res["error"] or "") + f" | 截图失败: {type(e).__name__}"

    return res


# ---------------------------------------------------------------- 主流程

def collect(case_dir, platforms=None, version=None, dry_run=False, headless=True,
            screenshot=True, limit=None, explicit_state=None, on_progress=None):
    """
    采集主流程。

    case_dir   : cases/<name> 目录
    platforms  : 平台 key 列表或逗号串；None → 按 version 取全套
    version    : domestic | overseas | both
    dry_run    : 只输出问题清单与平台可达性，不提问
    limit      : 只跑前 N 题（调试用）
    """
    case_dir = os.path.abspath(case_dir)
    case_name = os.path.basename(case_dir)
    questions = load_questions(case_dir)
    if limit:
        questions = questions[:limit]
    brand_terms, rival_terms = _load_brand_terms(case_dir)

    # version 可从 config 推导
    if not version:
        cfg_p = os.path.join(case_dir, "config.py")
        version = "domestic"
        if os.path.isfile(cfg_p):
            try:
                version = getattr(_load_module(cfg_p), "VERSION", "domestic") or "domestic"
            except Exception:
                pass
    pkeys = resolve_keys(platforms, version if version != "both" else "both")

    out_dir = os.path.join(case_dir, "evidence")
    out_shots = os.path.join(out_dir, "shots")
    os.makedirs(out_shots, exist_ok=True)

    manifest = {
        "case": case_name,
        "version": version,
        "collected_at": _now(),
        "collector": "weimob-geo-plan/scripts/collect (Playwright headless)",
        "data_disclaimer": (
            "本文件记录的是浏览器实际访问各 AI 平台所得的问答与截图，"
            "status 字段为采集状态唯一真相源。未成功采集的平台/问题一律如实标记，"
            "不做任何数据填充或推算。"
        ),
        "brand_terms": brand_terms,
        "rival_terms": rival_terms,
        "platforms": pkeys,
        "questions": questions,
        "items": [],
        "platform_report": {},
        "summary": {},
    }

    def log(msg):
        if on_progress:
            on_progress(msg)

    # ---- 载入浏览器 ----
    try:
        from playwright.sync_api import sync_playwright
    except ImportError:
        raise RuntimeError(
            "[collector] 未安装 Playwright。请执行：\n"
            "  pip install playwright && playwright install chromium"
        )

    with sync_playwright() as pw:
        browser = pw.chromium.launch(headless=headless,
                                     args=["--no-sandbox", "--disable-dev-shm-usage",
                                           "--disable-blink-features=AutomationControlled"])

        for pkey in pkeys:
            cfg = get_platform(pkey)
            spath = session_path(pkey, explicit_state)
            sinfo = describe(spath) if spath else {"valid": False, "reason": "未提供登录态"}
            log(f"[{cfg['name']}] 登录态: {'已加载 ' + os.path.basename(spath) if spath else '无'}")

            preport = {"name": cfg["name"], "version": cfg["version"],
                       "session": sinfo, "reachable": None, "note": ""}

            # ---- dry-run：只探可达性 ----
            if dry_run:
                ctx = None
                try:
                    ctx, _ = build_context(browser, pkey, explicit_state)
                    pg = ctx.new_page()
                    pg.goto(cfg["probe_url"], timeout=30000, wait_until="domcontentloaded")
                    pg.wait_for_timeout(3500)
                    preport["reachable"] = True
                    box, isel = _find_first(pg, cfg["input"], timeout=4000)
                    wall = detect_login_wall(pg, cfg)
                    preport["input_found"] = bool(box)
                    preport["input_selector"] = isel
                    preport["login_wall"] = wall
                    preport["note"] = ("可交互（输入框就绪）" if box and not wall
                                       else "停在登录墙" if wall
                                       else "输入框未找到")
                    log(f"[{cfg['name']}] 可达={True} 输入框={isel} 登录墙={wall}")
                except Exception as e:
                    preport["reachable"] = False
                    preport["note"] = f"访问失败: {type(e).__name__}: {str(e)[:120]}"
                    log(f"[{cfg['name']}] 访问失败: {type(e).__name__}")
                finally:
                    if ctx:
                        ctx.close()
                manifest["platform_report"][pkey] = preport
                continue

            # ---- 正式采集：整个平台共用一个 context（复用登录态）----
            ctx = None
            try:
                ctx, ctxinfo = build_context(browser, pkey, explicit_state)
                page = ctx.new_page()
                page.goto(cfg["url"], timeout=40000, wait_until="domcontentloaded")
                page.wait_for_timeout(4500)
                preport["reachable"] = True

                # 提前止损：无登录态且检测到登录墙 → 整个平台跳过
                if cfg["need_login"] and not sinfo.get("valid") and detect_login_wall(page, cfg):
                    preport["note"] = "未提供登录态且检测到登录墙，平台整体跳过"
                    log(f"[{cfg['name']}] 跳过：{preport['note']}")
                    for q in questions:
                        manifest["items"].append({
                            "qid": q["qid"], "question": q["question"],
                            "level": q["level"], "intent": q["intent"],
                            "platform": pkey, "platform_name": cfg["name"],
                            "status": "login_required", "shot": None, "text": "",
                            "brand_mentioned": False, "brand_hits": [],
                            "rivals_mentioned": [], "sentiment": "unknown",
                            "sentiment_evidence": [], "error": "平台需要登录态",
                            "collected_at": _now(),
                        })
                    manifest["platform_report"][pkey] = preport
                    ctx.close()
                    continue

                for idx, q in enumerate(questions, 1):
                    log(f"[{cfg['name']}] ({idx}/{len(questions)}) {q['question'][:26]}")
                    try:
                        res = collect_one(page, pkey, q, out_shots, brand_terms,
                                          rival_terms, screenshot=screenshot)
                    except Exception as e:
                        res = {"status": "failed", "text": "", "shot": None,
                               "brand_mentioned": False, "brand_hits": [],
                               "rivals_mentioned": [], "sentiment": "unknown",
                               "sentiment_evidence": [], "selector": {},
                               "waited": None, "error": f"{type(e).__name__}: {str(e)[:160]}",
                               "collected_at": _now()}

                    manifest["items"].append({
                        "qid": q["qid"], "question": q["question"],
                        "level": q["level"], "intent": q["intent"],
                        "platform": pkey, "platform_name": cfg["name"],
                        **res,
                    })

                    # 反爬：随机延迟，避免固定节奏
                    if idx < len(questions):
                        time.sleep(random.uniform(8, 15))

                    # 页面若被登录墙接管，后续题目必然失败 → 提前结束该平台
                    if res["status"] == "login_required":
                        log(f"[{cfg['name']}] 出现登录墙，剩余题目标记 login_required")
                        done = {it["qid"] for it in manifest["items"] if it["platform"] == pkey}
                        for rest in questions:
                            if rest["qid"] in done:
                                continue
                            manifest["items"].append({
                                "qid": rest["qid"], "question": rest["question"],
                                "level": rest["level"], "intent": rest["intent"],
                                "platform": pkey, "platform_name": cfg["name"],
                                "status": "login_required", "shot": None, "text": "",
                                "brand_mentioned": False, "brand_hits": [],
                                "rivals_mentioned": [], "sentiment": "unknown",
                                "sentiment_evidence": [], "error": "登录态在第 %d 题后失效" % idx,
                                "collected_at": _now(),
                            })
                        break

                preport["note"] = "采集完成"
            except Exception as e:
                preport["reachable"] = False
                preport["note"] = f"平台级异常: {type(e).__name__}: {str(e)[:140]}"
                log(f"[{cfg['name']}] 平台级异常: {type(e).__name__}")
                done = {it["qid"] for it in manifest["items"] if it["platform"] == pkey}
                for q in questions:
                    if q["qid"] in done:
                        continue
                    manifest["items"].append({
                        "qid": q["qid"], "question": q["question"],
                        "level": q["level"], "intent": q["intent"],
                        "platform": pkey, "platform_name": cfg["name"],
                        "status": "failed", "shot": None, "text": "",
                        "brand_mentioned": False, "brand_hits": [],
                        "rivals_mentioned": [], "sentiment": "unknown",
                        "sentiment_evidence": [], "error": preport["note"],
                        "collected_at": _now(),
                    })
            finally:
                if ctx:
                    try:
                        ctx.close()
                    except Exception:
                        pass
            manifest["platform_report"][pkey] = preport

        browser.close()

    # ---- 汇总 ----
    items = manifest["items"]
    by_status = {}
    for it in items:
        by_status[it["status"]] = by_status.get(it["status"], 0) + 1
    ok_items = [it for it in items if it["status"] == "ok"]
    qids_ok = {it["qid"] for it in ok_items}
    manifest["summary"] = {
        "platforms_total": len(pkeys),
        "questions_total": len(questions),
        "attempts": len(items),
        "ok": len(ok_items),
        "by_status": by_status,
        "coverage": round(len(ok_items) / len(items), 3) if items else 0.0,
        "questions_with_any_ok": len(qids_ok),
        "brand_missing_count": len([it for it in ok_items
                                    if not it["brand_mentioned"] and it["rivals_mentioned"]]),
        "brand_negative_count": len([it for it in ok_items
                                     if it["brand_mentioned"] and it["sentiment"] in ("negative", "mixed")]),
    }

    # ---- 落盘 ----
    raw_path = os.path.join(out_dir, "raw.json")
    with open(raw_path, "w", encoding="utf-8") as f:
        json.dump(manifest, f, ensure_ascii=False, indent=2)
    man_path = os.path.join(out_dir, "manifest.json")
    with open(man_path, "w", encoding="utf-8") as f:
        json.dump(manifest, f, ensure_ascii=False, indent=2)

    return manifest
