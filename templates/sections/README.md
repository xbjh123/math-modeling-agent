# templates/sections 目录说明

本目录是**模板占位**（论文骨架），不是实际运行产物。实际论文在
`.modeling/manuscript/sections/`（由 chapter_writer 按题生成）。

## 文件约定（V2 重做后）

| 文件 | 用途 |
|---|---|
| `01_intro_assump.tex` | 第 1 章：问题重述/背景/假设/判据口径/符号说明 |
| `07_sensitivity_conclusion.tex` | 末章：模型检验/灵敏度/评价/附录 |
| `template_problem_chapter.tex` | **通用问题章模板**（每问固定六项子结构），不直接编译 |

## 问题章（02_problem1 .. 0X_problemN）由谁生成？

问题章**不预置单独占位**，因为章节数随题目问题数变化，预置文件覆盖不全。
正确做法：
1. 按 blueprint 章节树的"全篇结构"确定问题数 X；
2. 把 `template_problem_chapter.tex` 复制为 `02_problem1.tex`、`03_problem2.tex`、…、`(X+1)_problemX.tex`；
3. 在 main_template.tex 的章节树中 `\input` 它们（章节树与 blueprint 对齐）。

这样模板对**任何问题数的题目**都适用：3 问 → 01+02..04+05；4 问 → 01+02..05+06；5 问 → 01+02..06+07。末章文件名随问题数变为 `(X+2)_sensitivity_conclusion.tex`，需同步改 main_template.tex。

## 一致性要求
- 章节树与 `blueprints/paper_blueprint.md` 的"全篇结构"一节严格一致。
- 每问六项子结构（模型/求解/结果/策略规律/亮点/判据示意）必须齐全，缺一即回到 blueprint 标【待补】。
