#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
平台适配器注册表
==================
每个平台的「入口 URL / 输入框选择器 / 发送方式 / 回复容器 / 等待策略 / 登录要求」。

设计原则：
- 选择器写成**候选列表**，按顺序尝试第一个命中的——平台改版时只需加候选，不必改采集逻辑。
- 探测得到的真实观测写在注释里（`# 实测：`），便于后续维护判断。
- 海外版平台与国内版完全对称，仅 URL 与语言不同。

维护提示：平台前端改版会导致选择器失效。失效表现是 status="selector_not_found"，
此时用 `--probe <platform>` 打开可见浏览器人工核对新选择器，补进候选列表首位即可。
"""

# 平台维度归属（与 SKILL.md 的「平台双版本」固定框架一致）
DOMESTIC = ["doubao", "deepseek", "qwen", "baidu", "yuanbao", "kimi"]
OVERSEAS = ["chatgpt", "perplexity", "claude", "gemini", "copilot"]


PLATFORMS = {
    # ---------------- 国内版 6 平台 ----------------
    "doubao": {
        "name": "豆包",
        "version": "domestic",
        "url": "https://www.doubao.com/chat/",
        "probe_url": "https://www.doubao.com/chat/",
        "input": ["div[contenteditable='true']", "textarea[placeholder]", "textarea"],
        "send": ["button[type='submit']", "button[aria-label*='发送']", "div[data-testid*='send']"],
        "reply": ["div[data-testid='message_text_content']", "div[class*='message']", "div[class*='markdown']"],
        "send_mode": "enter",          # enter | click
        "wait": 20,                    # 秒，等待回答
        "need_login": True,
        # 实测：游客模式输入框存在但不可点击（ElementHandle.click 超时），必须登录态
        "login_hint": "游客被禁，必须提供登录态；未登录时输入框不可交互",
    },
    "deepseek": {
        "name": "DeepSeek",
        "version": "domestic",
        "url": "https://chat.deepseek.com/",
        "probe_url": "https://chat.deepseek.com/",
        "input": ["textarea#chat-input", "textarea", "div[contenteditable='true']"],
        "send": ["div[role='button'][aria-disabled='false']", "button[type='submit']"],
        "reply": ["div[class*='ds-markdown']", "div[class*='markdown']"],
        "send_mode": "enter",
        "wait": 22,
        "need_login": True,
        # 实测：强制登录（页面直接弹「+86 发送验证码」登录框），无游客入口
        "login_hint": "强制登录，无游客入口，必须提供登录态",
    },
    "qwen": {
        "name": "通义千问",
        "version": "domestic",
        "url": "https://www.tongyi.com/",
        "probe_url": "https://www.tongyi.com/",
        "input": ["div[contenteditable='true']", "textarea"],
        "send": ["button[type='submit']", "div[class*='send']"],
        "reply": ["div[class*='markdown']", "div[class*='answer']", "div[class*='message']"],
        "send_mode": "enter",
        "wait": 20,
        "need_login": True,
        # 实测：游客可发送，但返回的是「推荐视频列表」而非 AI 直接回答（降级输出），需登录
        "login_hint": "游客返回推荐列表而非 AI 回答，需登录态才能拿到真实回答",
    },
    "baidu": {
        "name": "百度AI",
        "version": "domestic",
        "url": "https://chat.baidu.com/",
        "probe_url": "https://chat.baidu.com/",
        "input": ["textarea#chat-textarea", "textarea", "div[contenteditable='true']"],
        "send": ["button[type='submit']", "div[class*='send-btn']"],
        "reply": ["div[class*='markdown']", "div[class*='answer-content']", "div[class*='message']"],
        "send_mode": "enter",
        "wait": 20,
        "need_login": True,
        "login_hint": "需登录态",
    },
    "yuanbao": {
        "name": "腾讯元宝",
        "version": "domestic",
        "url": "https://yuanbao.tencent.com/chat/",
        "probe_url": "https://yuanbao.tencent.com/chat/",
        "input": ["div[contenteditable='true']", "textarea"],
        "send": ["button[type='submit']", "div[class*='send']"],
        "reply": ["div[class*='agent-chat__bubble']", "div[class*='markdown']", "div[class*='message']"],
        "send_mode": "enter",
        "wait": 20,
        "need_login": True,
        "login_hint": "需登录态",
    },
    "kimi": {
        "name": "Kimi",
        "version": "domestic",
        "url": "https://kimi.moonshot.cn/",
        "probe_url": "https://kimi.moonshot.cn/",
        "input": ["div[contenteditable='true']", "textarea", "div[role='textbox']"],
        "send": ["button[type='submit']", "div[class*='send-button']"],
        "reply": ["div[class*='markdown']", "div[class*='segment-content']", "div[class*='message']"],
        "send_mode": "enter",
        "wait": 20,
        "need_login": True,
        # 实测：可输入可发送，但随即弹「微信扫码登录/手机号码登录」遮罩，拿不到回答
        "login_hint": "发送后弹登录遮罩，必须提供登录态",
    },

    # ---------------- 海外版 5 平台 ----------------
    "chatgpt": {
        "name": "ChatGPT",
        "version": "overseas",
        "url": "https://chatgpt.com/",
        "probe_url": "https://chatgpt.com/",
        "input": ["div#prompt-textarea", "textarea#prompt-textarea", "textarea"],
        "send": ["button[data-testid='send-button']", "button[aria-label*='Send']"],
        "reply": ["div[data-message-author-role='assistant']", "div[class*='markdown']"],
        "send_mode": "enter",
        "wait": 25,
        "need_login": True,
        "login_hint": "需登录态（免费账号即可）",
    },
    "perplexity": {
        "name": "Perplexity",
        "version": "overseas",
        "url": "https://www.perplexity.ai/",
        "probe_url": "https://www.perplexity.ai/",
        "input": ["textarea[placeholder]", "textarea", "div[contenteditable='true']"],
        "send": ["button[aria-label*='Submit']", "button[type='submit']"],
        "reply": ["div[class*='prose']", "div[class*='answer']", "div[class*='markdown']"],
        "send_mode": "enter",
        "wait": 25,
        "need_login": False,
        "login_hint": "游客可问但要过验证码；有登录态更稳",
    },
    "claude": {
        "name": "Claude",
        "version": "overseas",
        "url": "https://claude.ai/new",
        "probe_url": "https://claude.ai/",
        "input": ["div[contenteditable='true']", "div[role='textbox']"],
        "send": ["button[aria-label*='Send']", "button[type='submit']"],
        "reply": ["div[class*='font-claude-message']", "div[class*='markdown']"],
        "send_mode": "enter",
        "wait": 25,
        "need_login": True,
        "login_hint": "需登录态",
    },
    "gemini": {
        "name": "Gemini",
        "version": "overseas",
        "url": "https://gemini.google.com/app",
        "probe_url": "https://gemini.google.com/",
        "input": ["div.ql-editor[contenteditable='true']", "div[contenteditable='true']", "textarea"],
        "send": ["button[aria-label*='Send']", "button[type='submit']"],
        "reply": ["div[class*='model-response-text']", "div[class*='markdown']"],
        "send_mode": "enter",
        "wait": 25,
        "need_login": True,
        "login_hint": "需 Google 登录态",
    },
    "copilot": {
        "name": "Copilot",
        "version": "overseas",
        "url": "https://copilot.microsoft.com/",
        "probe_url": "https://copilot.microsoft.com/",
        "input": ["textarea#userInput", "textarea", "div[contenteditable='true']"],
        "send": ["button[title*='Submit']", "button[type='submit']"],
        "reply": ["div[class*='markdown']", "div[class*='response']"],
        "send_mode": "enter",
        "wait": 25,
        "need_login": False,
        "login_hint": "游客可问，有登录态更稳",
    },
}


def get_platform(key):
    """取平台配置；未知 key 抛 KeyError 并列出全部可用 key。"""
    if key not in PLATFORMS:
        raise KeyError(f"[platforms] 未知平台 '{key}'，可用: {list(PLATFORMS)}")
    return PLATFORMS[key]


def resolve_keys(spec=None, version=None):
    """
    把用户输入的平台规格解析为 key 列表。

    spec: None → 按 version 取全套；"doubao,kimi" → 逗号分隔；["doubao"] → 列表
    version: "domestic" | "overseas" | "both"
    """
    if spec:
        if isinstance(spec, str):
            keys = [k.strip() for k in spec.split(",") if k.strip()]
        else:
            keys = list(spec)
        for k in keys:
            get_platform(k)          # 校验
        return keys
    if version == "overseas":
        return list(OVERSEAS)
    if version == "both":
        return DOMESTIC + OVERSEAS
    return list(DOMESTIC)
