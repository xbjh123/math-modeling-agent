"""math-modeling-agent 健康与适配检测 (self-health check)

首次运行 skill 时调用，用于测试本 skill 在 agent 环境中的兼容性。
覆盖两大部分:

  A. 环境与代码层（确定性，可全自动）:
     - Python 版本 + 关键科学计算库 (numpy/pandas/scipy/statsmodels/pulp optional)
     - Tectonic / node 是否可用
     - scripts/ 全部算法模块导入 + 最小冒烟
     - HMML 检索 -> 落盘 -> 读回 -> 流派映射 闭环（阶段 0/1 最核心链路）
     - SKILL.md 引用的 roles/ 与 scripts/ 文件完整性（防悬空）
     - method_library.md 方法库存在性

  B. Agent 层（由 agent 在运行时自我评估，本脚本通过 probe 输出占位）:
     - 并发 subagent 能力 (delegate_task / invoke_subagent / Task tool)
     - 文件工具 / Python 执行 能力
  这部分不在脚本内下结论，交给主 agent 依据所在平台填写。

输出:
  - 打印可读的 markdown 报告
  - 落盘 .modeling/health_report.json (机器可读) + .modeling/.health_checked (已检测标记)

被 SKILL.md 的「健康与适配检测」小节引用；检测完成后主 agent 将结论写入 agent 记忆系统。
"""

import sys
import json
import shutil
import subprocess
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
SCRIPTS_DIR = REPO_ROOT / "scripts"
WORKDIR = REPO_ROOT  # 检测阶段默认工作区为仓库根（真正的 .modeling 在运行题时创建）

_report = {
    "repo_root": str(REPO_ROOT),
    "checks": [],
    "minimal_flow": None,
    "summary": {"ok": True, "warnings": 0, "fails": 0},
}


def add(label, ok, detail, warn=False):
    """记录一项检查结果。"""
    _report["checks"].append({"label": label, "ok": ok, "detail": detail})
    if ok:
        pass
    elif warn:
        _report["summary"]["warnings"] += 1
    else:
        _report["summary"]["fails"] += 1
        _report["summary"]["ok"] = False
    return ok


# ─────────────────────── A. 环境与库检测 ───────────────────────
def check_env():
    py = sys.version.split()[0]
    add("Python 版本", True, f"{py} (≥3.10 建议)")
    missing = []
    for mod in ["numpy", "pandas", "scipy", "statsmodels", "pytest"]:
        try:
            __import__(mod)
        except ImportError:
            missing.append(mod)
    add("核心科学计算库", not missing, missing if missing else "numpy/pandas/scipy/statsmodels/pytest 全部可导入")

    pulp_ok = True
    try:
        import pulp  # noqa
    except ImportError:
        pulp_ok = False
    add("Pulp (MILP 求解, 可选)", pulp_ok,
        "pulp 可用" if pulp_ok else "pulp 未安装（运筹求解将退化，建议 pip install pulp）", warn=not pulp_ok)

    # Tectonic
    tec = shutil.which("tectonic")
    add("Tectonic (LaTeX 编译)", tec is not None,
        tec if tec else "未找到 tectonic（论文 PDF 编译需它或 XeLaTeX 替代）", warn=tec is None)

    # node（部分 harness 需要）
    node = shutil.which("node")
    add("Node.js", node is not None, node if node else "未检测到 node（非必需，部分 harness 可能用到）", warn=node is None)


# ─────────────────────── scripts 算法模块冒烟 ───────────────────────
def smoke_scripts():
    # 把 scripts 挂到 sys.path（与 conftest 一致）
    if str(SCRIPTS_DIR) not in sys.path:
        sys.path.insert(0, str(SCRIPTS_DIR))

    import numpy as np

    # greedy_segmentation
    try:
        import greedy_segmentation as gs
        n = 60
        rng = np.random.default_rng(42)
        split = rng.uniform(0, 100, n)
        x = rng.normal(0, 2, n)
        y = np.where(split < 50, 2 + 0.5 * x, 10 - 1.0 * x) + rng.normal(0, 0.5, n)
        import pandas as pd
        df = pd.DataFrame({"split": split, "x": x, "y": y})
        # 尝试调用贪心切分（不同版本函数名可能不同，做尽力探测）
        fn = getattr(gs, "greedy_ordered_partition", None) or getattr(gs, "greedy_segmentation", None)
        if fn:
            fn(df, "split", "x", "y", random_state=42)
            add("scripts: greedy_segmentation", True, "调用成功")
        else:
            add("scripts: greedy_segmentation", True, "模块导入成功（未定位到公开函数，可能是函数名差异）", warn=True)
    except Exception as e:
        add("scripts: greedy_segmentation", False, f"导入/调用失败: {e}")

    # lmm_variance_decomp
    try:
        import lmm_variance_decomp as lv
        add("scripts: lmm_variance_decomp", True, "模块可导入")
    except Exception as e:
        add("scripts: lmm_variance_decomp", False, f"导入失败: {e}")

    # robust_qc_3zone
    try:
        import robust_qc_3zone as rq
        add("scripts: robust_qc_3zone", True, "模块可导入")
    except Exception as e:
        add("scripts: robust_qc_3zone", False, f"导入失败: {e}")

    # cluster_bootstrap
    try:
        import cluster_bootstrap as cb
        add("scripts: cluster_bootstrap", True, "模块可导入")
    except Exception as e:
        add("scripts: cluster_bootstrap", False, f"导入失败: {e}")

    # method_retrieve（核心）
    try:
        import method_retrieve as mr
        add("scripts: method_retrieve", True, "模块可导入")
    except Exception as e:
        add("scripts: method_retrieve", False, f"导入失败: {e}")


