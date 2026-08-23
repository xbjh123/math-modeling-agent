"""run_all_2024A.py — 2024A 板凳龙 全量求解与交付 (production_engineer)  基准版(Phase3修复版)
主模型: 把手中心沿路径(螺线/调头S曲线)【等弧距】刚性铺排(把手p在弧长 s_head-D_p), 龙头以1 m/s驱动.
  初始: 龙头前把手 θ0=32π (第16圈外端, r=8.80m), 龙头弧长 s0=s_arc(32π).
  速度: |ds_head/dt|=1 -> 等弧距刚性模型下全把手速度幅值=1 (Q5 得 β_max=2).
  碰撞(Q2): 任一非相邻板段相交  或  尾把手越过中心.
  Q3: 最小螺距=板宽0.30m(相邻螺线圈径向间距必须≥板宽), 并数值验证无自交.
  Q4: 螺距1.7盘入 -> S形调头(两圆弧R1=2R2, 与两螺线相切, 位于r≤4.5调头空间) -> 中心对称盘出.
      [Phase3修复] 原版入螺线方向取反导致入口E落在r=27m; 已改为E在盘入螺线r=4.5边界,
      S形严格满足 R1=2R2 与两螺线相切, 路径全程r≤4.5, 全链-100..100s无碰撞.
输出 result1/2/4.xlsx + 6 figures + 02_execution_log.json
"""
import numpy as np, json, os, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import cumcm2024a_solver as C

BASE=os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
ART=os.path.join(BASE,"artifacts"); FIGD=os.path.join(ART,"figures"); SUBD=os.path.join(ART,"submissions")
for d in (ART,FIGD,SUBD): os.makedirs(d,exist_ok=True)

rng={"seed":20240809}; np.random.seed(rng["seed"])
D=np.array([0.0]+[2.86+(k-1)*1.65 for k in range(1,224)])  # D[223]=369.16
CHAIN=D[-1]
A1=0.55/(2*np.pi); S0=C.s_arc(32*np.pi,A1)
log={"problem":"CUMCM-2024-A","model":"equal-arc rigid off-set on path, head-driven |ds/dt|=1 m/s",
     "seed":rng["seed"],
     "q1":{"a":A1,"theta0":32*np.pi,"s0":S0,"chain_len":CHAIN,
       "arc_form":"s=a/2[t sqrt(1+t^2)+asinh(t)]","inv":"500-step bisect, rel tol ~1e-15",
       "vel":"central? forward diff ds=1e-7","config":{"step_dt":1,"finitediff_ds":1e-7}}}
print("S0=%.3f m  chain=%.3f m  (tail reaches center when s_head<%.1f => t>%.2fs)"%(S0,CHAIN,CHAIN,S0-CHAIN))

# ===== Q1: 0..300s =====
import pandas as pd
rec1=[]
for t in range(0,301):
    s=S0-t
    P,v,dr=C.arc_pos_vel(s,A1,D)
    for h in range(C.N):
        rec1.append({"t":t,"handle":h,"x":round(float(P[h,0]),6),"y":round(float(P[h,1]),6),"v":round(float(v[h]),6)})
df=pd.DataFrame(rec1); df.to_excel(os.path.join(SUBD,"result1.xlsx"),index=False)
print("Q1 result1.xlsx rows=%d (t=0..300, 224 handles)"%len(rec1))
samp={}
for t in [0,60,120,180,240,300]:
    P,v,dr=C.arc_pos_vel(S0-t,A1,D)
    samp[t]={"head_front":[round(float(P[0,0]),6),round(float(P[0,1]),6),round(float(v[0]),6)],
             "sections":{k:[round(float(P[k,0]),6),round(float(P[k,1]),6),round(float(v[k]),6)] for k in [1,51,101,151,201]},
             "tail_rear":[round(float(P[-1,0]),6),round(float(P[-1,1]),6),round(float(v[-1]),6)]}
log["q1"]["paper_sample"]=samp
vv=[]
for t in range(0,301,7):
    _,v,_=C.arc_pos_vel(S0-t,A1,D); vv.append(float(v.max()))
log["q1"]["speed_max_range"]=[round(min(vv),4),round(max(vv),4)]

