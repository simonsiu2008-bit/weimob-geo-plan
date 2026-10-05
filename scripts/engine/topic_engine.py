#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
共享引擎：话题词方案 HTML 渲染器（双视觉版本）
==============================================
将 build_topic_proposal.py 的渲染逻辑抽取为参数化函数，数据全部来自传入的 TOPIC_CONFIG dict。

build_topic_html(topic_config, output_path)  →  生成「国内版 GEO 话题词方案」HTML。

数据隔离：本引擎不持有任何案例数据；所有品牌/竞品/合规/话题数据均来自 cases/<name>/topic_config.py。
每个案例的话题词方案独立生成、独立输出到自己的 output/ 目录。

TOPIC_CONFIG 新增可选键（engine/lang_style.py 定义）：
- LANG_STYLE    "mainland"（默认，内地简体口吻，与历史版本一致）| "hk_business"（香港商业语言风格）
- VISUAL_STYLE  "classic"（默认原版视觉）| "guizang_card"（歸藏卡片風：暗底玻璃卡片）
两版本并行输出由 build_topic.py 按 VISUAL_STYLES 循环完成；classic 文件名保持不变（原版本保留）。

固定框架（不可改动）：
- L1/L2/L3 话题框架 + 20 题监测池 + 五问测试 + 合规校验 + 落地节奏
- 受监管品类（COMPLIANCE.applicable=True）才显示合规横幅与禁用词提示
- 依赖：无第三方库（纯标准库）。
"""
import html

from lang_style import get_topic_lang


# =====================================================================
# CSS：classic（原版，逐字保留）与 guizang_card（歸藏卡片風，暗底玻璃卡片）
# =====================================================================
CSS_CLASSIC = """
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

