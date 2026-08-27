"""人在回路（HITL）门禁编排器 —— 主线程在关键决策点调用，等人确认。

设计取向：差异化于主流开源 agent 的"全自动"路线。在数学建模这个"没有唯一标准答案、
人的领域判断最值钱"的场景里，于高信息熵决策点拦截，让人把关。

分层门禁（见 references/hitl_design.md）：
  🔴 强制门禁（必须人确认）: 阶段0题意理解 / 阶段2模型方案 / 阶段4放行 / 阶段5报告审批
  🟡 可选介入（agent给建议，人一键过）: 阶段1方向 / 阶段3结果量级
  ⚪ 全自动（人不介入）: 脚本冒烟/图表/格式校验 —— 本脚本不处理，直接放行

用途（两种模式）：
  - 实战模式: gate() 展示待确认项 + agent 建议，收人 5 动作反馈，落盘，返回审核结论。
  - benchmark 模式: probe() 直接 mock 一个审核结论（人缺席也能出分），不阻塞。

用法（主线程）：
  from hitl_gate import gate
  verdict = gate(
      phase="phase0_understanding",           # 门禁标识（落盘文件名用）
      question="……agent 对题意理解对不对？有没有漏读题目？",
      items=["Q2 终止判据是碰撞非到达……", "Q3 最小螺距需动态约束……"],
      suggestions=["参考答 Q2=412s, AI基线误判73s……"],
      mode="live"                             # live(等人) 或 auto(自动放行)
  )
  if verdict["action"] == "abort": ...        # 人中止，回退
  elif verdict["action"] == "regenerate": ... # 人让重来
  # else: 把 verdict["constraints"] 作为硬约束注入后续阶段

依赖：仅标准库 json + datetime + pathlib。轻量、可跑、可复用。
"""

import json
import datetime
from pathlib import Path


# 人可选的 5 种反馈动作
ACTIONS = ["confirm", "edit", "regenerate", "skip", "abort"]


def _ensure_hitl_dir(workdir):
    """确保 .modeling/hitl/ 目录存在。"""
    d = Path(workdir) / ".modeling" / "hitl"
    d.mkdir(parents=True, exist_ok=True)
    return d


def _format_prompt(question, items, suggestions):
    """把待确认项格式化成给"人"看的文本。"""
    lines = [f"\n======== {question} ========"]
    if items:
        lines.append("\n【待确认项】")
        lines += [f"  - {x}" for x in items]
    if suggestions:
        lines.append("\n【Agent 建议】")
        lines += [f"  - {x}" for x in suggestions]
    lines.append("\n请选择动作 [confirm/edit/regenerate/skip/abort]，或直接输入修改意见文本:")
    return "\n".join(lines)


def _read_user_input(prompt_text):
    """收人的反馈：优先读取 stdin（主线程交互输入），返回 (action, comment)。"""
    print(prompt_text, flush=True)
    raw = input().strip()
    if not raw:
        return "confirm", ""
    low = raw.lower()
    if low in ACTIONS:
        return low, ""
    # 非标准动作文本，视为"修改意见"
    return "edit", raw


def _build_verdict(action, comment, constraints):
    """构造审核结论对象。"""
    return {
        "action": action,
        "comment": comment,
        "constraints": constraints,   # 注入后续阶段的硬约束（人改方向的就按人的来）
    }


def gate(phase, question, items=None, suggestions=None, workdir=".",
         mode="live", hard_auto_action="confirm"):
    """主线程在门禁点调用：展示待确认项 → 收人反馈 → 落盘 → 返回审核结论。

    Args:
        phase: 门禁标识，如 "phase0_understanding"（用于落盘文件名）。
        question: 这个门禁要人判断的核心问题。
        items: 待确认项列表（agent 当前的产出/关键判据）。
        suggestions: agent 的建议/参考信息（供人参考）。
        workdir: 工作区根（.modeling 的上级）。
        mode: "live"=等真人确认；"auto"=benchmark 自动放行（不阻塞）。
        hard_auto_action: auto 模式下的默认动作（benchmark 通常 confirm）。

    Returns:
        dict: {action, comment, constraints} —— action∈{confirm,edit,regenerate,skip,abort}
    """
    hitl_dir = _ensure_hitl_dir(workdir)
    items = items or []
    suggestions = suggestions or []

    if mode == "auto":
        # benchmark 模式：人缺席，自动放行，不阻塞
        verdict = _build_verdict(hard_auto_action, "[auto] benchmark 自动放行", items)
        action, comment = verdict["action"], verdict["comment"]
    else:
        # live 模式：展示 + 等人
        prompt_text = _format_prompt(question, items, suggestions)
        action, comment = _read_user_input(prompt_text)
        verdict = _build_verdict(action, comment, items if action != "edit" else items + [comment])

    # 落盘（当次生效，不沉淀回灌）
    record = {
        "phase": phase,
        "timestamp": datetime.datetime.now().isoformat(),
        "question": question,
        "items": items,
        "suggestions": suggestions,
        "action": action,
        "comment": comment,
        "mode": mode,
    }
    out = hitl_dir / f"{phase}.json"
    out.write_text(json.dumps(record, ensure_ascii=False, indent=2), encoding="utf-8")

    # 打印审核结论摘要
    print(f"\n✔ HITL 门禁 [{phase}] 记录到 {out}")
    print(f"  动作: {action}  |  人意见: {comment or '(无)'}  |  注入硬约束: {len(verdict['constraints'])} 条")
    return verdict


def probe(phase, question, items=None, suggestions=None, workdir="."):
    """benchmark 模式专用：自动放行，不阻塞人。等价 gate(mode='auto') 的便捷封装。"""
    return gate(phase, question, items, suggestions, workdir, mode="auto")


if __name__ == "__main__":
    # 自测：演示一个 🔴 门禁（阶段0 题意理解）
    gate(
        phase="phase0_understanding",
        question="agent 对题意理解对不对？有没有漏读/误读题目？",
        items=[
            "Q2 终止时刻判据是'相邻板凳碰撞'而非'几何到达'（参考答 412.47s）",
            "Q3 最小螺距需全程无碰撞 + 能进入调头空间（约 0.45m）",
            "Q4 需证明'调头曲线长度不变'（S 形相切圆弧约束）",
            "Q5 龙头最大速度随路径曲率变化（约 1.2463 m/s），非简单 2.0 上限",
        ],
        suggestions=["AI 基线曾把 Q2 误判成 73.43s、Q5 直接给 2.0，全靠这道门禁拦截"],
        workdir=".",
        mode="live",
    )
