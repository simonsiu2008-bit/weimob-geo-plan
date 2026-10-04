#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
登录态管理
============
负责：定位 storage_state.json、加载、探活、过期检测。

存储约定（隐私边界）：
    _private/sessions/<platform>.json     ← 真实登录态，永不入库（.gitignore 已排除 _private 类目录）
    _private/sessions/_default.json       ← 通用登录态（部分平台可共用）

无登录态时的行为：**如实降级**——该平台标记 status="login_required" 并跳过，
绝不用模型估算数据冒充真实采集结果。
"""
import json
import os
import time

# 登录态根目录：技能根/_private/sessions/
_HERE = os.path.dirname(os.path.abspath(__file__))
_SKILL_ROOT = os.path.dirname(os.path.dirname(_HERE))
SESSIONS_DIR = os.path.join(_SKILL_ROOT, "_private", "sessions")


def sessions_root():
    """返回登录态目录（不存在则创建）。"""
    os.makedirs(SESSIONS_DIR, exist_ok=True)
    return SESSIONS_DIR


def session_path(platform, explicit=None):
    """
    定位某平台的登录态文件。优先级：
      1. explicit（CLI 显式指定）
      2. _private/sessions/<platform>.json
      3. _private/sessions/_default.json
    都找不到返回 None。
    """
    if explicit:
        return explicit if os.path.isfile(explicit) else None
    sessions_root()
    for name in (f"{platform}.json", "_default.json"):
        p = os.path.join(SESSIONS_DIR, name)
        if os.path.isfile(p):
            return p
    return None


def load_state(path):
    """读入 storage_state；文件损坏或结构不符返回 None（不抛异常，交给上层降级）。"""
    if not path or not os.path.isfile(path):
        return None
    try:
        with open(path, "r", encoding="utf-8") as f:
            state = json.load(f)
    except Exception:
        return None
    if not isinstance(state, dict):
        return None
    # Playwright storage_state 至少要有 cookies 或 origins 之一
    if "cookies" not in state and "origins" not in state:
        return None
    return state


def describe(path):
    """给人看的登录态摘要：文件、cookie 数、最早/最晚过期时间。"""
    state = load_state(path)
    if not state:
        return {"path": path, "valid": False, "reason": "文件缺失或结构不符"}
    cookies = state.get("cookies", [])
    expires = [c.get("expires") for c in cookies if isinstance(c.get("expires"), (int, float)) and c["expires"] > 0]
    now = time.time()
    expired = [e for e in expires if e < now]
    return {
        "path": path,
        "valid": True,
        "cookies": len(cookies),
        "origins": len(state.get("origins", [])),
        "earliest_expiry": min(expires) if expires else None,
        "expired_count": len(expired),
        "expired_all": bool(expires) and len(expired) == len(expires),
        "cookie_names": sorted({c.get("name", "") for c in cookies})[:12],
    }


def build_context(browser, platform, explicit_state=None, locale="zh-CN", viewport=None):
    """
    为某平台创建 BrowserContext，自动套用可用登录态。

    返回 (context, session_info)：
      session_info = {"used": bool, "path": str|None, "note": str}
    """
    path = session_path(platform, explicit_state)
    state = load_state(path) if path else None

    kwargs = {
        "locale": locale,
        "viewport": viewport or {"width": 1440, "height": 900},
        "user_agent": (
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
            "(KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36"
        ),
    }
    if state:
        kwargs["storage_state"] = state

    ctx = browser.new_context(**kwargs)
    return ctx, {
        "used": bool(state),
        "path": path,
        "note": "已加载登录态" if state else "无登录态（将走游客模式，多数平台会被拦截）",
    }


def detect_login_wall(page, platform_cfg):
    """
    粗判当前页面是否停在登录墙。

    策略：页面可见文本里出现登录关键词、且回答容器不存在 → 视为登录墙。
    这是启发式判断（平台改版可能失效），因此仅用于**提前止损**，
    真正的失败判定以「是否取到回复文本」为准。
    """
    try:
        body = page.inner_text("body")[:3000]
    except Exception:
        return False
    keys = ["扫码登录", "手机号码登录", "发送验证码", "登录以同步", "Sign in", "Log in", "Sign up"]
    return any(k in body for k in keys)
