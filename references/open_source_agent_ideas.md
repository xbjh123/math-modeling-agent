# 开源科研 Agent 框架调研 —— 对 math-modeling-agent 的可吸收灵感

> 编制时间：2026-08-27（Hermes）
> 用途：作为 `math-modeling-agent` 八阶段流水线的一次"标杆巡检"，定位当前实现相对薄弱、可从开源处借鉴的环节。**不是**框架大全，而是**针对性吸收点清单**。
> 对照基线：本项目三层解耦 + Phase 0→5b 状态机 + Artifact DAG + 具身自验证 + benchmark 驱动评测。

---

## 一、调研范围（三条主线）

| 主线 | 代表项目 | 命题 | 与本项目的关系 |
| :--- | :--- | :--- | :--- |
| **A. 数学建模专用** | MathModelAgent (jihe520, 3.8k★)、MM-Agent (HKUST, NeurIPS 2025)、OR-LLM-Agent | 竞赛/真题端到端建模→论文 | 最贴近，直接竞品 |
| **B. 通用科研自动化** | The AI Scientist (Sakana)、Agent Laboratory (AMD)、SciAgents (MIT)、Google AI co-scientist | 开放科学发现 / 假设生成 / 文献综述→实验→报告 | 结构启示 |
| **C. 竞争性数据科学 / ML 工程** | AIDE (WecoAI)、AutoKaggle (ICLR 2025)、MLAgentBench、DeepResearch 系 | 表格竞赛 / 树搜索调优 / 深研 | 求解与评测方法论 |
| **D. 数学/推理专用** | SciAgent (IMO/IMC 金牌级)、DeepMath (IntelLabs)、VibeMath | 数学推理、证明、符号求解 | 单点能力 |

---

## 二、逐项目速览（含"对它最值得抄的点"）

### 1. MathModelAgent（jihe520）—— 与你的定位最重合
- **定位**：专为数学建模设计的 Agent + SKILLS，`/1start-mathmodel` 一条命令端到端出可提交 PDF 论文。
- **亮点（值得抄）**：
  - **19 阶段流水线拆成独立 SKILL**，每阶段可单独调用（只跑分析、只写论文）。
  - **17 套 Typst 论文模板**自动匹配赛事（国赛/华数杯/华为杯/MCM）；你用 LaTeX+Tectonic，它是 Typst，二者可互相借鉴模板结构。
  - **内置建模知识库 + 模型选择决策树**（AHP、TOPSIS、ARIMA、GA 等），降低模型幻觉——对应你 roles/ 里的流派，但它是"检索式决策树"。
  - **HIL 人机协作**：关键节点暂停等用户审批，6 种决策动作 `confirm / edit / regenerate / ask / skip / abort`。**这一项你阶段 5a 只有 approve/reject，可扩展成 6 动作。**
  - **四层容错**：有限重试 → Fallback Hand Off → Evaluator Shadow Mode → Feedback Rerun。
  - **9 步自动验收**：文本泄漏检测、数值一致性校验、Typst 编译、PDF 可视化检查。
  - **Web Search（Tavily）+ RAG 知识库（ChromaDB + Rerank）**：从本地知识库检索建模方法与代码模板。
- **它的短板（你已做或该更好）**：作者自己说"workflow agentless 不依赖 agent 框架"、无评测驱动 benchmark；你的 Artifact DAG + 具身自验证 + benchmark 三件套比它强。
- **借鉴优先级**：⭐⭐⭐⭐（同赛道，HIL 6 动作 + RAG + 决策树 + 模板引擎最直接）

### 2. MM-Agent (usail-hkust / LLM-MM-Agent) —— NeurIPS 2025，竞赛实绩
- **定位**：模拟人类建模四步——问题分析 → 数学建模 → 计算求解 → 结果汇报，端到端。
- **亮点（值得抄）**：
  - **HMML 层级化数学建模知识库**：Domain → Subdomain → 98 个 Method Node 的三级知识层次；"problem-aware + solution-aware" 双路检索；**actor-critic 机制做方法选择**。这是对你阶段 1/2 最强的输入——用结构化建模方法库做检索+评价，而非纯靠 6 个 prompt 流派发散。
  - **MLE-Solver**：自主生成并迭代改进代码求解器。
  - **已辅助两支队伍拿 MCM/ICM 2025 Finalist**（前 2.0%），有真实竞赛验证。
  - 自带 **MM-Bench** 基准（problem_id 如 `2024_C`，直接对标你的 benchmarks/ 真题库）。
- **它的短板**：仍是单通道 workflow，缺 Artifact DAG、缺可追溯数值、缺并行章节编纂。
- **借鉴优先级**：⭐⭐⭐⭐⭐（HMML 库 + actor-critic 检索是最大启发点）

### 3. OR-LLM-Agent —— 运筹问题三段式
- **定位**：把 OR 问题分解为 数学建模(Math Agent) → 代码生成(Code Agent) → 执行调试(Debugging Agent) 三段，各由独立 sub-agent 承担。
- **核心结论可抄**：**先建模后写码**平均准确率提升 ~4%，因为"建模前置改善了模型对问题的结构理解"。**这直接印证你阶段 2 公理化规格书 → 阶段 3 求解器 的铁律是对的。**
- **借鉴优先级**：⭐⭐（方法论佐证）

