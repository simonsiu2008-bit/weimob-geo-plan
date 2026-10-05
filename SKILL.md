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
| ⑤ 版本範圍 | 國內版 / 海外版 / 雙版的平台池、DIAG 口徑、監測池差異 | `references/version_scope.md` |
| ⑥ 線上實查 + 痛點證據 | 先實查後估算、A/B/C 證據分級、三類痛點問答還原卡 | `references/evidence_capture.md` |
| ⑦ 白話表達 | 術語→白話對照、圖表優先、每頁「重點+下一步」 | `references/plain_language.md` |

所有估算數據嚴格標註「診斷模型估算」，禁用 虛擬 / ⚠️ / website / {{ 等標記。

---

## 架構：共享引擎 + 隔離 case（先讀）

```
weimob-geo-plan/
├── scripts/
│   ├── engine/               # 共享引擎（無任何案例數據，顏色只走邏輯色名）
│   │   ├── palette.py        # 配色數據模型 + 預設（weimob_blue / meiriki_teal / heritage_green）
│   │   ├── lang_style.py     # 語言包（mainland / hk_business）+ 視覺風格註冊表（classic / guizang_card）
│   │   ├── deck_engine.py    # build_deck(config, palette, out)  → 20 頁客戶版 PPT
│   │   ├── topic_engine.py   # build_topic_html(topic_config, out) → 話題詞方案 HTML
│   │   ├── talktrack.py      # build_talktrack(config, topic_config, out) → 銷售話術/講稿
│   │   └── qa_engine.py      # run_qa(case, ...) 含跨 case 自動反查（掃描 output/ 全部交付物）
│   ├── build_deck.py         # CLI: python3 scripts/build_deck.py cases/<name> [--style guizang_card]
│   ├── build_topic.py        # CLI: python3 scripts/build_topic.py cases/<name> [--style ...]
│   ├── build_talktrack.py    # CLI: python3 scripts/build_talktrack.py cases/<name> [--lang ...]
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
- **語言與視覺是兩個獨立開關**：`LANG_STYLE` 管用語（mainland/hk_business），`VISUAL_STYLES` 管
  視覺版本（classic/guizang_card），可任意組合、並行輸出。見下方「語言風格與視覺版本」。

---

## 語言風格 / 視覺版本 / 投放版本（三個正交維度）

每個案例交付物由三個互不衝突的維度決定，均為 config 數據、不改引擎：

**① 語言風格 `LANG_STYLE`**（寫在 `config.py` 的 CONFIG / `topic_config.py` 的 TOPIC_CONFIG）

| 值 | 語域 | 用途 |
|---|---|---|
| `"mainland"`（默認） | 簡體書面語，逐字與歷史版本一致 | 內地客戶 |
| `"hk_business"` | 繁體港式商業書面語；內部話術允許粵語口語 | 香港客戶 / 繁體交付 |

用語決策規則見 `references/hk_style.md`。品牌專名（微盟星启）與 QA 關鍵字（診斷模型估算）兩包逐字一致。

**② 視覺版本 `VISUAL_STYLES`**（寫在 `config.py` / `topic_config.py`，列表，並行輸出）

| 值 | 視覺 | 輸出文件名 |
|---|---|---|
| `"classic"`（默認） | 原版視覺（藍色豎條頁眉 / 經典封面） | `OUT_FILENAME` **原名不變**（原版本保留） |
| `"guizang_card"` | 歸藏卡片風（編號 chip 頁眉 / 卡片柵格封面與結尾 / 粗描邊 / 暗底玻璃卡片 HTML） | `OUT_FILENAME` 去擴展名 + `_歸藏卡片版` + 原擴展名 |

**③ 投放版本 `VERSION`**（**Step 1.5 硬性詢問後**寫入；省略 = `"both"`）

| 值 | 含義 | 引擎行為 |
|---|---|---|
| `"domestic"` | 國內版 | 只講國內 6 平台（豆包/DeepSeek/千問/百度AI/元寶/Kimi） |
| `"overseas"` | 海外版 | 只講海外 5 平台（ChatGPT/Perplexity/Claude/Gemini/Copilot）；KPI 走 AI Citation Rate / Brand Word Visibility / Category Word Visibility 英文口徑 |
| `"both"`（默認） | 雙版本 | 國內 6（主）+ 海外 5（輔），歷史默認敘事 |

`VERSION` 只改「平台敘述與 KPI 口徑」，**20 頁結構與 QA 約束完全不變**。
話題詞 HTML（題材即國內版交付物）的 `VERSION` 只影響平台行，標題恆為「國內版 / 海外版 GEO 話題詞方案」。

> **`VERSION`（引擎開關）與 `VERSION_SCOPE`（展示字段）的關係**：
> `VERSION` 是唯一引擎真源（`"domestic"/"overseas"/"both"`），決定平台池與 KPI 口徑；
> `VERSION_SCOPE` 是寫在 `evidence_config.py` 的**中文展示字段**（`"国内版"/"海外版"/"双版"`），
> 僅用於證據卡頁眉 badge，**必須由 `VERSION` 映射而來、不得手工獨立維護**：
> `domestic→国内版`、`overseas→海外版`、`both→双版`。差異對照見 `references/version_scope.md`。

```python
# cases/<name>/config.py
CONFIG = dict(
    ...
    LANG_STYLE    = "hk_business",                    # 省略 = "mainland"
    VISUAL_STYLES = ["classic", "guizang_card"],      # 省略 = ["classic"]
    VERSION       = "overseas",                       # 省略 = "both"
)
```

- `python3 scripts/build_deck.py cases/<name>` 按 `VISUAL_STYLES` **循環輸出全部版本**；
  `--style guizang_card` 只構建指定版本。
- 三個維度各自獨立：可「港式繁體 + 歸藏卡片 + 海外版」任意組合。
- 語言包鍵集一致性由 `python3 scripts/check_lang_parity.py` 硬門守住（新增語言包必跑）。
- 兩個語言包的佔位符一一對應；QA 對 output/ 目錄的**每一份** pptx/html 逐份執行同一套檢查。
- 新增視覺版本 = 在 `lang_style.py` 的 `PPT_VISUAL_STYLES` 註冊 + 引擎按 `header_mode / cover_mode /
  end_mode / outline_boost` 分支渲染，不改 case 配置結構。

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
並按 `references/version_scope.md` 的對照表，確認平台池 / 語言 / DIAG 口徑 / 監測池 / 敘事重點
與下一步確認的 `VERSION` 一致。

### Step 1.5 — 確認投放版本（硬性 · 不可跳過）
> **必須在動任何配置之前，主動向用戶提出以下問題**（用 AskUserQuestion），不得自行假設：
>
> **「這份方案要投國內版、海外版，還是國內 + 海外版？」**
>
> | 選項 | `VERSION` | 影響 |
> |---|---|---|
> | 國內版 | `"domestic"` | 只講國內 6 平台（豆包/DeepSeek/千問/百度AI/元寶/Kimi） |
> | 海外版 | `"overseas"` | 只講海外 5 平台（ChatGPT/Perplexity/Claude/Gemini/Copilot）；KPI 用 AI Citation Rate / Brand Word Visibility / Category Word Visibility 英文口徑 |
> | 雙版本 | `"both"` | 國內 6（主）+ 海外 5（輔）——歷史默認敘事 |
>
> 拿到答案後，在 `cases/<name>/config.py` **與** `topic_config.py` 同時寫入：
> ```python
> VERSION = "domestic"   # 或 "overseas" / "both"
> ```
> 並確保該鍵已進入 `CONFIG` / `TOPIC_CONFIG` dict（`VERSION=VERSION`）。
>
> **為什麼硬性**：採集引擎（`scripts/collect_run.py`）、話題詞問題池、KPI 口徑、平台影響力表
> 全都依賴這個開關；選錯會導致整份方案講錯市場，且後期落地時平台清單全錯。
> 若方案需要**同時**產出國內版與海外版兩份獨立交付物，則跑兩次（建兩個 case，`_cn` / `_ovs` 後綴），
> 各自設 `VERSION`。
>
> **採集平台聯動**：`VERSION="domestic"` → 採集引擎只跑國內 6 平台；
> `"overseas"` → 只跑海外 5；`"both"` → 兩組都跑（見 Step 4.5）。

### Step 1.7 — 線上數據實查（硬性前置；解決「報告太簡單」的根因）
診斷數據**先實查、後估算**，不得直接用模擬數填充。兩種實查手段並用：

1. **方法論實查（必做 · 零依賴）**：按 `references/evidence_capture.md` 實查清單，用
   WebSearch / WebFetch 收集公開證據——官網可抓性、權威平臺收錄（百科/新聞/百家號/知乎）、
   社媒聲量、負面信息、競品內容佈局。
2. **採集引擎實測（可選 · 需 Playwright + 登錄態）**：以無頭瀏覽器在各 AI 平臺模擬提問並截圖，
   產出 `cases/<name>/evidence/manifest.json`（見 Step 4.5）。無瀏覽器/登錄態時**如實降級**，
   不得偽造採集數據。
3. 證據分三級標註：**A 線上實查**（帶日期＋來源）、**B 客戶提供**、**C 診斷模型估算**（只補實查不到的缺口）。
4. 實查結果直接餵入 PPT 第 4/5/7/12/14/15 頁數據卡——A/B 級優先，**報告厚度由證據量決定，不是由模板決定**。
5. 把三類痛點場景（對手出現本品牌缺席 / 本品牌負面提及 / 信息錯誤過時）整理為
   `cases/<name>/evidence_config.py`，供 Step 4.5 生成痛點問答證據卡。

### Step 1.8 — 白話表達基線（填 CONFIG 前必讀）
按 `references/plain_language.md` 定基線：結論先行（每頁一句話重點）、一頁一重點、圖表優先；
術語首次出現須配白話（如「品類詞可見度（客戶沒指名、只問品類時 AI 會不會推薦你——**這才是新客來源**）」）；
每個數字旁須有參照對象（行業基準 / 競品 / 上期）。規範適用於 PPT 全部 20 頁、話題詞 HTML、證據卡與講稿。

### Step 2 — 決定風格（design_system.md 決策規則）
按行業 + 客戶信息，在 `cases/<name>/config.py` 設 `PALETTE`：
- 鐘錶/珠寶/奢侈零售、金融/財富 → `weimob_blue`（商務藍）
- 保健品/健康食品/日系健康 → `meiriki_teal`（日式健康青）
- 客戶有明確品牌色 → 自定義 palette dict

**同時決定語言風格**：香港客戶 / 繁體交付 → `CONFIG["LANG_STYLE"] = "hk_business"`（詳見 `references/hk_style.md`）；
並按客戶需要設 `VISUAL_STYLES`（如 `["classic", "guizang_card"]` 兩版本並行）。

> 風格是數據不是代碼。詳見 `references/design_system.md`。
> 三個開關各管一維，互不衝突：`LANG_STYLE`（怎麼說：简体/港式繁体）、
> `VISUAL_STYLES`（怎麼排版：經典/歸藏卡片）、`VERSION`（說給誰聽：國內/海外/雙版本）。

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

### Step 4.5 — 生成第 3/4 份交付物（證據）
本 skill 提供**兩套互不依賴**的證據實現，可按客戶情況擇一或都出：

**① 痛點問答證據卡（零依賴 · 強烈建議）** — 手填模擬問答還原
```bash
python3 scripts/build_evidence_cards.py cases/<name>
```
- 讀 `cases/<name>/evidence_config.py` 的 `EVIDENCE_CONFIG`（Step 1.7 整理的三類卡）。
- 產出 `<品牌>_<版本>GEO問答證據卡.html`：對話氣泡還原「客戶問 → AI 答」，高亮競品與本品牌，
  每卡附白話痛點與建議下一步。
- 標註紀律：頁眉聲明「示意問答還原」，每卡帶 A/B/C 證據級別。規範見 `references/evidence_capture.md`。

**② AI 實測證據報告（需 Playwright + 各平台登錄態）** — 真實採集 + 截圖
```bash
python3 scripts/collect_run.py cases/<name> --dry-run   # ① 預檢（題目 + 登錄態）
python3 scripts/collect_run.py cases/<name>             # ② 正式採集（按 VERSION 選平台組）
python3 scripts/build_evidence_report.py cases/<name>            # ③ 相對路徑版
python3 scripts/build_evidence_report.py cases/<name> --embed    # ④ 單文件自包含版（base64 內聯）
```
- 讀 `cases/<name>/evidence/manifest.json`（`status` 為唯一真相源，未採到的如實標記，**絕不偽造**）。
- 產出 `<品牌>_AI实测证据报告.html`：品牌缺席（雙欄對比截圖）/ 負面引用 / 數據缺口如實披露。
- 登錄態配置見 `scripts/collect/README.md`；采集產物 `evidence/` 已 gitignore，**永不入庫**。

### Step 5 — 生成客戶版 PPT（Stage 3）
```bash
python3 scripts/build_deck.py cases/<name>
```
按 `VISUAL_STYLES` 循環輸出全部視覺版本到 `cases/<name>/output/`（classic 保持原文件名，
guizang_card 加 `_歸藏卡片版` 後綴；`--style` 可只構建單版本）。
**本引擎不讀 `script_v`（現場話術），客戶版天然純淨。**

### Step 6 — 生成銷售話術/講稿（雙軌 B 軌）
```bash
python3 scripts/build_talktrack.py cases/<name>
```
語言默認跟隨 `CONFIG["LANG_STYLE"]`（`--lang` 可臨時覆蓋）。
產出 `<品牌>_销售话术讲稿.md`：開場/報價/異議/收尾話術 + 20 頁逐頁講稿 + 可引用硬數據 + 合規紅線。
**內部資料，僅限銷售使用，不進入客戶版。**

### Step 7 — QA（交付前必做）
```bash
python3 scripts/check_lang_parity.py        # ① 語言包鍵集一致性（新增語言包/改版必跑）
python3 scripts/qa_check.py <case>          # ② 交付物 QA（逐份掃描 output/ 全部 pptx + html + md）
```
QA 第 8 項為**術語白話化**：`engine/jargon.py` 掃 L1 內地黑話（基線／口徑／閉環／矩陣／對齊／錨點…），
交付物命中數**必須為 0**；L2 框架詞（AIVO／召回／收錄…）保留專業感，僅統計。新客戶專有術語可入 `JARGON_ALLOW` 白名單。
**第 ① 道門**：三個註冊表（`TOPIC_LANG` / `DECK_LANG` / `TT_LANG`）任意兩個語言包的
鍵集、版本分支鍵（domestic/overseas/both）集合必須完全一致——不一致即渲染時 KeyError，必須先修。

**第 ② 道門**：檢查器自動掃描 output/ 目錄**全部** pptx 與 html 交付物（含 `_歸藏卡片版`）逐份檢查：
頁數=20 / 禁忌標記=0 / 佔位符=0 / OOB=0 / `診斷模型估算`≥2 /
**跨 case 污染反查（掃描全部其他 case 的 pollute_words）/ 話題詞 HTML 反查 / 合規功效詞否定語境**。
若 `cases/<name>/evidence/manifest.json` 存在，**額外補一層「採集原文級」審查**：
對採集到的 AI 回答原文（`items[].text`）執行同樣的禁忌標記 / 跨 case 污染 / 合規功效詞三項檢查——
彌補「截圖內文字無法被 HTML 文本掃描覆蓋」的盲區。退出碼 0 為通過。

人工另需複核：
- **版本口徑一致**：`VERSION` 對應的平台清單在封面 / P3 / P5 / P18 四處口徑統一
  （國內版只現國內 6、海外版只現海外 5、雙版本雙列），KPI 標題與腳註同版本。
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
- `lang_style.py` — 語言包（TOPIC_LANG / DECK_LANG / TT_LANG：mainland + hk_business，佔位符一一對應）
  與視覺風格註冊表（PPT_VISUAL_STYLES：classic / guizang_card）+ `resolve_styles` / `versioned_filename`。
- `deck_engine.py` — 20 頁客戶版 PPT 渲染核心，`build_deck(config, palette, out)`；按 config 的
  `LANG_STYLE` / `VISUAL_STYLE` 切換語言與視覺分支（chip 頁眉 / 卡片柵格封面結尾 / 描邊增強）。
- `topic_engine.py` — 話題詞方案 HTML 渲染核心，`build_topic_html(topic_config)`；內置 classic 與
  歸藏卡片風（暗底玻璃卡片）兩套 CSS。
- `talktrack.py` — 銷售話術/講稿生成核心，`build_talktrack(config, topic_config, out, lang_style)`。
- `qa_engine.py` — 交付前 QA，`run_qa(case, ...)` 含跨 case 自動反查；掃描 output/ 全部 pptx/html/md。
- `jargon.py` — 術語白話化字典與掃描器（L1 黑話必換 / L2 框架詞保留 / `JARGON_ALLOW` 白名單）；供 QA 硬性檢查。
- `evidence_engine.py` — 證據渲染核心，兩個出入口：
  `build_evidence_cards(cfg)`（痛點問答卡，讀 `evidence_config.py`）/
  `build_evidence_html(ec)`（AI 實測報告，讀 `evidence/manifest.json` + 截圖）。

### scripts/（CLI 薄封裝）
- `build_deck.py` / `build_topic.py` / `build_talktrack.py` — 傳 `cases/<name>`，動態載入該 case 配置。
- `build_evidence_cards.py` — 痛點問答證據卡 CLI（讀 `evidence_config.py`，零依賴）。
- `build_evidence_report.py` — AI 實測證據報告 CLI（讀 `evidence/manifest.json`，需採集；`--embed` 單文件版）。
- `collect_run.py` — 線上採集 CLI（Playwright，按 `VERSION` 選國內 6 / 海外 5 / 雙組）。
- `check_lang_parity.py` — 語言包鍵集一致性硬門（改 `lang_style.py` 後必跑）。
- `qa_check.py` — `python3 scripts/qa_check.py <case>`。

### cases/
> ⚠️ **隱私：本 skill 發佈版不攜帶任何真實客戶案例**。`cases/` 僅含脫敏樣例與結構模板。
> 真實客戶數據獨立存儲於 `_private_cases/`（已 gitignore，不隨 skill 分發）。
- `acme/` — **公開脫敏樣例**（鐘錶零售）：config.py / topic_config.py / evidence_config.py /
  pollute_words.txt / README.md 齊全，clone 後可直接構建跑通完整流程。
- `_template/` — **脫敏結構模板**：同上一套文件但為純佔位（示例客戶），**新客戶案例的起點**。
每個新案例都應有 `pollute_words.txt`，供跨 case 反查。

### references/
- `style_guide.md` — 架構與生成入口、雙軌交付物、20 頁結構、配色、AIVO 口徑、數據標註紀律、QA 清單、LibreOffice 坑。**執行前必讀**。
- `hk_style.md` — **香港商業語言風格規範**（hk_business）：繁體規則、詞彙對照（運營→營運 / 頭部→龍頭 / 門店→門市）、語域分級、稱謂與數字單位。**香港客戶必讀**。
- `design_system.md` — **風格按行業/客戶自動匹配的決策規則** + palette 數據模型 + 新增風格方法。
- `dual_track.md` — **客戶版（A 軌）vs 銷售版（B 軌）分離規範** + 字段隔離 + QA 純淨性。
- `workflow_stages.md` — **報價前→報價→報價後三階段工作流** + 每階段動作與交付物 + 話題詞一致性。
- `weimob_geo_service.md` — 平臺雙版本、四大能力模塊、4 階段流水線、客戶三項核心關切、KPI 示例。
- `topic_framework.md` — L1/L2/L3 話題分層、五問測試 + TEST06、20 題監測池、可見度公式、語義場校驗、三階段節奏。**Step 4 必讀**。
- `version_scope.md` — 國內版/海外版/雙版的平台池、語言、DIAG 口徑、監測池、敘事重點對照表 + config 落地規則。**Step 1 必讀**。
- `evidence_capture.md` — 線上實查清單、A/B/C 證據分級、三類痛點問答卡、`evidence_config.py` 字段。**Step 1.7 / 4.5 必讀**。
- `plain_language.md` — 術語→白話對照表、圖表優先規範、每頁「重點+下一步」模板。**填 CONFIG 前必讀**。
- `compliance_guide.md` — SAMR 24 項合規功能、藍帽子資質、四條內容安全邊界、禁用詞表、功效→硬事實改寫劇本、合規檢查表。**受監管品類必讀**。
- `sales_power.md` — 六項成交焦慮要素、到頁面映射、話術增強片段、使用邊界。
- `visibility_dual.md` — 品牌詞/品類詞雙指標方案、呈現規範、口徑對照。

---

## Notes

- 本 skill 的引擎與方法論設計已覆蓋多個行業（商務藍 / 日式健康青 / 自然保育綠 等 palette，非監管與受監管品類）。**發佈版不含任何真實客戶案例**；真實案例以脫敏模板為基礎按需生成。
- **數據隔離是本 skill 最高優先硬性要求**：案例間不得穿透。換新客戶 = 新建 `cases/<name>/`，QA 自動跨 case 反查兜底。
- **模板污染是第二高風險**：換客戶時務必逐項替換 CONFIG 的 `ECO_MAP` / `SOURCE_TABLE` / `SENTIMENT_BULLETS` / `GAP_ROWS` / `CAPABILITY_MAP` / `ROADMAP_TABLE`，並在 Step 7 用其他 case 的 `pollute_words` 反查。
- **合規污染是第三高風險**：功效詞一旦出現在交付物，客戶可能承擔廣告法與食品安全法風險。受監管品類務必四處同查。
- **報告太簡單的根因是「沒做線上數據收集」**：必須先執行 Step 1.7 線上實查（WebSearch 實查 + 可選採集引擎），
  A/B 級證據優先，報告厚度由證據量決定。估算數據為模型模擬收錄，非真實 API 調用；C 級只補實查不到的缺口。
- 20 頁是硬約束。新增能力一律以「CONFIG 條件插字」或「獨立 HTML 交付物」實現，不得新增頁面或形狀。
- 不對診斷結果做法律或商業決策背書；合規結論以客戶法務與監管機關口徑為準。
