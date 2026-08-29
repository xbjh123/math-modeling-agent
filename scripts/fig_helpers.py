# -*- coding: utf-8 -*-
"""fig_helpers.py — 数学建模论文配图统一工具库.

用途：全论文配图用同一套配色/样式/导出规范，杜绝 tab:blue 等默认色与风格漂移。
依赖：matplotlib；无求解引擎依赖（纯通用工具库）。

规范来源：references/paper_figures.md（唯一取色/样式来源）。

导出的主要接口：
    PALETTE                —— 配色字典（唯一取色来源）
    setup_mpl()            —— 统一 rcParams 样式（SciencePlots 基底 + 自研中文）
    style_ax(ax)           —— 去框 + 灰网格
    style_legend(ax)       —— 无框图例
    palette(name)          —— 按名取色
    fig_save(fig, path)    —— 统一导出 PNG(200dpi)+PDF 双格式
    anno(ax, x, y, text)   —— 直接标注（图内文字，减少依赖图例）
用法示例见 __main__ 冒烟：python scripts/fig_helpers.py
"""
from __future__ import annotations

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

# =====================================================================
# 唯一配色来源（references/paper_figures.md）
# =====================================================================
PALETTE = {
    "blue1":  "#8FC9E2",
    "blue2":  "#9FC9DF",
    "blue3":  "#C8D7EB",
    "blue4":  "#C3CEE4",
    "cream1": "#FAEBC7",
    "cream2": "#F1E1C7",
    "cream3": "#E8D6B6",
    "gold":   "#ECC97F",
    "dark":   "#3A3A3A",
    "grey":   "#AAAAAA",
    "white":  "#FFFFFF",
    "red":    "#D9534F",
    "green":  "#5CB85C",
    "purple": "#9467BD",
}


def palette(name: str) -> str:
    """按名取色；未知名抛 KeyError 并提示改用 PALETTE 键。"""
    if name not in PALETTE:
        raise KeyError(f"未知配色 '{name}'。可用: {list(PALETTE)}——请从 PALETTE 取色，不要用 tab:* 或 hex 硬编码。")
    return PALETTE[name]


def setup_mpl(font_zh=("SimHei", "Microsoft YaHei"), font_size=9,
              style="science"):
    """统一全局样式。返回 plt 供链式用。

    基底采用 SciencePlots 'science' 期刊样式（细线/无笨重边框/内置刻度/衬线基调），
    但保留我们自己的中文字体与配色板——science 只提供期刊级骨架，字体用 font_zh
    （避免 science 默认 serif 导致中文豆腐块），配色仍由 PALETTE 主导。
    style: 传 None 禁用 scienceplots（纯自研样式）；'science'/'science+ieee' 启用。
    """
    import matplotlib.pyplot as _plt
    if style and style != "None":
        try:
            import scienceplots  # noqa: F401
            _plt.style.use(["science", "no-latex"])
            if "+" in style:
                for s in style.split("+")[1:]:
                    _plt.style.use([s])
        except Exception as e:  # scienceplots 未装或样式缺失 -> 退回自研样式
            print(f"[fig_helpers] scienceplots 不可用({e})，使用自研默认样式。")
    _plt.rcParams.update({
        "font.family": "sans-serif",               # 用 sans-serif 承载中文，避免 serif 豆腐块
        "font.sans-serif": list(font_zh) or ["SimHei", "Microsoft YaHei"],
        "axes.unicode_minus": False,
        "axes.facecolor": PALETTE["white"],
        "figure.facecolor": PALETTE["white"],
        "axes.edgecolor": PALETTE["dark"],
        "axes.labelcolor": PALETTE["dark"],
        "text.color": PALETTE["dark"],
        "xtick.color": PALETTE["dark"],
        "ytick.color": PALETTE["dark"],
        "grid.color": PALETTE["grey"],
        "grid.alpha": 0.25,
        "font.size": font_size,
        "axes.titlesize": font_size + 2,
        "axes.titleweight": "bold",
        "axes.labelsize": font_size + 1,
        "legend.frameon": False,
        # science 细线基调整调：轴框细、刻度内置、无 top/right
        "axes.linewidth": 0.8,
        "xtick.direction": "in",
        "ytick.direction": "in",
    })
    return _plt


def style_ax(ax, grid=True):
    """去上/右脊 + 灰网格 + 深灰文字。"""
    ax.spines["top"].set_visible(False)
    ax.spines["right"].set_visible(False)
    ax.spines["left"].set_color(PALETTE["grey"])
    ax.spines["bottom"].set_color(PALETTE["grey"])
    if grid:
        ax.grid(True, axis="both", color=PALETTE["grey"], alpha=0.25, ls="--", lw=0.7)
    ax.tick_params(colors=PALETTE["dark"])
    return ax


def style_legend(ax, fontsize=10, loc="best", ncol=1):
    """无框图例（统一风格）。"""
    ax.legend(frameon=False, fontsize=fontsize, loc=loc, ncol=ncol)
    return ax


def fig_save(fig, path, dpi=200, pdf=True):
    """统一导出：PNG(指定 dpi, bbox_tight) + 可选 PDF（矢量）。返回 PNG 路径。"""
    from pathlib import Path
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    png = path.with_suffix(".png")
    fig.savefig(png, dpi=dpi, bbox_inches="tight")
    if pdf:
        fig.savefig(path.with_suffix(".pdf"), bbox_inches="tight")
    return str(png)


def anno(ax, x, y, text, fontsize=8, color="dark", dx=0, dy=0, ha="center", va="center", **kw):
    """图内直接标注（减少对图例依赖）。"""
    ax.text(x + dx, y + dy, text, fontsize=fontsize,
            color=PALETTE.get(color, color), ha=ha, va=va, **kw)


# =====================================================================
# 冒烟测试：python scripts/fig_helpers.py（生成示范图到 scratch/）
# =====================================================================
def _smoke():
    import tempfile
    from pathlib import Path
    plt = setup_mpl()
    fig, ax = plt.subplots(figsize=(6, 4))
    style_ax(ax)
    ax.plot([0, 1, 2], [0, 1, 0.5], color=palette("blue1"), lw=2, label="示例")
    ax.plot([0, 1, 2], [0.2, 0.8, 0.7], color=palette("gold"), lw=2, ls="--", label="示例2")
    style_legend(ax)
    ax.set_xlabel("x"); ax.set_ylabel("y"); ax.set_title("fig_helpers 冒烟测试")
    out = Path(tempfile.gettempdir()) / "fig_helpers_smoke"
    png = fig_save(fig, out / "demo.png")
    print("saved:", png)


if __name__ == "__main__":
    _smoke()
