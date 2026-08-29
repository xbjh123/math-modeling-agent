# Paper Figures — Unified Style & Figure-Type Methodology

> 目的：让数学建模论文的所有配图风格统一、达到国奖/期刊级观感。
> 本文件是**方法论**，不含任何具体赛题（2025A/Bollard 等）的残留——只讲"怎么画"。
> 配套：`templates/tikz/`（几何示意图/流程图模板）、`scripts/fig_helpers.py`（绘图工具）。

---

## 1. 配图形态分类（先分清类型，再选工具）

论文配图分四类，每类用不同工具、不同风格。

| 类型 | 典型内容 | 推荐工具 | 风格要点 |
|---|---|---|---|
| **数据图** | 结果对比、灵敏度曲线、收敛、甘特图 | matplotlib + SciencePlots | 细线、无笨重框、期刊字号 |
| **几何/机理示意图** | 判据定义、空间几何关系、归约定理证明 | TikZ（矢量） | 虚线=隐藏边、灰实体、红=关键轮廓 |
| **算法流程图** | 求解算法、迭代逻辑 | TikZ（标准符号） | 椭圆起止、圆角框过程、菱形判断、平行四边形IO |
| **概念示意/布局图** | 对象空间分布、问题关系、调度方案 | matplotlib 3D 或 TikZ | 色块分区、图例清晰、直接标注 |

**关键原则**：
- 几何精度 > 美观（数值/坐标必须来自求解引擎真实数据，不臆造）。
- 概念示意类图必须标注"非真实比例"。
- 配色全走统一 PALETTE，杜绝 `tab:*` / 裸 hex。

---

## 2. 统一配色（PALETTE，唯一取色来源）

```python
PALETTE = {
    "blue1": "#8FC9E2", "blue2": "#9FC9DF", "blue3": "#C8D7EB", "blue4": "#C3CEE4",
    "cream1": "#FAEBC7", "cream2": "#F1E1C7", "cream3": "#E8D6B6",
    "gold": "#ECC97F", "dark": "#3A3A3A", "grey": "#AAAAAA", "white": "#FFFFFF",
    "red": "#D9534F", "green": "#5CB85C", "purple": "#9467BD",
}
```

**撞色红线**：同图内各对象颜色唯一可辨。某对象（如弹道/危险物）用红，则同类对象禁红（用蓝系逐一区分）；同图避免同类色撞车。

## 3. Matplotlib 数据图：SciencePlots 基底 + 自研中文/配色

用 `science` 样式作基底（细线/无笨重框/内置刻度/衬线基调），但**必须覆盖中文字体**避免豆腐块，配色仍由 PALETTE 主导。

```python
import matplotlib.pyplot as plt
import scienceplots

def setup_mpl(font_zh=("SimHei", "Microsoft YaHei"), font_size=9, style="science"):
    import matplotlib.pyplot as _plt
    if style:
        try:
            import scienceplots
            _plt.style.use(["science", "no-latex"])
        except Exception as e:
            print(f"[fig] scienceplots 不可用({e})，退回自研样式。")
    _plt.rcParams.update({
        "font.family": "sans-serif",                      # 用 sans-serif 载中文，避免 serif 豆腐块
        "font.sans-serif": list(font_zh) or ["SimHei", "Microsoft YaHei"],
        "axes.unicode_minus": False,
        "axes.facecolor": PALETTE["white"], "figure.facecolor": PALETTE["white"],
        "axes.edgecolor": PALETTE["dark"], "text.color": PALETTE["dark"],
        "grid.color": PALETTE["grey"], "grid.alpha": 0.25,
        "font.size": font_size, "axes.titlesize": font_size + 2,
        "axes.labelsize": font_size + 1, "legend.frameon": False,
        "axes.linewidth": 0.8, "xtick.direction": "in", "ytick.direction": "in",
    })
    return _plt
```

**通用去框/保存**：
```python
def style_ax(ax, grid=True):
    ax.spines["top"].set_visible(False); ax.spines["right"].set_visible(False)
    ax.spines["left"].set_color(PALETTE["grey"]); ax.spines["bottom"].set_color(PALETTE["grey"])
    if grid: ax.grid(True, color=PALETTE["grey"], alpha=0.25, ls="--", lw=0.7)

def fig_save(fig, path, dpi=200, pdf=True):
    fig.savefig(str(path) + ".png", dpi=dpi, bbox_inches="tight")
    if pdf: fig.savefig(str(path) + ".pdf", bbox_inches="tight")
```

## 4. 几何/机理示意图 & 流程图：TikZ（矢量、学术）

