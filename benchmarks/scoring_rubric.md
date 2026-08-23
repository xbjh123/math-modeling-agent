# scoring_rubric.md —— 百分制双轨评分体系

> 本文件定义 benchmarks 的**唯一评分口径**。总分为 100 分，由两条轨道合成：
> **A. 自动检查（40 分）**——由 `auto_checks.py` 确定性输出，可重放、无主观偏差；
> **B. 人工评审（60 分）**——按 `references/cumcm_reviewer_pitfalls.md` 的评阅逻辑展开为 checklist。
>
> 凡 `score.md` 与本文档口径不一致，一律回读本文档复核；本文档为裁定基准。

---

## A. 自动检查（40 分）

自动得分为 `auto_checks.py --run-dir <run>` 的 `total` 字段。分项映射如下：

| 检查项 ID | 满分 | 得分规则 |
|---|---|---|
| `deliverables` | **12** | `.modeling/artifacts/submissions/` 非空（齐备 4 分）；抽查**所有** `.xlsx` sheet，按空单元格占比线性扣分（填满分 8）。`checks_config.json` 声明 `expected_deliverables` 时逐一核对存在性。 |
| `traceability` | **7** | 论文正文抽取前 20 个数值，舍入容差匹配 `02_execution_log.json`（论文 3.0215 vs log 3.02148… 判命中；题面输入常数经 problem.md 豁免）。得分 = `7 × found / checked`。 |
| `compile` | **3** | `paper.pdf` 页数 ≥20 得 3 分；10–19 页 1.5 分；<10 页或缺失 0 分。 |
| `compliance` | **8** | 无身份泄露词 2.5 分；无 `\tableofcontents` 2.5 分；存在 AI 声明文件 3 分。 |
| `answer_check` | **10** | **对照人工共识答案硬校验（2024A 教训新增）**：若 `problems/<id>/reference_answers.json` 存在，逐问检查论文/log 中是否出现容差内一致的共识值；每错一问扣 10/n 问。无标准答案的题按 N/A 满分计并注明。自洽 ≠ 正确。 |

> **映射约定**：生成 `auto_checks.json` 后，`score.md` 的"自动检查"列= `total/40`，直接转录
> 各 `{item, max, got}`，不得二次改写。
> **建答案表义务**：凡优秀论文库可提取共识数值的题，入库时必须同时生成 `reference_answers.json`
> （格式见 2024A 实例），否则该题 answer_check 恒为缺省满分、失去正确性校验能力。

---

## B. 人工评审（60 分）

复用 `references/cumcm_reviewer_pitfalls.md` 的评阅视角，展开为 4 个维度 checklist。
每一维按"倒扣 + 升级梯子"两段评分：命中扣分点按左列扣，命中升级梯子按右列加（不超上界）。

| 维度 | 满分 | 评分细则（劣→优） | 上界 |
|---|---|---|---|
| **模型正确性与假设合理性** | 20 | 每命中一个 pitfalls 扣分点（如把有序特征直接 K-means、把重复测量当 i.i.d.、忽略右删失等）扣 4–6；每完成一个对应"升级梯子"（有序异质性贪心、LMM 随机效应、区间删失生存等）加回。假设均在论文中显式列明并给适任理由得满分。 | 20 |
| **创新性与理论深度** | 15 | 在 pitfalls 模板之上有原创建模元素（新目标函数、新约束、跨层次组合、理论性质证明如凸性/KKT/极值）得 10–15；仅正确复用模板得 5–9；模板都未达到 0–4。 | 15 |
| **结果可信度与灵敏度完备性** | 15 | 结果有收敛判定、随机种子、置信区间；做灵敏度/多情景分析（单参数扰动、蒙特卡洛、S=1000 等）且结论稳健得 12–15；有结果但缺灵敏度 6–11；仅有孤立数字无交叉验证 0–5。 | 15 |
| **论文表达与图表质量** | 10 | 结构统一、公式编号正确、图表有编号/标题/来源、变量符号量纲闭环得 7–10；局部不齐 4–6；缺图表或图文不符 0–3。 | 10 |
| **合计** | **60** | — | 60 |

---

## C. 人机对比协议

> 目的不是"证明 AI 比人强"，而是**让每轮迭代都向人机合影上限逼近**——缩小差距、沉淀亮点。

对**同一道题**，依次记录三条记录：

1. **纯人工 baseline** —— 该题历史上（人工队伍）取得的行奖级成绩/评委评分，作为对照锚点。
2. **AI 全流程成绩** —— 本引擎在该题跑出的 `score.md` 百分制总分 + 各维度。
3. **差异归因表** —— 逐项列出：

| 归因方向 | 具体项（例） | 处置 |
|---|---|---|
| 人做对、AI 没做到 | 人发现"地块有最小起种面积约束"而 AI 漏掉；人敏感地处理了右删失 | **回灌**：写入 `roles/` 对应角色提示词（deep_formalizer / production_engineer / chapter_writer…），使下轮不再犯 |
| AI 做得更好 | AI 稳定产出 21+ 页排版、数值全溯源、无空单元格 Excel | **沉淀**：提炼为新亮点/自动化检查，固化进模板与 `auto_checks.py` |

> **迭代目标是缩小差距而非掩盖**：归因表中"人做对、AI 没做到"项，必须在下一轮
> 前转化为 `roles/` 提示词或 `references/cumcm_reviewer_pitfalls.md` 的升级梯子；
> 只记录不处置的归因项视为未闭环。

---

## D. 版本绑定规则（可复现对比硬性要求）

每份 `score.md` 的 YAML 头**必须**记录以下字段，缺一不可；缺则自动得分无法通过验收：

```yaml
git_commit_sha: <git rev-parse --short HEAD>   # 被测时点
skill_version:  <SKILL.md 中 version 或 git describe>
model_name:     <实际跑全流程用的模型/引擎，如 deepseek-v4-flash>
date:           <运行日期 YYYY-MM-DD>
problem_id:     <题号，如 2021A>
prev_score:     <上一轮同类题 score.md 的 total，无则为 null>
```

> 版本绑定的意义：任何两个 run 的分数可对比，仅当 `(problem_id, git_commit_sha, skill_version, model_name)`
> 与被比较对象同源或 diff 已审；跨版本无差异归因的分数对比一律视为无效。