import numpy as np, sys
from scipy.optimize import fsolve
a4=1.7/(2*np.pi); thE=4.5/a4
def Pin(th):
    r=a4*th; return np.array([r*np.cos(th),r*np.sin(th)])
def dPin(th):
    r=a4*th
    return a4*np.array([np.cos(th)-th*np.sin(th), np.sin(th)+th*np.cos(th)])
def s_arc(th,a):
    t=np.asarray(th,dtype=float); return a/2*(t*np.sqrt(1+t*t)+np.arcsinh(t))
def make_path(TH_MAR=100.0):
    E=Pin(thE); X=-E
    din=dPin(thE); v=din/np.linalg.norm(din); v_out=-v
    n=np.array([-v_out[1],v_out[0]])
    th_in=np.linspace(TH_MAR,thE,1500)
    Pin_=np.array([Pin(t) for t in th_in])
    R2=1.5027; R1=2*R2; b=3.021
    C1=E+R1*(-n)
    a0=np.arctan2((E-C1)[1],(E-C1)[0])
    arc1=[C1+R1*np.array([np.cos(a0-k*b/59),np.sin(a0-k*b/59)]) for k in range(60)]
    J=arc1[-1]
    c,s=np.cos(-b),np.sin(-b); vJ=np.array([c*v_out[0]-s*v_out[1],s*v_out[0]+c*v_out[1]])
    nvJ=np.array([-vJ[1],vJ[0]])
    C2=J+R2*nvJ
    aJ=np.arctan2((J-C2)[1],(J-C2)[0])
    arc2=[C2+R2*np.array([np.cos(aJ+k*b/59),np.sin(aJ+k*b/59)]) for k in range(60)]
    th_out=np.linspace(thE,TH_MAR,1500)
    Pout=np.array([-Pin(t) for t in th_out])
    path=np.vstack([Pin_,np.array(arc1),np.array(arc2),Pout])
    return path,E,X
TH_MAR=100.0
path,E,X=make_path(TH_MAR)
arc=np.concatenate([[0],np.cumsum(np.linalg.norm(np.diff(path,axis=0),axis=1))])
iE=np.argmin(np.linalg.norm(path-E,axis=1)); uE=arc[iE]
print("total path len=%.2f uE=%.2f"%(arc[-1],uE))
CHAIN=369.16
print("tail arc at head t=-100: uE-100-CHAIN=%.1f (need>=0)"%(uE-100-CHAIN))
print("head reachable u=[%.0f,%.0f] within [0,%.0f]?"%(uE-100,uE+100,arc[-1]))
N=224; D=np.array([0.0]+[2.86+(k-1)*1.65 for k in range(1,224)])
def path_pos(u):
    i=int(np.searchsorted(arc,u,side='right'))-1;i=max(0,min(len(path)-2,i))
    f=(u-arc[i])/max(arc[i+1]-arc[i],1e-12)
    return path[i]+f*(path[i+1]-path[i])
def seg_inter(A,B,C,Dd,tol=1e-9):
    def cr(o,p,q): return (p[0]-o[0])*(q[1]-o[1])-(p[1]-o[1])*(q[0]-o[0])
    d1=cr(C,Dd,A);d2=cr(C,Dd,B);d3=cr(A,B,C);d4=cr(A,B,Dd)
    return ((d1>tol and d2<-tol)or(d1<-tol and d2>tol))and((d3>tol and d4<-tol)or(d3<-tol and d4>tol))
def coll(P):
    for i in range(N-1):
        for j in range(i+2,N-1):
            if seg_inter(P[i],P[i+1],P[j],P[j+1]): return (i,j)
    return None
bad=0
for t in range(-100,101,2):
    uh=uE+t; P=np.array([path_pos(uh-D[k]) for k in range(N)])
    c=coll(P)
    if c: bad+=1; print("collision t=%d pair=%s"%(t,c))
print("collision checks: %d bad of %d"%(bad,len(range(-100,101,2))))
mi=1e9
for t in range(-100,101,10):
    uh=uE+t; P=np.array([path_pos(uh-D[k]) for k in range(N)])
    for k in range(N-1):
        mi=min(mi,np.linalg.norm(P[k+1]-P[k]))
print("worst adjacent-handle euclidean gap over -100..100 = %.4f m"%mi)