### 4. AIDE (WecoAI) —— 竞争性 ML 的树搜索
- **定位**：LLM 引导的 agent 在代码空间中做**树搜索**：每个 Python 脚本是一个节点，LLM 生成的 patch 产生子节点，metric 反馈剪枝并引导搜索。MLE-Bench（75 个 Kaggle）上赢过 OpenHands 等线性 agent 4 倍奖牌。
- **值得抄**：**用"指标反馈"驱动分支探索**——你阶段 3 目前是一次性全尺寸求解，可引入"候选求解器/候选模型结构的树形探索 + 指标（RMSE/AUC/目标函数值）反馈剪枝"，尤其在方案仲裁后做"主模型 vs 基线的多候选对比"时。
- **借鉴优先级**：⭐⭐⭐⭐（求解阶段的探索策略）

### 5. AutoKaggle（ICLR 2025）—— 多智能体解题竞赛
- **定位**：五智能体（Reader / Planner / Developer / Reviewer / Summarizer），六阶段工作流（理解/EDA/清洗/特征工程/建模）。**Reader 读 overview → Planner 规划 → Developer 生成+调试+单元测试 → Reviewer 审 → Summarizer 汇总。**
- **值得抄**：
  - **迭代调试 + 单元测试**保证代码正确性（对应你阶段 3 的"先小规模冒烟再全量"，可加单元测试门禁）。
  - **阶段化多智能体协作 + 可解释性**：每个阶段产物可解释，`gpt-4o` 优于 `AIDE` 28%。
- **借鉴优先级**：⭐⭐⭐（多智能体分工范式)

### 6. The AI Scientist（Sakana AI）→ 2026 登 Nature 封面
- **定位**：端到端自动做 ML 研究——idea 生成 → 实验 → 报告 → 评审。Nature 2026 版本有"模板模式 + 开放模式"。
- **值得抄**：**自动生成 + 自评审闭环**；**评审器给出 NeurIPS 风格评分（quality/significance/clarity/soundness/presentation/contribution）**——可映射到你的 model_critic 各维度。
- **它的短板**：常见失败模式正是你三令五申要防的——naive/underdeveloped ideas、实现错误、**重复配图**、**幻觉引用**。你的数值溯源 + 反过拟合纪律正好是解药。
- **借鉴优先级**：⭐⭐⭐（评审维度 + 失败模式清单）

### 7. Agent Laboratory（AMD，Findings EMNLP 2025）
- **定位**：三阶段——文献综述 / 实验 / 报告写作，多智能体协作，集成 arXiv/HF/Python/LaTeX。
- **值得抄**：**报告写作 Agent 的独立分工**；`arXiv 检索` 的文献综述 Agent。
- **借鉴优先级**：⭐⭐

### 8. SciAgents（MIT，LAMM）—— 知识图谱 + 假设生成
- **定位**：用**大规模本体知识图谱**组织科学概念，LLM + 数据检索工具 + **多智能体 + 原地学习**，自动生成并精炼科研假设，用于生物启发材料。
- **值得抄**：**知识图谱驱动的假设生成与跨概念连接**——可对标你阶段 1 的联网组 prior/benchmark，但改为"从结构化知识图谱检索相邻概念"。
- **借鉴优先级**：⭐⭐⭐（知识图谱整合）

### 9. Google AI co-scientist / ToolUniverse / SciAgent / DeepMath
- **Google co-scientist**：六个专职 agent（Generation/Reflection/Ranking/Evolution/Proximity/Meta-review）模拟科学方法，用自动反馈迭代生成-评估-精炼假设，Supervisor 管理 worker queue 并灵活缩放算力。**借鉴：迭代假设生成-评估-精炼循环 + Supervisor 资源编排。**
- **ToolUniverse（Harvard/Zitnik）**：提供 600+ 科学工具作为可调用仪器，标准化 LLM 访问组合工具。**借鉴：工具注册表/沙盒标准化。**
- **SciAgent（OpenDCAI）**：**IMO 2025 / IMC / IPhO / CPhO 金牌级**，动态编排"符号推导 / 概念建模 / 数值计算 / 验证"四类推理 Sub-agent，自组装推理流水线。**借鉴：符号推导 + 数值计算 + 验证 的子系统编排**——与你具身自验证高度互补。
- **DeepMath（IntelLabs）**：用 GRPO + 本地小模型训练"短计算驱动轨迹"，把确定性计算卸载给 executor 减少算术错误。**借鉴：把确定性计算（求导/求值）卸载给 Python/SymPy，LLM 只负责策略。**

---

## 三、对 math-modeling-agent 的"可落地点"（按吸收优先级排序）

### P0 最值得立刻做（直接补当前短板）

