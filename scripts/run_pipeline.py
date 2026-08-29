"""主流程编排器 —— 把六阶段 + HITL 门禁串成一条可运行的流水线。

定位：这是主线程的"骨架 + 门禁注入器"，**不替 subagent 干活**。
它负责：
  1. 建立 .modeling/ 标准目录；
  2. 按阶段顺序推进，并在每个 🔴/🟡 决策点调用 hitl_gate 等人确认；
  3. 把各阶段产物/状态落盘（.modeling/ 目录 + phase_status.json）；
  4. HITL 门禁返回的人反馈作为硬约束注入后续阶段。

各阶段的具体建模/求解/写作工作，由主线程在编排器返回后的动作槽里派 subagent
（或按环境串行）完成——编排器不穷举这些实现，只定义流程与门禁骨架。

典型用法（主线程）：
  from run_pipeline import MathModelingPipeline
  p = MathModelingPipeline(problem_path, workdir)
  p.run(mode="live")      # 实战模式：人等确认
  # 或 p.run(mode="auto")  # benchmark：门禁自动放行

依赖：仅标准库 + hitl_gate + method_retrieve。轻量、可跑、可复用。
"""

import json
import datetime
from pathlib import Path

# 复用项目里的 HITL 门禁编排器
import sys
HERE = Path(__file__).resolve().parent
if str(HERE) not in sys.path:
    sys.path.insert(0, str(HERE))


# 标准目录（与 SKILL.md 约定对齐）
STD_DIRS = [
    "scratch",
    "drafts",
    "specs",
    "engines",
    "artifacts/submissions",
    "artifacts/figures",
    "manuscript/sections",
    "manuscript/blueprints",
    "audit",
    "hitl",
]

# 六阶段 + 门禁定义
# 每个 stage: (name, gate_level, question, phase_tag)
# gate_level: red=强制门禁(必须等人), yellow=可选介入, auto=全自动(不设gate)
STAGES = [
    {
        "name": "phase0_recon",
        "label": "阶段0 数据摸底",
        "gate_level": "red",
        "phase_tag": "phase0_understanding",
        "question": "agent 对题意理解对不对？有没有漏读/误读题目？",
        "next": "phase1_retrieve",
    },
    {
        "name": "phase1_retrieve",
        "label": "阶段1 HMML检索+定向发散",
        "gate_level": "yellow",
        "phase_tag": "phase1_direction",
        "question": "检索命中的建模方向贴合题意吗？要不要加/换方向？",
        "next": "phase2_refine",
    },
    {
        "name": "phase2_refine",
        "label": "阶段2 Actor-Critic精炼",
        "gate_level": "red",
        "phase_tag": "phase2_model_plan",
        "question": "这个模型方案（模型+关键假设+目标函数）符合领域直觉吗？假设成立吗？",
        "next": "phase3_solve",
    },
    {
        "name": "phase3_solve",
        "label": "阶段3 求解",
        "gate_level": "yellow",
        "phase_tag": "phase3_result_magnitude",
        "question": "这些关键数值量级合理吗？",
        "next": "phase4_review",
    },
    {
        "name": "phase4_review",
        "label": "阶段4 轻审稿",
        "gate_level": "red",
        "phase_tag": "phase4_pass",
        "question": "审稿通过，要放行进写作吗？",
        "next": "phase5a_report",
    },
    {
        "name": "phase5a_report",
        "label": "阶段5a 建模报告",
        "gate_level": "red",
        "phase_tag": "phase5_report_approve",
        "question": "建模报告 OK 吗？措辞/结论要不要调整？",
        "next": "phase5b_plan",
    },
    {
        "name": "phase5b_plan",
        "label": "阶段5b-1 论文蓝图规划",
        "gate_level": "yellow",
        "phase_tag": "phase5_blueprint",
        "question": "论文结构蓝图（章节树 + 每问六项子结构 + 参考文献席）符合预期吗？",
        "next": "phase5c_write",
    },
    {
        "name": "phase5c_write",
        "label": "阶段5b-2 论文正文写作",
        "gate_level": "red",
        "phase_tag": "phase5_writing",
        "question": "论文正文按蓝图写好并编译通过了吗？",
        "next": "phase5d_structural",
    },
    {
        "name": "phase5d_structural",
        "label": "阶段5b-3 结构审校",
        "gate_level": "red",
        "phase_tag": "phase5_structural_review",
        "question": "结构审校通过了吗？（每问策略规律/参考文献/定理清单/递进承接/匿名）",
        "next": None,   # 结束
    },
]


