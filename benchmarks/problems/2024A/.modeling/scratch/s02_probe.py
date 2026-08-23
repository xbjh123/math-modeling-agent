"""s02_probe.py — 检查链的径向结构、最先失效把手、与真实板段相交碰撞时刻"""
import sys; sys.path.insert(0,"../engines")
import numpy as np
import cumcm2024a_solver as M
a=M.PITCH_Q1 if hasattr(M,'PITCH_Q1') else 0.55/(2*np.pi)
a=0.55/(2*np.pi)
s0=M.spiral_arc_length(32*np.pi,a)

def chain_th_failinfo(theta0,a):
    th=np.empty(M.N_HANDLES); th[0]=theta0
    for p in range(M.N_HANDLES-1):
        up=M.chord_backward(M.spiral_pt_f(a), th[p], M.GAPS[p])
        if up is None:
            return None,p,th
        th[p+1]=up
    return th,-1,th

th, failp, partial = chain_th_failinfo(32*np.pi,a)
if th is not None:
    th=np.array(th); r=a*th
    print("t=0 chain OK. head r=%.3f  tail theta=%.3f tail r=%.3f"%(r[0],th[-1],r[-1]))
    print("min r over handles=%.3f at handle id %d"%(r.min(),r.argmin()))
    print("tail(handle223) r=%.3f, neighbour handle222 r=%.3f"%(r[-1],r[-2]))
else:
    print("t=0 recursion FAILED at handle",failp)
    print("partial thetas tail:",partial[-3:] if partial is not None else None)
    if partial is not None:
        pr=a*np.array(list(partial)+[0]); print("where it broke, partial r at last few:",[round(x,3) for x in list(pr)])

# examine tail region geometry at t=0
th0,_=chain_th_failinfo(32*np.pi,a)
th0=np.array(th0); P=M.spiral_pt(th0,a).T
# first non-adjacent segment collision at t=0?
print("\nsegment collision at t=0:", M.first_collision_segment(P, idx_skip=1))

# find when recursion fails (which t) and which handle
print("\nbisect recursion-fail time (head winding inward):")
def ok(t):
    s=s0-t
    th0v=M.inv_spiral_theta(s,a)
    th,fp,_=chain_th_failinfo(th0v,a)
    return th is not None
lo,hi=0,600
for _ in range(60):
    mid=(lo+hi)/2
    if ok(mid): lo=mid
    else: hi=mid
print("recursion-fail critical t*=",round(hi,4))
# failing handle at hi
s=s0-hi; th0v=M.inv_spiral_theta(s,a); th,fp,part=chain_th_failinfo(th0v,a)
print("fail handle id=",fp, " head theta=%.3f r=%.3f"%(th0v,a*th0v))
if part is not None:
    par=np.array(list(part)+[0]); print("last partial r:",[round(x,4) for x in par[-4:]])