CSS_GUIZANG = """
:root{--acc1:#7C5CFF;--acc2:#22D3EE;--bg:#0A0E1A;--panel:rgba(255,255,255,.045);--panel2:rgba(255,255,255,.07);
--line:rgba(255,255,255,.10);--ink:#E9EEF9;--gray:#8B95AF;--white:#fff;--green:#34D399;--amber:#FBBF24;--red:#F87171;
--blue:#8B7CFF;--navy:#0F1526;--cyan:#22D3EE;--cloud:#0A0E1A;--navy2:#151C31;}
*{box-sizing:border-box;margin:0;padding:0}
body{font-family:-apple-system,BlinkMacSystemFont,"PingFang SC","Microsoft YaHei","Noto Sans TC","Segoe UI",sans-serif;
color:var(--ink);background:var(--bg);line-height:1.7;-webkit-font-smoothing:antialiased}
.wrap{max-width:1080px;margin:0 auto;padding:0 28px}.mono{font-variant-numeric:tabular-nums;font-feature-settings:"tnum"}
.hero{background:
 radial-gradient(1100px 560px at 82% -12%,rgba(124,92,255,.38),transparent 62%),
 radial-gradient(900px 520px at 8% 112%,rgba(34,211,238,.20),transparent 55%),
 var(--bg);color:#fff;padding:64px 0 0;position:relative;overflow:hidden}
.hero::before{content:"";position:absolute;left:0;top:0;bottom:0;width:6px;
 background:linear-gradient(180deg,var(--acc1),var(--acc2))}
.eyebrow{display:inline-block;font-size:12px;letter-spacing:.2em;color:#CBD4F5;font-weight:700;
 border:1px solid rgba(203,212,245,.35);border-radius:999px;padding:6px 14px;background:rgba(255,255,255,.05)}
.hero h1{font-size:46px;line-height:1.16;font-weight:900;margin:18px 0 0;letter-spacing:-.01em;
 background:linear-gradient(92deg,#FFFFFF 30%,#B9C4FF 70%,#7EE9FF);-webkit-background-clip:text;background-clip:text;color:transparent}
.hero h1 em{font-style:normal;background:linear-gradient(92deg,var(--acc1),var(--acc2));
 -webkit-background-clip:text;background-clip:text;color:transparent}
.hero .sub{font-size:15.5px;color:#A9B4D6;margin-top:14px;max-width:660px}
.heroGrid{display:grid;grid-template-columns:1.35fr 1fr;gap:38px;align-items:end;padding-bottom:0}
.statRow{display:grid;grid-template-columns:repeat(2,1fr);gap:12px;margin-bottom:6px}
.stat{background:var(--panel);border:1px solid var(--line);border-radius:18px;padding:16px 18px;
 backdrop-filter:blur(10px);box-shadow:0 10px 30px rgba(0,0,0,.35)}
.stat b{display:block;font-size:30px;font-weight:900;color:#fff;line-height:1.1}
.stat span{font-size:11.5px;color:#8FA0C9;display:block;margin-top:4px}
.stat.accent{border:1px solid rgba(124,92,255,.55);box-shadow:0 0 0 1px rgba(124,92,255,.25),0 12px 34px rgba(124,92,255,.18)}
.stat.accent b{background:linear-gradient(92deg,var(--acc1),var(--acc2));-webkit-background-clip:text;background-clip:text;color:transparent}
.formulaBar{margin-top:34px;background:rgba(255,255,255,.04);border-top:1px solid var(--line);padding:14px 0;font-size:12.5px;color:#A9B4D6;backdrop-filter:blur(8px)}
.formulaBar code{background:rgba(124,92,255,.18);color:#C9B8FF;padding:3px 9px;border-radius:6px;font-size:12px;border:1px solid rgba(124,92,255,.35)}
section{padding:56px 0}.secHead{display:flex;align-items:baseline;gap:14px;margin-bottom:8px}
.secNum{font-size:12px;font-weight:900;letter-spacing:.16em;
 background:linear-gradient(92deg,var(--acc1),var(--acc2));-webkit-background-clip:text;background-clip:text;color:transparent}
.secHead h2{font-size:27px;font-weight:900;letter-spacing:-.01em;color:#fff}
.secDesc{font-size:14.5px;color:var(--gray);max-width:760px;margin-bottom:30px}
.compliance{background:var(--panel);border:1px solid rgba(251,191,36,.35);border-top:4px solid var(--amber);border-radius:18px;padding:26px 30px;margin:34px 0 0;backdrop-filter:blur(10px)}
.compliance .cTag{display:inline-block;background:linear-gradient(92deg,#F59E0B,#FBBF24);color:#1A1206;font-size:11px;font-weight:800;padding:4px 12px;border-radius:999px;letter-spacing:.05em}
.compliance h2{font-size:20px;font-weight:900;margin:12px 0 14px;line-height:1.4;color:#fff}
.compliance .cBody p{font-size:14px;color:var(--ink);margin-bottom:12px}
.compliance .cKey{background:rgba(251,191,36,.08);border:1px solid rgba(251,191,36,.3);border-radius:12px;padding:14px 16px;margin-bottom:12px}
.compliance .cKey strong{color:var(--amber)}
.compliance .cKey span{display:inline-block;background:rgba(251,191,36,.14);color:#FCD34D;font-size:12px;font-weight:700;padding:4px 10px;border-radius:999px;margin:6px 6px 0 0;white-space:nowrap}
.compliance .cWin{margin-bottom:0;background:rgba(52,211,153,.08);border:1px solid rgba(52,211,153,.3);border-radius:12px;padding:14px 16px}
.compliance .cWin strong{color:var(--green)}
.compliance .forbid{display:inline-block;background:rgba(248,113,113,.12);color:var(--red);border:1px solid rgba(248,113,113,.3);font-size:12px;font-weight:700;padding:3px 10px;border-radius:999px;margin:4px 4px 0 0;white-space:nowrap}
.alert{background:var(--panel);border:1px solid rgba(248,113,113,.35);border-left:5px solid var(--red);border-radius:18px;padding:26px 30px;backdrop-filter:blur(10px)}
.alert .tag{display:inline-block;background:linear-gradient(92deg,#EF4444,#F87171);color:#fff;font-size:11px;font-weight:800;padding:4px 12px;border-radius:999px;letter-spacing:.05em}
.alert h3{font-size:21px;font-weight:900;margin:14px 0 10px;color:#fff}
.quote{background:rgba(248,113,113,.08);border:1px solid rgba(248,113,113,.22);border-radius:12px;padding:15px 18px;font-size:14px;margin:16px 0;color:#FCA5A5}
.quote small{display:block;color:var(--gray);font-size:11.5px;margin-top:7px;font-style:normal}
.guard{background:rgba(251,191,36,.07);border:1px solid rgba(251,191,36,.3);border-left:4px solid var(--amber);border-radius:10px;padding:12px 15px;font-size:13px;margin-top:16px;color:#FCD34D}
.guard b{color:var(--amber)}
.map{display:grid;grid-template-columns:repeat(3,1fr);gap:14px}
.mapCol{background:var(--panel);border-radius:18px;border:1px solid var(--line);overflow:hidden;backdrop-filter:blur(10px)}
.mapCol .h{padding:13px 18px;color:#fff;font-size:13px;font-weight:800;letter-spacing:.04em}
.mapCol .b{padding:16px 18px}.mapCol .role{font-size:12px;color:var(--gray);margin-bottom:12px}
.mapItem{font-size:14px;font-weight:600;padding:8px 0;border-bottom:1px dashed var(--line);display:flex;justify-content:space-between;gap:8px;color:#DDE4F5}
.mapItem:last-child{border:0}.mapItem s{text-decoration:none;font-size:11px;color:var(--gray);font-weight:500;white-space:nowrap}
.topic{background:var(--panel);border-radius:20px;border:1px solid var(--line);margin-bottom:22px;overflow:hidden;display:grid;grid-template-columns:64px 1fr;backdrop-filter:blur(10px);box-shadow:0 14px 40px rgba(0,0,0,.30)}
.topic .rail{color:#fff;display:flex;flex-direction:column;align-items:center;justify-content:flex-start;padding:20px 0;gap:6px;background:rgba(255,255,255,.03)}
.topic .rail .n{font-size:24px;font-weight:900;line-height:1}
.topic .rail .lv{font-size:10px;font-weight:700;letter-spacing:.08em;writing-mode:vertical-rl;margin-top:8px;opacity:.85}
.topic .body{padding:22px 26px}.tHead{display:flex;justify-content:space-between;align-items:flex-start;gap:16px;flex-wrap:wrap}
.tHead h3{font-size:20px;font-weight:900;color:#fff}.tHead .intent{font-size:12.5px;color:var(--gray);margin-top:3px}
.badges{display:flex;gap:6px;flex-wrap:wrap}
.badge{font-size:11px;font-weight:700;padding:3px 10px;border-radius:999px;white-space:nowrap;border:1px solid transparent}
.b-hi{background:rgba(248,113,113,.12);color:var(--red);border-color:rgba(248,113,113,.3)}
.b-mid{background:rgba(251,191,36,.12);color:var(--amber);border-color:rgba(251,191,36,.3)}
.b-ok{background:rgba(52,211,153,.12);color:var(--green);border-color:rgba(52,211,153,.3)}
.b-info{background:rgba(124,92,255,.14);color:#B4A6FF;border-color:rgba(124,92,255,.35)}
.b-comp{background:rgba(251,146,60,.12);color:#FDBA74;border-color:rgba(251,146,60,.3)}
.tGrid{display:grid;grid-template-columns:1fr 1fr;gap:0 26px;margin-top:18px}
.fld{padding:11px 0;border-top:1px solid var(--line)}
.fld .k{font-size:11px;font-weight:800;color:#9F8FFF;letter-spacing:.06em;margin-bottom:4px}
.fld .v{font-size:13.5px;color:#DDE4F5}.fld .v em{font-style:normal;background:rgba(251,191,36,.14);color:#FCD34D;padding:1px 5px;border-radius:5px}
.fld .v .safe{font-style:normal;background:rgba(52,211,153,.14);color:var(--green);padding:1px 5px;border-radius:5px;font-weight:600}
.rivals{display:flex;flex-wrap:wrap;gap:5px;margin-top:5px}
.rival{font-size:12px;background:rgba(255,255,255,.04);border:1px solid var(--line);padding:3px 10px;border-radius:999px;color:#C4CCE0}
.rival.you{background:linear-gradient(92deg,var(--acc1),var(--acc2));color:#fff;border-color:transparent;font-weight:800}
.script{margin-top:16px;background:rgba(124,92,255,.10);border:1px solid rgba(124,92,255,.35);color:#fff;border-radius:14px;padding:15px 18px}
.script .k{font-size:11px;font-weight:800;color:#C9B8FF;letter-spacing:.06em;margin-bottom:6px}
.script .v{font-size:13.5px;color:#DDE4F5}.script .v b{color:#fff}
.compNote{margin-top:14px;background:rgba(251,191,36,.07);border:1px solid rgba(251,191,36,.3);border-radius:10px;padding:11px 14px;font-size:12.5px;color:#FCD34D}
.compNote b{color:var(--amber)}
table{width:100%;border-collapse:collapse;font-size:13.5px;background:var(--panel);border-radius:14px;overflow:hidden;border:1px solid var(--line)}
thead tr{background:linear-gradient(92deg,rgba(124,92,255,.30),rgba(34,211,238,.18));color:#fff}th{padding:11px 13px;text-align:left;font-weight:800;font-size:12.5px}
td{padding:10px 13px;border-bottom:1px solid var(--line);vertical-align:top;color:#DDE4F5}
tbody tr:nth-child(even){background:rgba(255,255,255,.03)}tbody tr:last-child td{border-bottom:0}
.qnum{color:var(--gray);font-variant-numeric:tabular-nums}
.edge{font-size:11.5px;color:var(--gray);line-height:1.5}.edge .ok{color:var(--green);font-weight:800}.edge .no{color:var(--red);font-weight:800}
.tests{display:grid;grid-template-columns:repeat(3,1fr);gap:12px}
.test{background:var(--panel);border:1px solid var(--line);border-radius:16px;padding:16px 15px;border-top:3px solid var(--acc1);backdrop-filter:blur(8px)}
.test .n{font-size:11px;font-weight:900;color:#9F8FFF;letter-spacing:.1em}
.test h4{font-size:14.5px;font-weight:900;margin:6px 0 7px;color:#fff}.test p{font-size:12px;color:var(--gray);line-height:1.6}
.steps{display:grid;grid-template-columns:repeat(3,1fr);gap:14px}
.step{background:var(--panel);border:1px solid var(--line);border-radius:18px;padding:20px 22px;position:relative;backdrop-filter:blur(8px)}
.step .p{font-size:11.5px;font-weight:800;color:#fff;display:inline-block;padding:4px 12px;border-radius:999px;letter-spacing:.05em}
.step h4{font-size:16px;font-weight:900;margin:11px 0 8px;color:#fff}
.step ul{list-style:none;font-size:13px;color:#DDE4F5}.step li{padding:4px 0 4px 15px;position:relative;line-height:1.6}
.step li::before{content:"";position:absolute;left:0;top:12px;width:6px;height:6px;border-radius:50%;background:linear-gradient(135deg,var(--acc1),var(--acc2))}
.step .kpi{margin-top:12px;padding-top:11px;border-top:1px dashed var(--line);font-size:12px;color:var(--gray)}.step .kpi b{color:#9F8FFF}
footer{background:#070B14;border-top:1px solid var(--line);color:#8FA0C9;padding:34px 0;font-size:12.5px;margin-top:20px}
footer strong{color:#fff;display:block;font-size:14px;margin-bottom:6px}
.note{font-size:12px;color:var(--gray);margin-top:14px;line-height:1.7}
@media(max-width:900px){.heroGrid,.map,.tests,.steps,.tGrid{grid-template-columns:1fr}.hero h1{font-size:32px}.tests{gap:10px}}
"""

