# HITL 人工审校的提示词注入式重构（设计）

> 2026-08-29。**背景**：2025A 全流程测试中，人工审校（HITL 门禁）从未被成功运行——`scripts/hitl_gate.py` 的 live 模式依赖 `input()` 在 stdin 收真人输入，但 agent 编排（ZCode/Hermes）不是交互式 CLI，人在脚本 stdin 里无法打字；实际测试一律 `mode='auto'` 兜底 `confirm` 放行，门禁形同虚设。
> **方向**（用户拍板）：废弃 `hitl_gate.py`（脚本等待式），改为**角色式提示词**（`roles/hitl_reviewer.md`），由**主 agent 在对话流中主动停下、读出待审项、等用户回复后继续**——人工审校真正发生在 agent 对话里，而非卡在脚本 stdin。
> **边界**：仅改"信息载体"，层级（🔴/🟡/⚪）、门禁点（6 个）、动作类型（5 个）全部**保持现状**，不做精简——只解决"人工审校能跑起来"这一件事。
> **auto 模式**：即使 `mode='auto'` 也强制注入一条审校提醒（强调"人工必审"），不再静默 confirm。

---

## 1. 为什么脚本等待式失效

原 `hitl_gate.py` 的设计假设"主线程是交互式 CLI，能 `input()` 等人"：
```
gate(mode='live') → _read_user_input() → input() 等 stdin
```
但真实的运行载体是 **agent 编排**（ZCode/Hermes 的 agent 会话）。agent 通过工具调用驱动流水线，**没有交互 stdin 让人在脚本执行中途打字**。于是：
- `mode='auto'` 时进 benchmark 分支，直接 `confirm`，门禁零拦截；
- `mode='live'` 时 `input()` 会**阻塞挂起**（无人输入），同样跑不动。

结论：**人工介入的"触发"和"接收"被错误地放在脚本层**。应该移到 **agent 对话层**——由 agent 在门禁点主动向用户呈现、由用户在对话里决策。

## 2. 新方案的机制：角色式提示词注入

废弃 `hitl_gate.py`（脚本），改用 `roles/hitl_reviewer.md`（角色提示词）。核心是**让主 agent 具备"到门禁点主动停下问人"的行为**。

### 2.1 角色扮演者与触发
- **执行者**：主 agent（编排层，不是 subagent——subagent 独立上下文、看不到人）。
- **触发**：`run_pipeline.py` 在进入每个门禁阶段时，把该阶段的**待审内容**写入 `.modeling/hitl/<phase>_gate.md`，并在阶段状态里标记 `waiting_human`。
- **主 agent 行为**（由 `roles/hitl_reviewer.md` 约束，注入对话）：检测到 `waiting_human` → **停下流水线** → 读出 `.modeling/hitl/<phase>_gate.md` 的待审项 → 在对话中明确向用户提问 → **等用户回复** → 按用户动作处理 → 继续。

### 2.2 门禁内容（待审项）怎么生成
保留 `run_pipeline.py` 各阶段动作槽**已经返回的 items/suggestions**（它们本就是为该门禁准备的待确认项）。新流程：
1. 动作槽执行完，产出 items（待确认项）+ suggestions（agent 建议），与现在一致；
2. **不再**调用 `hitl_gate.py` 等 stdin；
3. 改为：把 `question + items + suggestions` 写入 `.modeling/hitl/<phase>_gate.md`（人可读版，含 5 个动作选项说明）；
4. 把 `phase_status.json` 该阶段标记为 `waiting_human`（信号给主 agent）。

### 2.3 主 agent 的注入对话（信息载体）
主 agent 读取 `<phase>_gate.md` 后，在对话中呈现：
```
📌 需要人工审校：[阶段 X 门禁名]
【待确认项】
  - item1
  - item2
【Agent 建议】
  - suggestion1  (供参考)
【请选择】confirm / edit / regenerate / skip / abort
（或直接输入你的修改意见）
```
主 agent **闭嘴等待用户回复**，不继续推进后续阶段。

### 2.4 用户回复 → 主 agent 处理
| 用户动作 | 主 agent 处理 |
|---|---|
| `confirm` | 记录 action=confirm，放行下一阶段 |
| `edit` | 把用户修改意见作为硬约束，修改当前产物后重跑该阶段 |
| `regenerate` | 清空该阶段产物，换思路重跑 |
| `skip` | 标记 SKIPPED，继续下一步 |
| `abort` | 停止，回退或重新选题 |
| 自由文本 | 视为 edit，作为硬约束注入 |

### 2.5 落盘
- 每次审校，主 agent 把动作 + 人意见写 `.modeling/hitl/<phase>_feedback.json`（**当次生效，不沉淀回灌**，与现设计一致）。
- `<phase>_gate.md` 保留当次待审内容留痕。

---

## 3. auto 模式下仍强制注入审校提醒

改动关键点：`run_pipeline.py` 的 `mode='auto'` 分支**不再**直接 `confirm` 静默放行。改为：
- `mode='auto'` 时，门禁阶段照常生成 `_gate.md` + 标记 `waiting_human`，**照样注入一条审校提醒给主 agent**；
- 区别仅在于：auto 模式下，如果**用户没回应**（agent 在 benchmark 静默跑），主 agent 在无人回复时**降级为 confirm 继续**（保住 benchmark 出分能力）；
- 但**必须**先尝试注入审校提醒（体现"人工必审"的强倾向），而不是从一开始就静默。

> 语义：auto = "**先尝试问人，人不在才降级**"，而不是"不问人"。这修正了原来 auto 直接跳过人工的缺陷。

---

## 4. 保持现状的部分（明确不改）

- **分级**：🔴 强制 / 🟡 可选 / ⚪ 全自动——不变。
- **6 个门禁点**：阶段0 题意 / 阶段1 方向 / 阶段2 模型 / 阶段3 量级 / 阶段4 放行 / 阶段5 报告——不变。
- **5 个动作**：confirm / edit / regenerate / skip / abort——不变。
- **落盘位置** `.modeling/hitl/`——不变。

## 5. Skill 侧写入

在 `references/hitl_design.md` 补一段"提示词注入式人工审校"（替代原脚本等待式），并新增 `roles/hitl_reviewer.md` 角色（约束主 agent 在门禁点主动停下问人）。`SKILL.md` 的 HITL 总则相应更新"实现位置"——从"主线程编排层用脚本等人"改为"主 agent 在对话流中按角色提示词主动问人"。

---

## 6. 已决项与开发点

**已决（用户拍板）**：
- [x] **主 agent 停下问人的机制**：**强提示词约束**（不依赖任何"等用户"原语，适配 ZCode/Hermes/Claude Code 等）。`roles/hitl_reviewer.md` 用**强指令**约束主 agent：检测到门禁 → 必须停下流水线 → 读出待审项 → 提问 → **必须等用户回复，绝不自答继续**。双保险：`phase_status.json` 的 `waiting_human` 标记（信号）+ 角色强约束（行为）。

**后续开发点**：
- [ ] `roles/hitl_reviewer.md` 措辞（强约束：问完必须等回复，禁止自问自答/自作主张放行）
- [ ] auto 降级 confirm 的确切触发（拟：benchmark 跑批由编排器统一处理"无人回应→降级"，不靠超时计时）
- [ ] 与 `run_pipeline.py` 的接口：`waiting_human` 状态标记的读写约定
