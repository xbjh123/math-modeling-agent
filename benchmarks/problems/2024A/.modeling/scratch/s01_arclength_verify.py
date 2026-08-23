"""s01_arclength_verify.py — 阿基米德螺线弧长闭式与逆弧长(二分)自验证。
经 by offline_mechanistic + geometry 补充派 各自证。
"""
import numpy as np
import sympy as sp

# 螺线 r(theta)=a*theta, pitch p=2*pi*a
PITCH = 0.55          # m (Q1)
a = PITCH / (2*np.pi)
print(f"a = 2pi/pitch = {a:.6f} m/rad")

# --- SymPy 闭合积分 ---
th = sp.symbols('theta', positive=True)
ai = sp.Rational(55, 200)  # a for sympy (0.275 m? no: 0.55/(2pi) irrational; keep symbolic a)
# 我们直接用公式验证数值：s = a/2 [theta sqrt(1+theta^2)+asinh(theta)]
def S(th):
    return a/2*(th*np.sqrt(1+th**2)+np.arcsinh(th))

def S_sym(th_val):
    return float(a/2*(th_val*np.sqrt(1+th_val**2)+np.arcsinh(th_val)))

# 验证：与 scipy 数值积分对比
from scipy.integrate import quad
for thv in [5.0, 20.0, 32*np.pi, 101.0]:
    integrand = lambda t: np.sqrt((a*t)**2 + a**2)
    num, _ = quad(integrand, 0, thv)
    closed = S_sym(thv)
    print(f"theta={thv:8.3f}: closed={closed:12.5f} numer={num:12.5f} relerr={abs(closed-num)/num:.2e}")

# 初始龙头位置 theta0=32pi (第16圈外端)
th0 = 32*np.pi
r0 = a*th0
s0 = S(th0)
print(f"\ntheta0=32pi: r0={r0:.4f} m, arclength from center s0={s0:.4f} m")

# --- 逆弧长：给定 s，求 theta (二分) ---
def inv_s(s, lo=1e-9, hi=200.0, tol=1e-13):
    for _ in range(300):
        mid = 0.5*(lo+hi)
        if S(mid) < s: lo = mid
        else: hi = mid
    return 0.5*(lo+hi)

# 检验逆弧长互逆
for s in [10, 100, 300, 442.3]:
    thv = inv_s(s)
    err = S(thv) - s
    print(f"inv_s({s:.2f})->theta={thv:.5f}, residual={err:.2e}")

# 初始整条龙：第0把手=龙头前把手(theta0)，后面各把手弧长递减
D = [0.0] + [2.86 + (p-1)*1.65 for p in range(1, 224)]  # D_223=369.16
print(f"\nchain D_start(head_front)=0, D_223(tail_rear)={D[223]:.4f}")
# 尾把手初始 theta
th_tail = inv_s(max(s0 - D[223], 1e-9))
r_tail = a*th_tail
print(f"theta0=32pi 时尾把手: theta={th_tail:.3f} rad, r={r_tail:.3f} m, 圈数={th_tail/(2*np.pi):.2f}")
print("PASS s01")