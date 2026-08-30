# -*- coding: utf-8 -*-
"""fig_initial_3d.py — 复刻 A196 图3右侧：三维初始布局散点图.

用真实的 2025A 初始数据（无人机 FY1-5、导弹 M1-3、真/假目标），
画 3D 空间布局：绿色半透明地面 + 各对象散点。风格对齐 A196 图3(b)。
用法：python scripts/fig_initial_3d.py
输出：.modeling/artifacts/figures/fig_initial_3d.png/.pdf
"""
from __future__ import annotations
import sys
from pathlib import Path
import numpy as np
import matplotlib
matplotlib.use("Agg")
HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import fig_helpers as fh

# 真实初始数据（题面常数，同 smoke_core）
UAV0 = np.array([[17800, 0, 1800], [12000, 1400, 1400], [6000, -3000, 700],
                 [11000, 2000, 1800], [13000, -2000, 1300]], float)
MISSILE0 = np.array([[20000, 0, 2000], [19000, 600, 2100], [18000, -600, 1900]], float)
TARGET = np.array([0, 200, 0])  # 真目标底心
FALSE_T = np.array([0, 0, 0])   # 假目标原点

plt = fh.setup_mpl(font_size=9)
from mpl_toolkits.mplot3d import Axes3D  # noqa: F401

fig = plt.figure(figsize=(6.4, 5.2), dpi=200)
ax = fig.add_subplot(111, projection="3d")

# 地面（半透明绿色——复刻 A196 图3(b) 风格）
xx, yy = np.meshgrid(np.linspace(-5000, 22000, 2), np.linspace(-4000, 3000, 2))
ax.plot_surface(xx, yy, np.zeros_like(xx), color=fh.palette("green"), alpha=0.18)

# 导弹（红叉）
ax.scatter(MISSILE0[:, 0], MISSILE0[:, 1], MISSILE0[:, 2],
           marker="x", color=fh.palette("red"), s=70, depthshade=False,
           label="导弹 M1-3")
# 无人机（蓝系逐机）
mk = fh.scatter_attrs()
for u in range(5):
    ax.scatter(UAV0[u, 0], UAV0[u, 1], UAV0[u, 2],
               marker=mk["uav_markers"][u], color=mk["uav_colors"][u], s=60,
               depthshade=False, label=f"FY{u+1}")
# 真目标（圆柱, 蓝色大点）
ax.scatter(TARGET[0], TARGET[1], TARGET[2], marker="o",
           color=fh.palette("blue1"), s=150, edgecolors=fh.palette("dark"),
           linewidths=1.2, depthshade=False, label="真目标")
# 假目标（黑方块）
ax.scatter(FALSE_T[0], FALSE_T[1], FALSE_T[2], marker="s",
           color=fh.palette("dark"), s=70, depthshade=False, label="假目标")

ax.set_xlabel("x (m)"); ax.set_ylabel("y (m)"); ax.set_zlabel("z (m)")
ax.set_xlim(-2000, 22000); ax.set_ylim(-4500, 3500); ax.set_zlim(0, 2600)
ax.set_title("初始布局（3D）：无人机、导弹、真/假目标")
# 修正 3D 刻度格式（避免 no-latex 下出现 "1/1000" 之类的异常前缀）
import matplotlib.ticker as mticker
ax.xaxis.set_major_formatter(mticker.FuncFormatter(lambda v, p: f"{int(v)}"))
ax.yaxis.set_major_formatter(mticker.FuncFormatter(lambda v, p: f"{int(v)}"))
ax.zaxis.set_major_formatter(mticker.FuncFormatter(lambda v, p: f"{int(v)}"))
fh.style_legend(ax, fontsize=7.5, loc="upper left")
ax.view_init(elev=26, azim=-62)

fig.tight_layout()
out_dir = Path(__file__).resolve().parents[1] / "benchmarks" / "runs" / "2025A" \
    / "20260828_m2_first_run" / ".modeling" / "artifacts" / "figures"
out_dir.mkdir(parents=True, exist_ok=True)
png = fh.fig_save(fig, out_dir / "fig_initial_3d", dpi=200)
print("saved:", png)
