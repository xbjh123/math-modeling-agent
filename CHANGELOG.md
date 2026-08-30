# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Added (2026-08-30 2022A 轮 RCA 后的四条门禁加固)

- 背景：2022A Q2(2) 初版结论（α*=0）被对比测评推翻（近似论证误差与判决量同阶 + 切片证据覆盖不全 + 优化全局性无门禁 + Critic 任务书被被审者框定），SKILL.md 四处最小改动：
  - **阶段0**：题意基线逐条附题面原文逐字引用，提示词/摘要与原文冲突以原文为准（本轮幂律口径两道门禁漏检的根因）；
  - **阶段2（3.5）**：判决性论证分级——全局性结论的论证须标级（精确证明 > 全空间收敛扫描 > 近似论证），近似论证声明误差 < 被判定差异 1/3 否则只作佐证；可选外部证据参照（历年论文/文献结论对照）；
  - **阶段3（1.5）**：优化题全局性门禁——快/慢评估 ≥3 点定标（偏差超候选间隔 1/3 即快评估失格）、最优点及邻域收敛档复评、边界最优报 unconstrained 最优+松弛走势；
  - **阶段4**：Critic 任务书由题型检查单生成、不由被审者起草；优化题固定含独立重寻优/边界检查/定标抽查；固定任务"主动寻找与主结论相反的证据"。

### Changed (2026-08-29 论文编写层架构重做)

- **论文编写从"串行写作"重构为"规划→写作→结构审校"三段式**（对齐 2025A 对比国奖论文 A196 的差距归因：写作层三处结构性缺失——每问缺策略规律提炼段/缺参考文献节/缺精确归约定理）：
  - **新增"论文结构蓝图"层**：`references/paper_structure.md` 定义 `paper_blueprint.md` 固定格式（全篇章节树 + 每问固定六项子结构：模型/求解/结果/**策略规律**/亮点/判据示意 + 参考文献席 + 定理/命题清单 + 跨问递进承接句 + 结构自检表）。**没有蓝图不进入写作**。
  - **新增 `roles/paper_planner.md`（5b-1 蓝图规划）**：写作前产出 `.modeling/manuscript/blueprints/paper_blueprint.md`，把"论文必须有什么"从 chapter_writer 的一行提示词固化为一整张装配图。
  - **改造 `roles/chapter_writer.md`（5b-2 正文写作）**：从"写段落"升级为"对照蓝图填段"，A196 三优势（策略规律/参考文献/判据归约）从提示词变成**必填字段**；参考文献**禁编造**，来源以蓝图参考文献席为准。
  - **新增 `roles/paper_structural_reviewer.md`（5b-3 结构审校，🔴 门禁）**：对照蓝图逐项核对兑现度，缺一项即回退重写，**不带着缺结构进入最终交付**；与 model_critic（数值对错）职责分离。
  - **重做 `templates/main_template.tex` + `templates/sections/`**：章节化名不再硬编码题型（milp/cvar/corr），改为通用占位（`01_intro_assump` / `template_problem_chapter` / `07_sensitivity_conclusion`），章节树与 blueprint 对齐；新增"参考文献"节骨架。
  - **`scripts/run_pipeline.py`**：`manuscript/blueprints` 入 `STD_DIRS`；`phase5_write` 拆为 `phase5a_report`/`phase5b_plan`/`phase5c_write`/`phase5d_structural` 四动作槽，门禁与目录与 SKILL 阶段 5 对齐。
  - **`SKILL.md` 阶段 5**：改为"建模报告 → 论文蓝图 → 论文正文 → 结构审校"四步（原两步），批判纪律新增 **A196 对比回灌**三条。
- 说明：本次改动**只动了仓库内角色/模板/流程**，未改 Hermes 侧 `math-modeling` skill 载体；下次跑题自动走新架构。

### Fixed (2026-08-28 2024A 回灌恢复)

- **以轻量形式恢复被精简重构（0746c63）随重型审计一并裁掉的 2024A 回灌条款**（来源题目与证据：`benchmarks/runs/2024A/20260823_first_baseline/human_comparison.md` 差异归因表 #1/#4、`score.md` 首轮发现 #3；原条款见提交 1121054）：
  - `roles/model_critic.md` 新增两条强制回灌纪律——**答案共识性校验**（对照 `reference_answers.json` 共识值或第二种独立方法交叉验证，自洽≠正确）与**约束满足性数值扫描**（约束易违背处独立抽查，不只信引擎自报的满足标志）；"不做的"清单同步改为不做*全量*逐点交叉审计。
  - `roles/deep_formalizer.md` 判据溯源从"尽量"升回**强制**（引题面原文 + 多解读显式讨论），新增**理论性质必须尝试、不适用须说明**；仍不做 KKT/公理化推导，维持精简取向。
  - `SKILL.md` 阶段 2 / 阶段 4 措辞同步（轻审稿三件事 → 四件事）。
  - offline_optimization / offline_mechanistic 两派回灌条款与 `benchmarks/problems/2024A/reference_answers.json`、`auto_checks.py` answer_check 已在 1121054 / 0746c63 落地，本轮核验未动。

### Added (2026-08 精简重构)

