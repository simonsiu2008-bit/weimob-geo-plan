#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
脱敏模板：痛点问答证据卡数据（evidence_config.py）
==================================================
字段说明见 references/evidence_capture.md。
kind:   absent=对手出现本品牌缺席 / negative=本品牌负面提及 / wrong=信息错误或过时
level:  A=线上实查（带日期与来源）/ B=客户提供 / C=诊断模型估算
所有品牌、竞品均为通用占位，新案例复制本文件后逐项替换。

> 版本说明：`VERSION_SCOPE` 是**展示字段**，须与 config.py 的引擎开关 `VERSION` 一致——
>   VERSION="domestic" → VERSION_SCOPE="国内版"
>   VERSION="overseas" → VERSION_SCOPE="海外版"
>   VERSION="both"     → VERSION_SCOPE="双版"
> 平台来源见 references/version_scope.md。
"""

EVIDENCE_CONFIG = {
    "OUT_FILENAME": "示例客户_国内版GEO问答证据卡.html",
    "BRAND_CN": "示例客户",
    "VERSION_SCOPE": "国内版",   # 国内版 / 海外版 / 双版（须与 config.py 的 VERSION 对应）
    "SOURCE_NOTE": "2026-XX 线上实查 + 微盟星启 GEO 診斷模型估算",
    "PALETTE_HEX": {
        "BLUE": "#2A5BEA", "NAVY": "#0B1F4D", "CYAN": "#18C8FF",
        "CLOUD": "#F5F7FC", "INK": "#16213A", "GRAY": "#6E7689",
        "WHITE": "#FFFFFF", "GREEN": "#059669", "AMBER": "#D97706",
        "RED": "#DC2626", "LIGHTBLUE": "#E8EEFD",
    },
    "FONT": "微軟雅黑",
    "CARDS": [
        {
            "kind": "absent", "level": "A", "platform": "示例平臺A",
            "question": "示例品類怎麼選？（客戶客群高頻問法占位）",
            "answer": "可以考慮 示例競品A 與 示例競品B，它們在品質與口碑方面表現突出（回答還原占位，基於線上實查）。",
            "mentions": ["示例競品A", "示例競品B"],
            "pain": "客戶問的是品類問題，AI 推薦的全是競品——本品牌連入場資格都沒有。",
            "action": "本月內在權威內容平台補齊 L1 品類話題內容，讓 AI 有答案可抄（占位，替換為具體動作）。",
        },
        {
            "kind": "negative", "level": "B", "platform": "示例平臺B",
            "question": "示例客戶的產品靠譜嗎？（占位）",
            "answer": "有用戶反饋 示例客戶 存在售後響應慢的評價，建議購買前確認渠道（負面提及還原占位）。",
            "mentions": [],
            "pain": "AI 有提到本品牌，但講的是負面評測——等於幫對手做廣告。",
            "action": "先處理負面來源（回覆/下架/更新），再補正面權威內容覆蓋（占位）。",
        },
        {
            "kind": "wrong", "level": "A", "platform": "示例平臺C",
            "question": "示例客戶 在哪裡有門店？（占位）",
            "answer": "示例客戶 門店位於……（信息為過時內容還原占位）。",
            "mentions": [],
            "pain": "AI 給出的門店/價格信息是舊的——客戶未見面已被錯誤信息勸退。",
            "action": "修正官網與權威平台的基础信息，讓 AI 抄到最新版本（占位）。",
        },
    ],
}