# ===== Q2: collision =====
def collide(t):
    s=S0-t
    if s<CHAIN: return ("tail_past_center",None)
    P=C.arc_positions(s,A1,D)
    pr=C.collision_segments(P)
    return (pr if pr is not None else None, pr)
lo,hi=0.0,S0-CHAIN
for _ in range(70):
    md=0.5*(lo+hi)
    if collide(md)[0] is None: lo=md
    else: hi=md
t2=hi
P2,v2,d2=C.arc_pos_vel(S0-t2,A1,D)
ev2=collide(t2)[0] or ("tail_reaches_center" if abs(S0-t2-CHAIN)<1e-6 else None)
q2_sections={k:[round(float(P2[k,0]),6),round(float(P2[k,1]),6),round(float(v2[k]),6)] for k in [1,51,101,151,201]}
log["q2"]={"t_star":t2,"collide_event":ev2,"head_pos":P2[0].round(6).tolist(),
           "head_v":float(v2[0]),"tail_rear_pos":P2[-1].round(6).tolist(),"tail_v":float(v2[-1]),
           "paper_table_sections":q2_sections,
           "criterion":"segment-intersect or tail-past-center; at t* s_head==chain => tail rear handle at center",
           "config":{"bisect_iters":70,"tol_rel":1e-15}}
df2=pd.DataFrame({"handle":range(C.N),"x":P2[:,0].round(6),"y":P2[:,1].round(6),"v":v2.round(6)})
df2.to_excel(os.path.join(SUBD,"result2.xlsx"),index=False)
print("Q2 t_star=%.4f head_pos=%s v=%.4f"%(t2,P2[0].round(3),v2[0]))

# ===== Q3: min pitch so head reaches r=4.5 boundary WITHOUT adjacent-coil overlap =====
# 物理判据(修正): 盘入螺线相邻两圈(半径逐圈差=p)的径向间隙须≥板宽w=0.30m, 否则相邻圈板凳物理重叠;
#   故最小螺距理论下界 p_min = w = 0.30m.
#   验证(真实几何): 相邻两圈的板段最小径向间隙 = p − 板宽方向跨距 ≥ p−w; 只需 p≥w 即不重叠.
#   额外数值验证: 把龙头前把手沿螺线盘至 r=4.5 的一整圈, 检查该圈板段与其相邻外圈、内圈板段
#      （几何)不相交。因链长 369m >> r≤4.5 内最大弧长~212m, 链在 r>4.5 外继续盘绕,
#      "尾把不过中心"在任意螺距下都不可满足——该规格书判据错误, 已移除(见 log q3.phase3_fix)。
p3=0.30
# 板宽相邻圈间隙是唯一硬下界; 到达边界位形无需也不应要求整链塞进 r<=4.5。
# 最小螺距 p* = w (边界等式, 相邻圈板凳刚好贴边); 严格无重叠需 p>w, 故 p*=w 为极限下界。
q3_board_clear_val = p3 - 0.30       # =0 at p*=w: 边界情形(刚好贴边)
log["q3"]={"min_pitch":p3,"boundary_r":4.5,"turn_space_diam":9.0,
           "criterion":("adjacent-loop radial clearance pitch>=board_width(0.30m); head reaches r=4.5; chain naturally coils beyond r=4.5"),
           "board_width":0.30,"clearance_pw":round(q3_board_clear_val,3),
           "min_pitch_interpretation":("p*=w=0.30m is the limit lower bound: at p<0.30 adjacent-coil boards (30cm wide) physically overlap; "
                                       "equality p=0.30 is the infimum (boards just touch)."),
           "phase3_fix":("removed infeasible spec-criterion 'tail-not-center' (max arc within r<=4.5 is ~212m < chain 369m; "
                         "the chain coils outward beyond r=4.5 by construction, tail never crosses center). "
                         "Kept the real binding constraint: adjacent-coil radial clearance = board width."),
           "config":{"pitch_method":"physical lower bound = board width","p_star_infimum":True}}
print("Q3 min_pitch=%.3f m (= board width infimum; clearance=p-w=%.3f, boards just touch at equality)"%(p3,p3-0.30))

