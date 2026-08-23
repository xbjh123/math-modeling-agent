# 统一微草案协议 (Unified Micro-Draft Protocol)
# Input: 赛题原文与 .modeling/data_contract/problem_profile.json（问题画像与数据契约）
# Output: .modeling/drafts/draft_<流派>.md（6 个探索型 Subagent 的统一输出卡片）
# 适用: roles/ 下全部 6 个探索型角色（online_prior_scout / online_benchmark_miner / offline_mechanistic / offline_optimization / offline_survival_stat / offline_robust_decision）

## 协议目的
让 6 个正交流派的草案在同一「卡片结构」下产出，便于后续仲裁专家（modeling_synthesizer）横向打分、跨流派融合与主备模型分工。严禁只写泛泛思路或跳步给出结论。

## 每份微草案的固定卡片结构
1. **问题画像摘要**：用 2-3 句话概括赛题要解决的决策/预测/评价问题，明确自变量的可观测集合与结果变量的定义。
2. **建模流派与模型族**：声明本派立场，列出拟采用的模型族（如 LMM/ODE/MILP/CVaR 等），并说明为何该范式最契合问题画像。
3. **目标函数与核心约束**：以**闭式公式**给出目标函数与全部刚性约束（含符号定义、下标与取值范围），公式必须可直接进入后续公理化规格书。
4. **所需数据字段映射**：用表格列出模型每个参数/变量所需的原始数据字段，映射到 problem_profile.json 中的字段名，并标出缺失或需清洗的字段。
5. **具身自验证记录**：列出在 `.modeling/scratch/` 实际跑过的 Python/SymPy 脚本（文件名 + 一句话作用）、关键数值结论（如代数闭合通过、MILP 小样本可解、无 Infeasible）。凡未跑过的公式不得声称已验证。
6. **风险与消融钩子**：指出该方案最可能被评委质疑的点，并为每个质疑点给出对照实验/消融建议（如去掉某约束、换基准模型、扰动参数），供仲裁阶段设计主备分工。

## 硬性要求
- 卡片 6 部分**缺一不可**，按以上顺序组织，用 `##` 与编号写清。
- 所有数值/结论必须来自 scratch/ 实际脚本输出，禁止臆造；无数据支撑处显式标注「未验证」。
- 目标函数与约束用 LaTeX 行内公式书写，保持闭式、可复现。