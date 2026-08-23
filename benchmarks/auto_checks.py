#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""auto_checks.py —— benchmarks 确定性自动检查器（满分 40 分）

对一个 run 快照目录执行四类检查，输出得分明细。供 benchmarks/scoring_rubric.md 的
A 轨道（自动检查 40 分）使用。纯标准库 + openpyxl + pypdf。

用法示例
--------
# 打印人类可读得分明细
python benchmarks/auto_checks.py --run-dir benchmarks/runs/2021A/2026-08-23_176172f

# 落盘 JSON 结果（供 score.md 转录 / 长期审计）
python benchmarks/auto_checks.py --run-dir benchmarks/runs/2021A/2026-08-23_176172f \\
    --json benchmarks/runs/2021A/2026-08-23_176172f/auto_checks.json

# 校验 JSON 输出本身可重复（不确定性为零：同目录两次运行 total 必相等）
"""

import argparse
import json
import os
import pathlib
import re
import sys

# --------------------------------------------------------------------------
# 依赖：openpyxl 读 xlsx 单元格，pypdf 读 pdf 页数。二者缺失时相应检查降级而非崩溃。
# --------------------------------------------------------------------------
try:
    import openpyxl
except ImportError:  # pragma: no cover
    openpyxl = None

try:
    from pypdf import PdfReader
except ImportError:  # pragma: no cover
    PdfReader = None


# 头部高校院校名单关键词表（compile/compliance 用 "school names" 泄漏检测内置 20 所）
SCHOOL_NAMES = [
    "清华大学", "北京大学", "浙江大学", "上海交通大学", "复旦大学",
    "中国科学技术大学", "南京大学", "华中科技大学", "武汉大学", "西安交通大学",
    "哈尔滨工业大学", "中山大学", "四川大学", "山东大学", "同济大学",
    "中国人民大学", "天津大学", "北京航空航天大学", "东南大学", "南开大学",
]

# 身份泄露检测词：队号/队员/评委关注的高校全称
IDENTITY_TERMS = ["参赛队", "队员"] + SCHOOL_NAMES

# 合规文件命名：AI_Tool_Disclosure.md 或含 "AI声明"/"AI 声明"/"AI_声明" 等
AI_DISCLOSURE_PATTERNS = [
    re.compile(r"AI[_ ]?tool[_ ]?disclosure\.md$", re.IGNORECASE),
    re.compile(r"AI[_ ]?声明", re.IGNORECASE),
]

# 数值抽取：≥4 位有效数字，或带小数；排除纯年份与页码引用样式的常见噪声
NUM_RE = re.compile(
    r"(?<![\d.])(?:(?:\d{4,}(?:\.\d+)?)|(?:\d+\.\d+))(?![\d.])"
)
# 过滤：去掉常见假阳性——年份 1900-2099、孤立页码（形如 \pageref{x} / 第3页 / [7] 引用）
YEAR_RE = re.compile(r"^(19|20)\d{2}$")


# --------------------------------------------------------------------------
# 工具函数
# --------------------------------------------------------------------------
def _read_json(path):
    """读到则返回 dict，否则返回 None（优雅降级）。"""
    try:
        with open(path, "r", encoding="utf-8") as fh:
            return json.load(fh)
    except (OSError, ValueError):
        return None


def _item(item_id, max_score, got, details):
    return {"item": item_id, "max": max_score, "got": got, "details": details}


def _iter_xlsx(run_dir):
    """遍历 submissions 下所有 .xlsx 文件，返回路径列表；目录不存在返回 []。"""
    sub = run_dir / ".modeling" / "artifacts" / "submissions"
    if not sub.is_dir():
        return []
    return sorted(p for p in sub.iterdir() if p.suffix.lower() in (".xlsx", ".xlsm"))


def grep_tex_contents(run_dir):
    """读取 manuscript/sections/*.tex 全部文本串起来；缺失返回 ''。"""
    sec = run_dir / ".modeling" / "manuscript" / "sections"
    if not sec.is_dir():
        return ""
    chunks = []
    for f in sorted(sec.glob("*.tex")):
        try:
            chunks.append(f.read_text(encoding="utf-8", errors="replace"))
        except OSError:
            continue
    return "\n".join(chunks)


# --------------------------------------------------------------------------
# 检查项 1：deliverables（15）
# --------------------------------------------------------------------------
def _check_deliverables(run_dir, cfg):
    xlsx_files = _iter_xlsx(run_dir)
    details = []
    if not xlsx_files:
        return _item("deliverables", 12, 0.0,
                     details + ["submissions/ 为空或缺失：0 分"])

    got = 0.0
    # (a) 期望文件名核对：checks_config.json 的 expected_deliverables
    expected = (cfg or {}).get("expected_deliverables", []) or []
    present = {p.name for p in xlsx_files}
    missing = [e for e in expected if e not in present]
    if expected:
        if missing:
            got += 0.0
            details.append(f"期望交付物缺失 {len(missing)}/{len(expected)}: {missing}")
        else:
            got += 5.0
            details.append(f"期望交付物齐全: {expected}")
    else:
        got += 4.0
        details.append("无 expected_deliverables 声明，按非空给 4 分")

    # (b) 全满检测：任一 sheet 存在空单元格即扣（按空单元格占比线性扣，上限 10 分）
    if openpyxl is None:
        details.append("openpyxl 未安装：空单元格检测跳过（保留非空 5 分）")
        got += 4.0
    else:
        empty_total = 0
        cell_total = 0
        for xf in xlsx_files:
            try:
                wb = openpyxl.load_workbook(xf, read_only=True, data_only=True)
                for ws in wb.worksheets:
                    for row in ws.iter_rows():
                        for cell in row:
                            cell_total += 1
                            if cell.value in (None, ""):
                                empty_total += 1
                wb.close()
            except Exception as exc:  # noqa: BLE001  坏文件按整体缺失处理
                details.append(f"{xf.name} 读取失败({exc})：视为全空")
                # 无法读取视为最差：整表记空且计入总量，确保扣分
                # 简化：该表记 1 空 / 1 总 => 该表全部为空
                empty_total += 1000
                cell_total += 1000
        if cell_total == 0:
            details.append("xlsx 存在但无任何单元格")
        else:
            empty_ratio = empty_total / cell_total
            fill_score = 8.0 * (1.0 - empty_ratio)
            got += fill_score
            details.append(
                f"空单元格 {empty_total}/{cell_total} (占 {empty_ratio:.1%})，"
                f"fill 得分 {fill_score:.1f}/8"
            )

    got = round(min(12.0, got), 2)
    details.insert(0, f"{len(xlsx_files)} 个 xlsx, 得分 {got}/12")
    return _item("deliverables", 12, got, details)


# --------------------------------------------------------------------------
# 检查项 2：traceability（10）
# --------------------------------------------------------------------------
def _check_traceability(run_dir):
    # 论文文本来源：优先 paper.pdf（读不出文字则退而吃 sections/*.tex）
    pdf_path = run_dir / ".modeling" / "manuscript" / "paper.pdf"
    body = ""
    source = "sections/*.tex"
    if PdfReader is not None and pdf_path.is_file():
        try:
            reader = PdfReader(str(pdf_path))
            body = "\n".join((page.extract_text() or "") for page in reader.pages)
            if body.strip():
                source = "paper.pdf"
        except Exception:  # noqa: BLE001
            body = ""
    if not body.strip():
        body = grep_tex_contents(run_dir)

    # 抽取数值
    raw_nums = NUM_RE.findall(body)
    nums = [
        n for n in raw_nums
        if not YEAR_RE.match(n)           # 排除年份
        and not re.match(r"^\d+$", n)     # 存活的纯整(排除引用页码 _ 由年份覆盖，再剔纯整数以便抽有效数字)
    ]
    # 上述已过滤；再补一条：剔除 1-3 位纯整数（这些更像页码/小整数，值权重低）
    checked = []
    for n in nums:
        if re.match(r"^\d+$", n) and len(n) < 4:
            continue
        checked.append(n)
        if len(checked) >= 20:
            break

    if not checked:
        return _item("traceability", 7, 0.0,
                     [f"论文正文({source})未抽取到有效数值：0 分"])

    log = _read_json(run_dir / ".modeling" / "artifacts" / "02_execution_log.json")
    if log is None:
        return _item("traceability", 7, 0.0,
                     ["02_execution_log.json 缺失或非 JSON：0 分"])
    log_str = json.dumps(log, ensure_ascii=False)

    # 收集 log 全部数值（含嵌套），供 4 位小数舍入容差匹配
    log_nums = []
    def _walk(o):
        if isinstance(o, bool):
            return
        if isinstance(o, (int, float)):
            log_nums.append(float(o))
        elif isinstance(o, dict):
            for v in o.values():
                _walk(v)
        elif isinstance(o, list):
            for v in o:
                _walk(v)
    try:
        _walk(log)
    except Exception:  # noqa: BLE001
        pass

    def _hit(n_str):
        # 1) 原精确串匹配（保留旧行为）
        if n_str in log_str:
            return True
        # 2) 舍入容差：论文值 round(log值, len(小数位)) 相等即命中
        #    论文写 3.0215、log 存 3.0214868... → round(3.0214868,4)==3.0215 判命中
        try:
            pv = float(n_str)
        except ValueError:
            return False
        dec = len(n_str.split(".")[1]) if "." in n_str else 0
        if dec == 0:
            # 纯整数串（≥4位）：允许 ±1 内的浮点表示差异
            return any(abs(v - pv) < 1.0 for v in log_nums)
        tol = 10 ** (-dec) / 2 + 1e-12
        if any(abs(v - pv) < tol for v in log_nums):
            return True
        # 3) 输入参数豁免：题面给定常数（螺距 55 cm、板宽 30 cm 等）在 problem.md 中
        #    以"数值+单位"形式出现即视为有据——log 只强制记录输出，不要求复录输入。
        #    匹配策略：数值本身，或 数值×100（cm↔m 换算）两种形态。
        try:
            prob = (run_dir / "problem.md").read_text(encoding="utf-8")
            variants = {n_str}
            try:
                fv = float(n_str)
                for scaled in (fv * 100, fv / 100):
                    s_round = round(scaled, 6)          # 消浮点噪声: 55.00000000000001 -> 55.0
                    variants.add(repr(s_round))
                    variants.add(str(int(s_round)) if s_round == int(s_round) else repr(s_round))
            except ValueError:
                pass
            for v in variants:
                if v and re.search(r"(?<![\d.])" + re.escape(v) + r"(?![\d.])", prob):
                    return True
            return False
        except Exception:  # noqa: BLE001
            return False

    found = [n for n in checked if _hit(n)]
    miss = [n for n in checked if not _hit(n)]
    got = round(7.0 * len(found) / len(checked), 2)
    details = [
        f"数值来源={source}，抽查 {len(checked)}/20 个，命中 {len(found)} 个",
        f"miss: {miss}",
    ]
    return _item("traceability", 7, got, details)


# --------------------------------------------------------------------------
# 检查项 3：compile（5）
# --------------------------------------------------------------------------
def _check_compile(run_dir):
    pdf_path = run_dir / ".modeling" / "manuscript" / "paper.pdf"
    if pdf_path.is_file() and PdfReader is not None:
        try:
            n_pages = len(PdfReader(str(pdf_path)).pages)
            if n_pages >= 20:
                got = 3.0
                note = "达标 (≥20 页)"
            elif n_pages >= 10:
                got = 1.5
                note = f"半分 ({n_pages} 页，10-19)"
            else:
                got = 0.0
                note = f"不足 (<10 页: {n_pages})"
            return _item("compile", 3, got, [f"paper.pdf 共 {n_pages} 页 → {note}"])
        except Exception as exc:  # noqa: BLE001
            return _item("compile", 3, 0.0, [f"paper.pdf 损坏无法读取: {exc}"])
    if pdf_path.is_file() and PdfReader is None:
        return _item("compile", 3, 0.0, ["pypdf 未安装无法判页数：0 分"])
    return _item("compile", 3, 0.0, ["paper.pdf 不存在：0 分"])


# --------------------------------------------------------------------------
# 检查项 4：compliance（10）
# --------------------------------------------------------------------------
def _check_compliance(run_dir):
    body = grep_tex_contents(run_dir)
    details = []
    got = 0.0

    # (a) 身份泄露检测（3 分）
    leaks = [t for t in IDENTITY_TERMS if t in body]
    if leaks:
        details.append(f"身份泄露命中词语: {leaks} (0/3)")
    else:
        got += 2.5
        details.append("无身份泄露词 (3/3)")

    # (b) 无目录页（3 分）
    if "\\tableofcontents" in body:
        details.append(f"出现 \\tableofcontents (0/3)")
    else:
        got += 2.5
        details.append("无 \\tableofcontents (3/3)")

    # (c) AI 声明文件（4 分）
    mdir = run_dir / ".modeling" / "manuscript"
    found_name = None
    if mdir.is_dir():
        for f in mdir.iterdir():
            if f.is_file() and any(pt.search(f.name) for pt in AI_DISCLOSURE_PATTERNS):
                found_name = f.name
                break
    if found_name:
        got += 3.0
        details.append(f"存在 AI 声明文件 {found_name} (4/4)")
    else:
        details.append("manuscript/ 下无 AI_Tool_Disclosure.md / AI声明 文件 (0/4)")

    return _item("compliance", 8, round(got, 2), details)


# --------------------------------------------------------------------------
# 检查项 5：answer_check（10）—— 对照人工共识答案（reference_answers.json）
# 2024A 教训：自洽≠正确。数值题答案与人工共识偏离即重扣。
# 权重调整说明：加入本项后总分上限仍为 40——traceability 10→7，
# compile 5→3，compliance 10→8，answer_check 占 10。旧 run 无
# reference_answers.json 时本项按缺省满分处理并在 details 注明 N/A。
# --------------------------------------------------------------------------
def _check_answer(run_dir):
    ref = _read_json(run_dir / "reference_answers.json")
    if not ref or "answers" not in (ref or {}):
        return _item("answer_check", 10, 10.0,
                     ["N/A: 无 reference_answers.json（该题未建标准答案），按缺省满分计"])
    log = _read_json(run_dir / ".modeling" / "artifacts" / "02_execution_log.json")

    # 收集论文文本（答案可能只在论文/表格中出现）
    body = ""
    pdf_path = run_dir / ".modeling" / "manuscript" / "paper.pdf"
    if PdfReader is not None and pdf_path.is_file():
        try:
            body = "\n".join((p.extract_text() or "") for p in PdfReader(str(pdf_path)).pages)
        except Exception:  # noqa: BLE001
            pass
    if not body.strip():
        body = grep_tex_contents(run_dir)
    log_str = json.dumps(log, ensure_ascii=False) if log else ""

    per_q = ref["answers"]
    n_pass = 0
    details = []
    n_scored = 0
    for qid, spec in per_q.items():
        cons = spec.get("consensus")
        if cons is None:
            continue
        # 该类目若是定性描述（如理论证明）则跳过数值比对
        if isinstance(cons, str):
            continue
        tol = float(spec.get("tolerance", 0.01))
        n_scored += 1
        hit = False
        # 在论文文本中找与共识值容差内一致的数字
        pat = re.compile(r"(?<![\d.])" + re.escape(f"{cons:.4f}".rstrip("0").rstrip(".")) +
                         r"|(?<![\d.])" + re.escape(f"{round(cons, 3)}") +
                         r"|(?<![\d.])" + re.escape(f"{round(cons, 2)}") + r"(?![\d.])")
        m = re.search(pat, body) if body else None
        if m:
            hit = True
        elif log_str:
            # 或在 log 中找容差内的浮点值
            def _walk(o):
                if isinstance(o, bool):
                    return
                if isinstance(o, (int, float)):
                    yield float(o)
                elif isinstance(o, dict):
                    for v in o.values():
                        yield from _walk(v)
                elif isinstance(o, list):
                    for v in o:
                        yield from _walk(v)
            try:
                hit = any(abs(v - float(cons)) <= tol for v in _walk(log))
            except Exception:  # noqa: BLE001
                hit = False
        if hit:
            n_pass += 1
            details.append(f"{qid}: 命中共识值 {cons} ✓")
        else:
            details.append(f"{qid}: 未找到共识值 {cons}（±{tol}）→ 答案疑似错误 ✗")

    if n_scored == 0:
        return _item("answer_check", 10, 10.0,
                     ["N/A: reference_answers.json 无可数值比对的条目"])
    got = round(10.0 * n_pass / n_scored, 2)
    return _item("answer_check", 10, got, details)


# --------------------------------------------------------------------------
# 主流程
# --------------------------------------------------------------------------
def run_all(run_dir: pathlib.Path) -> dict:
    cfg = _read_json(run_dir / "checks_config.json")
    checks = [
        _check_deliverables(run_dir, cfg),
        _check_traceability(run_dir),
        _check_compile(run_dir),
        _check_compliance(run_dir),
        _check_answer(run_dir),
    ]
    total = round(sum(c["got"] for c in checks), 2)
    return {
        "run_dir": str(run_dir),
        "checks": checks,
        "total": total,
        "max": 40,
    }


def _fmt(result: dict) -> str:
    lines = [f"run_dir: {result['run_dir']}"]
    for c in result["checks"]:
        lines.append(f"  [{c['item']:<13}] {c['got']:>5}/{c['max']:<3}  {'; '.join(c['details'])}")
    lines.append(f"  TOTAL: {result['total']}/{result['max']}")
    return "\n".join(lines)


def main(argv=None):
    ap = argparse.ArgumentParser(
        description="benchmarks 确定性自动检查器（满分 40）。"
    )
    ap.add_argument("--run-dir", required=True, help="某次 run 快照目录")
    ap.add_argument("--json", default=None, help="可选：将结果落盘的 JSON 路径")
    args = ap.parse_args(argv)

    run_dir = pathlib.Path(args.run_dir)
    if not run_dir.is_dir():
        print(f"错误：--run-dir 不是有效目录: {run_dir}", file=sys.stderr)
        return 2

    result = run_all(run_dir)
    print(_fmt(result))

    if args.json:
        out = pathlib.Path(args.json)
        out.write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8")
        print(f"[json] 结果已落到 {out}")
    return 0


if __name__ == "__main__":
    sys.exit(main())