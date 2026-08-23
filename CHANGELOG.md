# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Added

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