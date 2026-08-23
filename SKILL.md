---
name: math-modeling-agent
description: 工业级/竞赛级数学建模多智能体协同流水线（CUMCM/MCM）。数据契约摸底 → 6 正交流派 Subagent 发散与具身自验证 → 仲裁打分与公理化规格书 → 确定性引擎全尺寸求解与 Excel 填报 → Model-Critic 三级审计 → 参数化章节并行编纂与 Tectonic 总装编译，全程产物 DAG 持久化于 .modeling/。
---

# 数学建模多智能体协同全景工作流

接获数学建模赛题或科研建模任务时，按以下八阶段状态机执行（Phase 0 → 1 → 2 → 3 → 4 → 5a → 5b）。所有中间状态与产物强制持久化至当前工作区 `.modeling/`，任何阶段不得跳过其前置阶段的产物核验。

## 平台适配（先读我）

本技能平台无关。调度原语按运行环境替换：

| 能力 | Antigravity / Gemini CLI | Claude Code / Cursor | Hermes |
| :--- | :--- | :--- | :--- |
| 并发子代理 | `invoke_subagent` | Task tool 多实例并发 | `delegate_task(tasks=[...])` |
| 文件读写 | 内置文件工具 | Read/Write/Edit | `read_file` / `write_file` / `patch` |
| Python 执行 | 内置代码执行沙盒 | Bash + python | `terminal` / Jupyter kernel |

