import numpy as np
from scipy.optimize import fsolve
A4=1.7/(2*np.pi); TH_MAR=100.0
def solve_R2(A4, TH_MAR):
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
        J=C1+R1*np.array([np.cos(a0-b),np.sin(a0-b)])
        c,s=np.cos(-b),np.sin(-b); vJ=np.array([c*v_out[0]-s*v_out[1],s*v_out[0]+c*v_out[1]])
        nvJ=np.array([-vJ[1],vJ[0]])
        C2=J+R2*nvJ
        aJ=np.arctan2((J-C2)[1],(J-C2)[0])
        return C2+R2*np.array([np.cos(aJ+b),np.sin(aJ+b)])
    f=lambda z: np.array([serp_end(2*z[0],z[0],z[1])[0]-X[0], serp_end(2*z[0],z[0],z[1])[1]-X[1]])
    out=fsolve(f,[1.0,0.5],full_output=True)
    sol,info,ier,msg=out
    print("ier=",ier,"msg=",msg,"sol=",np.asarray(sol).ravel())
    return sol
try:
    print(solve_R2(A4,TH_MAR))
except Exception as e:
    import traceback; traceback.print_exc()