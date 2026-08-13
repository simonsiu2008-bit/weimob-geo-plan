# 设计系统：风格按行业 / 客户自动匹配（决策规则）

> 目标：同一个共享引擎，根据行业与客户信息自动匹配视觉风格，无需改一行 slide 绘制代码。
> 实现方式：**逻辑色名映射**。引擎只用 11 个逻辑色名（BLUE/NAVY/CYAN/CLOUD/INK/GRAY/WHITE/GREEN/AMBER/RED/LIGHTBLUE），
> 每个案例的 `PALETTE` 提供一个「色名 → hex」映射表，slide 代码零修改。

---

## 一、逻辑色名（引擎唯一使用的 11 个名字）

| 逻辑名 | 语义 | 默认（微盟商务蓝）hex |
|---|---|---|
| `BLUE` | 主色 / 标题条 / 表格头 | `#2A5BEA` |
| `NAVY` | 封面 / 结尾底 / 深色卡 | `#0B1F4D` |
| `CYAN` | 强调 / 副标题 / 左条 | `#18C8FF` |
| `CLOUD` | 页面底色 | `#F5F7FC` |
| `INK` | 正文深色字 | `#16213A` |
| `GRAY` | 辅助说明字 | `#6E7689` |
| `WHITE` | 深色底上的字 | `#FFFFFF` |
| `GREEN` | 正向 / 合规 | `#059669` |
| `AMBER` | 警示 / 待优化 | `#D97706` |
| `RED` | 风险 / 红线 | `#DC2626` |
| `LIGHTBLUE` | 浅蓝底 / 卡片底色 | `#E8EEFD` |

引擎代码里**绝不出现具体 hex**，只出现上述逻辑名；`palette.py` 负责把逻辑名解析成 hex。

---

## 二、决策规则：按行业 + 客户信息匹配 Palette

`cases/<name>/config.py` 的 `PALETTE` 字段取值，建议按下表规则选择。规则是**方法论建议**，允许按客户品牌色覆盖。

| 行业 / 客户特征 | 建议 Palette | 视觉气质 | 设计理由 |
|---|---|---|---|
| 钟表 / 珠宝 / 奢侈零售 | `weimob_blue`（商务蓝） | 专业、克制、可信 | 高客单价决策靠信任感 |
| 美妆 / 护肤 | `weimob_blue` 或自定义粉调 | 干净、现代 | 强调成分安全与专业背书 |
| 金融 / 财富管理 / 家族办公室 | `weimob_blue`（商务蓝） | 权威、稳重 | 高净值客群信任优先 |
| **保健品 / 健康食品 / 日系健康** | `meiriki_teal`（日式健康青） | 舒适、自然、健康 | 「日式健康」调性贴合食品/保健认知 |
| 任何客户有明确品牌色 | 自定义 dict | 贴合品牌 | 用客户 VI 色做等价映射，保留品牌感 |

### 决策的三问（写方案前自问）

1. **客单价与信任强度**：越高越倾向沉稳商务色（蓝/深蓝），而非活泼高饱和。
2. **行业联想色**：健康/食品→青绿；科技→蓝青；美妆→柔和粉/肤调；金融→深蓝金。
3. **客户现有 VI**：若有明确品牌主色，用其替代 BLUE 位，其余色按同比例推演。

---

## 三、Palette 数据模型（palette.py 结构）

```python
# scripts/engine/palette.py
PALETTES = {
    "weimob_blue": {
        "BLUE": "#2A5BEA", "NAVY": "#0B1F4D", "CYAN": "#18C8FF",
        "CLOUD": "#F5F7FC", "INK": "#16213A", "GRAY": "#6E7689",
        "WHITE": "#FFFFFF", "GREEN": "#059669", "AMBER": "#D97706",
        "RED": "#DC2626", "LIGHTBLUE": "#E8EEFD",
        "font": "微軟雅黑",
    },
    "meiriki_teal": {
        "BLUE": "#16706A", "NAVY": "#0F4A46", "CYAN": "#2E7D5B",
        "CLOUD": "#FAFAF8", "INK": "#18201D", "GRAY": "#5C6661",
        "WHITE": "#FFFFFF", "GREEN": "#2E7D5B", "AMBER": "#B5793A",
        "RED": "#C0473A", "LIGHTBLUE": "#D9E6E3",
        "font": "Noto Sans CJK SC",
    },
}
```

> 日式健康青（meiriki_teal）对微盟蓝做了**等价映射**：BLUE→青绿、NAVY→深青、CYAN→青、CLOUD→暖白、INK→墨绿灰。
> 语义不变（主色/深底/强调/底色/正文），观感从「商务蓝」切换为「日式健康」。

---

## 四、新增 Palette 的方法

1. 在 `palette.py` 的 `PALETTES` 增加一个命名 palette（或案例里直接写自定义 dict 传 `PALETTE`）。
2. 提供完整 11 个逻辑名的 hex + `font`。
3. 在 `cases/<name>/config.py` 设 `PALETTE = "<名字或 dict>"`。
4. `build_deck.py` 自动解析：名字→查表，dict→直接用。
5. 跑 `python3 scripts/qa_check.py <case>`，确认 OOB 仍为 0、内容无污染。

> 原则：**风格是数据，不是代码**。加新风格 = 加一条数据，不改引擎。

---

## 五、底线约束

- 引擎代码内禁写具体 hex；一切颜色经 `palette.py` 的逻辑名解析。
- 新增 palette 不得破坏 20 页版面（OOB 仍须 0）。
- 封面深色底上的字必须为 WHITE（或 palette 定义的深底亮字），雾灰勿用深底。
- 字体名来自 palette 的 `font` 字段，不再硬编码「微軟雅黑」。
