---
name: weimob-geo-plan
description: "This skill should be used when producing a 微盟星启 GEO 优化方案 (GEO optimization proposal) for a brand/client — a fixed 20-slide PPT, a 话题词方案 HTML, plus a separate 销售话术/讲稿 (internal sales talk-track) and optional PDF. It runs on a shared engine + per-case isolated config architecture (data never leaks between cases), applies the locked framework: domestic 6 AI platforms (主) plus overseas 5 (輔), palette-based styling auto-matched by industry/client, AIVO four-dimension scoring, the L1/L2/L3 topic-keyword framework with 五问测试, the 可见度双指标 (brand-word vs category-word) discipline, 销售转化增强 elements (rank anchor / source citation board), and — for regulated categories such as overseas 保健品 selling into mainland China without 蓝帽子 — the 合规红线 that forbids all function/efficacy claims. Also enforces data-labeling discipline (估算 data labeled 診斷模型估算, forbidden markers 虛擬/⚠️/website/{{). Trigger when a user asks to redo a client proposal, produce a GEO plan, design GEO 话题词, or wants current AI-platform exposure, question-frequency, and competitor-tactics data embodied and highlighted in the proposal."
---

# 微盟星启 GEO 优化方案生成器

## Overview

生成面向客戶的「微盟星启 GEO 優化方案」交付套件。採用**共享引擎 + 每案例隔離配置**架構：
數據在案例之間不穿透，每一案例可單獨、有針對性呈現。

方案圍繞客戶最關切的三件事——**當前 AI 平臺曝光度、高頻問題被提及次數、對手在 AI 平臺的做法**——用數據體現並重點標注。

本 skill 整合三個版本優點：

| 整合 | 體現 |
|---|---|
| ① V1 專業 + 雙軌 | 客戶版（PPT/HTML）純淨 + 獨立銷售話術文件（見 `references/dual_track.md`） |
| ② V2 設計感 + 自動風格 | 配色/字體作為 palette 數據按行業/客戶自動匹配（見 `references/design_system.md`） |
| ③ V3 具體 + 銷售清晰 | 報價後三階段工作流（診斷→話題詞→報價後最終版，見 `references/workflow_stages.md`） |
| 硬性：數據隔離 | 每案例獨立目錄 + QA 自動跨 case 反查（見 §架構） |

基礎 20 頁框架之上內建四項增強能力：

| 能力 | 作用 | 參考文件 |
|---|---|---|
| ① 話題詞框架 | L1 品類主話題 / L2 場景話題 ×3 / L3 信任話題，配 20 題監測池與五問測試 | `references/topic_framework.md` |
| ② 合規紅線 | 受監管品類（尤其海外保健品進內地無藍帽子）禁止一切功效表述 | `references/compliance_guide.md` |
| ③ 銷售轉化增強 | 排名錨點 / 零價值曝光 / 信源引用次數榜 / 公式透明 | `references/sales_power.md` |
| ④ 可見度雙指標 | 品牌詞可見度 vs 品類詞可見度分開呈現，避免單一數字被誤讀 | `references/visibility_dual.md` |

