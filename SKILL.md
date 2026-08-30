---
name: math-modeling-agent
description: 竞赛级数学建模快速流水线（精简版）。数据摸底 → HMML 方法检索定向发散 → Actor-Critic 精炼 → 求解 → 轻审稿 → 串行写作。保留多流派发散与反过拟合纪律，砍掉过度验证与并行编纂。
---

# 数学建模快速流水线（精简版）

接获数学建模赛题或科研建模任务时，按以下精简状态机执行（Phase 0 → 1 → 2 → 3 → 4 → 5）。核心原则：**默认走最短路径，严谨只在真正需要的那一步才上**。多子智能体发散模式保留，但提示词只做方向引导，不做强制约束。

## 平台适配（先读我）

本技能平台无关。调度原语按运行环境替换：

| 能力 | Antigravity / Gemini CLI | Claude Code / Cursor | Hermes |
| :--- | :--- | :--- | :--- |
| 并发子代理 | `invoke_subagent` | Task tool 多实例并发 | `delegate_task(tasks=[...])` |
| 文件读写 | 内置文件工具 | Read/Write/Edit | `read_file` / `write_file` / `patch` |
| Python 执行 | 内置代码执行沙盒 | Bash + python | `terminal` / Jupyter kernel |

若环境不支持并发子代理，阶段 1 的多个流派**串行**逐个加载对应 roles/*.md 并依次产出方向卡片。禁止因平台能力不足而跳过。

## 健康与适配检测（首次运行必做，之后跳过）

> [!important] 首次运行本 skill 时的前置步骤
> 本项目库未出现 `.modeling/.health_checked` 标记时，**必须**先跑一次健康与适配检测，用于确认该 skill 在当前 agent 环境中的兼容性（subagent 并发、工具调用、脚本可运行、最小流程链路）。检测通过后再进入正式流水线；以后运行（存在 `.health_checked`）直接跳过，不再重复消耗。

### 执行步骤

1. **环境与代码层自检**（确定性，自动）：
   ```bash
   python scripts/health_check.py
   ```
   会检查：Python 版本与科学计算库、Tectonic/Node 可用性、`scripts/` 5 个算法模块导入+冒烟、HMML 方法库存在性、SKILL 引用完整性、以及**最小流程**（HMML 检索 → 落盘 `00_retrieval.json` → 读回 → 流派 school 合法）。结果打印为人类可读报告并落盘 `.modeling/health_report.json` + `.modeling/.health_checked`。

2. **Agent 层适配自评**（由主 agent 依据当前平台填写，脚本只做占位提示）：
   - **并发 subagent**：`delegate_task(tasks=[...])`（Hermes）/ `invoke_subagent`（Antigravity）/ Task 多实例（Claude Code）是否可用？若不可用，阶段 1 需退化为**串行**加载 roles/*.md。
   - **文件工具**：`read_file` / `write_file` / `patch` 是否可用？
   - **Python 执行**：`terminal` / Jupyter kernel 可否运行脚本？
   - 把上述 3 项结论**写入 agent 记忆系统**（`memory` 工具，target=memory），记录"本 skill 在此平台的 subagent/工具兼容性"，供后续会话复用，避免每次重测。

### 首次运行后

- 若检测**通过**：在 agent 记忆里记下 `math-modeling-agent 在<平台> 适配 OK（delegate_task 可用/串行退化/…）`，并继续进入阶段 0。
- 若检测**失败**（如 scripts 报错、pulp 缺失影响运筹求解、subagent 不可用）：先修复，再重跑 health_check；无法修复的项（如 pulp）在 agent 记忆里注明"运筹求解需 pip install pulp"。

## 探索流派与归属映射（HMML school → roles/）

| HMML 归属 school | 角色文件 | 覆盖的建模方向 |
| :--- | :--- | :--- |
| `opt` | `roles/offline_optimization.md` | 运筹/时空规划：LP、MILP、DP、图论、GA/SA/PSO、KKT、网络流 |
| `mech` | `roles/offline_mechanistic.md` | 机理/纵向动力学：ODE/PDE、LMM、传染病、守恒/传播方程 |
| `surv` | `roles/offline_survival_stat.md` | 随机/生存/风险：Cox/AFT、GARCH、排队论、CVaR、MDP |
| `robust` | `roles/offline_robust_decision.md` | 稳健/评价：熵权法、TOPSIS、AHP、秩相关检验、ANOVA |
| `pred` | `roles/offline_prediction_ml.md` | **预测/机器学习（本次新增）**：ARIMA、灰色GM(1,1)、SVM、K-means、PCA、Boosting、岭/泊松回归 |
| （联网） | `roles/online_prior_scout.md` / `roles/online_benchmark_miner.md` | 领域先验/常数 / 顶刊基准与数学范式 |

阶段 1 由 `method_retrieve.py` 的 school 字段决定派哪个 subagent；命中多个方向则只派相关的 2-3 个，其余跳过。

## 人在回路（Human-in-the-Loop）总则

> [!important] 差异化设计——每个高信息熵决策点引入人反馈
> 与主流开源 agent 的"全自动"路线不同，本框架在**关键决策点让人类介入**。但**不是每步都问**：采用**分层门禁**，只在 3 个关键点强制介入（🔴 题意理解 / 模型方案 / 报告审批），其余自动或可选（🟡），确定性环节全自动（⚪）。详见 `references/hitl_design.md`。

| 档位 | 语义 | 动作 |
| :-- | :-- | :-- |
| 🔴 强制门禁 | 必须人确认，否则停 | `confirm / edit / regenerate / skip / abort` 之一 |
| 🟡 可选介入 | agent 给出建议，人可一键通过/修改 | 同上 |
| ⚪ 全自动 | 人默认不介入 | 直接放行 |

**实现位置**：人工审校由**主 agent 在对话流中执行**（角色式提示词注入，2026-08-29 重构，非 subagent）。主 agent 读到门禁标记（`.modeling/hitl/<phase>_gate.md` + `phase_status.json` 的 `waiting_human`）→ 停下流水线 → 读出待审项 → 在对话中提问（5 个动作）→ **等用户回复**（强约束，不自答）→ 按动作处理 → 落盘 `.modeling/hitl/<phase>_feedback.json`（当次生效，不沉淀回灌）。详见 `roles/hitl_reviewer.md` + `references/hitl_prompt_design.md`。**auto 模式也先注入审校提醒**（人工必审），仅用户缺席才降级 confirm。

**模式**：实战模式 🔴 全开；benchmark 模式先注入审校提醒，用户缺席才降级 confirm（人缺席也能出分）。

## 阶段 0：数据摸底 (Brief Recon) — 🔴 强制门禁

1. 读赛题原文 + 附件数据，**粗读**即可，不做画像。题意基线逐条附**题面原文逐字引用**；启动提示词/摘要与原文冲突时，以原文为准并记录差异。
2. 落盘 `.modeling/problem_profile.json`，只记三样：
   - `scale`：问题规模（如 {地块 I, 品种 K, 周期 T} 或 {被试 n, 时点 m}）；
   - `deliverables[]`：要求提交的结果文件（Excel 表名、图表、结论形式）；
   - `constraints[]`：题目明示的刚性约束（简短列出，不展开）。
3. **🔴 人等确认题意理解**：把 agent 对赛题约束/交付物/规模的理解展示给人，问——"有没有漏读/误读题目？"人确认后进入阶段 1。

## 阶段 1：HMML 方法检索 + 定向发散 (Retrieve & Diverge) — 🟡 可选介入

检索结果传送给 subagent 的机制（关键）：**检索结果 → 落盘 `00_retrieval.json` → 主线程读回 → 按归属流派派 subagent → 方法与核心思想塞进该 subagent 的任务书 context**。subagent 是独立上下文，看不到主进程变量，所以必须经"落盘 + 任务书注入"这条链，而不是靠 Python 内存传。

1. **检索**：用 `references/method_library.md`（HMML）+ `scripts/method_retrieve.py` 对题目做关键词匹配，筛出相关方法。每个检索结果带一个**归属流派 school**（opt/mech/surv/robust/pred 之一，见脚本内置映射）。
2. **落盘**：调用 `save_to_json(结果, 工作区根)` 把命中方法写入 `.modeling/specs/00_retrieval.json`（含 method / core_idea / school / hits）。
3. **主线程读回**：`load_from_json(工作区根)` 读回命中方法。
4. **定向发散**：按每个命中方法的 `school` 决定派哪个 subagent；只让命中的 2-3 个方向各派一个 Subagent 发**方向卡片**（`drafts/draft_<方向>.md`），其余方向跳过。**任务书（context）必须包含：该方向的完整检索方法 + 核心思想 + 题目关键信息**，让 subagent 无需回读文件即可开工。
5. 每张方向卡片只写三样：**建模哲学**（为何契合）/**拟用模型族**（候选模型）/ **关键难点**（最可能被质疑的点 + 一句话化解）。
6. 方向卡片统一用 `roles/draft_protocol.md` 结构（三部分）。
7. **🟡 人看方向**：把命中的 2-3 个方向展示给人，问——"这些建模方向贴合题意吗？要不要加/换方向？"人可一键通过，或指示调整方向。

## 阶段 2：Actor-Critic 精炼 (Refine) — 🔴 强制门禁

1. **Actor** 建模 agent：基于检索到的候选方法 + 方向卡片，产出**初始建模方案**（模型 + 目标函数闭式 + 关键假设）。
2. **Critic** 审稿 agent：评估该方案质量，给出**针对性反馈**（哪里过度简化、哪里假设不稳、哪里能加分）。
3. **Actor 修正**：整合 critic 反馈，迭代 **2 轮**收敛，产出 `.modeling/specs/01_math_formulation.md`，只含：符号表、闭式目标函数、关键假设。
3.5 **判决性论证分级**：凡支撑"全局最优/唯一/上界"类结论的论证必须标级——精确代数证明 > 全空间收敛扫描 > 近似论证（谐波平衡/描述函数/摄动）；近似论证的声明误差须小于被判定差异的 1/3，否则只能标"佐证"，不得作主证据。**可选外部证据参照**：有历年优秀论文/文献时，定稿前提取同类问题结论作参照系，与本方案的差异须解释或触发复算。
4. **🔴 人等确认模型方案**：把最终模型 + 关键假设 + 目标函数展示给人，问——"这个模型选择符合领域直觉吗？假设成立吗？"人确认后进入阶段 3。
5. 不做公理化 KKT / 凸性推导。**理论性质必须尝试**：对核心对象证明至少一条不变性 / 单调性 / 上下界 / 唯一性，不适用须显式说明已尝试路径、禁止静默跳过（"调头曲线长度不变"这类证明是人工优秀论文的标配）。

## 阶段 3：求解 (Solve) — 🟡 可选介入

1. 实现代码（scipy/numpy/pandas/pulp），**先小规模冒烟再全量**。
1.5 **优化题全局性门禁**（含参数寻优的题强制）：①快/慢评估在 ≥3 个代表点对拍定标，偏差超过候选最优间隔 1/3 即宣告快评估失格、终值与最优点改用高保真档重寻优；②最优点及其邻域（含活动约束方向）用收敛档复评，确认邻域无更优；③最优解顶约束时，报告 unconstrained 最优与松弛约束后的功率/目标走势。
2. 求解正确 + 填满 `.modeling/artifacts/submissions/` 交付表（Excel 各 sheet 不留空）。
3. **轻纪律**：进入论文的关键数字必须能被脚本复现（一次运行记录），不做全套 log 审计。
4. **🟡 人看关键结果量级**：把主要数值量级展示给人，问——"这些数值量级合理吗？"人可一键通过，或指出异常。

## 阶段 4：轻审稿 (Quick Review) — 🔴 强制门禁

一轮 critic 快速检查四件事：
- 答案**是否合理且与参照一致**（量级、常识、有无 NaN/穿越；数值题对照 `reference_answers.json` 共识值或用独立方法交叉验证——**自洽≠正确**）；
- 含路径/几何/过程约束时，在**约束易违背处独立数值抽查**（不只信引擎自报的满足标志）；
- 关键数字**能否复现**（脚本一次运行）；
- 交付表**是否填满**。
- **（优化题）全局性复核**：Critic 任务书由题型检查单生成、不由被审者起草；优化题固定包含——用 Critic 独立实现**重寻优**复核、活动约束/边界检查、快慢评估定标抽查；并固定一项任务：**主动寻找与主结论相反的证据**（"复算通过"不等于"结论成立"，当结论依赖全局性时）。

**🔴 人等确认放行**：把审稿结论展示给人，问——"要放行进写作吗？"人确认后进入阶段 5；不通过才回退修复。不做二级分级、不做交叉审计。

## 阶段 5：论文编写 (Write) — 🔴 强制门禁

分四步，**不并行**：

1. **建模报告**（`roles/modeling_reporter.md`）：产出 `.modeling/manuscript/modeling_report.md`——一页速览 + 逐问题要点 + 符号附录，给人看的交接依据。置 `STATUS: PENDING_REVIEW`，**🔴 等人审批**（人工/Model-Critic）后进入下一步。

2. **论文蓝图**（`roles/paper_planner.md`，阶段 5b-1）：在写任何段落**之前**，基于已审批报告产出 `.modeling/manuscript/blueprints/paper_blueprint.md`——整篇论文的**装配图**。把"论文必须有什么"固化成结构化字段：全篇章节树 + 每问固定六项子结构（模型/求解/结果/**策略规律**/亮点/判据示意）+ 参考文献席 + 定理/命题清单 + 跨问递进承接句 + 结构自检表。**没有蓝图不进入写作**。格式见 `references/paper_structure.md`。

