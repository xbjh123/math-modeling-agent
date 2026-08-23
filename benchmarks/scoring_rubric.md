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
| `deliverables` | **15** | `.modeling/artifacts/submissions/` 非空（0 分则整项 0）；抽查**所有** `.xlsx` sheet，若存在任意空单元格即按空占比扣分（满分 15 = 齐备 + 全满）。`checks_config.json` 的 `expected_deliverables` 若声明了文件名列表，则逐一核对存在性（缺一个扣 15/len）。 |
| `traceability` | **10** | 论文正文（优先 `paper.pdf`，读不了则退而查 `manuscript/sections/*.tex`）中抽取数值，抽查前 20 个是否都能在 `artifacts/02_execution_log.json` 字符串化 JSON 中精确匹配到。得分 = `10 × found / checked`。 |
| `compile` | **5** | `manuscript/paper.pdf` 存在且页数 ≥ 20 得 5 分；10–19 页得 2.5 分；< 10 页或不存在得 0 分。 |
| `compliance` | **10** | 拆 4 项：无身份泄露词（`参赛队`/`队员`/20 所头部高校名）3 分；无 `\tableofcontents` 目录页 3 分；存在 `AI_Tool_Disclosure.md`（或 `AI声明` 类似命名）4 分。 |

> **映射约定**：生成 `auto_checks.json` 后，`score.md` 的"自动检查"列= `total/40`，直接转录
> 各 `{item, max, got}`，不得二次改写。

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