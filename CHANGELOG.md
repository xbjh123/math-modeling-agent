# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

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