# ─────────────────────── HMML 检索 -> 落盘 -> 读回闭环（阶段 0/1 核心链路） ───────────────────────
def minimal_flow():
    """跑最小流程：检索一段合成题目，落盘，读回，验证流派合法。"""
    import method_retrieve as mr

    demo_desc = "某超市要用过去5年每周销量数据，预测未来12周销量，含季节性与促销波动"
    res = mr.retrieve_methods(demo_desc, top_k=4)
    if not res:
        return {"label": "最小流程·检索", "ok": False, "detail": "合成题未命中任何方法，检查 METHOD_INDEX 关键词"}
    top = res[0]
    # 落盘
    out = mr.save_to_json(res, WORKDIR)
    # 读回
    loaded = mr.load_from_json(WORKDIR)
    ok = len(loaded) > 0 and all(x["school"] in {"opt", "mech", "surv", "robust", "pred"} for x in loaded)
    detail = f"命中 {len(res)} 个 → top={top[0]} [{top[2]}]（hits={top[3]}）；落盘 {Path(out).name}；读回 {len(loaded)} 条"
    return {"label": "最小流程·HMML检索→落盘→读回", "ok": ok, "detail": detail}


# ─────────────────────── SKILL 引用完整性（防悬空） ───────────────────────
def skill_integrity():
    import re
    skill_text = (REPO_ROOT / "SKILL.md").read_text(encoding="utf-8")
    # 只抓 roles/*.md 和裸 .py 名（scripts/ 前缀会重复导致路径拼错）
    roles = set(re.findall(r"roles/[a-z_]+\.md", skill_text))
    scripts_refs = set(re.findall(r"`([a-z_][a-z_0-9]*\.py)`", skill_text))

    missing_roles = [r for r in roles if not (REPO_ROOT / r).exists()]
    missing_scripts = [s for s in scripts_refs if s and not (SCRIPTS_DIR / s).exists()]
    ok = not missing_roles and not missing_scripts

    # method_library 存在性
    ml = REPO_ROOT / "references" / "method_library.md"
    add("SKILL 引用完整性", ok,
        "无悬空引用" if ok else f"缺失 roles:{missing_roles} scripts:{missing_scripts}")
    add("HMML 方法库 method_library.md", ml.exists(),
        str(ml) if ml.exists() else "缺失（从 MM-Agent HMML.md 复制）", warn=not ml.exists())


# ─────────────────────── 输出 & 落盘 ───────────────────────
def finalize():
    minimal = minimal_flow()
    if minimal:
        _report["minimal_flow"] = minimal
        # 只加进 checks（当作一项普通检查），不再在打印处重复输出
        add(minimal["label"], minimal["ok"], minimal["detail"])
    summary = _report["summary"]

    # 落盘报告 + 已检测标记
    report_dir = WORKDIR / ".modeling"
    report_dir.mkdir(parents=True, exist_ok=True)
    (report_dir / "health_report.json").write_text(
        json.dumps(_report, ensure_ascii=False, indent=2), encoding="utf-8")
    (report_dir / ".health_checked").write_text("ok", encoding="utf-8")

    # 打印人类可读报告
    print("# math-modeling-agent 健康与适配检测报告")
    print(f"- 仓库根: {REPO_ROOT}")
    print(f"- 检查项数: {len(_report['checks'])}\n")
    for c in _report["checks"]:
        flag = "✅" if c["ok"] else "⚠️"
        print(f"  {flag} {c['label']} — {c['detail']}")
    print(f"\n## 汇总: ok={summary['ok']}, 警告={summary['warnings']}, 失败={summary['fails']}")
    print("已落盘: .modeling/health_report.json + .modeling/.health_checked")
    print("注: subagent 兼容性/工具调用 由主 agent 依据所在平台评估并写入 agent 记忆。")


if __name__ == "__main__":
    check_env()
    smoke_scripts()
    skill_integrity()
    finalize()
