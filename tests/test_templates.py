# -*- coding: utf-8 -*-
"""templates/main_template.tex 合规性校验。

覆盖国赛匿名性 / 目录页禁令 / 摘要关键词 / 已完成编译验证标记，
以及 \input 引用的全部 sections 文件真实存在。
"""
import re
from pathlib import Path


def _load_template(repo_root):
    p = Path(repo_root) / "templates" / "main_template.tex"
    assert p.is_file(), f"main_template.tex not found at {p}"
    return p.read_text(encoding="utf-8")


def _active_lines(tex: str) -> str:
    """剔除注释行（以 % 开头），仅对实际生效的 LaTeX 指令做校验。"""
    return "\n".join(
        line for line in tex.splitlines()
        if not line.strip().startswith("%")
    )


def test_no_tableofcontents(repo_root):
    tex = _active_lines(_load_template(repo_root))
    assert "\\tableofcontents" not in tex, "模板不得含 \\tableofcontents（国赛禁目录页）"


def test_no_author_field(repo_root):
    tex = _active_lines(_load_template(repo_root))
    assert "\\author{" not in tex, "模板不得含 \\author{（匿名性规定）"


def test_contains_keywords(repo_root):
    tex = _load_template(repo_root)
    assert "关键词" in tex, "摘要必须含“关键词”行"


def test_contains_verified_comment(repo_root):
    tex = _load_template(repo_root)
    assert re.search(r"Verified", tex), "模板应含 Verified 编译验证注释行"


def test_all_input_sections_exist(repo_root):
    tex = _load_template(repo_root)
    sections_dir = Path(repo_root) / "templates" / "sections"

    inputs = re.findall(r"\\input\{([^}]+)\}", tex)
    assert len(inputs) == 5, f"预期 5 个 \\input，实际 {len(inputs)}: {inputs}"

    for ref in inputs:
        # 形如 "sections/01_intro_eda.tex"，从 templates/ 解析相对路径
        rel = Path(ref)
        target = sections_dir / rel.name
        assert target.is_file(), (
            f"\\input{{sections/{rel.name}}} 引用的文件不存在于 {sections_dir}")


def test_sections_dir_placeholder_files(repo_root):
    """确保 sections/ 目录确实是 5 个占位文件相对齐。"""
    sections_dir = Path(repo_root) / "templates" / "sections"
    files = sorted(p.name for p in sections_dir.glob("*.tex"))
    expected = {
        "01_intro_eda.tex", "02_problem1_milp.tex", "03_problem2_cvar.tex",
        "04_problem3_corr.tex", "05_sensitivity_app.tex",
    }
    assert set(files) == expected, f"sections 文件不齐: {files}"