3. **论文正文**（`roles/chapter_writer.md`，阶段 5b-2）：基于蓝图，按题目问题顺序**逐段**写论文段落（`sections/*.tex`），每段对照蓝图子结构填写，再汇总用 Tectonic 编译为 `paper.pdf`——给评委看的成品。**写完每段、编译前跑 `scripts/check_ai_style.py` 去 AI 味自检**（规则库 `references/no_ai_style.md`）：方括号标签/说教套话/括注堆命中即回改，句长 CV < 0.25 打散句式；去 AI 味只改措辞、**数值/单位/结论/文献不动**（红线）。

4. **结构审校**（`roles/paper_structural_reviewer.md`，阶段 5b-3，🔴 门禁）：对照蓝图**逐项核对兑现度**——每问策略规律段/参考文献节/定理清单/递进承接/匿名合规是否齐全；缺一项即**回退**重写，**不得带着缺结构进入最终交付**。此环节只校验"结构全不全"，不覆盖 model_critic 的"数值对不对"（两者独立）。

   结构审校的同时，**数值审校归阶段 4 的 model_critic**：若阶段 4 已做，本阶段不再重复；若数值在写作中修改，需回阶段 4 复核数值。

批判纪律（写作两条线都遵守，沿用并扩展）：
- **A196 对比回灌（2025A）**：每问结果后必须含"策略规律提炼"段（从最优解回提炼可迁移规律，非复述数值）；正文后必须设"参考文献"节（真实文献 2-4 条 + AI 工具使用披露，**禁编造**）；能归约的判据优先用"精确归约"型定理（如圆柱全遮蔽归约为两底面圆周），把采样近似变精确。
- **反过拟合纪律**（保留）：数据驱动的结构选择（切点/分组/变量筛选）须有显著性检验或交叉验证证据；惩罚/正则超参数做灵敏度说明。
- **竞赛合规红线**（保留）：匿名性、无目录页、摘要独立成页、主节"一、二、三、"编号；AI 使用声明如实填写。
- **失败诚实**（保留）：求解不收敛、检验不显著、编译报错，如实写入，禁止静默跳过。

