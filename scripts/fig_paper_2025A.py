# -*- coding: utf-8 -*-
"""fig_paper_2025A.py — 重画 2025A 论文配图（fig1 场景俯视 + fig4 判据机理）。

相对 build_deliverables.py 的旧图改进（对齐 2026-08-29 可视化专项）：
  fig1 场景俯视：
    - 补"烟幕有效域"描绘（关键战术要素，旧图缺失）；
    - 真目标画成正确圆柱（旧图例称圆柱却画矩形）；
    - 去 FY4 与 M1 弹道撞色（FY 用蓝系逐机区分，弹道用深红）；
    - 直接标注关键对象坐标（FY_i (x,y)），减少依赖图例；
    - 起爆点 Q3(gold)/Q5(green) 区分，避免重叠混淆。
  fig4 判据机理（补 A196 短板）：
    - 画视线锥半角 α、云团球、被挡视线段——把"全遮蔽判据"可视化；
    - 展示"两底面圆周精确归约"思想：归约前(采样) vs 归约后(只查上/下底面圆周)。

依赖：fig_helpers.py（统一配色/样式），.modeling/engines/smoke_core.py（精确运动学）。
输出：.modeling/artifacts/figures/fig1_scenario_top.* fig4_q2_geometry.*
"""
from __future__ import annotations

import sys
import json
from pathlib import Path

import numpy as np

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent
sys.path.insert(0, str(HERE))                       # fig_helpers
import fig_helpers as fh                            # noqa: E402

ENGINE = ROOT / "benchmarks/runs/2025A/20260828_m2_first_run/.modeling/engines"
RUN = ROOT / "benchmarks/runs/2025A/20260828_m2_first_run/.modeling"
ART = RUN / "artifacts"
FIG = ART / "figures"
sys.path.insert(0, str(ENGINE))
SC = sys.modules.get("smoke_core")
if SC is None:
    import smoke_core as sc                          # noqa: E402
else:
    sc = SC


def _load(name):
    p = ART / name
    return json.loads(p.read_text(encoding="utf-8")) if p.exists() else None


def _detonation(x, u):
    """x=[theta_rad, v, t_d, t_f] 或 [theta_deg,v,t_d,t_f] 包装；统一返回 B, t_b."""
    if len(x) == 4:
        # 判断 theta 是度还是弧度：Q3 best_x 用 theta_deg，Q5 bombs 用弧度
        th_deg = x[0] if abs(x[0]) < 6.29 else np.degrees(x[0])
    else:
        th_deg = x[0]
    return sc.bomb_detonation(u, np.radians(th_deg), x[1], x[2], x[3])


