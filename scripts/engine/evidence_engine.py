#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
共享引擎：AI 实测证据报告 HTML 渲染器
========================================
把采集引擎产出的 manifest.json（真实浏览器访问各 AI 平台的问答与截图）
渲染成客户可读的「AI 实测证据报告」——用截图说话，不堆术语。

设计目标（对应客户反馈）：
1. 让客户**亲眼看到**「问 AI 时对手出现了、你没有出现」；
2. 让客户看到自家品牌被 AI 引用的负面评测；
3. 用最直白的话说明现状，降低后期落地运营的理解门槛。

四大区块：
    ① 采集概览      平台数/题数/成功率/采集时间 + 数据来源声明
    ② 品牌缺席证据  提问后竞品被点名、本品牌零提及（左：竞品出现 / 右：您未出现）
    ③ 负面引用证据  本品牌被提及但情感偏负
    ④ 数据缺口清单  未成功采集的平台与原因（如实披露，不美化）

图片策略（混合模式）：
    默认 → <img src="shots/xxx.png"> + 同目录 shots/（打包 zip 分发）
    embed=True → 读图转 base64 内联，生成单文件自包含 HTML

数据隔离：本引擎不持有任何案例数据，全部来自传入的 EVIDENCE_CONFIG。
"""
import base64
import html
import json
import mimetypes
import os


def _esc(s):
    return html.escape(str(s if s is not None else ""))


def _pct(v):
    try:
        return f"{float(v):.0%}"
    except Exception:
        return "—"


# =====================================================================
# CSS（沿用话题词方案的视觉语言，保证同一套交付物观感一致）
# =====================================================================
CSS = """
:root{--blue:#2A5BEA;--navy:#0B1F4D;--navy2:#1B3366;--cyan:#18C8FF;--cloud:#F5F7FC;--ink:#16213A;
--gray:#6E7689;--line:#E6EAF3;--white:#fff;--green:#059669;--amber:#D97706;--red:#DC2626;}
*{box-sizing:border-box;margin:0;padding:0}
body{font-family:-apple-system,BlinkMacSystemFont,"PingFang SC","Microsoft YaHei","Segoe UI",sans-serif;
color:var(--ink);background:var(--cloud);line-height:1.7;-webkit-font-smoothing:antialiased}
.wrap{max-width:1120px;margin:0 auto;padding:0 28px}
.mono{font-variant-numeric:tabular-nums;font-feature-settings:"tnum"}

/* ---- hero ---- */
.hero{background:var(--navy);color:#fff;padding:60px 0 0;position:relative;overflow:hidden}
.hero::before{content:"";position:absolute;left:0;top:0;bottom:0;width:6px;background:var(--cyan)}
.eyebrow{font-size:12px;letter-spacing:.22em;color:var(--cyan);font-weight:700}
.hero h1{font-size:42px;line-height:1.18;font-weight:800;margin:14px 0 0;letter-spacing:-.01em}
.hero h1 em{font-style:normal;color:var(--cyan)}
.hero .sub{font-size:15.5px;color:#B9C7E8;margin-top:14px;max-width:720px}
.heroGrid{display:grid;grid-template-columns:1.3fr 1fr;gap:38px;align-items:end}
.statRow{display:grid;grid-template-columns:repeat(2,1fr);gap:10px;margin:30px 0 34px}
.stat{background:var(--navy2);border-radius:10px;padding:14px 16px}
.stat b{display:block;font-size:30px;font-weight:800;color:#fff;line-height:1.1}
.stat span{font-size:11.5px;color:#8FA3D0;display:block;margin-top:3px}
.stat.accent{border:1px solid var(--cyan)} .stat.accent b{color:var(--cyan)}
.stat.warn{border:1px solid #F87171} .stat.warn b{color:#FCA5A5}

/* ---- 区块 ---- */
section{padding:52px 0}
.secHead{display:flex;align-items:baseline;gap:14px;margin-bottom:8px}
.secNum{font-size:12px;font-weight:800;color:var(--blue);letter-spacing:.14em}
.secHead h2{font-size:26px;font-weight:800;letter-spacing:-.01em}
.secDesc{font-size:14.5px;color:var(--gray);max-width:820px;margin-bottom:28px}
.note{background:#fff;border:1px solid var(--line);border-left:5px solid var(--cyan);border-radius:10px;
padding:16px 20px;font-size:13.5px;color:var(--ink);margin-bottom:26px}
.note b{color:var(--blue)}

/* ---- 证据卡：左竞品出现 / 右您缺席 ---- */
.card{background:#fff;border:1px solid var(--line);border-radius:14px;padding:22px 24px;margin-bottom:18px;
box-shadow:0 4px 18px rgba(11,31,77,.05)}
.cardTop{display:flex;align-items:center;gap:12px;flex-wrap:wrap;margin-bottom:6px}
.qid{font-size:11px;font-weight:800;color:#fff;background:var(--navy);padding:3px 9px;border-radius:5px;letter-spacing:.04em}
.qtext{font-size:17px;font-weight:700;color:var(--ink)}
.tagLv{font-size:11px;font-weight:700;color:var(--blue);background:#E8EEFD;padding:3px 9px;border-radius:5px}
.plat{font-size:11.5px;color:var(--gray);margin-left:auto}
.vs{display:grid;grid-template-columns:1fr 1fr;gap:14px;margin-top:14px}
.pane{border-radius:10px;overflow:hidden;border:1px solid var(--line);background:#FAFBFE}
.paneHead{padding:10px 14px;font-size:12.5px;font-weight:700;display:flex;align-items:center;gap:8px}
.paneHead.hit{background:#FEF2F2;color:#B91C1C;border-bottom:1px solid #FECACA}
.paneHead.miss{background:#F0FDF4;color:#15803D;border-bottom:1px solid #BBF7D0}
.paneHead .dot{width:8px;height:8px;border-radius:50%;display:inline-block}
.paneHead.hit .dot{background:#DC2626} .paneHead.miss .dot{background:#059669}
.pane img{width:100%;display:block;background:#fff}
.shotWrap{max-height:340px;overflow:auto;background:#F8FAFC}
.placeholder{padding:24px 16px;text-align:center;font-size:12.5px;color:var(--gray);background:#F8FAFC;min-height:140px;
display:flex;align-items:center;justify-content:center;flex-direction:column;gap:8px}
.placeholder b{font-size:26px;color:#CBD5E1;display:block}
.mentions{margin-top:12px;font-size:12.5px;color:var(--gray);display:flex;gap:8px;flex-wrap:wrap;align-items:center}
.chip{font-size:11.5px;font-weight:700;padding:3px 10px;border-radius:99px;white-space:nowrap}
.chip.rival{background:#FEF2F2;color:#B91C1C}
.chip.self{background:#E8EEFD;color:var(--blue)}
.chip.none{background:#F1F5F9;color:#94A3B8}

/* ---- 负面证据 ---- */
.negCard{background:#fff;border:1px solid #FCA5A5;border-radius:14px;padding:22px 24px;margin-bottom:18px;
box-shadow:0 4px 18px rgba(220,38,38,.07)}
.negTag{display:inline-block;background:var(--red);color:#fff;font-size:11px;font-weight:700;padding:3px 10px;border-radius:5px}
.evidenceList{margin-top:10px;font-size:12.5px;color:#7F1D1D}
.evidenceList span{display:inline-block;background:#FEE2E2;color:#991B1B;padding:2px 8px;border-radius:5px;margin:3px 4px 0 0}

/* ---- 缺口表 ---- */
table{width:100%;border-collapse:collapse;font-size:13px;background:#fff;border-radius:12px;overflow:hidden;
box-shadow:0 4px 18px rgba(11,31,77,.05)}
th{background:var(--navy);color:#fff;text-align:left;padding:11px 14px;font-size:12.5px;font-weight:700}
td{padding:10px 14px;border-bottom:1px solid var(--line);color:var(--ink)}
tr:last-child td{border-bottom:none}
tr:nth-child(even) td{background:#FAFBFE}
.st-ok{color:var(--green);font-weight:700}
.st-bad{color:var(--red);font-weight:700}
.st-warn{color:var(--amber);font-weight:700}

/* ---- 空态 ---- */
.empty{background:#fff;border:1px dashed #CBD5E1;border-radius:12px;padding:40px 28px;text-align:center;color:var(--gray)}
.empty b{display:block;font-size:16px;color:var(--ink);margin-bottom:8px}
.empty code{background:#F1F5F9;padding:2px 8px;border-radius:5px;font-size:12.5px}

footer{background:var(--navy);color:#8FA3D0;padding:34px 0;font-size:12.5px}
footer .fbrand{color:#fff;font-weight:700;font-size:14px}
"""


# ------------------------------------------------------------------ 工具

def _img_tag(shot_rel, base_dir, embed):
    """生成 <img> 标签。embed=True 时转 base64 内联。"""
    if not shot_rel:
        return None
    path = os.path.join(base_dir, shot_rel)
    if not os.path.isfile(path):
        return None
    if embed:
        mime = mimetypes.guess_type(path)[0] or "image/png"
        with open(path, "rb") as f:
            b64 = base64.b64encode(f.read()).decode("ascii")
        return f'<img src="data:{mime};base64,{b64}" alt="AI 回答截图">'
    # 相对路径：用 posix 风格，保证跨平台
    return f'<img src="{_esc(shot_rel.replace(os.sep, "/"))}" alt="AI 回答截图" loading="lazy">'


def _pick_pair(by_q_platform):
    """
    为一个问题挑选最具说服力的一对证据：
      hit  = 竞品出现（且优先本品牌未出现）的截图
      miss = 本品牌未出现的截图
    返回 (hit_item, miss_item)。
    """
    ok = [it for it in by_q_platform if it.get("status") == "ok"]
    if not ok:
        return None, None
    # 优先：竞品出现 + 本品牌未出现
    both = [it for it in ok if it.get("rivals_mentioned") and not it.get("brand_mentioned")]
    if both:
        return both[0], both[0]
    hit = [it for it in ok if it.get("rivals_mentioned")] or ok
    miss = [it for it in ok if not it.get("brand_mentioned")] or ok
    return hit[0], miss[0]


# ------------------------------------------------------------------ 渲染

def build_evidence_html(ec):
    """
    ec = EVIDENCE_CONFIG dict：
        BRAND        品牌名
        BRAND_SUB    副标题
        MANIFEST     采集结果 manifest.json 路径（或已加载的 dict）
        BASE_DIR     截图相对路径的参照目录（默认 manifest 所在目录）
        EMBED        True → base64 内联
        OUT_TITLE    可选，报告标题
    """
    man = ec.get("MANIFEST")
    if isinstance(man, str):
        with open(man, "r", encoding="utf-8") as f:
            man = json.load(f)
    if not man:
        raise ValueError("[evidence] EVIDENCE_CONFIG 缺少 MANIFEST（manifest.json 路径或 dict）")

    base_dir = ec.get("BASE_DIR") or (
        os.path.dirname(os.path.abspath(ec["MANIFEST"])) if isinstance(ec.get("MANIFEST"), str) else "."
    )
    embed = bool(ec.get("EMBED", False))
    brand = ec.get("BRAND") or man.get("case") or "本品牌"
    brand_sub = ec.get("BRAND_SUB", "")

    items = man.get("items", [])
    questions = man.get("questions", [])
    summary = man.get("summary", {})
    pdefs = man.get("platforms", [])

    # --- 汇总统计 ---
    ok_items = [it for it in items if it.get("status") == "ok"]
    absent = [it for it in ok_items if not it.get("brand_mentioned") and it.get("rivals_mentioned")]
    negative = [it for it in ok_items if it.get("brand_mentioned") and it.get("sentiment") in ("negative", "mixed")]

    # --- 按问题分组 ---
    by_q = {}
    for it in items:
        by_q.setdefault(it["qid"], []).append(it)
    q_order = [q["qid"] for q in questions] or sorted(by_q.keys())
    qtext = {q["qid"]: q for q in questions}

    # ---- 缺口统计 ----
    gap_rows = []
    for pk in pdefs:
        reps = [it for it in items if it.get("platform") == pk]
        if not reps:
            continue
        st = {}
        for r in reps:
            st[r.get("status")] = st.get(r.get("status"), 0) + 1
        okn = st.get("ok", 0)
        name = reps[0].get("platform_name", pk)
        if okn == len(reps):
            verdict, cls = "全部成功", "st-ok"
        elif okn > 0:
            verdict, cls = f"部分成功（{okn}/{len(reps)}）", "st-warn"
        else:
            verdict, cls = "未采集到数据", "st-bad"
        reason = ""
        for r in reps:
            if r.get("status") != "ok" and r.get("error"):
                reason = r["error"][:90]
                break
        gap_rows.append((name, verdict, cls, reason))

    h = []
    h.append('<!DOCTYPE html><html lang="zh-CN"><head><meta charset="utf-8">')
    h.append('<meta name="viewport" content="width=device-width,initial-scale=1">')
    h.append(f'<title>{_esc(ec.get("OUT_TITLE") or (brand + " · AI 实测证据报告"))}</title>')
    h.append(f"<style>{CSS}</style></head><body>")

    # ================= HERO =================
    collected_at = man.get("collected_at", "—")
    h.append('<div class="hero"><div class="wrap"><div class="heroGrid"><div>')
    h.append('<div class="eyebrow">AI 实测证据报告 · EVIDENCE REPORT</div>')
    h.append(f'<h1>{_esc(brand)}<br><em>问 AI 的时候，它到底说了谁？</em></h1>')
    h.append('<p class="sub">本报告不引用任何行业推测，全部内容来自浏览器实际访问 AI 平台'
             '所得到的问答截图——你看得到每一张画面，也看得到哪些平台没问到。</p>')
    if brand_sub:
        h.append(f'<p class="sub" style="margin-top:8px;color:#8FA3D0;font-size:13px">{_esc(brand_sub)}</p>')
    h.append('</div><div>')
    h.append('<div class="statRow">')
    h.append(f'<div class="stat accent"><b>{len(pdefs)}</b><span>AI 平台数</span></div>')
    h.append(f'<div class="stat"><b>{len(questions)}</b><span>提问数</span></div>')
    h.append(f'<div class="stat"><b>{summary.get("ok", 0)}</b><span>成功取证次数</span></div>')
    h.append(f'<div class="stat warn"><b>{len(absent)}</b><span>对手出现 · 你缺席</span></div>')
    h.append('</div></div></div>')
    h.append(f'<div style="padding:0 0 30px;font-size:12px;color:#8FA3D0">采集时间：{_esc(collected_at)}'
             f'　·　采集方式：{_esc(man.get("collector", "浏览器实测"))}</div>')
    h.append('</div></div>')

    # ================= ① 一句话结论 =================
    h.append('<section><div class="wrap">')
    h.append('<div class="secHead"><span class="secNum">01</span><h2>先看结论</h2></div>')
    if ok_items:
        rate = summary.get("coverage", 0)
        h.append('<div class="secDesc">下面每个数字背后都有截图，你可以逐张核对。</div>')
        concl = []
        if absent:
            concl.append(f"在 <b>{len(absent)}</b> 次提问里，AI 点名了竞争对手，却<b>一次都没提到你</b>。"
                         f"这正是客户流失发生的地方——用户还没听说过你，就已经被推荐给了别人。")
        if negative:
            concl.append(f"另有 <b>{len(negative)}</b> 次提问虽提到了你，但 AI 同时带出了负面信息。"
                         f"这是品牌在 AI 里的「口碑污点」，会直接影响成交。")
        if not absent and not negative:
            concl.append("本轮实测中，未发现明显的品牌缺席或负面引用——表现好于同类客户。")
        concl.append(f"本轮共在 {len(pdefs)} 个平台上完成 {summary.get('ok', 0)} 次有效取证，"
                     f"整体采集覆盖率 {_pct(rate)}。")
        h.append('<div class="note">' + '<br>'.join(concl) + '</div>')
    else:
        h.append('<div class="secDesc">当前尚未取得有效采集数据。</div>')
        h.append('<div class="empty"><b>还没有可展示的实测证据</b>'
                 '需要先在环境里配置 AI 平台登录态，然后运行采集命令：<br><br>'
                 '<code>python3 scripts/collect_run.py cases/&lt;name&gt;</code><br><br>'
                 '配置方法见 <code>scripts/collect/README.md</code></div>')
    h.append('</div></section>')

    # ================= ② 品牌缺席证据 =================
    h.append('<section><div class="wrap">')
    h.append('<div class="secHead"><span class="secNum">02</span><h2>对手出现了，你没有</h2></div>')
    h.append('<div class="secDesc">这些是同一个问题下的 AI 回答截图：左边能看到 AI 提到了哪些竞品，'
             '右边是你在该次回答中的出现情况。<br>建议按顺序逐张看——这是最有说服力的一页。</div>')

    if absent:
        shown = 0
        for qid in q_order:
            group = by_q.get(qid, [])
            hit, miss = _pick_pair(group)
            if not hit or not (not hit.get("brand_mentioned") and hit.get("rivals_mentioned")):
                continue
            q = qtext.get(qid, {})
            shown += 1
            h.append('<div class="card">')
            h.append('<div class="cardTop">')
            h.append(f'<span class="qid">{_esc(qid.upper())}</span>')
            h.append(f'<span class="qtext">{_esc(hit.get("question", q.get("question", "")))}</span>')
            if q.get("level"):
                h.append(f'<span class="tagLv">{_esc(q["level"])}</span>')
            h.append(f'<span class="plat">平台：{_esc(hit.get("platform_name", ""))}</span>')
            h.append('</div>')
            h.append('<div class="vs">')
            # 左：竞品出现
            h.append('<div class="pane">')
            h.append(f'<div class="paneHead hit"><span class="dot"></span>AI 提到了这些对手</div>')
            img = _img_tag(hit.get("shot"), base_dir, embed)
            h.append('<div class="shotWrap">' + (img if img else
                     '<div class="placeholder"><b>!</b>截图缺失</div>') + '</div>')
            h.append('</div>')
            # 右：我方缺席
            h.append('<div class="pane">')
            h.append(f'<div class="paneHead miss"><span class="dot"></span>{_esc(brand)} 未出现</div>')
            h.append('<div class="placeholder"><b>0</b>'
                     f'该次回答中，{_esc(brand)} 的提及次数为 0</div>')
            h.append('</div>')
            h.append('</div>')
            # 提及品牌 chips
            h.append('<div class="mentions"><span>本次点名：</span>')
            for r in hit.get("rivals_mentioned", [])[:8]:
                h.append(f'<span class="chip rival">{_esc(r)}</span>')
            h.append(f'<span class="chip none">{_esc(brand)}：未提及</span>')
            h.append('</div>')
            h.append('</div>')
            if shown >= 12:
                break
        if shown == 0:
            h.append('<div class="empty"><b>本轮未发现「竞品出现且本品牌缺席」的证据</b>'
                     '可能是采集覆盖不足，或品牌可见度确实较好。</div>')
    else:
        h.append('<div class="empty"><b>暂无可展示的缺席证据</b>'
                 '需要先完成线上采集，或本轮采集未发现此类情况。</div>')
    h.append('</div></section>')

    # ================= ③ 负面引用证据 =================
    h.append('<section><div class="wrap">')
    h.append('<div class="secHead"><span class="secNum">03</span><h2>你被提到时，AI 说了什么</h2></div>')
    h.append('<div class="secDesc">品牌被提及不等于口碑良好。下面这些回答里，AI 在提到你的同时'
             '带出了负面或争议信息——这条信息会被每一个提问的用户看到。</div>')
    if negative:
        for it in negative[:10]:
            h.append('<div class="negCard">')
            h.append('<div class="cardTop">')
            h.append(f'<span class="qid">{_esc(it["qid"].upper())}</span>')
            h.append(f'<span class="qtext">{_esc(it.get("question", ""))}</span>')
            h.append(f'<span class="plat">平台：{_esc(it.get("platform_name", ""))}</span>')
            h.append('</div>')
            h.append(f'<div style="margin:8px 0"><span class="negTag">'
                     f'{"负面" if it.get("sentiment") == "negative" else "褒贬并存"}</span></div>')
            img = _img_tag(it.get("shot"), base_dir, embed)
            h.append('<div class="shotWrap" style="border:1px solid var(--line);border-radius:10px">' +
                     (img if img else '<div class="placeholder"><b>!</b>截图缺失</div>') + '</div>')
            ev = it.get("sentiment_evidence", [])
            if ev:
                h.append('<div class="evidenceList">判定依据（回答中出现的关键词）：')
                for w in ev[:10]:
                    h.append(f'<span>{_esc(w)}</span>')
                h.append('</div>')
            h.append('</div>')
    else:
        h.append('<div class="empty"><b>本轮未发现针对本品牌的负面 AI 回答</b>'
                 '这是好消息——但也可能是品牌声量太低、AI 根本没提，请结合上一节一起看。</div>')
    h.append('</div></section>')

    # ================= ④ 数据缺口（如实披露） =================
    h.append('<section><div class="wrap">')
    h.append('<div class="secHead"><span class="secNum">04</span><h2>数据完整性说明</h2></div>')
    h.append('<div class="secDesc">我们如实列出每个平台的采集情况。没采集到的就没有结论，'
             '不用推测数据填充——这是本报告与市面报告最大的区别。</div>')
    if gap_rows:
        h.append('<table><tr><th style="width:20%">AI 平台</th>'
                 '<th style="width:22%">采集情况</th><th>说明</th></tr>')
        for name, verdict, cls, reason in gap_rows:
            h.append(f'<tr><td><b>{_esc(name)}</b></td><td class="{cls}">{_esc(verdict)}</td>'
                     f'<td style="color:#6E7689;font-size:12.5px">{_esc(reason) or "—"}</td></tr>')
        h.append('</table>')
    else:
        h.append('<div class="empty"><b>暂无采集记录</b>请先运行采集命令。</div>')
    h.append('<div class="note" style="margin-top:22px"><b>数据来源声明：</b>'
             + _esc(man.get("data_disclaimer", "本报告数据来自浏览器实际访问各 AI 平台所得。")) +
             '</div>')
    h.append('</div></section>')

    # ================= footer =================
    h.append('<footer><div class="wrap">')
    h.append('<div class="fbrand">微盟星启 · GEO 优化服务</div>')
    h.append('<div style="margin-top:6px">本报告为 AI 平台实测取证，截图未经修饰。'
             '截图为采集时点的真实画面，平台回答会随模型与时间变化。</div>')
    h.append('</div></footer>')
    h.append('</body></html>')
    return "\n".join(h)


# ==================================================================
# 痛点问答证据卡（并入自 v4 · 手填模拟问答还原）
# ------------------------------------------------------------------
# 与上方「AI 实测证据报告」并存：
#   build_evidence_html(ec)  ← 采集版（manifest.json + 截图，需 Playwright）
#   build_evidence_cards(cfg)← 卡片版（evidence_config.py 手填，零依赖）
# 由 scripts/build_evidence_report.py / build_evidence_cards.py 两个 CLI 分别调用。
# 规范见 references/evidence_capture.md。
# ==================================================================

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
    s = html.escape(str(text))
    tokens = {}

    def reg(name, color):
        key = f"\x00{len(tokens)}\x00"
        tokens[key] = f'<span style="color:{color};font-weight:700">{html.escape(name)}</span>'
        return key

    entries = [(brand, brand_hex)] + [(m, comp_hex) for m in mentions if m and m != brand]
    entries = [e for e in entries if e[0] and html.escape(e[0]) in s]
    entries.sort(key=lambda e: -len(e[0]))
    for name, color in entries:
        s = s.replace(html.escape(name), reg(name, color))
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
        <span class="badge" style="background:{tag_hex}">{html.escape(tag)}</span>
        <span class="chip" style="color:{pal['BLUE']};border-color:{pal['BLUE']}">{html.escape(c['platform'])}</span>
        <span class="chip" style="color:{pal['GRAY']};border-color:{pal['GRAY']}">證據級別 {html.escape(c['level'])} · {html.escape(LEVEL_META[c['level']])}</span>
        <span class="no">卡 {idx}</span>
      </div>
      <div class="chat">
        <div class="row user"><div class="bubble user-b" style="background:{pal['BLUE']};color:{pal['WHITE']}">{q}</div></div>
        <div class="row ai"><div class="avatar" style="background:{pal['NAVY']};color:{pal['WHITE']}">AI</div>
        <div class="bubble ai-b" style="background:{pal['CLOUD']};color:{pal['INK']};border:1px solid {pal['LIGHTBLUE']}">{a}</div></div>
      </div>
      <div class="foot">
        <div class="pain" style="background:{pal['LIGHTBLUE']};border-left:4px solid {tag_hex};color:{pal['INK']}">
          <b>客戶視角痛點</b>{html.escape(c['pain'])}</div>
        <div class="act" style="background:{pal['WHITE']};border-left:4px solid {pal['GREEN']};color:{pal['INK']}">
          <b>建議下一步</b>{html.escape(c['action'])}</div>
      </div>
    </div>""")

    scope_badge = f'<span class="scope" style="background:{pal["CYAN"]};color:{pal["NAVY"]}">{html.escape(scope)}</span>' if scope else ""
    summary = (f'{len(cfg["CARDS"])} 張卡 · 缺席 {counts["absent"]} / 負面 {counts["negative"]} / 過時 {counts["wrong"]}')

    return f"""<!DOCTYPE html>
<html lang="zh">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{html.escape(brand)} · AI 平臺問答痛點證據卡</title>
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
    <h1>{html.escape(brand)} · AI 平臺問答痛點證據卡</h1>
    <div class="sub">{scope_badge}<span>{html.escape(summary)}</span></div>
  </header>
  <div class="notice"><b>示意問答還原聲明</b>　{html.escape(note)}。
    證據級別：A＝線上實查（帶日期與來源）／B＝客戶提供／C＝診斷模型估算。本卡用於說明痛點場景與優先方向，不構成對平臺結果的保證。</div>
  {''.join(cards)}
  <footer>微盟星启 GEO · 痛點問答證據卡（示意問答還原）</footer>
</div>
</body>
</html>"""
