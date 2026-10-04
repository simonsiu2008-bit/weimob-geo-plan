# 云端部署指南（Cloud Deployment）

weimob-geo-plan 技能 v2.4 · 自包含包，解压即可在任意 Linux/macOS 云主机/容器运行。
构建路径无网络依赖；**采集引擎（可选）需要网络 + Playwright**。

## 1. 环境要求

| 项 | 要求 |
|---|---|
| Python | ≥ 3.8（v3.11 验证通过） |
| 第三方依赖（构建） | 仅 `python-pptx` |
| 第三方依赖（采集，可选） | `playwright` + Chromium |
| 磁盘 | < 20 MB（不含采集截图） |
| 网络 | 构建不需要；采集引擎需要 |

```bash
pip install python-pptx
# —— 以下仅当需要「线上数据采集 + 证据报告」时安装 ——
pip install playwright && playwright install chromium
```

## 2. 快速开始（3 步）

```bash
unzip weimob-geo-plan-skill-v2.4-transfer.zip
cd weimob-geo-plan

# 冒烟自检：语言包一致性 + 构建示例 case + QA，预期两处 ===> ALL OK / ALL PASS
python3 scripts/check_lang_parity.py
python3 scripts/build_deck.py   cases/acme
python3 scripts/build_topic.py  cases/acme
python3 scripts/build_talktrack.py cases/acme
python3 scripts/qa_check.py acme
```

> **重要**：所有命令必须在技能根目录（本文件所在目录）执行——
> 脚本按相对路径 `scripts/engine/*` 与 `cases/<name>/*` 定位模块与数据。

## 3. 为新客户出方案（标准流程）

```bash
# 1) 复制模板
cp -r cases/_template cases/<new_case>
# 2) 编辑 cases/<new_case>/config.py + topic_config.py + pollute_words.txt
#    （全部诊断数据需标注「診斷模型估算」口径；品牌事实先经 WebSearch 核实）
#    ② 硬性：先向用户确认 VERSION（domestic 国内 / overseas 海外 / both 双版本）再动配置
# 3) 构建（自动按 config 的 VISUAL_STYLES 输出 classic/歸藏卡片双版本）
python3 scripts/build_deck.py       cases/<new_case>   # 20 页 PPT
python3 scripts/build_topic.py      cases/<new_case>   # 话题词 HTML
python3 scripts/build_talktrack.py  cases/<new_case>   # 销售话术 md
# 4) QA（语言包一致性 → 页数/禁忌/越界/估算/污染/合规 全检）
python3 scripts/check_lang_parity.py            # 必须 ===> ALL OK
python3 scripts/qa_check.py <new_case>          # 必须 ===> ALL PASS
```

产物输出在 `cases/<new_case>/output/`。

### 3.1 证据交付物（两套可选，互不依赖）

**① 痛点问答证据卡（零依赖 · 推荐先做）** —— 手填模拟问答还原
```bash
# 按 references/evidence_capture.md 填 cases/<new_case>/evidence_config.py（三卡 absent/negative/wrong）
python3 scripts/build_evidence_cards.py cases/<new_case>
# → cases/<new_case>/output/<品牌>_国内版GEO问答证据卡.html
```

**② AI 实测证据报告（需 Playwright + 各平台登录态）** —— 真实采集 + 截图
```bash
# ① 准备登录态：把导出的 storage_state JSON 放到 _private/sessions/<platform>.json
#    详见 scripts/collect/README.md（含 3 种导出方式）
python3 scripts/collect_run.py cases/<new_case> --dry-run   # ② 预检题目与登录态
python3 scripts/collect_run.py cases/<new_case>             # ③ 正式采集（按 VERSION 选平台组）
python3 scripts/build_evidence_report.py cases/<new_case>            # ④ 相对路径版
python3 scripts/build_evidence_report.py cases/<new_case> --embed    # ⑤ 单文件自包含版
```

采集产物落在 `cases/<new_case>/evidence/`（**含客户品牌截图，已在 .gitignore 隔离，永不入库**）：
`manifest.json`（status 为唯一真相源，未采到的如实标记，绝不伪造）/ `raw.json` / `shots/*.png`。
QA 会自动扫描 `manifest.json` 的 `items[].text` 做禁忌/污染/合规三项原文级审查。

> 线上实查的方法论（先实查后估算、A/B/C 证据分级、三卡字段）见 `references/evidence_capture.md`。

## 4. 目录结构

```
weimob-geo-plan/
├── SKILL.md              # 技能定义（Agent 工作流 Step 0-10）
├── README.md             # 技能概览
├── DEPLOY.md             # 本文件
├── references/           # 方法论文档（design_system / compliance / hk_style / collect 等）
├── scripts/
│   ├── build_deck.py / build_topic.py / build_talktrack.py
│   ├── build_evidence_cards.py   # 痛点问答证据卡（零依赖）
│   ├── build_evidence_report.py  # AI 实测证据报告（需采集）
│   ├── collect_run.py    # 线上采集 CLI
│   ├── qa_check.py / check_lang_parity.py
│   ├── collect/          # 采集引擎（platforms / session / collector）
│   └── engine/           # 共享引擎（deck/topic/talktrack/evidence/qa/lang_style/palette）
├── cases/                # 公开脱敏样例（acme 钟表零售）、骨架模板（_template）
│   ├── acme/             # clone 后可直接构建跑通完整流程
│   └── <case>/evidence/  # 采集证据（gitignore，不入库）
├── _private/sessions/    # AI 平台登录态（gitignore，不入库）
└── _private_cases/       # 私有案例数据（不含输出产物）
```