### 4.1 公共导言（tikz_geometry_preamble.tex，被 \input 的片段）
```latex
\usepackage{tikz}
\usepackage{amsmath,amssymb}
\usetikzlibrary{arrows.meta,calc,3d,shapes.geometric,shapes.misc,positioning,decorations.pathreplacing}
% A196 极简黑白 + 关键色红/蓝
\definecolor{ink}{RGB}{40,40,40}         % 主墨色(非纯黑)
\definecolor{keyred}{RGB}{200,40,40}     % 关键轮廓/重点红
\definecolor{keyblue}{RGB}{60,110,180}   % 辅助蓝
\definecolor{fillsolid}{RGB}{235,235,235}% 实心浅灰
\definecolor{fillgrad}{RGB}{200,200,200} % 渐变中灰(球体阴影)
\tikzset{
  hidden/.style={draw=ink, dashed, line width=0.6pt},   % 隐藏边
  solid/.style={draw=ink, line width=0.6pt},            % 可见边
  keyline/.style={draw=keyred, line width=1.4pt},       % 关键轮廓
  solidbody/.style={draw=ink, fill=fillsolid, line width=0.6pt},
  sphere/.style={draw=ink, fill=fillsolid, line width=0.6pt},
  proc/.style={draw=ink, rounded corners, fill=white, align=center, inner sep=5pt, font=\small},
  decision/.style={draw=ink, diamond, aspect=1.8, align=center, inner sep=3pt, font=\small},
  terminator/.style={draw=ink, rounded corners=10pt, fill=white, align=center, inner sep=5pt, font=\small},
  io/.style={draw=ink, trapezium, trapezium left angle=70, trapezium right angle=110, align=center, inner sep=4pt, font=\small},
  flow/.style={-{Stealth[length=2.6mm]}, thick, draw=ink},
  lbl/.style={font=\small, inner sep=1pt, fill=white},
}
```
主文档：`\documentclass[border=8pt]{standalone}` + `\usepackage{ctex}` + `\input{tikz_geometry_preamble.tex}`。

### 4.2 绘图规范（对齐国奖论文手法）
- **几何示意图**：虚线=隐藏边，灰实体=球/柱体，红色粗线=关键轮廓（外轮廓/归约对象）；标准几何符号标注点/线/圆。
- **流程图**：椭圆=起止，圆角框=过程，菱形=判断，平行四边形=输入/输出；**每个判断菱形必须有两个明确出口（是/否）**；循环回环路径清晰。
- **证明类图**：核心过渡元素（如弦、切点）用关键色强调，辅以文字说明推理链。
- 编译：`tectonic xxx.tex`（自动拉宏包，含中文需 ctex）。

### 4.3 常见图种与必含要素
| 图种 | 出现位置 | 必含要素 |
|---|---|---|
| 场景/对象俯视图 | 问题重述/第1章 | 全部对象 + 坐标系 + 关键坐标直标 + 主对象区分(不撞色) |
| 判据/机理示意图 | 判据定义处 | 几何要素(锥角/球/几何体/视线/关键交点) + 数值标注 |
| 算法流程图 | 主算法 >3 步 | 标准符号 + 判断双出口 + 循环回环 |
| 归约定理配图 | 有精确归约性质 | 归约前(采样) vs 归约后(有限特征)对比 |
| 结果对比/甘特图 | 各问结果处 | 本文值 vs 文献/基线 |

**概念示意/布局图必须标注"非真实比例"**；几何/数值图数据必须来自求解引擎。

## 5. gpt-image2 兜底
当 matplotlib 反复调不好（复杂布局示意、几何插画）时，委托 gpt-image2 生成。Prompt 需指定：横/竖版、PALETTE 具体色值、尺寸标注数值、注明用于 CUMCM 学术论文。接受生成结果，用户可外部迭代。但**机理/判据这类对几何精度要求高的图，优先 TikZ 手绘**（AI 生图易画错锥角/比例）。

## 6. 质量验收（配图写入结构审校）
凡必配图，画完核对：
- 图题简洁（表达结论，非"示意图"泛题）；坐标轴含单位；主对象直标坐标/名称。
- 配色全部来自 PALETTE，同图内对象颜色唯一可辨、无撞色。
- 判据/机理图必须标注关键数值（锥角/时间/距离）；概念示意标"非真实比例"。
- 数据真实（来自求解引擎），无臆造坐标；dpi≥200 + PDF 双导。
- 几何示意图虚线隐藏边/灰实体/红轮廓规范；流程图判断双出口、循环完整。