若当前环境不支持并发子代理，阶段 1 的 6 个探索组退化为**串行逐个加载**对应 roles/*.md 提示词并依次产出草案；阶段 5b 的章节写作同理。禁止因平台能力不足而跳过任何产物。

## 运行模式

| | 实战模式（默认） | benchmark 模式 |
| :-- | :-- | :-- |
| 触发条件 | 用户未声明时 | 工作区存在 `benchmarks/runs/` 调度标记或用户明示 |
| 建模报告审批 | 必须人工批准（阶段 5 门禁） | Model-Critic 代审并记录结论后自动放行 |
| 用途 | 真实参赛交付 | 版本回归评测 / 人机对比 |

## 阶段 0：数据摸底与强类型契约初始化 (Contract Init)

1. 创建标准工作区：`.modeling/{data_contract,scratch,drafts,specs,engines,audit}/`、`.modeling/artifacts/{submissions,figures}/`、`.modeling/manuscript/sections/`
2. 通读赛题原文与附件数据集，构建 `.modeling/data_contract/problem_profile.json`：
   - `scale`：问题规模维度（如 {地块数 I, 品种数 K, 周期数 T} 或 {受试者 n, 观测时点 m}），**必须从赛题实际抽取，禁止预设数值**；
   - `constraints[]`：赛题明示的全部刚性约束清单（每条含编号、数学表述、违反后果）；
   - `deliverables[]`：赛题要求提交的结果文件（Excel 表名、图表、结论形式）；
   - `unknowns[]`：赛题未言明、需向参赛队确认的口径问题。
3. 若附件含数据集：先跑描述统计与缺失值画像，写入 `problem_profile.json` 的 `data_fingerprint` 字段。

## 阶段 1：6 正交流派并发探索与具身自验证 (Divergence & Self-Verification)

1. 按平台适配表并发（或串行退化）调起 6 个独立 Subagent，各自加载对应角色提示词：
   - 联网组 Prior：`roles/online_prior_scout.md` → `drafts/draft_online_prior.md`
   - 联网组 Benchmark：`roles/online_benchmark_miner.md` → `drafts/draft_online_benchmark.md`
   - 断网组 A Mechanistic：`roles/offline_mechanistic.md` → `drafts/draft_offline_mechanistic.md`
   - 断网组 B Optimization：`roles/offline_optimization.md` → `drafts/draft_offline_optimization.md`
   - 断网组 C Stochastic/Survival：`roles/offline_survival_stat.md` → `drafts/draft_offline_survival.md`
   - 断网组 D Robust/QC：`roles/offline_robust_decision.md` → `drafts/draft_offline_robust.md`
2. 全部草案统一遵循《统一微草案协议》（`roles/draft_protocol.md`）。
3. **具身代码自验证铁律**：建模 Agent 在输出任何公式前，必须在 `.modeling/scratch/` 运行 Python/SymPy 微脚本自测（代数求导核验、小规模可行域试解、协方差矩阵半正定性检查），并把运行记录写入草案卡片的"具身自验证记录"栏。无自验证记录的公式视为未经验证。

## 阶段 2：方案仲裁与公理化规格书展开 (Formalization)

1. 调起 `roles/modeling_synthesizer.md` 对 6 份草案做四维量化打分，生成 `.modeling/specs/01a_arbitration_report.md`，确立主模型、基准对照模型与不确定性模块（主备分工，禁止直接丢弃次优草案）。
2. 调起 `roles/deep_formalizer.md`，将选定架构展开为 `.modeling/specs/01_math_formulation.md`：完整符号量纲闭环表、闭式目标函数、理论性质（凸性/KKT/极值条件）、参数辨识伪算法、基准对照模型形式化。杜绝"略、易得、同理可得"。

## 阶段 3：确定性算力引擎全尺寸求解 (Production Engines)

1. 调起 `roles/production_engineer.md` 承担本阶段全部工作。
2. **EDA 图谱**：先向 `.modeling/artifacts/figures/` 导出前置探索性图表（分布画像、相关性热力图、分组对比），数量以赛题实际需要为准，不设固定张数。
3. **全尺寸求解**：按规格书实现求解器，先小规模冒烟再全量运行；强制向 `.modeling/artifacts/submissions/` 导出 `problem_profile.json` 中 deliverables 列明的全部结果文件（Excel 须填满，不留空单元格）。
4. **数值溯源铁律**：所有进入论文的数值（参数估计、CI、检验统计量、目标函数值）必须同步写入 `.modeling/artifacts/02_execution_log.json`（含输入参数、随机种子、求解器配置、收敛标志）。论文中任何无法在 log 中溯源的数字视为幻觉数据。

## 阶段 4：审稿质检与产物 DAG 强核验 (Reviewer-2 Audit)

1. 调起 `roles/model_critic.md`，基于 `references/cumcm_reviewer_pitfalls.md` 对 specs + execution log + submissions 做交叉审计：
   - 代码-公式 100% 对齐审查；
   - 数值溯源校验：抽查论文拟用数值能否在 `02_execution_log.json` 复现；
   - 填报完整性：submissions 文件齐全且无空单元格；
   - 不确定性分析完备性（区间估计 / 灵敏度 / 噪声扰动至少其二）。
2. 输出 `.modeling/audit/03_audit_report.md`，问题按 Level 1（致命阻断）/ Level 2（附辩解放行）/ Level 3（高分亮点清单）三级裁决。存在 Level 1 时回退修复重跑，禁止带病进入阶段 5a。

## 阶段 5a：建模报告撰写与人工审批门禁 (Modeling Report & Gate)

1. 调起 `roles/modeling_reporter.md`，消费规格书、执行日志、submissions 与审计报告，产出面向论文手的交接文档 `.modeling/manuscript/modeling_report.md`（一页速览 + 逐问题思路/计算/结果解读 + 局限辩护 + 符号附录，全部数值带 log 溯源锚点）。
2. **审批门禁（实战模式强制）**：报告置 `STATUS: PENDING_REVIEW` 提交用户审批；仅当用户改为 `STATUS: APPROVED` 后方可进入阶段 5b；`REJECTED` 则按 `> REVIEW:` 意见修订重报。
3. benchmark 模式下由 Model-Critic 代行审批，在 score.md 记录代审结论后放行。

## 阶段 5b：章节规划与并行编纂 (Publication)

1. **先规划后写作**：依据赛题实际问题数生成 `.modeling/manuscript/chapter_plan.json`——每章条目含 chapter_id、title、source_specs、source_logs、target_pages。章节划分必须映射赛题的真实问题结构（例如三问赛题即"引言与EDA / 问题一模型 / 问题二模型 / 问题三模型 / 灵敏度与附录"五分法，两问赛题则四分法），禁止套用任何预设题目结构。Chapter-Writers 的素材以**已批准的 modeling_report.md 为第一输入**（其结论措辞与数值口径必须与报告一致）。
2. 并发调起 N 个 Chapter-Writers（共用角色文件 `roles/chapter_writer.md`，各自领取 plan 中的一个条目），产出 `.modeling/manuscript/sections/<chapter_id>.tex`。
3. **总装编译**：复制 `templates/main_template.tex` 至 `.modeling/manuscript/main.tex`（模板已内嵌 sections/ 占位结构），调用 Tectonic 编译：`tectonic main.tex`。编译错误按日志逐条修复后重跑，直至产出 `paper.pdf`。
4. **合规文件强制导出**：`.modeling/manuscript/AI_Tool_Disclosure.md`（基于 `templates/ai_disclosure_template.md` 按队伍真实使用情况填写）。此文件为编译完成后的**硬性验收项**：缺失即视为阶段 5b 未完成，须补齐后重新核验（auto_checks compliance 项会扣 4 分）。

## 全局铁律（贯穿所有阶段）

1. **产物 DAG 契约**：下游角色只消费上游落盘产物（草案→仲裁报告→规格书→执行日志→审计报告→章节 tex），口头传递一律无效。
2. **数值防幻觉**：论文中每个数字必须能在 `02_execution_log.json` 中溯源；Model-Critic 抽查复算。
3. **反过拟合统计纪律**：数据驱动的结构选择（切点、分组、变量筛选）必须附显著性检验或交叉验证证据，禁止在纯噪声上构造显著性；惩罚/正则超参数须做灵敏度说明。
4. **竞赛合规红线**：匿名性（无学校/姓名/赛区信息）、无目录页、摘要独立成页、主节"一、二、三、"编号；AI 使用声明按 2026 试行规定如实填写。
5. **失败诚实原则**：求解器不收敛、检验不显著、编译报错，均如实写入对应产物文件，禁止静默跳过或编造成功状态。

## 环境依赖

- Python ≥3.10：numpy / pandas / scipy / statsmodels（scripts/ 工具箱）
- Tectonic（LaTeX 总装编译）或 XeLaTeX + ctex 备选
- 联网组两个角色需要网络搜索工具，断网环境下自动降级为纯离线四流派（在仲裁报告中注明联网组缺席）

## scripts/ 确定性算法工具箱

| 脚本 | 用途 | 关键接口 |
| :--- | :--- | :--- |
| `greedy_segmentation.py` | 有序特征异质性贪心切分（max-T 置换检验停止准则，控制假切点率） | `greedy_ordered_partition(df, split_col, x_col, y_col, random_state=...)` |
| `lmm_variance_decomp.py` | LMM 拟合与方差分解（支持多随机效应，REML） | `fit_lmm_with_variance_decomposition(df, formula, group_col, re_formula)` |
| `robust_qc_3zone.py` | 非参数质控 + MAD 质量指数 + 三区双阈值判定 | `non_parametric_quality_control(...)` / `compute_quality_index_and_zones(...)` |
| `cluster_bootstrap.py` | 簇级 Bootstrap CI 与 MAD 噪声扰动分析（含失败率监控） | `cluster_bootstrap_ci(...)` / `mad_perturbation_analysis(...)` |

调用约定：全部函数带 `random_state` 参数保证可复现；返回值中的 `warning` 字段非空时必须在审计报告中说明。