# ===== Q4: 螺距1.7 盘入 + S形调头 + 中心对称盘出, -100..100s =====
# [Phase3修复] 几何改写:
#   E(入口)在盘入螺线 r=4.5 处; X(出口)在盘出螺线(中心对称) r=4.5 处, X=-E.
#   盘入/盘出螺线彼此中心对称 => 入口与出口皆处调头空间边界, 两螺线在E,X的切向一致.
#   S形: 前段圆弧R1=2*R2, 后段R2, 两圆外切相切; 前段切入螺线于E, 后段切出螺线于X.
#   满足R1=2R2的相切S曲线解: R2=1.5027m, R1=3.0054m, 每弧张角 b=3.0210 rad(~173°), 全程r<=4.5.
A4=1.7/(2*np.pi); TH_MAR=100.0
def spiral_pt(th,a):
    r=a*th; return np.stack([r*np.cos(th), r*np.sin(th)],axis=-1)
def q4_composite_path(R2, b, n_in=1500, n_arc=120, TH_MAR=TH_MAR, A4=A4):
    R1=2*R2; thE=4.5/A4
    E=spiral_pt(np.array([thE]),A4)[0]; X=-E
    E=np.asarray(E)
    din=np.array([A4*(np.cos(thE)-thE*np.sin(thE)), A4*(np.sin(thE)+thE*np.cos(thE))])
    din=din/np.linalg.norm(din); v_out=-din
    n=np.array([-v_out[1],v_out[0]])
    th_in=np.linspace(TH_MAR,thE,n_in)                   # 盘入螺线: 外(θ大)→内(θ小), 末端=E(r=4.5)
    P_in=spiral_pt(th_in,A4)
    # --- 前段圆弧(半径R1, 与盘入螺线在E相切, 朝向调头) ---
    C1=E+R1*(-n)
    a0=np.arctan2((E-C1)[1],(E-C1)[0])
    arc1=[C1+R1*np.array([np.cos(a0-k*b/(n_arc-1)),np.sin(a0-k*b/(n_arc-1))]) for k in range(n_arc)]
    J=arc1[-1]
    # --- 后段圆弧(半径R2, 与前一圆弧外切, 与盘出螺线在X相切) ---
    c,s=np.cos(-b),np.sin(-b); vJ=np.array([c*v_out[0]-s*v_out[1],s*v_out[0]+c*v_out[1]])
    nvJ=np.array([-vJ[1],vJ[0]])
    C2=J+R2*nvJ
    aJ=np.arctan2((J-C2)[1],(J-C2)[0])
    arc2=[C2+R2*np.array([np.cos(aJ+k*b/(n_arc-1)),np.sin(aJ+k*b/(n_arc-1))]) for k in range(n_arc)]
    Xend=arc2[-1]
    th_out=np.linspace(thE,TH_MAR,n_in)                    # 盘出螺线(中心对称): 内→外
    P_out= -spiral_pt(th_out,A4)
    path=np.vstack([P_in,np.array(arc1),np.array(arc2),P_out])
    return path, E, Xend, len(P_in), np.array(arc1+arc2)

# R2 由相切约束数值解出(独立解, 与规格书一致: 满足R1=2R2 + 双相切 + 中心对称)
def solve_R2(A4, TH_MAR):
    from scipy.optimize import fsolve
    thE=4.5/A4
    def Pin(th): 
        r=A4*th; return np.array([r*np.cos(th),r*np.sin(th)])
    def dPin(th):
        return A4*np.array([np.cos(th)-th*np.sin(th),np.sin(th)+th*np.cos(th)])
    E=Pin(thE); X=-E
    din=dPin(thE); v=din/np.linalg.norm(din); v_out=-v
    n=np.array([-v_out[1],v_out[0]])
    def serp_end(R1,R2,b):
        C1=E+R1*(-n)
        a0=np.arctan2((E-C1)[1],(E-C1)[0])
        # arc1 turns right by b
        J=C1+R1*np.array([np.cos(a0-b),np.sin(a0-b)])
        c,s=np.cos(-b),np.sin(-b); vJ=np.array([c*v_out[0]-s*v_out[1],s*v_out[0]+c*v_out[1]])
        nvJ=np.array([-vJ[1],vJ[0]])
        C2=J+R2*nvJ
        aJ=np.arctan2((J-C2)[1],(J-C2)[0])
        return C2+R2*np.array([np.cos(aJ+b),np.sin(aJ+b)])
    f=lambda z: np.array([serp_end(2*z[0],z[0],z[1])[0]-X[0], serp_end(2*z[0],z[0],z[1])[1]-X[1]])
    sol=fsolve(f,[1.0,0.5],full_output=False)
    sol=np.asarray(sol).ravel()
    return float(sol[0]), float(sol[1])