class MathModelingPipeline:
    def __init__(self, problem_path, workdir="."):
        """初始化流水线。

        Args:
            problem_path: 赛题问题描述路径（problem.md）。
            workdir: 工作区根目录（.modeling 的上级）。
        """
        self.problem_path = Path(problem_path)
        self.workdir = Path(workdir)
        self.modeling_dir = self.workdir / ".modeling"
        self.problem_profile = self._init_workdir()

    def _init_workdir(self):
        """建立 .modeling/ 标准目录，返回 problem_profile 字典骨架。"""
        for d in STD_DIRS:
            (self.modeling_dir / d).mkdir(parents=True, exist_ok=True)
        profile = {
            "problem_path": str(self.problem_path),
            "scale": None,
            "deliverables": [],
            "constraints": [],
            "problem_summary": None,
        }
        self._write_json("problem_profile.json", profile)
        return profile

    # ── 工具 ──
    def _write_json(self, rel, data):
        p = self.modeling_dir / rel
        p.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")
        return p

    def _read_json(self, rel, default=None):
        p = self.modeling_dir / rel
        if p.exists():
            return json.loads(p.read_text(encoding="utf-8"))
        return default

    def _stage_status(self, name, status, detail=""):
        """记录阶段状态到 phase_status.json。"""
        statuses = self._read_json("phase_status.json", {})
        statuses[name] = {
            "status": status,
            "detail": detail,
            "timestamp": datetime.datetime.now().isoformat(),
        }
        self._write_json("phase_status.json", statuses)

    def _stage_gate(self, stage, items, suggestions, mode):
        """生成 HITL 待审内容（不再等 stdin），返回"待用户审校"的 verdict。

        语义：把 gate 的产物从"脚本等 input()"改为"生成待审文件 + 标记 waiting_human"，
        由主 agent（读 roles/hitl_reviewer.md）在对话流中主动停下问用户。
        - 落盘 .modeling/hitl/<phase>_gate.md（人可读待审内容）
        - phase_status.json 标记 waiting_human（信号给主 agent）
        - 返回 verdict={action:'awaiting_human', ...}，主 agent 据此停下等用户。
        """
        phase = stage["phase_tag"]
        items = items or []
        suggestions = suggestions or []

        # 人可读的待审内容
        lines = [f"# {stage['label']} · 人工审校"]
        lines.append(f"\n> 门禁标识: {phase}  |  档位: {stage['gate_level']}")
        lines.append(f"\n## 待确认项")
        for it in items:
            lines.append(f"- {it}")
        if suggestions:
            lines.append(f"\n## Agent 建议（供参考）")
            for s in suggestions:
                lines.append(f"- {s}")
        lines.append(f"\n## 请选择动作")
        lines.append("confirm / edit / regenerate / skip / abort（或直接输入你的修改意见）")
        gate_path = self.modeling_dir / "hitl" / f"{phase}_gate.md"
        gate_path.parent.mkdir(parents=True, exist_ok=True)
        gate_path.write_text("\n".join(lines), encoding="utf-8")

        # 标记等待人工
        self._stage_status(stage["name"], "waiting_human",
                           f"待人工审校（{phase}），详见 {gate_path.name}")

        # 返回 verdict：主 agent 看到 awaiting_human 即停下问用户
        return {"action": "awaiting_human", "constraints": items,
                "gate_file": str(gate_path), "phase": phase,
                "mode": mode, "stage_label": stage["label"]}

    # ── 阶段动作槽（由主线程/子代理填充，编排器只定骨架）──
    def _action_phase0_recon(self):
        """阶段0: 数据摸底，读题构造 problem_profile（骨架）。"""
        profile = self.problem_profile
        # 提示主线程：此处读题，填 scale/deliverables/constraints
        profile["problem_summary"] = "[此处由主线程读题，用 HMML 检索+题意理解填充]"
        self._write_json("problem_profile.json", profile)
        self._stage_status("phase0_recon", "done", "题意画像已建")
        # 返回待确认项：题意理解关键判据
        return ["题目规模/约束/交付物的理解", "是否有漏读/误读的关键判据"]

    def _action_phase1_retrieve(self):
        """阶段1: HMML 检索 + 定向发散（骨架）。"""
        # 提示主线程调用 method_retrieve，落盘 00_retrieval.json
        self._stage_status("phase1_retrieve", "done", "HMML检索结果已落盘 00_retrieval.json")
        return ["检索命中的 2-3 个建模方向", "每个方向的贴合度判断"]

    def _action_phase2_refine(self):
        """阶段2: Actor-Critic 精炼建模方案（骨架）。"""
        self._stage_status("phase2_refine", "done", "模型方案已精炼")
        return ["最终模型 + 关键假设 + 目标函数", "Critic 反馈已整合"]

    def _action_phase3_solve(self):
        """阶段3: 求解（骨架）。"""
        self._stage_status("phase3_solve", "done", "求解完成，交付表已填")
        return ["关键数值量级", "求解是否收敛、交付表是否填满"]

    def _action_phase4_review(self):
        """阶段4: 轻审稿（骨架）。"""
        self._stage_status("phase4_review", "done", "轻审稿通过")
        return ["合理性检查结果", "可复现性检查", "交付表完整性"]

    def _action_phase5a_report(self):
        """阶段5a: 建模报告（骨架）。"""
        self._stage_status("phase5a_report", "done", "建模报告产出")
        return ["建模报告", "一页速览 + 逐问题要点 + 符号附录"]

    def _action_phase5b_plan(self):
        """阶段5b-1: 论文蓝图规划（骨架）。"""
        self._stage_status("phase5b_plan", "done", "论文结构蓝图已落盘 blueprints/paper_blueprint.md")
        return ["全篇章节树", "每问六项子结构（模型/求解/结果/策略规律/亮点/判据示意）", "参考文献席", "定理/命题清单", "结构自检表"]

    def _action_phase5c_write(self):
        """阶段5b-2: 论文正文写作（骨架）。"""
        self._stage_status("phase5c_write", "done", "论文正文写好并编译通过")
        return ["论文正文 sections/*.tex", "Tectonic 编译通过 paper.pdf"]

    def _action_phase5d_structural(self):
        """阶段5b-3: 结构审校（骨架）。"""
        self._stage_status("phase5d_structural", "done", "结构审校通过（蓝图兑现度核对）")
        return ["每问策略规律段", "参考文献节（真实文献+AI披露）", "定理清单兑现", "跨问递进承接", "匿名合规"]

    # ── 主入口 ──
    def run(self, mode="live"):
        """跑完整流水线，逐阶段推进 + 门禁。

        Args:
            mode: "live"=实战（人等确认）；"auto"=benchmark（门禁自动放行）。
        Returns:
            各阶段的审核结论 dict（action + constraints），供主线程注入后续。
        """
        print(f"\n🚀 启动 {Path(self.problem_path).name} 建模流水线（mode={mode}）")

        constraints_map = {}
        for stage in STAGES:
            action_fn = getattr(self, "_action_" + stage["name"])
            items = action_fn()
            print(f"\n—— {stage['label']} ——")

            if stage["gate_level"] == "auto":
                # ⚪ 全自动（确定性环节）：不用人，直接放行
                verdict = {"action": "confirm", "constraints": items,
                           "stage": stage["name"]}
                print(f"  [⚪] {stage['label']} 确定性环节，自动放行")
            else:
                # 🔴/🟡 门禁：生成待审内容 + 标记 waiting_human，交主 agent 问人。
                # auto 模式下仍先注入审校提醒（人工必审），但标记可降级（用户缺席时 confirm）。
                verdict = self._stage_gate(stage, items, [], mode)
                verdict["stage"] = stage["name"]
                # auto 模式下允许用户在缺席时降级为确认（保住 benchmark 出分）
                verdict["allow_degrade"] = (mode == "auto")
                print(f"  [{stage['gate_level']}] {stage['label']} 已写入待审内容，等待人工审校"
                      + ("（auto: 用户缺席可降级 confirm）" if mode == "auto" else ""))
                if mode == "auto":
                    # 透传一条审校提醒给主 agent（README 注释：主 agent 读到 awaiting_human 必须先尝试问人）
                    verdict["hint"] = ("即使 auto 模式，也请先向用户注入本次审校提醒；"
                                       "仅当用户明确缺席/无回复时才降级为 confirm。")

            constraints_map[stage["name"]] = verdict

            if verdict["action"] == "abort":
                print(f"\n⛔ 用户在 {stage['label']} 中止运行。可回退或重新选题。")
                break
            elif verdict["action"] == "regenerate":
                print(f"\n🔄 用户要求重新生成 {stage['label']}。需重跑该阶段。")
                break

        # 汇总阶段状态
        print("\n✅ 流水线结束。阶段状态:")
        for name, info in self._read_json("phase_status.json", {}).items():
            print(f"   - {name}: {info['status']}  {info.get('detail', '')}")

        return constraints_map


if __name__ == "__main__":
    # 自测：用一个真实题路径 + benchmark 模式（不阻塞人）跑一遍骨架
    import argparse
    ap = argparse.ArgumentParser()
    ap.add_argument("--problem", default="benchmarks/problems/2024A/problem.md")
    ap.add_argument("--workdir", default=".")
    ap.add_argument("--mode", default="auto", choices=["live", "auto"])
    args = ap.parse_args()

    p = MathModelingPipeline(args.problem, args.workdir)
    results = p.run(mode=args.mode)
    print("\n各阶段审核结论:")
    for k, v in results.items():
        print(f"   {k}: {v['action']}")
