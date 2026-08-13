#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
共享引擎：话题词方案 HTML 渲染器
================================
将 build_topic_proposal.py 的渲染逻辑抽取为参数化函数，数据全部来自传入的 TOPIC_CONFIG dict。

build_topic_html(topic_config, output_path)  →  生成「国内版 GEO 话题词方案」HTML。

数据隔离：本引擎不持有任何案例数据；所有品牌/竞品/合规/话题数据均来自 cases/<name>/topic_config.py。
每个案例的话题词方案独立生成、独立输出到自己的 output/ 目录。

渲染固定框架（不可改动，微盟四色 + 微軟雅黑）：
- L1/L2/L3 话题框架 + 20 题监测池 + 五问测试 + 合规校验 + 落地节奏
- 受监管品类（COMPLIANCE.applicable=True）才显示合规横幅与禁用词提示
- 依赖：无第三方库（纯标准库）。
"""
import html


# =====================================================================
# 渲染函数（参数化：所有数据来自 tc = TOPIC_CONFIG dict）
# =====================================================================
CSS = """
:root{--blue:#2A5BEA;--navy:#0B1F4D;--cyan:#18C8FF;--cloud:#F5F7FC;--ink:#16213A;
--gray:#6E7689;--line:#E6EAF3;--white:#fff;--green:#059669;--amber:#D97706;--red:#DC2626;--navy2:#1B3366;}
*{box-sizing:border-box;margin:0;padding:0}
body{font-family:-apple-system,BlinkMacSystemFont,"PingFang SC","Microsoft YaHei","Segoe UI",sans-serif;
color:var(--ink);background:var(--cloud);line-height:1.7;-webkit-font-smoothing:antialiased;}
.wrap{max-width:1080px;margin:0 auto;padding:0 28px}.mono{font-variant-numeric:tabular-nums;font-feature-settings:"tnum"}
.hero{background:var(--navy);color:#fff;padding:64px 0 0;position:relative;overflow:hidden}
.hero::before{content:"";position:absolute;left:0;top:0;bottom:0;width:6px;background:var(--cyan)}
.eyebrow{font-size:12px;letter-spacing:.22em;color:var(--cyan);font-weight:700}
.hero h1{font-size:44px;line-height:1.18;font-weight:800;margin:16px 0 0;letter-spacing:-.01em}
.hero h1 em{font-style:normal;color:var(--cyan)}
.hero .sub{font-size:15.5px;color:#B9C7E8;margin-top:14px;max-width:660px}
.heroGrid{display:grid;grid-template-columns:1.35fr 1fr;gap:38px;align-items:end;padding-bottom:0}
.statRow{display:grid;grid-template-columns:repeat(2,1fr);gap:10px;margin-bottom:6px}
.stat{background:var(--navy2);border-radius:10px;padding:14px 16px}
.stat b{display:block;font-size:30px;font-weight:800;color:#fff;line-height:1.1}
.stat span{font-size:11.5px;color:#8FA3D0;display:block;margin-top:3px}
.stat.accent{border:1px solid var(--cyan)} .stat.accent b{color:var(--cyan)}
.formulaBar{margin-top:34px;background:var(--navy2);border-top:1px solid #2C4A85;padding:14px 0;font-size:12.5px;color:#B9C7E8}
.formulaBar code{background:#0B1F4D;color:var(--cyan);padding:3px 9px;border-radius:5px;font-size:12px}
section{padding:56px 0}.secHead{display:flex;align-items:baseline;gap:14px;margin-bottom:8px}
.secNum{font-size:12px;font-weight:800;color:var(--blue);letter-spacing:.14em}
.secHead h2{font-size:27px;font-weight:800;letter-spacing:-.01em}
.secDesc{font-size:14.5px;color:var(--gray);max-width:760px;margin-bottom:30px}
.compliance{background:#fff;border:1px solid var(--line);border-top:4px solid var(--amber);border-radius:14px;padding:26px 30px;margin:34px 0 0;box-shadow:0 6px 24px rgba(11,31,77,.06)}
.compliance .cTag{display:inline-block;background:var(--amber);color:#fff;font-size:11px;font-weight:700;padding:4px 11px;border-radius:5px;letter-spacing:.05em}
.compliance h2{font-size:20px;font-weight:800;margin:12px 0 14px;line-height:1.4}
.compliance .cBody p{font-size:14px;color:var(--ink);margin-bottom:12px}
.compliance .cKey{background:#FFFBEB;border:1px solid #FDE68A;border-radius:9px;padding:14px 16px;margin-bottom:12px}
.compliance .cKey strong{color:var(--amber)}
.compliance .cKey span{display:inline-block;background:#FEF3C7;color:#92400E;font-size:12px;font-weight:700;padding:4px 10px;border-radius:5px;margin:6px 6px 0 0;white-space:nowrap}
.compliance .cWin{margin-bottom:0;background:#F0FDF4;border:1px solid #BBF7D0;border-radius:9px;padding:14px 16px}
.compliance .cWin strong{color:var(--green)}
.compliance .forbid{display:inline-block;background:#FEE2E2;color:var(--red);font-size:12px;font-weight:700;padding:3px 9px;border-radius:5px;margin:4px 4px 0 0;white-space:nowrap}
.alert{background:#fff;border:1px solid #FCA5A5;border-left:5px solid var(--red);border-radius:12px;padding:26px 30px}
.alert .tag{display:inline-block;background:var(--red);color:#fff;font-size:11px;font-weight:700;padding:4px 11px;border-radius:5px;letter-spacing:.05em}
.alert h3{font-size:21px;font-weight:800;margin:14px 0 10px}
.quote{background:#FEF2F2;border-radius:9px;padding:15px 18px;font-size:14px;margin:16px 0;color:#7F1D1D}
.quote small{display:block;color:var(--gray);font-size:11.5px;margin-top:7px;font-style:normal}
.guard{background:#FFF7ED;border:1pc solid #FED7AA;border-left:4px solid var(--amber);border-radius:8px;padding:12px 15px;font-size:13px;margin-top:16px;color:#9A3412}
.guard b{color:var(--amber)}
.map{display:grid;grid-template-columns:repeat(3,1fr);gap:14px}
.mapCol{background:#fff;border-radius:12px;border:1px solid var(--line);overflow:hidden}
.mapCol .h{padding:13px 18px;color:#fff;font-size:13px;font-weight:700;letter-spacing:.04em}
.mapCol .b{padding:16px 18px}.mapCol .role{font-size:12px;color:var(--gray);margin-bottom:12px}
.mapItem{font-size:14px;font-weight:600;padding:8px 0;border-bottom:1px dashed var(--line);display:flex;justify-content:space-between;gap:8px}
.mapItem:last-child{border:0}.mapItem s{text-decoration:none;font-size:11px;color:var(--gray);font-weight:500;white-space:nowrap}
.topic{background:#fff;border-radius:14px;border:1px solid var(--line);margin-bottom:20px;overflow:hidden;display:grid;grid-template-columns:64px 1fr}
.topic .rail{color:#fff;display:flex;flex-direction:column;align-items:center;justify-content:flex-start;padding:20px 0;gap:6px}
.topic .rail .n{font-size:24px;font-weight:800;line-height:1}.topic .rail .lv{font-size:10px;font-weight:700;letter-spacing:.08em;writing-mode:vertical-rl;margin-top:8px;opacity:.85}
.topic .body{padding:22px 26px}.tHead{display:flex;justify-content:space-between;align-items:flex-start;gap:16px;flex-wrap:wrap}
.tHead h3{font-size:20px;font-weight:800}.tHead .intent{font-size:12.5px;color:var(--gray);margin-top:3px}
.badges{display:flex;gap:6px;flex-wrap:wrap}
.badge{font-size:11px;font-weight:700;padding:3px 9px;border-radius:5px;white-space:nowrap}
.b-hi{background:#FEE2E2;color:var(--red)}.b-mid{background:#FEF3C7;color:var(--amber)}
.b-ok{background:#D1FAE5;color:var(--green)}.b-info{background:#E8EEFD;color:var(--blue)}.b-comp{background:#FFEDD5;color:#C2410C}
.tGrid{display:grid;grid-template-columns:1fr 1fr;gap:0 26px;margin-top:18px}
.fld{padding:11px 0;border-top:1px solid var(--line)}
.fld .k{font-size:11px;font-weight:700;color:var(--blue);letter-spacing:.06em;margin-bottom:4px}
.fld .v{font-size:13.5px;color:var(--ink)}.fld .v em{font-style:normal;background:#FEF3C7;padding:1px 4px;border-radius:3px}
.fld .v .safe{font-style:normal;background:#D1FAE5;color:var(--green);padding:1px 4px;border-radius:3px;font-weight:600}
.rivals{display:flex;flex-wrap:wrap;gap:5px;margin-top:5px}
.rival{font-size:12px;background:var(--cloud);border:1px solid var(--line);padding:3px 9px;border-radius:5px}
.rival.you{background:var(--navy);color:#fff;border-color:var(--navy);font-weight:700}
.script{margin-top:16px;background:var(--navy);color:#fff;border-radius:10px;padding:15px 18px}
.script .k{font-size:11px;font-weight:700;color:var(--cyan);letter-spacing:.06em;margin-bottom:6px}
.script .v{font-size:13.5px;color:#D5DFFA}.script .v b{color:#fff}
.compNote{margin-top:14px;background:#FFF7ED;border:1px solid #FED7AA;border-radius:8px;padding:11px 14px;font-size:12.5px;color:#9A3412}
.compNote b{color:var(--amber)}
table{width:100%;border-collapse:collapse;font-size:13.5px;background:#fff;border-radius:10px;overflow:hidden}
thead tr{background:var(--navy);color:#fff}th{padding:11px 13px;text-align:left;font-weight:700;font-size:12.5px}
td{padding:10px 13px;border-bottom:1px solid var(--line);vertical-align:top}
tbody tr:nth-child(even){background:var(--cloud)}tbody tr:last-child td{border-bottom:0}
.qnum{color:var(--gray);font-variant-numeric:tabular-nums}
.edge{font-size:11.5px;color:var(--gray);line-height:1.5}.edge .ok{color:var(--green);font-weight:700}.edge .no{color:var(--red);font-weight:700}
.tests{display:grid;grid-template-columns:repeat(3,1fr);gap:12px}
.test{background:#fff;border:1px solid var(--line);border-radius:11px;padding:16px 15px;border-top:3px solid var(--blue)}
.test .n{font-size:11px;font-weight:800;color:var(--blue);letter-spacing:.1em}
.test h4{font-size:14.5px;font-weight:800;margin:6px 0 7px}.test p{font-size:12px;color:var(--gray);line-height:1.6}
.steps{display:grid;grid-template-columns:repeat(3,1fr);gap:14px}
.step{background:#fff;border:1px solid var(--line);border-radius:12px;padding:20px 22px;position:relative}
.step .p{font-size:11.5px;font-weight:800;color:#fff;display:inline-block;padding:3px 10px;border-radius:5px;letter-spacing:.05em}
.step h4{font-size:16px;font-weight:800;margin:11px 0 8px}
.step ul{list-style:none;font-size:13px;color:var(--ink)}.step li{padding:4px 0 4px 15px;position:relative;line-height:1.6}
.step li::before{content:"";position:absolute;left:0;top:12px;width:5px;height:5px;border-radius:50%;background:var(--cyan)}
.step .kpi{margin-top:12px;padding-top:11px;border-top:1px dashed var(--line);font-size:12px;color:var(--gray)}.step .kpi b{color:var(--blue)}
footer{background:var(--navy);color:#8FA3D0;padding:34px 0;font-size:12.5px;margin-top:20px}
footer strong{color:#fff;display:block;font-size:14px;margin-bottom:6px}
.note{font-size:12px;color:var(--gray);margin-top:14px;line-height:1.7}
@media(max-width:900px){.heroGrid,.map,.tests,.steps,.tGrid{grid-template-columns:1fr}.hero h1{font-size:32px}.tests{gap:10px}}
"""

RAIL_COLOR = {"blue": "var(--blue)", "cyan": "#18C8FF", "green": "var(--green)"}
RAIL_TXT   = {"blue": "#fff", "cyan": "#0B1F4D", "green": "#fff"}


def _esc(s):
    return html.escape(str(s))


# ---- 各 section 渲染（tc 为 TOPIC_CONFIG）----

def render_compliance(tc):
    comp = tc.get("COMPLIANCE") or {}
    if not comp.get("applicable"):
        return ""
    forbidden = "".join(f'<span class="forbid">{_esc(w)}</span>' for w in comp["forbidden"])
    allowed = "".join(f'<span>{_esc(a)}</span>' for a in comp["allowed"])
    return f"""
<section style="padding:0"><div class="wrap"><div class="compliance">
  <span class="cTag">内容合规红线 · 硬性</span>
  <h2>海外品牌国内版 GEO 的特殊约束：不碰「功能 / 功效」二字</h2>
  <div class="cBody">
    <p>{_esc(comp['note'])}</p>
    <p class="cKey"><b>本方案在国内 6 平台投放的一切内容，只做四件事：</b>{allowed}
      <br><b>绝不出现以下表述：</b>{forbidden}</p>
    <p class="cWin"><b>这恰是差异化机会。</b>{_esc(comp['win'])}</p>
  </div>
</div></div></section>"""


def render_risk(tc):
    r = tc.get("RISK")
    if not r:
        return ""
    analysis = "".join(f"<p style='font-size:14.5px'>{_esc(a)}</p>" for a in r["analysis"])
    return f"""
<section><div class="wrap">
  <div class="secHead"><span class="secNum">01</span><h2>先看一个正在发生的风险</h2></div>
  <div class="secDesc">这不是推演，是本次检索在国内 AI 高权重信源上抓到的实际内容。</div>
  <div class="alert">
    <span class="tag">{_esc(r['tag'])}</span>
    <h3>{_esc(r['title'])}</h3>
    <p style="font-size:14.5px">检索「记忆力下降吃什么保健品」时，国内 AI 高频引用的百家号内容中出现这样的表述：</p>
    <div class="quote">「{_esc(r['quote'])}」<small>{_esc(r['quote_src'])}</small></div>
    {analysis}
    <div class="guard"><b>合规前提下的应对：</b>{_esc(r['guard'])}</div>
  </div>
</div></section>"""


def render_map(tc):
    cols = ""
    for m in tc["TOPIC_MAP"]:
        items = "".join(f'<div class="mapItem">{_esc(n)} <s>{_esc(t)}</s></div>' for n, t in m["items"])
        color = m["color"]
        txtcolor = "#0B1F4D" if color == "cyan" else "#fff"
        cols += f"""<div class="mapCol"><div class="h" style="background:var(--{color});color:{txtcolor}">{_esc(m['lv'])}</div>
      <div class="b"><div class="role">{_esc(m['role'])}</div>{items}</div></div>"""
    return f"""
<section style="padding-top:0"><div class="wrap">
  <div class="secHead"><span class="secNum">02</span><h2>话题三层结构</h2></div>
  <div class="secDesc">单一话题只能测出一个分数，测不出打法。三层结构分别解决「排名在哪」「新客从哪来」「为什么敢买」三个问题。所有话题的内容均限定在「成分 / 正品 / 品质 / 选购」边界内。</div>
  <div class="map">{cols}</div>
</div></section>"""


def render_topics(tc):
    cards = ""
    for t in tc["TOPICS"]:
        badges = "".join(f'<span class="badge {b[1]}">{_esc(b[0])}</span>' for b in t["badges"])
        rivals = "".join(f'<span class="rival">{_esc(r)}</span>' for r in t["rivals"])
        if t.get("you_in"):
            rivals += '<span class="rival you">本品牌（未进榜）</span>'
        fields = ""
        for k, v in t["fields"]:
            fields += f'<div class="fld"><div class="k">{_esc(k)}</div><div class="v">{v}</div></div>'
        comp = f'<div class="compNote"><b>合规提示：</b>{_esc(t["comp_note"])}</div>' if t.get("comp_note") else ""
        rail_color = RAIL_COLOR[t["rail"]]
        rail_txt = RAIL_TXT[t["rail"]]
        cards += f"""
    <div class="topic">
      <div class="rail" style="background:{rail_color};color:{rail_txt}"><span class="n mono">{_esc(t['no'])}</span><span class="lv">{_esc(t['lv'])}</span></div>
      <div class="body">
        <div class="tHead"><div><h3>{_esc(t['title'])}</h3><div class="intent">{_esc(t['intent'])}</div></div>
          <div class="badges">{badges}</div></div>
        <div class="tGrid">{fields}</div>
        {comp}
        <div class="script"><div class="k">现场话术</div><div class="v">{_esc(t['script_v'])}</div></div>
      </div>
    </div>"""
    return f"""
<section style="padding-top:0"><div class="wrap">
  <div class="secHead"><span class="secNum">03</span><h2>五个话题 · 逐个拆解</h2></div>
  <div class="secDesc">每个话题都给出：AI 当前实际召回的竞品、品牌所处位置、合规版内容处方、投放平台、以及现场可用的一句话说法。所有内容处方均不含功能 / 功效声称。</div>
  {cards}
</div></section>"""


def render_pool(tc):
    rows = ""
    for no, topic, q, intent, edge, flag in tc["QUESTION_POOL"]:
        cls = "ok" if flag == "ok" else "no"
        label = "完全合规" if flag == "ok" else "红线"
        rows += (f'<tr><td class="qnum">{_esc(no)}</td><td>{_esc(topic)}</td><td>{_esc(q)}</td>'
                 f'<td>{_esc(intent)}</td><td class="edge"><span class="{cls}">{label}</span> {_esc(edge)}</td></tr>')
    platforms = " / ".join(tc["PLATFORMS"])
    n = len(tc["QUESTION_POOL"]); np_ = len(tc["PLATFORMS"])
    return f"""
<section style="padding-top:0"><div class="wrap">
  <div class="secHead"><span class="secNum">04</span><h2>监测问题池 · {n} 条</h2></div>
  <div class="secDesc">全部为纯品类词 / 场景词，零品牌名。含品牌名的问题会让 AI 必然答出品牌，导致可见度虚高、无法与行业对标。
    {n} 条 × 国内 {np_} 平台 = <b>{n * np_} 个可监测场景</b>。右侧「我方内容边界」列明每个问题对应的内容红线——我们只监测竞品怎么说，自己绝不跟着声称功效。</div>
  <table><thead><tr><th style="width:4%">#</th><th style="width:18%">所属话题</th><th style="width:34%">监测问句（简体中文 · 内地用户口径）</th><th style="width:10%">意图类型</th><th style="width:34%">我方内容边界</th></tr></thead>
  <tbody>{rows}</tbody></table>
  <div class="note">监测平台（国内版 {np_} · 主）：{platforms}。每月同口径复测一次，产出「话题可见度趋势 + 竞品排名变化」双曲线。
    <b style="color:var(--red)">红线重申：</b>问题池用于「监测竞品说了什么」，我方据此生产的内容一律守法——只做成分 / 正品 / 品质 / 选购科普，绝不作功能功效声称。</div>
</div></section>"""


def render_tests(tc):
    tests = [
        ("TEST 01", "竞品召回", "用该话题问 AI，能否稳定返回 ≥5 个品牌名？返回不了就产不出排名，话题作废。"),
        ("TEST 02", "品牌纯净", "话题及派生问题不得含自家品牌名。含了会让可见度虚高，且无法与竞品同口径对比。"),
        ("TEST 03", "叙事一致", "AI 在该话题下的回答语境，是否与品牌核心叙事同一语义场？不同源 = 你是外来户，投产比极低。"),
        ("TEST 04", "意图深度", "话题落在决策链哪一环？科普层 &lt; 对比层 &lt; 选购层。纯科普型话题商业价值低。"),
        ("TEST 05", "内容可执行", "能否直接翻译成「写什么文 + 发哪个平台」？翻译不出来的话题，监测了也无法优化。"),
        ("TEST 06", "合规校验", "该话题下我方要发的内容，能否不写任何功效仍成立？落不了地（必须声称功效才能赢）的话题，对受限行业是雷区，弃用或换角度。"),
    ]
    cells = ""
    for n, h, p in tests:
        accent = 'style="border-top-color:var(--red)"' if n == "TEST 03" else ('style="border-top-color:var(--amber)"' if n == "TEST 06" else "")
        ncolor = 'style="color:var(--red)"' if n == "TEST 03" else ('style="color:var(--amber)"' if n == "TEST 06" else "")
        cells += f'<div class="test" {accent}><div class="n" {ncolor}>{n}</div><h4>{_esc(h)}</h4><p>{_esc(p)}</p></div>'
    return f"""
<section style="padding-top:0"><div class="wrap">
  <div class="secHead"><span class="secNum">05</span><h2>话题词五问测试 + 合规校验</h2></div>
  <div class="secDesc">上述话题均通过以下全部测试与合规校验。这套测试可复用于任何品牌 —— 也是判断一个话题「值不值得投钱」的标准。</div>
  <div class="tests">{cells}</div>
</div></section>"""


def render_steps(tc):
    cells = ""
    for s in tc["STEPS"]:
        color = s["color"]
        txtcolor = "#0B1F4D" if color == "cyan" else "#fff"
        items = "".join(f"<li>{_esc(i)}</li>" for i in s["items"])
        cells += f"""<div class="step"><span class="p" style="background:var(--{color});color:{txtcolor}">{_esc(s['phase'])}</span>
      <h4>{_esc(s['title'])}</h4><ul>{items}</ul>
      <div class="kpi">交付：<b>{_esc(s['kpi'])}</b></div></div>"""
    return f"""
<section style="padding-top:0"><div class="wrap">
  <div class="secHead"><span class="secNum">06</span><h2>话题落地节奏</h2></div>
  <div class="secDesc">先建基线，再打增量，最后固化。每阶段都有可复测的数字，且全程守住合规红线。</div>
  <div class="steps">{cells}</div>
</div></section>"""


def render_footer(tc):
    cite_line = ""
    if tc.get("SOURCE_CITE"):
        chips = "　".join(f'<b style="color:var(--cyan)">{_esc(n)}</b> {c} 次'
                          for n, c in tc["SOURCE_CITE"][:5])
        cite_line = (f'<b>信源引用次数榜（Top {len(tc["SOURCE_CITE"][:5])}）：</b>{chips}'
                     f'　·　上榜信源 = AI 的取材来源，内容投放优先级按此排序。<br>')
    comp_line = ""
    comp = tc.get("COMPLIANCE") or {}
    if comp.get("applicable"):
        comp_line = (f'<span style="color:var(--amber)"><b style="color:var(--amber)">合规声明：</b>'
                     f'{_esc(comp["industry"])}。本方案所有内容处方仅作成分事实科普、正品/原装辨别、'
                     f'品质认证与渠道背书、选购方法与品牌背景之用，不作任何功能/功效声称。具体文案发布前须经合规复核。</span>')
    platforms = " / ".join(tc["PLATFORMS"])
    return f"""
<footer><div class="wrap">
  <strong>微盟星启 GEO 运营团队</strong>
  国内版 {len(tc['PLATFORMS'])} 平台：{platforms}　·　话题可见度与竞品排名按统一口径每月复测<br>
  {cite_line}本方案中「AI 当前召回的竞品池」与「AI 叙事风险」均来自国内公开检索的实际返回内容；话题可见度数值需按本页口径完成基线跑测后填入。<br>
  {comp_line}
</div></footer>"""


def build_topic_html(tc):
    """tc: TOPIC_CONFIG dict（来自 cases/<name>/topic_config.py）"""
    n_topic = len(tc["TOPICS"])
    n_q = len(tc["QUESTION_POOL"])
    np_ = len(tc["PLATFORMS"])
    n_scen = n_q * np_

    rank_card = ""
    if tc.get("RANK_POOL"):
        rank_card = (f'<div class="stat accent"><b class="mono">#{tc["RANK_POOL"]["rank"]}'
                     f'<span style="font-size:17px;font-weight:700">/{tc["RANK_POOL"]["total"]}</span></b>'
                     f'<span>品类话题行业排名 · 竞品池 {tc["RANK_POOL"]["total"]} 个品牌</span></div>')
    else:
        rank_card = f'<div class="stat"><b class="mono">{n_q}</b><span>问题池 · 零品牌名</span></div>'

    dual_card = ""
    if tc.get("VIS_DUAL"):
        vd = tc["VIS_DUAL"]
        dual_card = (f'<div class="stat accent"><b class="mono">'
                     f'{int(vd["brand_word"]*100)}%<span style="font-size:17px;font-weight:700;color:#8FA3D0"> / </span>'
                     f'{int(vd["category_word"]*100)}%</b>'
                     f'<span>品牌词 / 品类词 可见度（行业头部≈{int(vd["industry_top"]*100)}%）</span></div>')
    else:
        dual_card = f'<div class="stat"><b class="mono">{np_}</b><span>国内平台</span></div>'

    hero_stats = f"""
      <div class="statRow">
        <div class="stat"><b class="mono">{n_topic}</b><span>核心话题 · 三层结构</span></div>
        <div class="stat"><b class="mono">{n_scen}</b><span>可监测场景（{n_q} 问 × {np_} 平台）</span></div>
        {dual_card}
        {rank_card}
      </div>"""

    formula = (f'计算口径统一：<code>话题可见度 = 命中该话题的场景数 ÷ 该话题场景总数 × 100%</code>'
               f'　·　场景数 = 问题数 × 平台数　·　全部问题不含品牌名，确保数据可对标、可复测')
    if tc.get("VIS_DUAL"):
        vd = tc["VIS_DUAL"]
        formula += (f'<br><b style="color:#fff">为什么要拆成两个数：</b>'
                    f'品牌词可见度 {int(vd["brand_word"]*100)}% 说明「别人指名问你，你在」；'
                    f'品类词可见度 {int(vd["category_word"]*100)}% 才是「还不认识你的人能不能碰到你」。'
                    f'只报一个数会把前者当成竞争力，误判方向。')

    brand = tc["BRAND"]; sub = tc["BRAND_SUB"]
    body = f"""<div class="hero"><div class="wrap"><div class="heroGrid">
      <div style="padding-bottom:34px">
        <div class="eyebrow">微盟星启 GEO · 国内版</div>
        <h1>国内版 GEO<br><em>话题词方案</em></h1>
        <div class="sub">{_esc(brand)} ｜ {_esc(sub)}<br>
          话题词决定分母、竞品池与优化方向。本方案的 {n_topic} 个话题全部经过真实召回验证，非经验推测。</div>
      </div>
      <div style="padding-bottom:34px">{hero_stats}</div>
    </div></div>
    <div class="formulaBar"><div class="wrap">{formula}</div></div></div>
    {render_compliance(tc)}
    {render_risk(tc)}
    {render_map(tc)}
    {render_topics(tc)}
    {render_pool(tc)}
    {render_tests(tc)}
    {render_steps(tc)}
    {render_footer(tc)}"""
    return f"""<!DOCTYPE html><html lang="zh-CN"><head><meta charset="UTF-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>国内版 GEO 话题词方案 · {_esc(brand)}</title><style>{CSS}</style></head><body>{body}</body></html>"""