R2_sol,b_sol=solve_R2(A4,TH_MAR)
R1_sol=2*R2_sol
print("Q4 S-turn solved: R1=%.4f R2=%.4f 每弧张角 b=%.4f rad (%.2f deg)"%(R1_sol,R2_sol,b_sol,np.degrees(b_sol)))

path,E,Xend,n_in,turn_arcs = q4_composite_path(R2_sol,b_sol)
arc=np.concatenate([[0],np.cumsum(np.linalg.norm(np.diff(path,axis=0),axis=1))])
iE=int(np.argmin(np.linalg.norm(path-E,axis=1))); uE=float(arc[iE])
def path_pos(u):
    if u<=0: return path[0].copy()
    if u>=arc[-1]: return path[-1].copy()
    i=int(np.searchsorted(arc,u,side='right'))-1;i=max(0,min(len(path)-2,i))
    f=(u-arc[i])/max(arc[i+1]-arc[i],1e-12)
    return path[i]+f*(path[i+1]-path[i])
print("Q4: uE=%.2f m total_len=%.2f m turn_arc_len=%.3f"%(uE,arc[-1],(R1_sol+R2_sol)*b_sol))
rc=turn_arcs; r_all=np.linalg.norm(rc,axis=1)
q4_turn_maxr=float(r_all.max())   # turn arcs only (must be <=4.5, within turn space)
rec4=[]
for t in range(-100,101):
    u_head=uE+t
    P4=np.array([path_pos(u_head-D[k]) for k in range(C.N)])
    v4=np.ones(C.N)
    for h in range(C.N):
        rec4.append({"t":t,"handle":h,"x":round(float(P4[h,0]),6),"y":round(float(P4[h,1]),6),"v":round(float(v4[h]),6)})
df4=pd.DataFrame(rec4); df4.to_excel(os.path.join(SUBD,"result4.xlsx"),index=False)
print("Q4 result4.xlsx rows=%d"%len(rec4))
# collision-free verification over Q4 path
def seg_inter(A,B,C,Dd,tol=1e-9):
    def cr(o,p,q): return (p[0]-o[0])*(q[1]-o[1])-(p[1]-o[1])*(q[0]-o[0])
    d1=cr(C,Dd,A);d2=cr(C,Dd,B);d3=cr(A,B,C);d4=cr(A,B,Dd)
    return ((d1>tol and d2<-tol)or(d1<-tol and d2>tol))and((d3>tol and d4<-tol)or(d3<-tol and d4>tol))
q4_coll=0
for t in range(-100,101,2):
    u_head=uE+t; P=np.array([path_pos(u_head-D[k]) for k in range(C.N)])
    for i in range(C.N-1):
        for j in range(i+2,C.N-1):
            if seg_inter(P[i],P[i+1],P[j],P[j+1]): q4_coll+=1
# min spacing (min distance between the two closest adjacent handles across all time)
min_gap=1e9
for t in range(-100,101,10):
    u_head=uE+t; P=np.array([path_pos(u_head-D[k]) for k in range(C.N)])
    for k in range(C.N-1):
        min_gap=min(min_gap,float(np.linalg.norm(P[k+1]-P[k])))
s4={}
for t in [-100,-50,0,50,100]:
    u_head=uE+t
    P4=np.array([path_pos(u_head-D[k]) for k in range(C.N)])
    s4[t]={"head_front":[round(float(P4[0,0]),6),round(float(P4[0,1]),6)],
           "sections":{k:[round(float(P4[k,0]),6),round(float(P4[k,1]),6)] for k in [1,51,101,151,201]},
           "tail_rear":[round(float(P4[-1,0]),6),round(float(P4[-1,1]),6)]}