## 5. 关键配置开关（cases/<name>/config.py）

| 配置 | 取值 | 说明 |
|---|---|---|
| `PALETTE` | weimob_blue / meiriki_teal / heritage_green / **xiaomi_orange** | 主题色（含 11 逻辑色定义，可自定义 dict） |
| `LANG_STYLE` | mainland / hk_business | 内地简体 / 香港商業繁體 |
| `VISUAL_STYLES` | ["classic", "guizang_card"] | 并行输出多视觉版本，classic 保持原文件名 |
| **`VERSION`** | **domestic / overseas / both** | **投放版本（国内 6 / 海外 5 / 双版本）；省略 = both** |

三个开关互相独立：`LANG_STYLE` 管怎么说、`VISUAL_STYLES` 管怎么排版、`VERSION` 管说给谁听。

## 6. 云端运行注意事项

1. **产物已随包附带**：`cases/*/output/` 内含已交付的 pptx/html/md，可直接取用；
   重新构建会覆盖同名文件（内容确定性输出，同配置重建结果一致）。
2. **字体**：生成 pptx 无需云端安装字体（字体名写入文件，由打开端解析）。
   若云端需渲染预览（如 LibreOffice 转 PDF），请安装 CJK 字体：
   `apt-get install -y fonts-noto-cjk`。
3. **时区/编码**：脚本全部 UTF-8，无时区依赖。
4. **qa_check 跨 case 污染反查**会扫描全部 `cases/*/pollute_words.txt`，
   新增案例务必提供 pollute_words.txt（模板见 `cases/_template/`）。
5. **语言包改版**：改动 `engine/lang_style.py` 后必须先跑 `check_lang_parity.py`，
   确保所有语言包的键集与 `domestic/overseas/both` 版本分支齐全，否则渲染时 KeyError。
6. **隐私隔离**：`_private/`（登录态）与 `cases/*/evidence/`（客户截图）已在 `.gitignore`，
   云端也勿打包外发；采集证据仅本地留存。
7. 容器化最小镜像示例（含采集能力）：
   ```dockerfile
   FROM mcr.microsoft.com/playwright/python:v1.44.0-jammy
   RUN pip install --no-cache-dir python-pptx
   COPY weimob-geo-plan /opt/weimob-geo-plan
   WORKDIR /opt/weimob-geo-plan
   ```
   （仅构建场景可用更小的 `python:3.11-slim` + `pip install python-pptx`）

## 7. 版本记录

### v2.4（当前）· v2.3 引擎 + v4 方法论整合
- **整合两套并行实现**（v2.3 引擎基座 + v4 方法论文档），两边能力皆保留：
  - **并入 v4 方法论文档**：`references/version_scope.md`（版本范围对照表）、
    `references/evidence_capture.md`（线上实查 + A/B/C 证据分级 + 三卡）、
    `references/plain_language.md`（术语→白话 + 图表优先）
  - **两套证据实现并存**：`build_evidence_cards.py`（痛点问答卡，零依赖）+
    `build_evidence_report.py`（AI 实测报告，需采集）；`evidence_engine.py` 同时导出
    `build_evidence_cards()` 与 `build_evidence_html()`
  - **引擎基座保持 v2.3**（lang_style / VISUAL_STYLES / VERSION / collect 采集引擎）
  - **`VERSION`（引擎开关）↔ `VERSION_SCOPE`（`evidence_config.py` 展示字段）** 口径对齐
  - SKILL.md 新增 Step 1.7 線上數據實查、Step 1.8 白話表達基線、Step 4.5 兩套證據交付物
  - 回归：私有案例 PPT 文本级零回归；acme 四份交付物 QA ALL PASS

### v2.3
- **Phase 1 线上数据采集引擎**：`scripts/collect/` + `collect_run.py`
  - 11 个平台适配器（国内 6：豆包/DeepSeek/千问/百度AI/元宝/Kimi；海外 5：ChatGPT/Perplexity/Claude/Gemini/Copilot）
  - 登录态复用（`_private/sessions/`）、回答稳定性采样、如实降级（status 为唯一真相源）
- **Phase 2 证据报告**：`build_evidence_report.py` + `engine/evidence_engine.py`
  - 品牌缺席证据（竞品出现 / 我方未出现双栏截图）、负面引用证据、数据缺口如实披露
  - 相对路径版 + `--embed` 单文件自包含版（base64 内联）
  - QA 新增采集原文级审查（扫 manifest.json 的 text 字段）
- **Phase 3 版本分支**：三维度开关（LANG_STYLE / VISUAL_STYLES / **VERSION**）
  - `VERSION` = domestic / overseas / both（默认 both = 历史叙事）
  - 引擎按版本分支 P1 封面 / P3 平台 / P5 视角 / P6 注释 / P7 / P10 / P14 / P18 的平台与 KPI 口径
  - 海外版 KPI：AI Citation Rate / Brand Word Visibility / Category Word Visibility
  - 新增 `check_lang_parity.py`（语言包键集一致性硬门）
  - SKILL.md 新增 **Step 1.5 版本确认**（硬性主动询问国内/海外/双版本）

### v2.2
- 新增 palette：xiaomi_orange（品牌橙 #FF6900 + 炭黑灰阶，消费科技/智能硬件配色）
- 语言包：SENT<60 分级文案（舆情「較差·語義簇風險需對沖」）+ P10 注释 config 覆盖
  （AIVO_INFRA_NOTE / AIVO_COMP_NOTE / AIVO_SENT_NOTE）
- 沿用：hk_business 港式语言包、classic + guizang_card 双视觉并行、QA 多文件扫描
