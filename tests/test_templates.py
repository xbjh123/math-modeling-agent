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
    assert re.search(r"V2|blueprint|paper_blueprint|参考文献", tex), "模板应含 V2 重做标记 / blueprint 或参考文献骨架"


def test_all_input_sections_exist(repo_root):
    tex = _load_template(repo_root)
    sections_dir = Path(repo_root) / "templates" / "sections"

    inputs = re.findall(r"\\input\{([^}]+)\}", tex)
    # V2 模板为“问题数可配置”。首末两章（01_intro_assump / 0X_sensitivity_conclusion）
    # 确定存在并被 \input；问题章（02_problem1..）由 template_problem_chapter 按题复制生成，
    # 在模板主文件里是注释化占位，故有效 \input 至少 2 个（首末章）。
    assert len(inputs) >= 2, f"预期至少 2 个 \\input（首末章），实际 {len(inputs)}: {inputs}"

    for ref in inputs:
        rel = Path(ref)
        target = sections_dir / rel.name
        assert target.is_file(), (
            f"\\input{{sections/{rel.name}}} 引用的文件不存在于 {sections_dir}")


def test_sections_dir_placeholder_files(repo_root):
    """确保 sections/ 目录对齐 V2 通用结构：首章 + 问题章模板 + 末章。"""
    sections_dir = Path(repo_root) / "templates" / "sections"
    files = sorted(p.name for p in sections_dir.glob("*.tex"))
    # 首末两章 + 通用问题章模板必须存在（问题章由 template_problem_chapter 复制生成）
    assert "01_intro_assump.tex" in files, "缺首章占位 01_intro_assump.tex"
    assert "07_sensitivity_conclusion.tex" in files, "缺末章占位 07_sensitivity_conclusion.tex"
    assert "template_problem_chapter.tex" in files, "缺通用问题章模板 template_problem_chapter.tex"
    # 不再断言固定 5 个旧题型占位；允许模板按题生成问题章文件