所有估算數據嚴格標註「診斷模型估算」，禁用 虛擬 / ⚠️ / website / {{ 等標記。

---

## 架構：共享引擎 + 隔離 case（先讀）

```
weimob-geo-plan/
├── scripts/
│   ├── engine/               # 共享引擎（無任何案例數據，顏色只走邏輯色名）
│   │   ├── palette.py        # 配色數據模型 + 預設（weimob_blue / meiriki_teal / heritage_green）
│   │   ├── deck_engine.py    # build_deck(config, palette, out)  → 20 頁客戶版 PPT
│   │   ├── topic_engine.py   # build_topic_html(topic_config, out) → 話題詞方案 HTML
│   │   ├── talktrack.py      # build_talktrack(config, topic_config, out) → 銷售話術/講稿
│   │   └── qa_engine.py      # run_qa(case, ...) 含跨 case 自動反查
│   ├── build_deck.py         # CLI: python3 scripts/build_deck.py cases/<name>
│   ├── build_topic.py        # CLI: python3 scripts/build_topic.py cases/<name>
│   ├── build_talktrack.py    # CLI: python3 scripts/build_talktrack.py cases/<name>
│   ├── qa_check.py           # CLI: python3 scripts/qa_check.py <case>
├── cases/<name>/             # 每案例隔離目錄（數據隔離的核心）
│   ├── config.py             # PPT 數據：CONFIG + PALETTE + OUT_FILENAME
│   ├── topic_config.py       # 話題詞方案數據：TOPIC_CONFIG（可選）
│   ├── pollute_words.txt     # 本案例行業詞（供其他 case 反查，勿列通用詞）
│   └── output/               # 本案例全部交付物輸出於此，獨立隔離
└── references/               # 方法論 / 決策規則（不硬編碼進引擎）
```

**核心規則**：
- **數據隔離（硬性）**：一個 case 的交付物不得出現其他 case 的品牌/競品/行業詞。`qa_check` 自動掃描
  **所有其他 case** 的 `pollute_words.txt` 反查，命中即失敗。每案例有獨立 `output/`，輸出互不覆蓋。
- **風格即數據**：引擎只用 11 個邏輯色名，實際 hex 由 `config.py` 的 `PALETTE` 決定；加新風格不改引擎。
- **雙軌**：客戶版（A 軌）不含現場話術；銷售話術（B 軌）獨立成 `.md`。見 `dual_track.md`。

---

## When to Use

- 用戶要求為某品牌/客戶出一份 GEO 優化方案（「再做一次這個客戶」「出 GEO 方案」）。
- 用戶關注 AI 搜索平臺曝光度、問題提及頻次、競品在 AI 平臺的做法，要求數據在方案中體現。
- 用戶要求設計 GEO 話題詞 / 內容選題框架。
- 用戶為受監管品類（保健品、醫療器械、化妝品功效、金融）做內容規劃，需要合規邊界。
- 用戶要求把現有整改方案固化為可復用流程。

---

## Fixed Framework (不可改動)

- **平臺雙版本**：國內版 6（主）= 豆包 / DeepSeek / 阿里千問 / 百度AI / 元寶 / Kimi；海外版 5（輔）= ChatGPT / Perplexity / Claude / Gemini / Copilot。
- **配色（邏輯色名）**：引擎用 11 個邏輯色名（BLUE/NAVY/CYAN/CLOUD/INK/GRAY/WHITE/GREEN/AMBER/RED/LIGHTBLUE），
  具體 hex 由 `config.py` 的 `PALETTE` 決定；字體也來自 palette 的 `font` 字段。
- **AIVO 四維等權（各 25%）**：AI搜索可見性 / 基建完善度 / 競爭優勢 / 輿情健康度；評級 ≥90優 / ≥75良 / ≥60一般 / <60較差。
- **頁數恰好 20**，結構順序固定（見 `references/style_guide.md` 第二節）。
- **數據標註**：估算一律標「診斷模型估算」並註口徑；禁用 實測 / 虛擬 / ⚠️ / website / {{。

---

## 合規紅線（硬性規則 · 先於一切內容決策）

**在寫任何一句文案之前，先判定客戶品類是否受監管。**

判定觸發條件（命中任一即進入合規模式）：

- 保健食品 / 膳食補充劑 / 營養品，**且**品牌為海外品牌、在中國內地無「保健食品註冊證書或備案憑證（藍帽子）」；
- 醫療器械、特殊醫學用途配方食品；
- 化妝品宣稱功效（美白/防脫/抗皺等需功效備案）；
- 金融理財類收益承諾。

進入合規模式後的硬規則：

1. **禁止一切功效與效果表述**。完整禁用詞表與 SAMR《允許保健食品聲稱的保健功能目錄 非營養素補充劑（2023年版）》24 項合規功能清單見 `references/compliance_guide.md`。
2. **內容只能落在四條安全邊界內**：① 成分事實科普 ② 正品/原裝辨別 ③ 品質認證與渠道背書 ④ 選購方法與品牌背景。
3. **話題詞、問題池、KPI、講稿、話術五處同步校驗**——不能只改 PPT，話題詞方案 HTML 與話術裡同樣不得出現功效詞。
4. **在 PPT 第 18 頁與話題詞方案首屏顯式聲明紅線**，讓客戶看見我們主動守法（這本身是專業度背書）。
5. 允許出現功效詞的**唯一場景**是「明確標示為禁用/需改寫」的紅線清單本身。QA 時需人工確認每一處功效詞都處於否定語境。

> 敘事轉換公式：**功效敘事 → 硬事實敘事**。
> 例：「改善記憶」→「含 XX 成分，日本原裝進口，第三方檢測報告可查」。
> 完整改寫劇本見 `references/compliance_guide.md` 第五節。

---

## Workflow

### Step 0 — 建立/定位 case 目錄
```bash
mkdir -p cases/<name>/output
```
每案例一個目錄，不共用數據文件。已有案例直接使用其 `config.py` / `topic_config.py`。

### Step 1 — 收集客戶輸入 + 合規判定
向用戶索取：品牌名（含子品牌）、產品類型、官網（可選）、競品列表、聯絡卡片。
若用戶提供網址，先用 WebSearch / WebFetch 核實品牌事實（門店、產品線、母公司、資質），再錨定數據。
**同時完成合規品類判定**，結論寫入 `config.py` 的 `COMPLIANCE`。

### Step 2 — 決定風格（design_system.md 決策規則）
按行業 + 客戶信息，在 `cases/<name>/config.py` 設 `PALETTE`：
- 鐘錶/珠寶/奢侈零售、金融/財富 → `weimob_blue`（商務藍）
- 保健品/健康食品/日系健康 → `meiriki_teal`（日式健康青）
- 客戶有明確品牌色 → 自定義 palette dict

> 風格是數據不是代碼。詳見 `references/design_system.md`。

### Step 3 — 填充 `cases/<name>/config.py`（Stage 1 診斷數據 + Stage 3 PPT）
將診斷數據（AIVO、被引用率、曝光缺口、輿情、競品、KPI、話題詞、增強變量、PALETTE、OUT_FILENAME）填入 CONFIG。
**所有行業相關敘事都已抽入 CONFIG，換客戶時必須逐項替換，否則會出現跨 case 模板污染。**

#### 增強變量（可選；不填則 20 頁結構完全不變）
| CONFIG 變量 | 對應頁 | 說明 | 參考 |
|---|---|---|---|
| `VIS_DUAL` | 5 | `{"brand_word":0.88,"category_word":0.17,"industry_top":0.14}` | `visibility_dual.md` |
| `SOURCE_CITE` | 8 | `[("百家号",84),...]` 信源引用次數榜 | `sales_power.md` |
| `RANK_POOL` | 14 | `{"total":41,"rank":16}` 競品池規模與排名錨點 | `sales_power.md` |
| `COMPLIANCE` | 18 | `{"applicable":True,...}` 合規紅線聲明 | `compliance_guide.md` |

**硬性規則**：`ECO_MAP` 必須填真實競品名稱，禁止保留「頭部競品 A / 頭部競品 B」等佔位符。

### Step 4 — 話題詞方案（Stage 2；產出第 2 份交付物）
1. 讀 `references/topic_framework.md`，按 **L1 品類主話題 ×1 / L2 場景話題 ×3 / L3 信任話題 ×1** 建立話題地圖。
2. 每個話題過 **五問測試**，受監管品類追加 **TEST06 合規校驗**。
3. 做 **語義場校驗**：話題詞召回的競品必須與品牌同場。
4. 生成 **20 題監測池**（零品牌名提問 × 6 平臺）。
5. 填 `cases/<name>/topic_config.py`，運行：
```bash
python3 scripts/build_topic.py cases/<name>
```
產出 `<品牌>_国内版GEO话题词方案.html`。含：合規紅線 / 風險提示 / 話題地圖 / L1-L3 話題卡 / 監測池 / 五問測試 / 三階段節奏。

> 話題詞方案 HTML 的 `TOPICS` 與 PPT `TOPIC_WORDS`（第 18 頁）必須一致；Stage 3 另须与报价表一字不差。

### Step 5 — 生成客戶版 PPT（Stage 3）
```bash
python3 scripts/build_deck.py cases/<name>
```
產出 20 頁客戶版 PPT 到 `cases/<name>/output/`。**本引擎不讀 `script_v`（現場話術），客戶版天然純淨。**

### Step 6 — 生成銷售話術/講稿（雙軌 B 軌）
```bash
python3 scripts/build_talktrack.py cases/<name>
```
產出 `<品牌>_销售话术讲稿.md`：開場/報價/異議/收尾話術 + 20 頁逐頁講稿 + 可引用硬數據 + 合規紅線。
**內部資料，僅限銷售使用，不進入客戶版。**

### Step 7 — QA（交付前必做）
```bash
python3 scripts/qa_check.py <case>
```
檢查器自動覆蓋：頁數=20 / 禁忌標記=0 / 佔位符=0 / OOB=0 / `診斷模型估算`≥2 /
**跨 case 污染反查（掃描全部其他 case 的 pollute_words）/ 話題詞 HTML 反查 / 合規功效詞否定語境**。
退出碼 0 為通過。

人工另需複核：
- **雙指標一致**：`VIS_DUAL` 與第 18 頁 KPI 基線、話題詞 HTML 三處同數。
- **話題詞一致**：PPT `TOPIC_WORDS` ↔ 話題詞 HTML `TOPICS` ↔ **報價表** 一字不差（Stage 3）。
- **合規功效詞**：檢查器標出的命中逐一確認是否處於否定語境（紅線清單/改寫對照）。

### Step 8 — 對話內嵌展示（交付呈現方式，固定）
生成完交付物後，**必須**在對話中直接內嵌一個交互式雙 Tab 展示組件（HTML widget），讓用戶無需下載即可查看：

- **Tab 1 · PPT 可翻頁**：將 20 頁 PPT 內容重建為可翻頁的互動組件（上一步 / 下一步 / 頁數 / 底部 1–20 縮略圖跳轉），配色與該 case 的 `PALETTE` 一致。
- **Tab 2 · 話題詞方案**：將話題詞方案核心內容內嵌（風險提示 / L1→L3 話題漏斗 / 監測池話題卡 / 雙指標與排名錨點監測機制）。

> 此為**固定交付呈現方式**（V3 第三版定案），非可選。作用是讓客戶在對話裡就能審閱方案內容，再決定是否落成正式文件。

### Step 9 — 詢問是否生成正式 PPT 文件（硬性）
完成 Step 8 內嵌展示後，**必須**主動向用戶提問：「是否把這份方案生成為正式 PPT 文件（.pptx）？」

- 若用戶確認 → 運行 `python3 scripts/build_deck.py cases/<name>` 產出正式 PPT，並可選渲染 PDF 備份。
- 若用戶尚未確認 → 停留在對話內嵌展示，不擅自生成正式文件。

> 內嵌展示 ≠ 正式交付物；正式 .pptx 以用戶明確要求為準。此為最終交付前的最後一步。

### Step 10 — 渲染 PDF 備份（可選）
本環境 soffice 對中文輸入檔名會報錯。解法見 `references/style_guide.md` 第八節：
先 `cp` 成 `/tmp/ascii.pptx`，ASCII 路徑渲染到 `/tmp`，再 `cp` 回中文檔名。

---

## Resources

### scripts/engine/（共享引擎，不含案例數據）
- `palette.py` — 配色數據模型 + 預設（weimob_blue 微盟藍 / meiriki_teal 日式健康青）。邏輯色名→hex。
- `deck_engine.py` — 20 頁客戶版 PPT 渲染核心，`build_deck(config, palette, out)`。
- `topic_engine.py` — 話題詞方案 HTML 渲染核心，`build_topic_html(topic_config, out)`。
- `talktrack.py` — 銷售話術/講稿生成核心，`build_talktrack(config, topic_config, out)`。
- `qa_engine.py` — 交付前 QA，`run_qa(case, ...)` 含跨 case 自動反查。

### scripts/（CLI 薄封裝）
- `build_deck.py` / `build_topic.py` / `build_talktrack.py` — 傳 `cases/<name>`，動態載入該 case 配置。
- `qa_check.py` — `python3 scripts/qa_check.py <case>`。

### cases/
> ⚠️ **隱私：本 skill 發佈版不攜帶任何真實客戶案例**。`cases/` 僅含一個脫敏結構模板。
> 真實客戶數據獨立存儲（不隨 skill 分發），用家複製模板自行填寫。
- `_template/` — **脫敏結構模板**：含 config.py / topic_config.py / pollute_words.txt / README.md，
  結構完整但全為通用佔位（示例客戶），無任何真實客戶數據。**新客戶案例的起點**。
每個新案例都應有 `pollute_words.txt`，供跨 case 反查。

### references/
- `style_guide.md` — 架構與生成入口、雙軌交付物、20 頁結構、配色、AIVO 口徑、數據標註紀律、QA 清單、LibreOffice 坑。**執行前必讀**。
- `design_system.md` — **風格按行業/客戶自動匹配的決策規則** + palette 數據模型 + 新增風格方法。
- `dual_track.md` — **客戶版（A 軌）vs 銷售版（B 軌）分離規範** + 字段隔離 + QA 純淨性。
- `workflow_stages.md` — **報價前→報價→報價後三階段工作流** + 每階段動作與交付物 + 話題詞一致性。
- `weimob_geo_service.md` — 平臺雙版本、四大能力模塊、4 階段流水線、客戶三項核心關切、KPI 示例。
- `topic_framework.md` — L1/L2/L3 話題分層、五問測試 + TEST06、20 題監測池、可見度公式、語義場校驗、三階段節奏。**Step 4 必讀**。
- `compliance_guide.md` — SAMR 24 項合規功能、藍帽子資質、四條內容安全邊界、禁用詞表、功效→硬事實改寫劇本、合規檢查表。**受監管品類必讀**。
- `sales_power.md` — 六項成交焦慮要素、到頁面映射、話術增強片段、使用邊界。
- `visibility_dual.md` — 品牌詞/品類詞雙指標方案、呈現規範、口徑對照。

---

## Notes

- 本 skill 的引擎與方法論設計已覆蓋多個行業（商務藍 / 日式健康青 / 自然保育綠 等 palette，非監管與受監管品類）。**發佈版不含任何真實客戶案例**；真實案例以脫敏模板為基礎按需生成。
- **數據隔離是本 skill 最高優先硬性要求**：案例間不得穿透。換新客戶 = 新建 `cases/<name>/`，QA 自動跨 case 反查兜底。
- **模板污染是第二高風險**：換客戶時務必逐項替換 CONFIG 的 `ECO_MAP` / `SOURCE_TABLE` / `SENTIMENT_BULLETS` / `GAP_ROWS` / `CAPABILITY_MAP` / `ROADMAP_TABLE`，並在 Step 7 用其他 case 的 `pollute_words` 反查。
- **合規污染是第三高風險**：功效詞一旦出現在交付物，客戶可能承擔廣告法與食品安全法風險。受監管品類務必四處同查。
- 估算數據為模型模擬收錄，非真實 API 調用；如需「真實收錄證據」應另做一輪實檢。
- 20 頁是硬約束。新增能力一律以「CONFIG 條件插字」或「獨立 HTML 交付物」實現，不得新增頁面或形狀。
- 不對診斷結果做法律或商業決策背書；合規結論以客戶法務與監管機關口徑為準。
