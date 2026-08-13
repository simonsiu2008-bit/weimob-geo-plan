# 案例模板（_template）

这是 skill 自带的**脱敏结构模板**，用于生成新客户案例。**不含任何真实客户数据**。

> ⚠️ 隐私说明：本 skill 发布时不携带任何真实客户案例。真实案例数据应独立存储，不随 skill 分发。

## 用法（生成新客户案例）

```bash
# 1. 复制模板为你的客户案例（用客户代号）
cp -r cases/_template cases/<客户代号>   # 如 cases/acme

# 2. 编辑 cases/<客户代号>/config.py
#    - 替换所有「示例/占位」内容为该客户真实诊断数据
#    - 按 design_system.md 设 PALETTE
#    - 受监管品类按 compliance_guide.md 填 COMPLIANCE

# 3.（可选）编辑 cases/<客户代号>/topic_config.py
#    - 生成话题词方案

# 4.（必做）编辑 cases/<客户代号>/pollute_words.txt
#    - 填入本客户品牌/竞品/行业词（供跨案例反查）

# 5. 生成交付物
python3 scripts/build_deck.py cases/<客户代号>
python3 scripts/build_topic.py cases/<客户代号>
python3 scripts/build_talktrack.py cases/<客户代号>

# 6. QA
python3 scripts/qa_check.py <客户代号>
```

## 字段说明

- `config.py` → 20 页 PPT 数据（字段结构见 references/style_guide.md 第二节）
- `topic_config.py` → 话题词方案 HTML（可选）
- `pollute_words.txt` → 本案例品牌/竞品/行业词，供其他案例反查隔离

## 注意

- 每个案例一个独立目录，数据不跨案例穿透
- 换新客户 = 新建 `cases/<客户代号>/`，不要复用旧案例目录
- 所有行业叙事（ECO_MAP / SOURCE_TABLE / GAP_ROWS 等）必须逐项替换，防止模板污染
