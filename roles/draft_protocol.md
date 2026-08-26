# 方向卡片协议 (Direction Card Protocol)
# Input: 赛题原文与 .modeling/problem_profile.json（问题画像）
# Output: .modeling/drafts/draft_<方向>.md（各流派 Subagent 的方向卡片）
# 适用: roles/ 下全部探索型角色（mechanistic / optimization / survival / robust / prior / benchmark）

## 协议目的
让各正交流派在同一「方向卡片」结构下产出，便于 Actor-Critic 精炼阶段横向比较与选型。**只做方向引导，不做强制验证。**

## 每份方向卡片的三部分结构
1. **建模哲学**：用 2 句话概括本派为何契合该题，明确本派的立场（如"机理演化"或"离散优化"）。
2. **拟用模型族**：列出本派拟采用的候选模型（如 LMM/ODE/MILP/CVaR/时间序列），并给出一句适用理由。
3. **关键难点**：指出该方案最可能被评委质疑的一个点，并给出一句话化解策略（供 Critic 阶段参考）。

## 约束
- 只写这三部分，**不要求**目标函数闭式、不要求自验证记录、不要求数据字段映射。
- 公式与结论允许先用直觉表述，具体化交给 Actor-Critic 精炼阶段。
- 目标函数/符号的具体展开，在阶段 2 由 Actor 统一落到 specs。