## 环境依赖

- Python ≥3.10：numpy / pandas / scipy / statsmodels
- Tectonic（LaTeX 编译）或 XeLaTeX + ctex 备选
- 联网组角色需要网络搜索工具，断网环境自动降级为离线流派

## scripts/ 工具箱

| 脚本 | 用途 | 关键接口 |
| :--- | :--- | :--- |
| `health_check.py` | **健康与适配检测**：环境/库/工具 + scripts 冒烟 + HMML 检索→落盘→读回最小流程 + SKILL 引用完整性，首次运行调用 | `python scripts/health_check.py` |
| `run_pipeline.py` | **主流程编排器**：九阶段（0-5 含 5a/b） + HITL 门禁，建 `.modeling/` 标准目录、落盘 `phase_status.json`；门禁阶段生成 `.modeling/hitl/<phase>_gate.md` 待审内容 + 标记 `waiting_human`，交主 agent（按 `roles/hitl_reviewer.md`）在对话流中问人 | `MathModelingPipeline(problem_path, workdir).run(mode='live'/'auto')` |
| `method_retrieve.py` | HMML 检索相关建模方法 → 落盘 `00_retrieval.json`（含归属流派 school），供 subagent 消费 | `retrieve_methods(problem_desc, top_k)` / `save_to_json(results, workdir)` / `load_from_json(workdir)` |
| `fig_helpers.py` | **论文配图统一工具库**：配色/样式/导出规范（`PALETTE`+`setup_mpl`+`style_ax`+`fig_save`），杜绝 tab:* 默认色；几何/数值图必须用求解引擎真实数据 | 配色见 `references/paper_figures.md`；`palette(name)` / `fig_save(fig, path)` |
| `check_ai_style.py` | **论文去 AI 味自检**：扫描方括号标签/说教套话/括注堆/口语化/AI高频词 + 句长 CV 量化 + 术语一致自检（规则库 `references/no_ai_style.md`），阶段 5b-2 写作后必跑 | `python scripts/check_ai_style.py <段.tex\|目录>` / `--dt "术语1\|术语2"` |
| `greedy_segmentation.py` | 有序特征异质性贪心切分 | `greedy_ordered_partition(...)` |
| `lmm_variance_decomp.py` | LMM 拟合与方差分解 | `fit_lmm_with_variance_decomposition(...)` |
| `robust_qc_3zone.py` | 非参数质控 + 三区双阈值 | `non_parametric_quality_control(...)` |
| `cluster_bootstrap.py` | 簇级 Bootstrap CI | `cluster_bootstrap_ci(...)` |

调用约定：全部函数带 `random_state` 保证可复现；`warning` 字段非空时在报告中说明。