**① 引入层级化建模方法库 + 检索/评价机制（对标 MM-Agent HMML）**
- 现状：阶段 1 靠 6 个固定 prompt 流派发散，阶段 2 靠四维打分仲裁。
- 吸收：建一份 `references/method_library.md`——Domain → Subdomain → Method Node 三级结构，每个 Method 含适用条件/符号/边界。阶段 1 分流派时**先据此做 problem-aware + solution-aware 双路检索**，再让 6 组据此发散；阶段 2 仲裁时引入 actor-critic（检索打分 + 迭代精炼）替代纯静态打分。
- 收益：降低"模型幻觉 / 选错方法论"，这是当前竞赛含金量的核心瓶颈。

**② HIL 审批从 2 动作扩到 6 动作（对标 MathModelAgent）**
- 现状：阶段 5a 只有 approve / reject。
- 吸收：`confirm / edit / regenerate / ask / skip / abort`。特别在阶段 2 方案仲裁处也放一个暂停点（"是否锁定该主模型 + 基准对照？"）。
- 收益：把"人工审批"从一个二元开关变成真正的协作门禁，能接住你想商量的关键点。

**③ 阶段 3 引入指标驱动的多候选探索（对标 AIDE 树搜索）**
- 现状：规格书 → 一次性全尺寸求解。
- 吸收：在方案仲裁后、全尺寸求解前，加一个**轻量候选探索层**：对主模型/基准/变体各跑小规模，用指标反馈（损失/命中率/目标函数值）做剪枝，选出进入全尺寸求解的候选，再锁定。
- 收益：避免"一次成型不理想只能回退"，符合你对"多方案+特征分化"的偏好。

**④ model_critic 评审维度升级为 NeurIPS 风格六维（对标 AI Scientist）+ 失败模式清单**
- 现状：Level 1/2/3 三级，较粗。
- 吸收：评审增加 quality / significance / clarity / soundness / presentation / contribution 六维打分，并维护一份 `references/ai_scientist_failure_modes.md`（重复配图、幻觉引用、实现错误等）作为 critic 的负面清单。

### P1 增强（补可扩展性与稳健性）

**⑤ 工具注册表 / 沙盒标准化（对标 ToolUniverse + DeepMath）**
- 把 scripts/ 工具箱抽象成"可调用仪器注册表"，LLM 按标准化接口访问；确定性计算（求导/求值/小规模试解）明确卸载给 Python/SymPy，LLM 只出策略。这和你数值溯源铁律一致。

**⑥ 断点续跑落地（ROADMAP P1，对标 Agent Laboratory 的 workflow 状态机）**
- 你 ROADMAP 里已列为 P1。开源各框架几乎都做"阶段状态落盘 + 从最高完成点续跑"，可参考其 `phase_status.json` 设计。

**⑦ 文献综述 Agent 标准化（对标 Agent Laboratory / SciAgents）**
- 阶段 1 联网组可拆成"文献综述 Agent（arXiv/HF 检索）"与"知识图谱概念连接"，输出带引用的综述节。

### P2 锦上添花

**⑧ 模板引擎多赛事自动匹配**：把模板目录按赛事自动匹配（国赛/MCM），参考 MathModelAgent 的 17 套 Typst 模板思路，但保留你的 LaTeX+Tectonic 管线。

---

## 四、一页权衡表

| 来源 | 核心机制 | 你的对应环节 | 采纳建议 |
| :--- | :--- | :--- | :--- |
| MM-Agent | HMML 三级方法库 + actor-critic 检索 | 阶段 1/2 | ⭐⭐⭐⭐⭐ 立刻 |
| MathModelAgent | HIL 6 动作、RAG、决策树、9 步验收 | 阶段 5a、全局 | ⭐⭐⭐⭐ 立刻 |
| AIDE | 指标驱动树搜索剪枝 | 阶段 3 | ⭐⭐⭐⭐ 近期 |
| AI Scientist | NeurIPS 六维评审 + 失败模式 | 阶段 4 | ⭐⭐⭐ 近期 |
| AutoKaggle | Reader→Planner→…阶段化五 agent | 阶段 0-3 分工 | ⭐⭐⭐ 参考 |
| SciAgents | 知识图谱假设生成 | 阶段 1 联网组 | ⭐⭐⭐ 参考 |
| OR-LLM-Agent | 建模前置提升编码准确率（+4%） | 阶段 2/3 | ⭐⭐ 佐证 |
| ToolUniverse | 600+ 工具注册表标准化 | scripts/ 工具箱 | ⭐⭐ 增强 |
| Google co-scientist | 迭代假设生成-评估-精炼 + Supervisor 扩缩容 | 阶段 1/2 | ⭐⭐⭐ 参考 |
| SciAgent / DeepMath | 符号+计算+验证子代理编排；计算卸载 | 阶段 1 自验证 | ⭐⭐⭐ 参考 |

---

## 五、一句话结论

你已经在"确定性、可溯源、评测驱动"上做到了当下开源框架普遍欠缺的严谨度；**最值得从开源吸收的是三层**：(1) 用层级化方法库+检索评价取代纯 prompt 流派发散（MM-Agent HMML 是标杆）；(2) 把人工审批升级为 HIL 6 动作协作门禁；(3) 阶段 3 引入指标驱动的多候选树搜索。其余多属工程增强，锦上添花。