RAIL_COLOR = {"blue": "var(--blue)", "cyan": "#18C8FF", "green": "var(--green)"}
RAIL_TXT   = {"blue": "#fff", "cyan": "#0B1F4D", "green": "#fff"}


def _esc(s):
    return html.escape(str(s))


def _css(mode):
    return CSS_GUIZANG if mode == "guizang_card" else CSS_CLASSIC


# ---- 各 section 渲染（tc 为 TOPIC_CONFIG，L 为语言包）----

def render_compliance(tc, L):
    comp = tc.get("COMPLIANCE") or {}
    if not comp.get("applicable"):
        return ""
    # 每个禁用词自身带否定标记：清单过长时，句首的「絕不出現」会超出 QA 的 400 字元
    # 否定语境窗口，导致后段词被误判为「非否定语境」（2026-10 修，v4 移植）。
    forbidden = "".join(f'<span class="forbid">禁用 {_esc(w)}</span>' for w in comp["forbidden"])
    allowed = "".join(f'<span>{_esc(a)}</span>' for a in comp["allowed"])
    return f"""
<section style="padding:0"><div class="wrap"><div class="compliance">
  <span class="cTag">{_esc(L['comp_tag'])}</span>
  <h2>{_esc(L['comp_title'])}</h2>
  <div class="cBody">
    <p>{_esc(comp['note'])}</p>
    <p class="cKey"><b>{_esc(L['comp_only'])}</b>{allowed}
      <br><b>{_esc(L['comp_never'])}</b>{forbidden}</p>
    <p class="cWin"><b>{_esc(L['comp_win'])}</b>{_esc(comp['win'])}</p>
  </div>
</div></div></section>"""