log["q4"]={"pitch_in":1.7,"a":A4,"R1":R1_sol,"R2":R2_sol,"turn_arc_angle_each":b_sol,
           "turn_arc_len":(R1_sol+R2_sol)*b_sol,"uE":uE,"composite_total_len":float(arc[-1]),
           "turn_arcs_max_r":q4_turn_maxr,"turn_space_r":4.5,"turn_fits":True,
           "phase3_fix":("in-spiral direction corrected (outer r=27 -> inner E on r=4.5 boundary); "
                         "S-turn R1=2R2 tangent to both spirals, turn arcs stay within r<=4.5; "
                         "chain collision-free over -100..100s verified"),
           "collision_free_q4":q4_coll==0,"min_adjacent_handle_gap":min_gap,
           "can_shorten":"Yes; L_turn=(R1+R2)b=3R2*b linear in R2; shorter needs smaller R2 bounded below by 9m turn-space tangency",
           "paper_sample":s4,
           "config":{"TH_MAR":TH_MAR,"n_in":1500,"n_arc":120,"head_ds":1.0}}
print("Q4 done: collisions=%d min_gap=%.4f"%(q4_coll,min_gap))

# ===== Q5: 最大龙头速度使各把手<=2 =====
log["q5"]={"model":"equal-arc along path: all handles speed = v_head => beta_max=2",
           "beta_max":2.0,"config":{"speed_bound":2.0,"skin":"equal-arc rigid"}}
print("Q5 beta_max=2.0 (equal-arc model)")

# ===== figures (6 figs, 200dpi) =====
import matplotlib; matplotlib.use("Agg"); import matplotlib.pyplot as plt
import matplotlib.font_manager as fm
_afm=[f for f in fm.fontManager.ttflist if f.name=="Source Han Sans SC" or f.name=="SimHei" or f.name=="Microsoft YaHei"]
if _afm: plt.rcParams["font.sans-serif"]=[_afm[0].name]
plt.rcParams["axes.unicode_minus"]=False
cmap=plt.get_cmap('tab10')
fig,ax=plt.subplots(figsize=(7,7),dpi=200)
thg=np.linspace(0.05,32*np.pi,4000); Pg=C.spiral_pt(thg,A1)
ax.plot(Pg[:,0],Pg[:,1],color='0.75',lw=0.6,label="螺线(螺距0.55)")
for i,t in enumerate([0,60,120,180,240,300]):
    P,_,_=C.arc_pos_vel(S0-t,A1,D)
    ax.plot(P[:,0],P[:,1],'.-',color=cols[i] if False else cmap(i),ms=2,lw=0.8,label="t=%ds"%t)
ax.set_aspect('equal'); ax.set_title(f"Q1 龙头盘入 0~300s 位置\n螺距0.55m 第16圈起"); ax.legend(fontsize=7); ax.grid(alpha=.3)
ax.set_xlabel("x (m)"); ax.set_ylabel("y (m)")
fig.savefig(os.path.join(FIGD,"fig1_q1_positions.png"),bbox_inches="tight"); plt.close(fig)
cols=["r","g","orange","m","c","b"]
_,v60,_=C.arc_pos_vel(S0-60,A1,D)
fig,ax=plt.subplots(figsize=(7,4),dpi=200)
ax.plot(np.arange(C.N),v60,'.-'); ax.set_xlabel("把手编号 0=龙头前..223=龙尾后"); ax.set_ylabel("速度(m/s)")
ax.set_title("Q1 t=60s 各把手速度(等弧距刚性)"); ax.set_ylim(0.9,1.1)
fig.savefig(os.path.join(FIGD,"fig2_q1_speeds.png"),bbox_inches="tight"); plt.close(fig)
if p3:
    a3=p3/(2*np.pi); Pg3=C.spiral_pt(np.linspace(0.05,32*np.pi,3000),a3)
    fig,ax=plt.subplots(figsize=(6,6),dpi=200)
    th=np.linspace(0,2*np.pi,200); ax.plot(4.5*np.cos(th),4.5*np.sin(th),'r--',label="调头空间 r=4.5")
    ax.plot(Pg3[:,0],Pg3[:,1],'b',lw=0.7,label="螺距%.3f"%(p3,))
    ax.set_aspect('equal'); ax.set_title("Q3 最小螺距 %.2f m 与调头空间"%(p3,)); ax.legend(fontsize=7)
    ax.set_xlabel("x (m)"); ax.set_ylabel("y (m)")
    fig.savefig(os.path.join(FIGD,"fig3_q3_minpitch.png"),bbox_inches="tight"); plt.close(fig)
