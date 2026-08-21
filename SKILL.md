---
name: math-modeling
description: 工业级/竞赛级数学建模多智能体协同流水线。支持从数据摸底、具身内嵌自验证的6正交Subagent发散、全尺寸大规模规划求解与Excel填报、Model-Critic审稿质检，到5章节并行编纂与Tectonic编译30+页国奖级学术论文的一站式全流程自动化交付。
---

# 数学建模多智能体协同全景工作流 (Mathematical Modeling Orchestration Pipeline)

当你接获数学建模赛题或科研建模任务时，严格按照以下三层解耦与六阶段状态机执行。所有中间状态与产物强制持久化至当前工作区的 `.modeling/` 目录。

---

## 阶段 0：数据摸底与强类型契约初始化 (Phase 0: Contract Init)
1. 创建标准工作区目录结构：
   - `.modeling/data_contract/`、`.modeling/scratch/`、`.modeling/drafts/`、`.modeling/specs/`、`.modeling/engines/`、`.modeling/artifacts/submissions/`、`.modeling/artifacts/figures/`、`.modeling/manuscript/sections/`
2. 读取用户提供的赛题文档与附件数据集，构建强类型契约文件 `.modeling/data_contract/problem_profile.json`，明确定义地块数 $I$、品种数 $K$、周期数 $T$、季次数 $S$ 及 12 项刚性农艺/物理约束。

---

## 阶段 1：6 正交 Subagent 并发探索与具身自验证 (Phase 1: Divergence & Self-Verification)
1. 使用 `invoke_subagent` 并发调起 6 个独立沙盒 Subagent（加载 `Zero-Lazy Policy`）：
   - **联网组 1 (Prior)**：加载 `roles/online_prior_scout.md` $\to$ 生成 `drafts/draft_online_prior.md`
   - **联网组 2 (Benchmark)**：加载 `roles/online_benchmark_miner.md` $\to$ 生成 `drafts/draft_online_benchmark.md`
   - **断网组 A (Mechanistic)**：加载 `roles/offline_mechanistic.md` $\to$ 生成 `drafts/draft_offline_mechanistic.md`
   - **断网组 B (Optimization)**：加载 `roles/offline_optimization.md` $\to$ 生成 `drafts/draft_offline_optimization.md`
   - **断网组 C (Stochastic/Survival)**：加载 `roles/offline_survival_stat.md` $\to$ 生成 `drafts/draft_offline_survival.md`
   - **断网组 D (Robust/Correlation)**：加载 `roles/offline_robust_decision.md` $\to$ 生成 `drafts/draft_offline_robust.md`
2. **具身代码自验证铁律**：建模 Agent 在输出任何公式前，必须在 `.modeling/scratch/` 运行 Python/SymPy 微脚本自测（验证代数求导、小样本可行域与矩阵半正定性）。

---

## 阶段 2：方案仲裁与公理化规格书展开 (Phase 2: Formalization)
1. **仲裁打分**：调起 `roles/modeling_synthesizer.md` 进行四维打分，生成 `.modeling/specs/01a_arbitration_report.md`，确立主模型与基准对比模型。
2. **深度展开**：调起 `roles/deep_formalizer.md`，展开包含完整证明、对数似然、KKT 条件与 12 项方程的 `.modeling/specs/01_math_formulation.md`。

---

## 阶段 3：确定性算力引擎全尺寸求解 (Phase 3: Production Engines)
1. **EDA 图谱引擎**：运行 `scripts/eda_cartography_suite.py`，向 `.modeling/artifacts/figures/` 导出 5~8 张前置探索性图表（双层饼图、梯形收益图、相关性热力图）；
2. **大规模求解引擎**：运行求解器，**强制向 `.modeling/artifacts/submissions/` 导出赛题要求的完整 Excel 填报文件（`result1_1.xlsx`、`result1_2.xlsx`、`result2.xlsx`）**，并生成逐年空间排产全景热力图；
3. **灵敏度与不确定性引擎**：运行 $S=1000$ 蒙特卡洛模拟，生成 CVaR 尾部分布与 729 点全域灵敏度响应面。
4. 保存全部运行数值与参数估计日志至 `.modeling/artifacts/02_execution_log.json`。

---

## 阶段 4：审稿质检与产物 DAG 强核验 (Phase 4: Reviewer-2 Audit)
1. 调起 `roles/model_critic.md`，基于 `references/cumcm_reviewer_pitfalls.md` 进行阻断性审查：
   - 检查 `submissions/*.xlsx` 是否填满且满足 0.5 面积下限；
   - 检查公式-代码-表格数据是否 100% 对应；
   - 检查是否包含 4 张以上高分辨率矢量图与方差分解/置信区间。
2. 输出 `.modeling/audit/03_audit_report.md`，确认无 Level 1 致命错误后放行。

---

## 阶段 5：5 章节并行编纂与 Tectonic 模块化总装 (Phase 5: Publication)
1. 并发调起 5 个专职 Chapter-Writers 撰写各子章节：
   - `Writer-Ch1` $\to$ 生成 `.modeling/manuscript/sections/01_intro_eda.tex` (6-8页，含完整符号表与详尽 EDA)
   - `Writer-Ch2` $\to$ 生成 `.modeling/manuscript/sections/02_problem1_milp.tex` (8-10页，含严格证明与逐地块排产)
   - `Writer-Ch3` $\to$ 生成 `.modeling/manuscript/sections/03_problem2_cvar.tex` (8-10页，含 CVaR 极值证明与风险分布)
   - `Writer-Ch4` $\to$ 生成 `.modeling/manuscript/sections/04_problem3_corr.tex` (6-8页，含互作矩阵与协方差对冲)
   - `Writer-Ch5` $\to$ 生成 `.modeling/manuscript/sections/05_sensitivity_app.tex` (6-8页，含灵敏度、合规声明与代码附录)
2. **总装编译**：使用 `templates/main_template.tex` 模块化拼接，调用 `C:\tools\bin\tectonic.exe` 编译生成 30+ 页高水平论文 `.modeling/manuscript/paper.pdf`；
3. 导出 2026 官方合规文件 `.modeling/manuscript/AI_Tool_Disclosure.md`。