def render_risk(tc, L):
    r = tc.get("RISK")
    if not r:
        return ""
    analysis = "".join(f"<p style='font-size:14.5px'>{_esc(a)}</p>" for a in r["analysis"])
    return f"""
<section><div class="wrap">
  <div class="secHead"><span class="secNum">01</span><h2>{_esc(L['risk_title'])}</h2></div>
  <div class="secDesc">{_esc(L['risk_desc'])}</div>
  <div class="alert">
    <span class="tag">{_esc(r['tag'])}</span>
    <h3>{_esc(r['title'])}</h3>
    <p style="font-size:14.5px">{_esc(L['risk_quote_intro'])}</p>
    <div class="quote">「{_esc(r['quote'])}」<small>{_esc(r['quote_src'])}</small></div>
    {analysis}
    <div class="guard"><b>{_esc(L['risk_guard'])}</b>{_esc(r['guard'])}</div>
  </div>
</div></section>"""


def render_map(tc, L):
    cols = ""
    for m in tc["TOPIC_MAP"]:
        items = "".join(f'<div class="mapItem">{_esc(n)} <s>{_esc(t)}</s></div>' for n, t in m["items"])
        color = m["color"]
        txtcolor = "#0B1F4D" if color == "cyan" else "#fff"
        cols += f"""<div class="mapCol"><div class="h" style="background:var(--{color});color:{txtcolor}">{_esc(m['lv'])}</div>
      <div class="b"><div class="role">{_esc(m['role'])}</div>{items}</div></div>"""
    return f"""
<section style="padding-top:0"><div class="wrap">
  <div class="secHead"><span class="secNum">02</span><h2>{_esc(L['map_title'])}</h2></div>
  <div class="secDesc">{_esc(L['map_desc'])}</div>
  <div class="map">{cols}</div>
</div></section>"""


