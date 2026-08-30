# -*- coding: utf-8 -*-
"""fig_initial_mission.py — 复刻 A196 图12：各无人机与各导弹的初始位置.

问题五（多机多弹）配图：3D 散点展示 5 架无人机 + 3 枚导弹初始空间位置，
图例只用 UAV / Missile（对齐 A196 图12），并点出"贪心就近分配"直觉。
用法：python scripts/fig_initial_mission.py
输出：.modeling/artifacts/figures/fig_initial_mission.png/.pdf
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

UAV0 = np.array([[17800, 0, 1800], [12000, 1400, 1400], [6000, -3000, 700],
                 [11000, 2000, 1800], [13000, -2000, 1300]], float)
MISSILE0 = np.array([[20000, 0, 2000], [19000, 600, 2100], [18000, -600, 1900]], float)

plt = fh.setup_mpl(font_size=9)
from mpl_toolkits.mplot3d import Axes3D  # noqa: F401
import matplotlib.ticker as mticker

fig = plt.figure(figsize=(6.4, 5.0), dpi=200)
ax = fig.add_subplot(111, projection="3d")

# 地面（淡绿半透明）
xx, yy = np.meshgrid(np.linspace(-5000, 22000, 2), np.linspace(-4000, 3000, 2))
ax.plot_surface(xx, yy, np.zeros_like(xx), color=fh.palette("green"), alpha=0.15)

# 导弹（红色，图12 风格）
ax.scatter(MISSILE0[:, 0], MISSILE0[:, 1], MISSILE0[:, 2],
           marker="o", color=fh.palette("red"), s=130, depthshade=False,
           edgecolors=fh.palette("dark"), linewidths=1.0, label="Missile (导弹)")
# 无人机（蓝色三角）
ax.scatter(UAV0[:, 0], UAV0[:, 1], UAV0[:, 2],
           marker="^", color=fh.palette("blue1"), s=90, depthshade=False,
           edgecolors=fh.palette("dark"), linewidths=1.0, label="UAV (无人机)")

# 逐机/逐弹编号标注
for i, p in enumerate(MISSILE0):
    ax.text(p[0], p[1], p[2]+150, f"M{i+1}", fontsize=7, color=fh.palette("dark"))
for u, p in enumerate(UAV0):
    ax.text(p[0], p[1], p[2]+150, f"FY{u+1}", fontsize=7, color=fh.palette("dark"))

ax.set_xlabel("x (m)"); ax.set_ylabel("y (m)"); ax.set_zlabel("z (m)")
ax.set_xlim(-2000, 22000); ax.set_ylim(-4500, 3500); ax.set_zlim(0, 2600)
ax.set_title("图12：各无人机与各导弹的初始位置示意")
for axis in (ax.xaxis, ax.yaxis, ax.zaxis):
    axis.set_major_formatter(mticker.FuncFormatter(lambda v, p: f"{int(v)}"))
fh.style_legend(ax, fontsize=8, loc="upper left")
ax.view_init(elev=26, azim=-62)

fig.tight_layout()
out_dir = Path(__file__).resolve().parents[1] / "benchmarks" / "runs" / "2025A" \
    / "20260828_m2_first_run" / ".modeling" / "artifacts" / "figures"
out_dir.mkdir(parents=True, exist_ok=True)
png = fh.fig_save(fig, out_dir / "fig_initial_mission", dpi=200)
print("saved:", png)
