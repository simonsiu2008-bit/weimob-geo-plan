# 线上数据采集 · 登录态配置指南

采集引擎用**无头浏览器**访问各 AI 平台网页版，模拟真实用户提问并截图。
多数平台（豆包 / DeepSeek / 千问 / Kimi / 百度AI / 元宝）**必须登录**才能提问，
因此需要你先提供登录态文件。

> **隐私**：登录态文件保存在 `_private/sessions/`，该目录已被 `.gitignore` 排除，永不入库、永不随包分发。
> 登录态等同账号凭证，请勿分享该文件。

---

## 一、为什么需要登录态（实测结论）

| 平台 | 游客模式实测结果 |
|---|---|
| 豆包 | 输入框存在但**不可点击**（拦截） |
| DeepSeek | 打开即**强制登录**，无游客入口 |
| Kimi | 可输入可发送，随后**弹登录遮罩**，拿不到回答 |
| 通义千问 | 可发送，但返回**推荐视频列表**而非 AI 回答（降级输出） |
| 百度AI / 元宝 | 需登录 |
| ChatGPT / Claude / Gemini | 需登录 |
| Perplexity / Copilot | 游客可问，但常遇验证码；有登录态更稳 |

**结论**：不提供登录态 → 采集覆盖率为 0。引擎会如实标记 `status: login_required`，不会伪造数据。

---

## 二、导出登录态（3 种方式，任选）

登录态文件需为 Playwright 的 `storage_state` 格式：

```json
{ "cookies": [ {"name":"...","value":"...","domain":".doubao.com","path":"/","expires":1790000000} ],
  "origins": [] }
```

### 方式 A · Playwright 交互式登录（推荐，最可靠）

```bash
cd /root/.codebuddy/skills/weimob-geo-plan
python3 - <<'EOF'
from playwright.sync_api import sync_playwright
import os
os.makedirs("_private/sessions", exist_ok=True)
TARGETS = {"doubao":"https://www.doubao.com/chat/", "deepseek":"https://chat.deepseek.com/"}
with sync_playwright() as p:
    b = p.chromium.launch(headless=False, args=["--no-sandbox"])
    ctx = b.new_context(locale="zh-CN", viewport={"width":1440,"height":900})
    for key, url in TARGETS.items():
        pg = ctx.new_page(); pg.goto(url, wait_until="domcontentloaded")
        input(f"请在浏览器里完成【{key}】登录，完成后回到终端按 Enter…")
        ctx.storage_state(path=f"_private/sessions/{key}.json")
        print(f"已保存 _private/sessions/{key}.json")
        pg.close()
    b.close()
EOF
```

### 方式 B · 从本地 Chrome/Edge 复制 Cookie

1. 本地浏览器登录目标平台
2. 用扩展（如 **Cookie-Editor**）导出为 JSON
3. 转换为 Playwright 格式后存入 `_private/sessions/doubao.json`

### 方式 C · 通用登录态

若多个平台共用同一账号体系（如腾讯系），可存为 `_private/sessions/_default.json` 作为兜底。

---

## 三、采集命令

```bash
# 预检：看问题清单 + 各平台可达性（不提问、不耗额度）
python3 scripts/collect_run.py cases/<name> --dry-run

# 正式采集（国内 6 平台）
python3 scripts/collect_run.py cases/<name>

# 只跑指定平台 / 前 3 题（调试）
python3 scripts/collect_run.py cases/<name> --platforms doubao,kimi --limit 3

# 海外版 5 平台
python3 scripts/collect_run.py cases/<name> --version overseas

# 人工核对选择器（平台改版时用，打开可见浏览器）
python3 scripts/collect_run.py cases/<name> --probe doubao
```

产物目录：

```
cases/<name>/evidence/
├── manifest.json     # 结构化结果（供证据报告消费）
├── raw.json          # 同上（原始备份）
└── shots/            # 回答区域截图 <平台>_<题号>.png
```

---

## 四、采集状态说明

| status | 含义 | 处理 |
|---|---|---|
| `ok` | 成功取到回答 | 正常入报告 |
| `login_required` | 需登录态但未提供/已失效 | 按本文导出登录态后重跑 |
| `selector_not_found` | 平台改版导致选择器失效 | 用 `--probe <平台>` 核对并更新 `platforms.py` |
| `timeout` | 等待回答超时 | 增大 `platforms.py` 中该平台 `wait` 值后重跑 |
| `failed` | 其他异常 | 看 `error` 字段 |

---

## 五、反爬与风控注意事项

- **串行采集**：平台之间不并发，且在题目之间插入 8–15 秒随机延迟。
- **建议单轮不超过 20 题**，避免触发风控。
- **不要频繁重跑**：同一账号短时间大量提问有被限流风险。建议一天不超过 2 轮。
- **截图即证据**：失败画面同样会截图留存，作为「该平台未产出有效回答」的证据，不做美化。
- **真实性优先**：引擎在任何情况下都不会用估算数据填补采集失败项。

---

## 六、平台改版维护

平台前端改版会使选择器失效，表现为 `selector_not_found`。修复步骤：

1. `python3 scripts/collect_run.py cases/<name> --probe <平台>` 打开可见浏览器
2. 用 DevTools 找到新的输入框 / 回复容器选择器
3. 补进 `scripts/collect/platforms.py` 中该平台的 `input` / `reply` **候选列表首位**（保留旧候选作兜底）
4. 重跑验证

> 选择器写成候选列表就是为了这个——平台改版只需加一行，不必改采集逻辑。