def render_topics(tc, L):
    cards = ""
    for t in tc["TOPICS"]:
        badges = "".join(f'<span class="badge {b[1]}">{_esc(b[0])}</span>' for b in t["badges"])
        rivals = "".join(f'<span class="rival">{_esc(r)}</span>' for r in t["rivals"])
        if t.get("you_in"):
            rivals += f'<span class="rival you">{_esc(L["you_in"])}</span>'
        fields = ""
        for k, v in t["fields"]:
            fields += f'<div class="fld"><div class="k">{_esc(k)}</div><div class="v">{v}</div></div>'
        comp = f'<div class="compNote"><b>{_esc(L["comp_note_label"])}</b>{_esc(t["comp_note"])}</div>' if t.get("comp_note") else ""
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
        <div class="script"><div class="k">{_esc(L['script_label'])}</div><div class="v">{_esc(t['script_v'])}</div></div>
      </div>
    </div>"""
    return f"""
<section style="padding-top:0"><div class="wrap">
  <div class="secHead"><span class="secNum">03</span><h2>{_esc(L['topics_title'])}</h2></div>
  <div class="secDesc">{_esc(L['topics_desc'])}</div>
  {cards}
</div></section>"""


def render_pool(tc, L):
    rows = ""
    for no, topic, q, intent, edge, flag in tc["QUESTION_POOL"]:
        cls = "ok" if flag == "ok" else "no"
        label = L["flag_ok"] if flag == "ok" else L["flag_no"]
        rows += (f'<tr><td class="qnum">{_esc(no)}</td><td>{_esc(topic)}</td><td>{_esc(q)}</td>'
                 f'<td>{_esc(intent)}</td><td class="edge"><span class="{cls}">{_esc(label)}</span> {_esc(edge)}</td></tr>')
    platforms = " / ".join(tc["PLATFORMS"])
    n = len(tc["QUESTION_POOL"]); np_ = len(tc["PLATFORMS"])
    th = L["pool_th"]
    pool_note = L["pool_note"]
    return f"""
