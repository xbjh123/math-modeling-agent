# benchmarks —— 评测驱动迭代引擎（Evaluation-Driven Iteration Engine）

> 本目录是整个 skill 的"回归测试 + 排行榜"。核心铁律：**任何提示词/脚本/流程改动，
> 必须在至少一道基准题上重跑全流程，并证明总分不降，方可合入。** 没有分数背书的
> 功能改动 = 未经验收的改动。

---

## 1. 目录约定

```
benchmarks/
├── README.md                    # 本文件
├── scoring_rubric.md            # 百分制双轨评分体系（自动 40 + 人工 60）
├── auto_checks.py               # 确定性自动检查器（自动 40 分部分）
├── problems/<year><题号>/       # 基准题库（用户提供真题后入库，题干只读区）
│   ├── problem.md               # 题目原文（考点、提交要求、deliverables）
│   └── data/                    # 官方附件数据
└── runs/<problem_id>/<date>_<git_short_sha>/   # 一次完整运行的产物快照
    ├── .modeling/               # 全套工作区产物（drafts/specs/artifacts/audit/manuscript）
    ├── score.md                 # 综合百分制评分 + 版本绑定（入库 git）
    ├── auto_checks.json         # 自动检查明细（入库 git）
    └── checks_config.json       # 可选：该题期望交付物清单等配置
```

大二进制（`data/`、`submissions/` 中的 PDF/xlsx、大图、`scratch/` 等）不入 git——
`benchmarks/.gitignore` 过滤 `runs/**` 中的产物，但**强制保留** `score.md`、
`auto_checks.json`、`checks_config.json`、`02_execution_log.json`、`sections/*.tex`、
`AI_Tool_Disclosure.md` 等小件，保证仓库轻量但历史分数与凭据长期可查。

---

## 2. 标准运行流程（六步）

1. **入库**：将真题原文整理为 `problems/<year><题号>/problem.md`，附件放 `data/`。
2. **跑全流程**：以该题目目录为工作区，按 SKILL.md 八阶段状态机执行完整建模（Phase 0→1→2→3→4→5a→5b，
   产物强落 `.modeling/`）。这是被测对象——被迭代的就是这条链路。
3. **快照**：复制全套 `.modeling/` 至 `runs/<problem_id>/<date>_<git_short_sha>/`。
4. **自动检查**：`python benchmarks/auto_checks.py --run-dir runs/<...> [--json ... 同名/auto_checks.json]`
   → 得到 0–40 分明细。
5. **人工评审**：按 `scoring_rubric.md` 的 60 分 checklist 打分，连同自动分写入 `score.md`
   （必须记录 git sha、skill 版本、模型名、日期，见第 D 节版本绑定）。
6. **对比回归**：与上一次同类题 `score.md` 对比出回归报告。总分下降 → 回滚或修复后再跑；
   新失分项 → 记入 issue 清单进入下一轮迭代。

---

## 3. 双模式说明

引擎支持两种运行模式，区别仅在**是否有人工审批门禁**：

| | 实战模式 | benchmark 模式 |
| :-- | :-- | :-- |
| 建模报告审批 | 必须**人工批准**（STATUS: APPROVED）后才进入论文写作 | **跳过门禁**：Model-Critic 代审记录结论，直接产出论文 |
| 最终产物 | 论文 PDF + AI 声明 + 建模报告 | 同左（评测对象是论文质量本身） |
| 用途 | 真实参赛/交付 | 版本回归 / 人机对比评测 |

> benchmark 模式刻意跳过审批门禁，是为让"模型→论文"链路可端到端自动化评测；但**不减配**
> model_critic 审计与数值溯源铁律——跳过的是门禁时序，不是质量要求。

---

## 4. 人机对比

协议详见 `scoring_rubric.md` 第 C 节。简述：同一道题记录**纯人工写作的历史成绩**作为
baseline，再记录 **AI 全流程成绩**，逐项做差异归因表——人做对而 AI 没做到的项回灌
`roles/` 提示词，AI 做得更好的项沉淀为新亮点。**迭代目标是缩小差距，不是掩盖差距。**

---

## 5. 一份 run 的"评测核心件"

| 文件 | 位置 | 生产者 | 用途 |
|---|---|---|---|
| `checks_config.json` | run 根 | 评测者 | 声明 `expected_deliverables` 等期望 |
| `auto_checks.json` | run 根 | `auto_checks.py --json` | 自动得分快照（40 分） |
| `score.md` | run 根 | 评测者 | 综合百分制评分 + 版本绑定 + 回归对比 |
| `.modeling/` 全套 | run 根 | SKILL.md 全流程 | 可重放被测产物 |

---

## 6. 与 references / roles 的关系

- 评分口径复用 `references/cumcm_reviewer_pitfalls.md` 的评阅逻辑，见 `scoring_rubric.md` 第 B 节。
- 归因项都要求落到提示词/模板层，而非只记在 score.md 里：
  人强项 → 回灌 `roles/`；AI 强项 → 沉淀为亮点进模板/检查器。

---

## 7. 常见问题（FAQ）

- **Q：自动 40 分全过，能代表论文获奖吗？** 不能。自动检查只保证"形式完备且有据可查"，
  模型对错、创新高低仍靠人工 60 分把关，两轨缺一不可。
- **Q：不想每次拷贝整个数据集。** 见 `.gitignore`：大二进制已忽略，仅小件入库。
- **Q：回归不降分但也不升算通过吗？** 算。铁律是"总分不降"；但不降且无归因亮点时应
  审视迭代是否真在改模型而非只调排版。

---

## 题库现状

**2021–2025 全部 25 题（A–E）已入库**，来源为竞赛官网历年赛题包（题目 PDF + 官方附件），
每题含 `problem.md`（自动提取题面，运行前须人工核对公式与表格）与 `data/`；
超过 10MB 的原始附件仅本地留存（见 `.gitignore`）。历史年份（2010–2020）与各题
参考解法论文在用户本机档案库，不随仓库分发。

- [x] 2021–2025 真题入库（25/25）
- [ ] 首轮跑分：从每类题型（机理/优化/统计评价）各选一道建立 baseline