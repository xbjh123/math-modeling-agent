# 数学规格书 (Math Formulation) — CUMCM 2024 A "板凳龙"
> 角色: deep_formalizer. 消费仲裁报告, 展开主模型与基准的完整符号/公式/性质/伪算法.

## 1. 符号与量纲闭环表
| 符号 | 意义 | 量纲/单位 | 值 |
|---|---|---|---|
| \(p\) | 螺距 | m | 0.55 (Q1/Q2), 1.7 (Q4), Q3待求 |
| \(a\) | 螺线尺度 \(a=p/2\pi\) | m/rad | 0.087535 / 0.270563 |
| \(r,\theta\) | 极坐标 | m, rad | — |
| \(L_h\) | 龙头孔距 | m | 2.86 |
| \(L_b\) | 龙身/尾孔距 | m | 1.65 |
| \(w\) | 板宽 | m | 0.30 |
| \(N\) | 把手中心数 | 1 | 224 (0=龙头前,…,223=龙尾后) |
| \(D_i\) | 把手 i 距龙头前把手弧长偏移 | m | \(0,(L_h,L_b,\dots)\) 累和, \(D_{223}=369.16\) |
| \(s(\cdot)\) | 螺线弧长 | m | 闭式 |
| \(s^{-1}(\cdot)\) | 逆弧长 | rad | 二分 |
| \(s_{\rm head}\) | 龙头前把手弧长 | m | \(S_0-t\) |
| \(S_0\) | 初始弧长 | m | 442.59026 |
| \(\mathbf p_i\) | 把手 i 位置 | m | — |
| \(\mathbf v_i\) | 把手 i 速度 | m/s | — |
| \(t^*\) | Q2 终止时刻 | s | 待求 |
| \(p^*\) | Q3 最小螺距 | m | 待求 |
| \(\beta_{\max}\) | Q5 龙头最大速度 | m/s | 待求 |
| \(R_2,R_1\) | 调头两圆弧半径 | m | \(R_1=2R_2\) |

## 2. 螺线几何
\[ r=a\theta,\quad x=a\theta\cos\theta,\;y=a\theta\sin\theta,\quad a=\frac{p}{2\pi}.\]
弧长闭式（精确，非数值积分）：
\[ s(\theta)=a\int_0^\theta\sqrt{1+u^2}\,du=\frac{a}{2}\Big[\theta\sqrt{1+\theta^2}+\operatorname{asinh}\theta\Big].\]

## 3. 主模型（等弧距刚性铺排）
位置：
\[ \theta_i(t)=s^{-1}\!\big(S_0-t-D_i\big),\qquad S_0=s(32\pi),\quad i=0,\dots,223,\]
\[ \mathbf p_i(t)=a\,\theta_i(t)\big(\cos\theta_i(t),\ \sin\theta_i(t)\big).\]
速度（龙头驱动 |ds/dt|=1，弧速沿链=1）：
\[ \mathbf v_i=\frac{\partial \mathbf p_i}{\partial s_{\rm head}}\cdot\frac{ds_{\rm head}}{dt},\qquad v_i=\|\mathbf v_i\|,\quad v_0=1.00\ \text{m/s}.\]
主模型下所有把手弧速=1（等弧距刚性位移），故 Q5 得 \(\beta_{\max}=2\)。

## 4. 基准模型（刚性弦长链）
相邻把手欧氏距离=板长：\( \|\mathbf p_{i+1}-\mathbf p_i\|=L_i\). 对龙头弧速1，把手 i 弧速由
\[ \frac{d}{dt}\|\mathbf p_{i+1}-\mathbf p_i\|^2=0
\;\Rightarrow\; (\mathbf p_{i+1}-\mathbf p_i)\cdot(\partial_s\mathbf p_{i+1}\dot\theta_{i+1}-\partial_s\mathbf p_i\dot\theta_i)=0\]
递推解出（顺链传播 \(\dot\theta_0\)）。该基准给出随曲率变化的非均匀速度幅值，用于 Q5 保守上界与灵敏度对照。

## 5. 目标函数与判据
- **Q2 终止时刻**：\[ t^*=\min\big\{\,t: s_{\rm head}(t)\le D_{223}\ \text{或}\ \exists\ \text{非相邻板段相交}\,\big\}.\]
- **Q3 最小螺距**：\[ p^*=\min p \text{ s.t.相邻两圈径向间隙 }p−w>0,\quad w=0.30\text{ m(板宽)}.\]
  - *修正说明*：原规格书"尾不越过中心"判据 \[ s^{-1}(s(\tfrac{2\pi\cdot4.5}{p})-D_{223})>0 \] 在任意螺距下均不可满足：r≤4.5 内螺线最大弧长 ≈212m << 链长 369m，链在 r>4.5 外自然继续盘绕，尾把手本就不从中心穿越。故该判据错误，弃用；保留真实物理下界（相邻圈板宽间隙）。
- **Q4 调头**：盘入螺线(螺距1.7)入口 \(E\) 位于 r=4.5 边界；盘出螺线(中心对称)=\(-P(\theta)\)，出口 \(X=-E\) 亦在 r=4.5。S形两圆弧 \[ R_1=2R_2,\quad R_2=1.5027\text{ m},\ R_1=3.0054\text{ m},\ \Delta=3.0215\text{ rad}\] 前段切入螺线于E、后段切出螺线于X，两圆外切，路径全程 r≤4.5。路径弧长 \(L_{\rm turn}=(R_1+R_2)\Delta=3R_2\Delta\)，减小 R2 可缩短，下限由 4.5m 空间与相切约束决定。
- **Q5**：\(\beta_{\max}=2/\max_{t,i}\|\partial_s\mathbf p_i\|\)。

## 6. 理论性质
- \(s(\theta)\) 严格单调、凸（\(s'(\theta)=a\sqrt{1+\theta^2}>0\)），故 \(s^{-1}\) 唯一、数值稳定。
- 主模型位置随 \(t\) 光滑；速度幅值在有界曲率下一致有界；等弧距下 \(\partial_s\mathbf p_i\) 为单位切向量 → \(v_i\equiv1\)。
- 二分求根线性收敛至机器精度；事件 \(t^*\) 在区间内单穿（s 单调）。

## 7. 参数辨识/求解伪算法
```
Q1: for t in 0..300:
      s_h = S0 - t
      for i in 0..223: theta_i = inv_arc(s_h - D_i); p_i = a*theta_i*(cos,sin)
      v_i = |(p_i(s_h+h)-p_i(s_h))/h|, h=1e-7
    save result1.xlsx
Q2: bisect t* in [0,S0-D223]: predicate = (s_h<=D223) or segments_intersect()
    result2.xlsx at t*
Q3: bisect p in [0.1,3]: feasible(p) = tail_not_center && no self-intersect at head_r=4.5
Q4: build composite path (in-spiral + S(2 arcs) + centered-symmetric out-spiral); arc-length param;
    for t in -100..100: place handles at arc offsets behind head; save result4.xlsx
Q5: beta_max = 2 / max_{t,i} |d p_i / d s|; baseline-chord gives conservative bound
```
**数值约束**：逆弧长 500 次二分（残差~1e-14）；速度差分 h=1e-7；碰撞段相交双线性 tol=1e-9；输出 6 位小数，全部数值入 02_execution_log.json。