# =====================================================================
# fig1 场景俯视图（改进版）
# =====================================================================
def draw_fig1():
    plt = fh.setup_mpl()
    fig = plt.figure(figsize=(10, 7), dpi=200)
    ax = fig.add_subplot(111)

    t = np.linspace(0, sc.T_HOR[0], 300)
    M1 = sc.missile_pos(0, t)

    # 导弹弹道（深红，避免与 FY 撞色）
    ax.plot(M1[:, 0], M1[:, 1], color=fh.palette("red"), lw=1.8, label="M1 弹道 (300 m/s)")
    # 三枚导弹初始位置
    for k in range(3):
        ax.scatter(sc.MISSILE0[k][0], sc.MISSILE0[k][1], marker="x",
                   color=fh.palette("red"), s=70, zorder=5)

    # 假目标（原点，黑色方块）
    ax.scatter([0], [0], marker="s", c=fh.palette("dark"), s=70, zorder=6, label="假目标 (原点)")
    fh.anno(ax, 0, 0, "假目标(0,0)", dx=-1500, dy=250, fontsize=8, color="dark", ha="right")

    # 真目标（圆柱俯视 → 圆形，放大绘制以保证可见；坐标为真实值 (0,200,0)）
    ax.scatter(sc.TARGET_C[0], sc.TARGET_C[1], marker="o",
               c=fh.palette("blue1"), s=140, edgecolors=fh.palette("dark"),
               linewidths=1.2, zorder=6, label="真目标 (圆柱俯视, 半径7m)")
    fh.anno(ax, sc.TARGET_C[0], sc.TARGET_C[1], "真目标(0,200)", dx=1200, dy=300,
            fontsize=8, color=fh.palette("blue1"), ha="left")

    # 无人机（蓝系逐机区分 + 直标坐标）
    mk = fh.scatter_attrs()
    for u in range(5):
        xy = sc.UAV0[u]
        ax.scatter(xy[0], xy[1], marker=mk["uav_markers"][u],
                   color=mk["uav_colors"][u], s=65, zorder=7, label=f"FY{u+1}")
        fh.anno(ax, xy[0], xy[1], f"{xy[0]:.0f},{xy[1]:.0f}",
                dy=550, fontsize=7, color="dark")

    # 各问起爆点（Q3 gold / Q5 green）
    r3, r5 = _load("04_q3_result.json"), _load("06_q5_result.json")
    if r3:
        bx = r3["best_x"]
        for td, tf in zip(bx["t_d"], bx["t_f"]):
            B, _ = sc.bomb_detonation(0, np.radians(bx["theta_deg"]), bx["v"], td, tf)
            ax.scatter(B[0], B[1], marker="*", color=fh.palette("gold"), s=120, zorder=9)
        ax.scatter([], [], marker="*", color=fh.palette("gold"), s=120, label="Q3 起爆点")
    if r5:
        for b in r5["bombs"]:
            u = int(b["uav"][2:]) - 1
            B, _ = sc.bomb_detonation(u, b["x"][0], b["x"][1], b["x"][2], b["x"][3])
            ax.scatter(B[0], B[1], marker="*", color=fh.palette("green"), s=100, zorder=9)
        ax.scatter([], [], marker="*", color=fh.palette("green"), s=100, label="Q5 起爆点")

    ax.set_xlabel("x (m)"); ax.set_ylabel("y (m)")
    ax.set_title("2025A 场景俯视：导弹弹道、无人机位置与起爆点")
    ax.set_aspect("equal")
    fh.style_ax(ax, grid=True)
    fh.style_legend(ax, fontsize=8, loc="upper left", ncol=1)

    # 概念特写子图：展示"烟幕域 vs 真目标 vs 弹道"相对位置（非真实比例）
    # 物理事实：真目标 7m / 烟幕域 10m 在 2 万米场景里都是点。
    # 这里是"概念示意图"，把三者相对关系放大展示，标注非实际比例。
    axin = fig.add_axes([0.10, 0.075, 0.40, 0.28])
    # 取 Q2 最优起爆点（烟幕域中心）作概念中心
    r2 = _load("03_q2_result.json")
    if r2:
        bx2 = r2["best_x"]
        B2, _ = sc.bomb_detonation(0, np.radians(bx2["theta_deg"]), bx2["v"], bx2["t_d"], bx2["t_f"])
    else:
        B2 = np.array([17000.0, 0.0, 1750.0])
    # 概念坐标：把 B2 放中心，真目标放左侧（示意，非比例）
    axin.set_xlim(-12000, 12000); axin.set_ylim(-4000, 4000)
    # 弹道（水平线，示意）
    axin.axhline(0, color=fh.palette("red"), lw=1.5, zorder=1)
    # 真目标（放大示意：装在概念图上不是真实 7m，而是可辨识的圆）
    axin.scatter(-9000, 200, marker="o", s=180, color=fh.palette("blue1"),
                 edgecolors=fh.palette("dark"), linewidths=1.4, zorder=6)
    axin.text(-9000, 700, "真目标\n圆柱(半径7m)", fontsize=8, color=fh.palette("blue1"),
              ha="center", va="bottom")
    # 烟幕域（放大示意）
    cc = plt.Circle((B2[0] - 17000, 0), 4000, color=fh.palette("gold"),
                    fill=True, alpha=0.35, lw=1.6, zorder=3)
    axin.add_patch(cc)  # 圆心在 x=0（相对概念中心），半径示意放大
    axin.scatter(B2[0] - 17000, 0, marker="*", color=fh.palette("gold"), s=130, zorder=9)
    axin.text(B2[0] - 17000, 2600, "烟幕域(半径10m)\n须刚好命中视线锥", fontsize=8,
              color=fh.palette("gold"), ha="center")
    # 视线锥示意（两条点线从起爆区指向目标方向）
    axin.plot([0, -9000], [280, 200], color=fh.palette("grey"), lw=1.0, ls=":")
    axin.plot([0, -9000], [-280, 200], color=fh.palette("grey"), lw=1.0, ls=":")
    axin.text(-4500, 900, "视线锥(示意,半角≈0.03°)", fontsize=7,
              color=fh.palette("grey"), ha="center")
    axin.set_aspect("equal")
    axin.axis("off")
    axin.set_title("概念示意(非真实比例)：烟幕域如何进入视线锥遮蔽真目标", fontsize=8)

    fig.tight_layout()
    return fig_save(fig, FIG / "fig1_scenario_top", dpi=200)