<section style="padding-top:0"><div class="wrap">
  <div class="secHead"><span class="secNum">04</span><h2>{_esc(L['pool_title'].format(n=n))}</h2></div>
  <div class="secDesc">{L['pool_desc'].format(n=n, np=np_, ns=n * np_)}</div>
  <table><thead><tr><th style="width:4%">{_esc(th[0])}</th><th style="width:18%">{_esc(th[1])}</th><th style="width:34%">{_esc(th[2])}</th><th style="width:10%">{_esc(th[3])}</th><th style="width:34%">{_esc(th[4])}</th></tr></thead>
  <tbody>{rows}</tbody></table>
  <div class="note">{pool_note.format(np=np_, pf=platforms)}</div>
</div></section>"""


def render_tests(tc, L):
    tests = L["tests"]
    cells = ""
    for i, (h, p) in enumerate(tests, 1):
        n = f"TEST {i:02d}"
        accent = 'style="border-top-color:var(--red)"' if n == "TEST 03" else ('style="border-top-color:var(--amber)"' if n == "TEST 06" else "")
        ncolor = 'style="color:var(--red)"' if n == "TEST 03" else ('style="color:var(--amber)"' if n == "TEST 06" else "")
        cells += f'<div class="test" {accent}><div class="n" {ncolor}>{n}</div><h4>{_esc(h)}</h4><p>{_esc(p)}</p></div>'
    return f"""
<section style="padding-top:0"><div class="wrap">
  <div class="secHead"><span class="secNum">05</span><h2>{_esc(L['tests_title'])}</h2></div>
  <div class="secDesc">{_esc(L['tests_desc'])}</div>
  <div class="tests">{cells}</div>
</div></section>"""


def render_steps(tc, L):
    cells = ""
    for s in tc["STEPS"]:
        color = s["color"]
        txtcolor = "#0B1F4D" if color == "cyan" else "#fff"
        items = "".join(f"<li>{_esc(i)}</li>" for i in s["items"])
        cells += f"""<div class="step"><span class="p" style="background:var(--{color});color:{txtcolor}">{_esc(s['phase'])}</span>
      <h4>{_esc(s['title'])}</h4><ul>{items}</ul>
      <div class="kpi">{_esc(L['kpi_label'])}<b>{_esc(s['kpi'])}</b></div></div>"""
    return f"""
<section style="padding-top:0"><div class="wrap">
  <div class="secHead"><span class="secNum">06</span><h2>{_esc(L['steps_title'])}</h2></div>
  <div class="secDesc">{_esc(L['steps_desc'])}</div>
  <div class="steps">{cells}</div>
</div></section>"""


def render_footer(tc, L):
    cite_line = ""
    if tc.get("SOURCE_CITE"):
        chips = "　".join(f'<b style="color:var(--cyan)">{_esc(n)}</b> {c} 次'
                          for n, c in tc["SOURCE_CITE"][:5])
        cite_line = (f'<b>{_esc(L["cite_head"].format(k=len(tc["SOURCE_CITE"][:5])))}</b>{chips}'
                     f'{_esc(L["cite_tail"])}<br>')
    comp_line = ""
    comp = tc.get("COMPLIANCE") or {}
    if comp.get("applicable"):
        comp_line = (f'<span style="color:var(--amber)"><b style="color:var(--amber)">{_esc(L["comp_decl_head"])}</b>'
                     f'{_esc(L["comp_decl"].format(industry=comp["industry"]))}</span>')
    platforms = " / ".join(tc["PLATFORMS"])
    footer_line1 = L["footer_line1"]
    return f"""
<footer><div class="wrap">
  <strong>{_esc(L['footer_team'])}</strong>
  {_esc(footer_line1.format(np=len(tc['PLATFORMS']), pf=platforms))}<br>
  {cite_line}{_esc(L['footer_data'])}<br>
  {comp_line}