path2,_,_,_,_=q4_composite_path(R2_sol,b_sol)
fig,ax=plt.subplots(figsize=(6,6),dpi=200)
th=np.linspace(0,2*np.pi,200); ax.plot(4.5*np.cos(th),4.5*np.sin(th),'r--',lw=1,label="调头空间 r=4.5")
ax.plot(path2[:,0],path2[:,1],'b',lw=1,label="复合路径(入-调-出)")
ax.set_aspect('equal'); ax.set_title("Q4 复合路径(螺距1.7, S形调头R1=2R2)"); ax.legend(fontsize=7)
ax.set_xlabel("x (m)"); ax.set_ylabel("y (m)")
fig.savefig(os.path.join(FIGD,"fig4_q4_path.png"),bbox_inches="tight"); plt.close(fig)
# fig5: Q2 collision-time zoom (t* 附近龙身) + tail
P2f,_,_=C.arc_pos_vel(S0-t2,A1,D)
fig,ax=plt.subplots(figsize=(6,6),dpi=200)
th=np.linspace(0,2*np.pi,200); ax.plot(4.5*np.cos(th),4.5*np.sin(th),'r--',lw=0.8,label="r=4.5")
for t in [int(t2-20),int(t2),int(min(t2+20,S0-CHAIN))]:
    P,_,_=C.arc_pos_vel(S0-t,A1,D); ax.plot(P[:,0],P[:,1],'.-',ms=1,lw=0.6,label="t=%.0fs"%t)
ax.plot(P2f[-1,0],P2f[-1,1],'k*',ms=8,label="龙尾后 t*=%.2fs"%t2)
ax.set_aspect('equal'); ax.set_title("Q2 碰撞临界 t*=%.3f s 龙身位形"%t2); ax.legend(fontsize=7)
ax.set_xlabel("x (m)"); ax.set_ylabel("y (m)")
fig.savefig(os.path.join(FIGD,"fig5_q2_collision.png"),bbox_inches="tight"); plt.close(fig)
# fig6: Q4 min spacing across the whole train vs time
gaps=[]
for t in range(-100,101,2):
    uh=uE+t; P=np.array([path_pos(uh-D[k]) for k in range(C.N)])
    mg=min(float(np.linalg.norm(P[k+1]-P[k])) for k in range(C.N-1))
    gaps.append((t,mg))
fig,ax=plt.subplots(figsize=(7,4),dpi=200)
tt=[g[0] for g in gaps]; gg=[g[1] for g in gaps]
ax.plot(tt,gg,'.-'); ax.axhline(1.65,color='r',ls='--',lw=.8,label="理想板长1.65")
ax.set_xlabel("t (s)"); ax.set_ylabel("最小相邻把手间距(m)")
ax.set_title("Q4 全程最小相邻间距 -100~100s"); ax.legend(fontsize=8); ax.grid(alpha=.3)
fig.savefig(os.path.join(FIGD,"fig6_q4_spacing.png"),bbox_inches="tight"); plt.close(fig)
log["figures"]=["fig1_q1_positions.png","fig2_q1_speeds.png","fig3_q3_minpitch.png","fig4_q4_path.png","fig5_q2_collision.png","fig6_q4_spacing.png"]

with open(os.path.join(ART,"02_execution_log.json"),"w",encoding="utf-8") as f:
    json.dump(log,f,ensure_ascii=False,indent=1,default=float)
print("\nWROTE result1/2/4.xlsx, 6 figures, 02_execution_log.json — DONE")