- **第 7 个探索流派**：`roles/offline_prediction_ml.md`（预测/机器学习派），补全 HMML 方法覆盖（ARIMA/灰色GM/SVM/K-means/PCA/Boosting 等）。
- **HMML 方法库**：`references/method_library.md`（取自 MM-Agent 的 HMML，约 98 个方法）。
- **方法检索脚本**：`scripts/method_retrieve.py`——关键词/概念匹配从 HMML 检索相关方法，带 `school` 归属流派，落盘 `00_retrieval.json` 供 subagent 消费。
- **健康与适配检测**：`scripts/health_check.py`——首次运行检测环境/库/工具、scripts 冒烟、HMML 检索→落盘→读回最小流程链路、SKILL 引用完整性。
- **开源调研文档**：`references/open_source_agent_ideas.md`（开源科研 agent 框架调研 + MM-Agent 论文精读）。

### Changed (2026-08 精简重构)

- **SKILL.md 精简为六阶段流水线**：数据摸底 → HMML 方法检索定向发散 → Actor-Critic 精炼 → 求解 → 轻审稿 → 串行写作；默认走最短路径，严谨只在必要时才上。
- **方向卡片协议**（`draft_protocol.md`）：六部分 → **三部分**（建模哲学 / 拟用模型族 / 关键难点），去掉强制自验证与数据字段映射。
- **建模精炼**（`modeling_synthesizer.md`）：四维打分矩阵 + 主备分工 → **Actor-Critic 迭代精炼**（actor 出方案 + critic 反馈 + 2 轮收敛）。
- **规格书**（`deep_formalizer.md`）：公理化五模块 + KKT/凸性证明 → **三块**（符号表 / 闭式目标 / 关键假设），去掉不必要的理论性质证明。
- **审稿**（`model_critic.md`）：四级交叉审计 + Level 1/2/3 裁决 → **一轮轻审稿**（合理性 / 可复现 / 填满），不做交叉审计与约束逐点扫描。
- **写作**（`chapter_writer.md`）：5 章节并行编纂 → **串行逐段写作**（按问题顺序）。
- **求解**（`production_engineer.md`）：数值溯源全套 log + 推导常量入 log → **轻纪律**（关键数字可复现一次运行即可）。
- **建模报告**（`modeling_reporter.md`）：逐问题详解 + log 锚点自检 → **一页速览 + 逐问题要点**。
- **scripts 工具箱**：新增 `method_retrieve.py`、`health_check.py`。

### Fixed

- **索引覆盖**：`method_retrieve.py` 的 `METHOD_INDEX` 补全至覆盖 HMML 全部约 96-98 个方法，并修正中英关键词匹配（统计检验/决策/分类类题目此前命中不全）。
- **仓库清理**：`.gitignore` 忽略 `.modeling` 运行产物（含 `_runN` 变体），从版本库移除既往误提交的 `.modeling` 文件（磁盘保留）。

---

## [Earlier Unreleased]（此前积压条目）

- **3 个新角色文件**：`roles/chapter_writer.md`（章节并行编纂）、
  `roles/draft_protocol.md`（统一微草案协议）、`roles/production_engineer.md`
  （阶段 3 确定性算力引擎）。
- **模板 sections 占位结构**：`templates/sections/01..05_*.tex` 五个分节占位文件，
  配套主模板 `main_template.tex` 的模块化 `\input` 总装结构。
- **测试套件**：`tests/` 收编原回归脚本并改造为 pytest 风格（`test_scripts.py`），
  新增 `test_templates.py`（模板合规/完整性）与 `test_skill_integrity.py`
  （SKILL.md 引用文件防悬空），附 `tests/README.md`。
- **CI**：`.github/workflows/ci.yml` —— push/PR(main) 触发，pytest 全量 +
  Tectonic 中文模板编译冒烟（页数断言）。
- **benchmarks 框架占位**：预留基准评测目录结构框架（尚未落盘实现）。

### Changed

- **SKILL.md 重写**：去硬编码（赛题规模/题目结构不再预设数值），新增平台适配表
  （Antigravity/Gemini CLI、Claude Code/Cursor、Hermes），并把阶段 5 拆分为
  “先规划后写作 + 并行编纂 + 总装编译”三小节。
- **`greedy_segmentation.py`**：停止准则由固定增益阈值改为 **max-T 置换检验**，
  强化对同质/噪声数据的假切点控制。
- **`lmm_variance_decomp.py`**：多随机效应方差改为按协方差矩阵对角线求和进入分解，
  并增加求解器收敛重试逻辑。
- **`cluster_bootstrap.py`**：`point_estimate` 改为原始完整样本点估计；记录
  `failed_replications` / `failure_rate`；新增 `random_state` 保证可复现。
- **`robust_qc_3zone.py`**：返回键名规范化（`n_samples`/`z_lo`/`z_hi`/
  `decision_rule`），NaN 防护（MAD 尺度与分位数计算 NaN 安全）。

### Fixed

- **贪心切分同质数据假切点 bug**：纯噪声/同质段上不再构造显著切点。
- **模板违规**：删除 `\tableofcontents`（国赛禁止目录页）与作者行
  （匿名性规定），摘要独立成页并含“关键词”行。