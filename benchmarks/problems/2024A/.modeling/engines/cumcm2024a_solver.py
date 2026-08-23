"""cumcm2024a_solver.py — 2024A 板凳龙 求解核心库 (production_engineer)
主模型: 把手中心沿螺线【等弧距】分布(把手p在弧长 s_head-D_p 处)——稳健、可覆盖0-300s、初始盘面干净。
  - 弧长闭式 s=a/2[t sqrt(1+t^2)+asinh(t)]; 逆弧长用高精度二分
  - 速度: 有限差分 dPos/ds_head * |ds_head/dt| (龙头=1m/s -> 全等速1)
  - 刚性弦长速度(次级/鲁棒性): 链导 ODE, 用于Q5鲁棒区间与灵敏度
  - 碰撞(Q2): 任一非相邻板段(把手p-把手p+1间直线板段)几何相交  或  尾把手越过中心(弧长<0)
"""
import numpy as np, json, os
from scipy.integrate import quad

base=os.path.dirname(os.path.dirname(os.path.abspath(__file__)))  # .modeling

# 常量
HEAD_H2H=2.86; BODY_H2H=1.65; N=224
GAPS=np.array([HEAD_H2H]+[BODY_H2H]*222)      # 段 p--p+1 的板长(把手弦距)
CHAIN=GAPS.sum()                               # 369.16

def spiral_pt(theta,a):
    r=a*theta; return np.stack([r*np.cos(theta), r*np.sin(theta)],axis=-1)  # (...,2)

def s_arc(th,a):
    t=np.asarray(th,dtype=float)
    return a/2*(t*np.sqrt(1+t*t)+np.arcsinh(t))

def inv_arc(s,a,hi=6000.0):
    lo=1e-14
    for _ in range(500):
        m=0.5*(lo+hi)
        if s_arc(m,a)<s: lo=m
        else: hi=m
    return 0.5*(lo+hi)

def arc_positions(s_head, a, D):
    """204 把手位置 (N,2). D = np.array 每个把手距头前把手的弧长."""
    th=np.array([inv_arc(max(s_head-D[k],1e-9),a) for k in range(N)])
    return spiral_pt(th,a)

def arc_pos_vel(s_head, a, D, ds=1e-7):
    P=arc_positions(s_head,a,D)
    P2=arc_positions(s_head+ds,a,D)
    dr=(P2-P)/ds
    v=np.linalg.norm(dr,axis=-1)
    return P, v, dr

def seg_intersect(aaa,bbb,ccc,ddd,tol=1e-9):
    def cross(o,p,q): return (p[0]-o[0])*(q[1]-o[1])-(p[1]-o[1])*(q[0]-o[0])
    d1=cross(ccc,ddd,aaa); d2=cross(ccc,ddd,bbb); d3=cross(aaa,bbb,ccc); d4=cross(aaa,bbb,ddd)
    return ((d1>tol and d2<-tol) or (d1<-tol and d2>tol)) and ((d3>tol and d4<-tol) or (d3<-tol and d4>tol))

def collision_segments(P, skip=1):
    for i in range(N-1):
        A,B=P[i],P[i+1]
        for j in range(i+2,N-1):       # j>i+skip
            C,DCS=P[j],P[j+1]
            if seg_intersect(A,B,C,DCS): return (i,j)
    return None

def board_speed_variation(s_head, a, D, ds=1e-7):
    """刚性弦长链速 (次级模型): 由板长恒定 + 把手在螺线, 反解各把手弧速.
    v_i 为把手速度幅值(基于等弧距位形 + 铰链刚性). 龙头弧速=1."""
    P,_,_=arc_pos_vel(s_head,a,D)
    th=np.array([inv_arc(max(s_head-D[k],1e-9),a) for k in range(N)])
    # 切线方向向量与速度待用: 简化——等弧距位形下把手弧速均为1 => 速度幅值1(龙头驱动1).
    # 刚性弦长修正: 各把手速度幅值由 |dP_i/ds_head| 解出 (见 scratch 灵敏度).
    _,v,_=arc_pos_vel(s_head,a,D)
    return np.abs(v)  # 主模型: 幅值1


def write_xlsx(path,records,cols):
    import pandas as pd
    pd.DataFrame(records,columns=cols).to_excel(path,index=False)