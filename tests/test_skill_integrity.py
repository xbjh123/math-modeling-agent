# -*- coding: utf-8 -*-
"""完整性校验：SKILL.md 引用的 roles/*.md 与 scripts/*.py 文件必须真实存在。

防止再次出现悬空引用（SKILL.md 提到某角色/脚本，但对应文件缺失）。
"""
import re
from pathlib import Path


def _skill_md(repo_root):
    p = Path(repo_root) / "SKILL.md"
    assert p.is_file(), f"SKILL.md not found at {p}"
    return p.read_text(encoding="utf-8")


def _referenced_files(repo_root):
    text = _skill_md(repo_root)
    refs = {
        "roles": re.findall(r"roles/[a-z_]+\.md", text),
        # SKILL.md 以反引号裸文件名（如 `greedy_segmentation.py`）引用脚本，
        # 也兼容 `scripts/xxx.py` 形式；统一按词边界抽取 .py 文件引用防悬空。
        "scripts": re.findall(r"scripts/[a-z_0-9]+\.py", text)
        or re.findall(r"\b[a-z_][a-z_0-9]*\.py\b", text),
    }
    return refs


def test_role_files_exist(repo_root):
    refs = _referenced_files(repo_root)
    assert refs["roles"], "SKILL.md 中未抽取到任何 roles/*.md 引用"
    for ref in refs["roles"]:
        target = Path(repo_root) / ref
        assert target.is_file(), f"悬空引用: {ref} 不存在"


def _resolve(repo_root, ref: str):
    """把引用解析为仓库内路径：带 scripts/ 前缀直接用，否则挂到 scripts/ 下。"""
    if ref.startswith("scripts/"):
        return Path(repo_root) / ref
    return Path(repo_root) / "scripts" / ref


def test_script_files_exist(repo_root):
    refs = _referenced_files(repo_root)
    assert refs["scripts"], "SKILL.md 中未抽取到任何 scripts/*.py 引用"
    for ref in refs["scripts"]:
        target = _resolve(repo_root, ref)
        assert target.is_file(), f"悬空引用: {ref} 不存在"


def test_main_script_table_matches_disk(repo_root):
    """SKILL.md 的 scripts/ 工具箱表格引用的 4 个脚本应与 scripts/ 目录一致。"""
    refs = _referenced_files(repo_root)
    on_disk = {p.name for p in (Path(repo_root) / "scripts").glob("*.py")}
    mentioned = {Path(r).name for r in refs["scripts"]}
    assert mentioned.issubset(on_disk), f"表格提到的脚本与磁盘不一致: {mentioned - on_disk}"