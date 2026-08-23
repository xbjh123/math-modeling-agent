import sys; sys.path.insert(0,"../engines")
import numpy as np
import cumcm2024a_solver as M
a=0.55/(2*np.pi)

# --- CHORD model chain at t=0 ---
th=np.empty(M.N_HANDLES); th[0]=32*np.pi; ok=True
for p in range(M.N_HANDLES-1):
    up=M.chord_backward(M.spiral_pt_f(a), th[p], M.GAPS[p], ubracket=np.pi)
    if up is None: ok=False; break
    th[p+1]=up
print("chord chain ok:",ok)
if ok:
    th=np.array(th); r=a*th
    P=M.spiral_pt(th,a).T
    pair=M.first_collision_segment(P)
    print("  chord: min_r=%.3f(handle%d) tail_r=%.3f seg_collide_pair=%s"%(r.min(),r.argmin(),r[-1],pair))

# --- ARC model: handle p at arc s0 - D_p ---
s0=M.spiral_arc_length(32*np.pi,a)
D=np.array([0.0]+[2.86+(p-1)*1.65 for p in range(1,224)])
thA=np.array([M.inv_spiral_theta(max(s0-D[p],1e-9),a) for p in range(224)])
rA=a*thA
PA=M.spiral_pt(thA,a).T
pairA=M.first_collision_segment(PA)
print("ARC model: head_r=%.3f tail_r=%.3f seg_collide_pair=%s (sane if None)"%(rA[0],rA[-1],pairA))
# arc model velocities: all =1
print("  ARC model implies all |v| = 1 m/s (fixed arc offset).")

# Q2: ARC+rigid-chord hybrid: collision = when inner arc model board chord can't fit?
# Let's instead find when ARC-model head theta reaches r where body outer board collides w/ adjacent loop.
# Simple physical criterion: collision when a board (0.3m wide, 1.65 len) on adjacent loop overlaps another.
# We'll just measure 'min radial gap between consecutive arc-adjacent boards spanning loops'.
print("DONE compare")