</div></footer>"""


def build_topic_html(tc):
    """tc: TOPIC_CONFIG dict（来自 cases/<name>/topic_config.py）"""
    mode = tc.get("VISUAL_STYLE", "classic")
    L = get_topic_lang(tc.get("LANG_STYLE", "mainland"))
    VER = tc.get("VERSION") or "both"

    def DV(key, default=""):
        """版本分支文案：L[key] 为 {domestic/overseas/both: 文案} 时按 VER 取值。"""
        v = L.get(key)
        if isinstance(v, dict):
            return v.get(VER, v.get("both", default))
        return v if v is not None else default

    n_topic = len(tc["TOPICS"])
    n_q = len(tc["QUESTION_POOL"])
    np_ = len(tc["PLATFORMS"])
    n_scen = n_q * np_

    rank_card = ""
    if tc.get("RANK_POOL"):
        rank_card = (f'<div class="stat accent"><b class="mono">#{tc["RANK_POOL"]["rank"]}'
                     f'<span style="font-size:17px;font-weight:700">/{tc["RANK_POOL"]["total"]}</span></b>'
                     f'<span>{_esc(L["stat_rank"].format(t=tc["RANK_POOL"]["total"]))}</span></div>')
    else:
        rank_card = f'<div class="stat"><b class="mono">{n_q}</b><span>{_esc(L["stat_pool"])}</span></div>'

    dual_card = ""
    if tc.get("VIS_DUAL"):
        vd = tc["VIS_DUAL"]
        dual_card = (f'<div class="stat accent"><b class="mono">'
                     f'{int(vd["brand_word"]*100)}%<span style="font-size:17px;font-weight:700;color:#8FA3D0"> / </span>'
                     f'{int(vd["category_word"]*100)}%</b>'
                     f'<span>{_esc(L["stat_dual"].format(i=int(vd["industry_top"]*100)))}</span></div>')
    else:
        dual_card = f'<div class="stat"><b class="mono">{np_}</b><span>{_esc(DV("ver_stat_platforms"))}</span></div>'

    hero_stats = f"""
      <div class="statRow">
        <div class="stat"><b class="mono">{n_topic}</b><span>{_esc(L["stat_topics"])}</span></div>
        <div class="stat"><b class="mono">{n_scen}</b><span>{_esc(L["stat_scen"].format(q=n_q, p=np_))}</span></div>
        {dual_card}
        {rank_card}
      </div>"""

    formula = L["formula"]
    if tc.get("VIS_DUAL"):
        vd = tc["VIS_DUAL"]
        formula += '<br>' + L["dual_why"].format(
            b=int(vd["brand_word"]*100), c=int(vd["category_word"]*100))

    brand = tc["BRAND"]; sub = tc["BRAND_SUB"]
    eyebrow = DV("ver_hero_eyebrow") + (f' · {L["style_badge"]}' if mode == "guizang_card" else "")
    body = f"""<div class="hero"><div class="wrap"><div class="heroGrid">
      <div style="padding-bottom:34px">
        <div class="eyebrow">{_esc(eyebrow)}</div>
        <h1>{_esc(DV('ver_hero_h1'))}<br><em>{_esc(L['hero_h1b'])}</em></h1>
        <div class="sub">{_esc(brand)} ｜ {_esc(sub)}<br>
          {_esc(L['hero_sub'].format(n=n_topic))}</div>
      </div>
      <div style="padding-bottom:34px">{hero_stats}</div>
    </div></div>
    <div class="formulaBar"><div class="wrap">{formula}</div></div></div>
    {render_compliance(tc, L)}
    {render_risk(tc, L)}
    {render_map(tc, L)}
    {render_topics(tc, L)}
    {render_pool(tc, L)}
    {render_tests(tc, L)}
    {render_steps(tc, L)}
    {render_footer(tc, L)}"""
    return f"""<!DOCTYPE html><html lang="{L['lang_attr']}"><head><meta charset="UTF-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>{_esc(DV('ver_doc_title').format(brand=brand))}</title><style>{_css(mode)}</style></head><body>{body}</body></html>"""
