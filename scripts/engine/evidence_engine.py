#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
痛點問答證據卡 HTML 引擎
========================
輸入 EVIDENCE_CONFIG（cases/<name>/evidence_config.py），輸出獨立單文件 HTML：
用「模擬 AI 平臺問答還原」的對話氣泡，把三類痛點做成客戶一眼看懂的截圖式證據——

  kind=absent   → 對手出現 · 本品牌缺席（零價值曝光）
  kind=negative → 本品牌負面提及（輿情風險）
  kind=wrong    → 信息錯誤 / 過時（基建缺口）

紀律（與 references/evidence_capture.md、style_guide.md 第六節一致）：
- 每卡必須帶 level：A=線上實查 / B=客戶提供 / C=診斷模型估算
- 頁眉聲明「示意問答還原」；全檔禁用 虛擬 / ⚠️ / website / {{ 標記（引擎內校驗，命中即報錯）
- 純標準庫，無外部依賴，雙擊即可在瀏覽器打開
"""
import html as _h

KIND_META = {
    "absent":   ("對手出現 · 本品牌缺席", "RED"),
    "negative": ("本品牌負面提及", "AMBER"),
    "wrong":    ("信息錯誤 / 過時", "AMBER"),
}
LEVEL_META = {"A": "線上實查", "B": "客戶提供", "C": "診斷模型估算"}
FORBIDDEN = ["虛擬", "⚠️", "website", "{{", "VIRTUAL"]
LOGICAL = ["BLUE", "NAVY", "CYAN", "CLOUD", "INK", "GRAY",
           "WHITE", "GREEN", "AMBER", "RED", "LIGHTBLUE"]


def _check(cfg):
    pal = cfg.get("PALETTE_HEX") or {}
    missing = [n for n in LOGICAL if n not in pal]
    if missing:
        raise ValueError(f"[evidence] PALETTE_HEX 缺少邏輯色名: {missing}")
    if not cfg.get("CARDS"):
        raise ValueError("[evidence] CARDS 為空：至少提供一張痛點卡")
    if not cfg.get("BRAND_CN"):
        raise ValueError("[evidence] 缺少 BRAND_CN")
    for i, c in enumerate(cfg["CARDS"], 1):
        if c.get("kind") not in KIND_META:
            raise ValueError(f"[evidence] 第 {i} 卡 kind 非法: {c.get('kind')!r}（可選 absent/negative/wrong）")
        if c.get("level") not in LEVEL_META:
            raise ValueError(f"[evidence] 第 {i} 卡 level 非法: {c.get('level')!r}（A/B/C，見 evidence_capture.md）")
        for field in ("question", "answer", "pain", "action", "platform"):
            text = str(c.get(field, ""))
            for bad in FORBIDDEN:
                if bad in text:
                    raise ValueError(f"[evidence] 第 {i} 卡 {field} 命中禁用標記 {bad!r}（數據標註紀律）")


def _hl(text, brand, mentions, brand_hex, comp_hex):
    """HTML 轉義後高亮品牌（brand_hex）與競品提及（comp_hex），先長後短避免子串重疊。"""
    s = _h.escape(str(text))
    tokens = {}

    def reg(name, color):
        key = f"\x00{len(tokens)}\x00"
        tokens[key] = f'<span style="color:{color};font-weight:700">{_h.escape(name)}</span>'
        return key

    entries = [(brand, brand_hex)] + [(m, comp_hex) for m in mentions if m and m != brand]
    entries = [e for e in entries if e[0] and _h.escape(e[0]) in s]
    entries.sort(key=lambda e: -len(e[0]))
    for name, color in entries:
        s = s.replace(_h.escape(name), reg(name, color))
    for key, span in tokens.items():
        s = s.replace(key, span)
    return s


def build_evidence_cards(cfg):
    _check(cfg)
    pal = cfg["PALETTE_HEX"]
    font = cfg.get("FONT", "微軟雅黑")
    brand = cfg["BRAND_CN"]
    scope = cfg.get("VERSION_SCOPE", "")
    note = cfg.get("SOURCE_NOTE", "")

    counts = {"absent": 0, "negative": 0, "wrong": 0}
    cards = []
    for idx, c in enumerate(cfg["CARDS"], 1):
        kind = c["kind"]
        counts[kind] += 1
        tag, color_key = KIND_META[kind]
        tag_hex = pal[color_key]
        brand_hex = pal["AMBER"] if kind == "negative" else pal["GREEN"]
        q = _hl(c["question"], brand, c.get("mentions", []), brand_hex, pal["RED"])
        a = _hl(c["answer"], brand, c.get("mentions", []), brand_hex, pal["RED"])
        cards.append(f"""
    <div class="card">
      <div class="card-head">
        <span class="badge" style="background:{tag_hex}">{_h.escape(tag)}</span>
        <span class="chip" style="color:{pal['BLUE']};border-color:{pal['BLUE']}">{_h.escape(c['platform'])}</span>
        <span class="chip" style="color:{pal['GRAY']};border-color:{pal['GRAY']}">證據級別 {_h.escape(c['level'])} · {_h.escape(LEVEL_META[c['level']])}</span>
        <span class="no">卡 {idx}</span>
      </div>
      <div class="chat">
        <div class="row user"><div class="bubble user-b" style="background:{pal['BLUE']};color:{pal['WHITE']}">{q}</div></div>
        <div class="row ai"><div class="avatar" style="background:{pal['NAVY']};color:{pal['WHITE']}">AI</div>
        <div class="bubble ai-b" style="background:{pal['CLOUD']};color:{pal['INK']};border:1px solid {pal['LIGHTBLUE']}">{a}</div></div>
      </div>
      <div class="foot">
        <div class="pain" style="background:{pal['LIGHTBLUE']};border-left:4px solid {tag_hex};color:{pal['INK']}">
          <b>客戶視角痛點</b>{_h.escape(c['pain'])}</div>
        <div class="act" style="background:{pal['WHITE']};border-left:4px solid {pal['GREEN']};color:{pal['INK']}">
          <b>建議下一步</b>{_h.escape(c['action'])}</div>
      </div>
    </div>""")

    scope_badge = f'<span class="scope" style="background:{pal["CYAN"]};color:{pal["NAVY"]}">{_h.escape(scope)}</span>' if scope else ""
    summary = (f'{len(cfg["CARDS"])} 張卡 · 缺席 {counts["absent"]} / 負面 {counts["negative"]} / 過時 {counts["wrong"]}')

    return f"""<!DOCTYPE html>
<html lang="zh">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{_h.escape(brand)} · AI 平臺問答痛點證據卡</title>
<style>
  * {{ box-sizing: border-box; margin: 0; padding: 0; }}
  body {{ font-family: "{font}", "PingFang TC", "Microsoft YaHei", sans-serif;
         background: {pal['CLOUD']}; color: {pal['INK']}; padding: 28px 16px 48px; }}
  .wrap {{ max-width: 880px; margin: 0 auto; }}
  header.top {{ background: {pal['NAVY']}; border-radius: 14px; padding: 26px 28px; color: {pal['WHITE']}; }}
  header.top h1 {{ font-size: 24px; letter-spacing: 1px; }}
  header.top .sub {{ margin-top: 8px; font-size: 13px; opacity: .85; display: flex; gap: 10px; align-items: center; flex-wrap: wrap; }}
  .scope {{ padding: 3px 12px; border-radius: 999px; font-weight: 700; font-size: 12px; }}
  .notice {{ margin-top: 12px; font-size: 12px; line-height: 1.7; color: {pal['GRAY']};
            background: {pal['WHITE']}; border: 1px dashed {pal['GRAY']}; border-radius: 10px; padding: 10px 14px; }}
  .card {{ background: {pal['WHITE']}; border-radius: 14px; margin-top: 22px; overflow: hidden;
          box-shadow: 0 2px 10px rgba(15,30,70,.08); }}
  .card-head {{ display: flex; align-items: center; gap: 10px; padding: 14px 18px; flex-wrap: wrap; }}
  .badge {{ color: {pal['WHITE']}; padding: 4px 12px; border-radius: 999px; font-size: 13px; font-weight: 700; }}
  .chip {{ border: 1px solid; border-radius: 999px; padding: 2px 10px; font-size: 12px; background: {pal['WHITE']}; }}
  .no {{ margin-left: auto; color: {pal['GRAY']}; font-size: 12px; }}
  .chat {{ padding: 6px 18px 16px; }}
  .row {{ display: flex; margin: 10px 0; gap: 10px; }}
  .row.user {{ justify-content: flex-end; }}
  .bubble {{ max-width: 78%; padding: 12px 16px; border-radius: 12px; font-size: 14.5px; line-height: 1.75; }}
  .user-b {{ border-bottom-right-radius: 3px; }}
  .ai-b {{ border-bottom-left-radius: 3px; }}
  .avatar {{ width: 34px; height: 34px; border-radius: 50%; display: flex; align-items: center;
            justify-content: center; font-size: 12px; font-weight: 700; flex-shrink: 0; }}
  .foot {{ display: grid; grid-template-columns: 1fr 1fr; gap: 12px; padding: 0 18px 18px; }}
  .pain, .act {{ border-radius: 10px; padding: 12px 14px; font-size: 13.5px; line-height: 1.7; }}
  .pain b, .act b {{ display: block; margin-bottom: 4px; font-size: 12px; letter-spacing: 1px; opacity: .8; }}
  @media (max-width: 640px) {{ .foot {{ grid-template-columns: 1fr; }} .bubble {{ max-width: 92%; }} }}
  footer {{ margin-top: 26px; text-align: center; font-size: 12px; color: {pal['GRAY']}; line-height: 1.8; }}
</style>
</head>
<body>
<div class="wrap">
  <header class="top">
    <h1>{_h.escape(brand)} · AI 平臺問答痛點證據卡</h1>
    <div class="sub">{scope_badge}<span>{_h.escape(summary)}</span></div>
  </header>
  <div class="notice"><b>示意問答還原聲明</b>　{_h.escape(note)}。
    證據級別：A＝線上實查（帶日期與來源）／B＝客戶提供／C＝診斷模型估算。本卡用於說明痛點場景與優先方向，不構成對平臺結果的保證。</div>
  {''.join(cards)}
  <footer>微盟星启 GEO · 痛點問答證據卡（示意問答還原）</footer>
</div>
</body>
</html>"""