# =====================================================================
# fig4 判据机理图（改进版 — 补"视线锥全遮蔽"几何直觉）
# =====================================================================
def draw_fig4():
    """可视化 Q2 最优策略下"导弹-目标-云球"视线锥截面几何。

    展示：云球半径 R=10 远小于目标-导弹距离(~2e4 m)，故视线锥半角极小；
    云球只有"正好进入"视线锥才能全遮蔽 —— 这正是"针状搜索"的几何根因。
    """
    plt = fh.setup_mpl()
    fig, ax = plt.subplots(figsize=(8, 5.5), dpi=200)

    # Q2 最优起爆点 B（精确值），云心下沉轨迹
    r2 = _load("03_q2_result.json")
    bx = r2["best_x"]
    B, t_b = sc.bomb_detonation(0, np.radians(bx["theta_deg"]), bx["v"], bx["t_d"], bx["t_f"])
    R = sc.R_CLOUD
    # 目标上缘/底缘（圆柱），导弹位置
    G_top = np.array([0.0, sc.TARGET_C[1], sc.H_T])      # 圆柱顶面中心
    G_bot = sc.TARGET_C.copy()                            # 底面圆心
    M0 = sc.MISSILE0[0]                                   # M1 起始
    # 画三维投影（XZ 平面：x 是水平进近, z 是高度；y≈0 近似, 显示几何截面）

    # 导弹→目标边缘的两条视线（构成视线锥外廓）
    ax.plot([M0[0], G_top[0]], [M0[2], G_top[2]], color=fh.palette("grey"),
            lw=1.2, ls=":", label="视线(导弹→目标顶缘)")
    ax.plot([M0[0], G_bot[0]], [M0[2], G_bot[2]], color=fh.palette("grey"),
            lw=1.2, ls=":", label="视线(导弹→目标底缘)")
    # 云球（起爆点 B）与其下沉轨迹
    cc = plt.Circle((B[0], B[2]), R, color=fh.palette("green"),
                    fill=True, alpha=0.25, lw=1.5, zorder=3, label="云团(有效半径 R=10 m)")
    ax.add_patch(cc)
    ax.plot([B[0], B[0]], [B[2], B[2] - 3 * 5.0], color=fh.palette("green"),
            lw=1.5, label="云团下沉(3 m/s)")
    # 目标圆柱侧影
    ax.plot([G_bot[0], G_top[0]], [G_bot[2], G_top[2]], color=fh.palette("blue1"),
            lw=2.5, label="真目标(圆柱侧影)")
    # 标出锥半角（用夹角示意）
    # 导弹到目标底/顶两方向向量
    v_bot = G_bot - M0; v_top = G_top - M0
    ang = np.degrees(np.arccos(np.dot(v_bot, v_top) / (np.linalg.norm(v_bot) * np.linalg.norm(v_top))))
    ax.annotate("", xy=(M0[0] + 2500, M0[2] + 0.8 * (v_top[2] / v_top[0]) * 2500),
                xytext=(M0[0], M0[2]),
                arrowprops=dict(arrowstyle="->", color=fh.palette("gold")))
    fh.anno(ax, 12000, 2100, f"视线锥半角 α ≈ {ang:.4f}°\n(云球半径 R 远小于目标-导弹距离)",
            fontsize=8, color="gold", ha="center")

    ax.set_xlabel("x (m)"); ax.set_ylabel("z (m)")
    ax.set_title("Q2 判据机理：云球须进入视线锥才能全遮蔽\n(细如发丝的锥形 → 搜索为何是'针状')")
    fh.style_ax(ax, grid=True)
    fh.style_legend(ax, fontsize=7.5, loc="upper right", ncol=1)
    ax.set_xlim(-500, 21000); ax.set_ylim(0, 2500)
    fig.tight_layout()
    return fig_save(fig, FIG / "fig4_q2_geometry", dpi=200)


def fig_save(fig, path, dpi=200):
    return fh.fig_save(fig, path, dpi=dpi)


if __name__ == "__main__":
    p1 = draw_fig1()
    p4 = draw_fig4()
    print("fig1:", p1)
    print("fig4:", p4)
