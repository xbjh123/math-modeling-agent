import sys; sys.path.insert(0,"../engines")
import numpy as np
import cumcm2024a_solver as M
a=0.55/(2*np.pi); s0=M.spiral_arc_length(32*np.pi,a)

def chain_chord(theta0):
    th=np.empty(M.N_HANDLES); th[0]=theta0
    for p in range(M.N_HANDLES-1):
        up=M.chord_backward(M.spiral_pt_f(a), th[p], M.GAPS[p], ubracket=np.pi)
        if up is None: return None
        th[p+1]=up
    return th

def collide(t):
    s=s0-t
    th0=M.inv_spiral_theta(s,a)
    th=chain_chord(th0)
    if th is None: return ("recfail",None)
    P=M.spiral_pt(th,a).T
    pair=M.first_collision_segment(P)
    return (pair if pair is not None else None, pair)

# scan coarse
print("coarse scan (0..400 step 5):")
for t in range(0,410,5):
    r=collide(t)
    if r[0] is not None:
        print("  first event at t=",t,r); break
else:
    print("  none in 0..400")
# refine around
def first_event():
    # binary search between lo(ok) and hi(event)
    lo,hi=0,400
    for _ in range(60):
        mid=(lo+hi)/2
        if collide(mid)[0] is None: lo=mid
        else: hi=mid
    return hi
te=first_event()
print("bisect first event t*≈%.3f"%te)
print("at t*:",collide(te))
# how far head moved
s=s0-te; th0=M.inv_spiral_theta(s,a)
print("at t* head theta=%.3f r=%.3f (loop %.2f)"%(th0,a*th0,th0/(2*np.pi)))
# inner end radius at t*
th=chain_chord(th0)
if th is not None:
    th=np.array(th); r=a*th
    print("min r=%.3f at handle %d, tail r=%.3f"%(r.min(),r.argmin(),r[-1]))