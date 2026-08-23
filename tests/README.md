# tests/ —— math-modeling-agent 测试套件

本目录存放仓库的回归测试与结构校验测试。

## 运行方式（本地）

```bash
# 从仓库根执行
python -m pytest tests/ -v
```

依赖：`numpy pandas scipy statsmodels pytest`（脚本算法测试需要）。

```bash
python -m pip install numpy pandas scipy statsmodels pytest
```

## 测试文件一览

| 文件 | 内容 |
| :--- | :--- |
| `conftest.py` | 公共 fixture：把 `scripts/` 挂到 `sys.path`，构造确定性合成数据（各场景保留 seed 42） |
| `test_scripts.py` | `scripts/` 下 4 个算法模块的冒烟回归（greedy / lmm / robust_qc / cluster_bootstrap） |
| `test_templates.py` | 校验 `templates/main_template.tex` 的匿名性、禁止目录页、摘要关键词、Verified 注释，以及 5 个 `\input` 的 sections 文件齐全 |
| `test_skill_integrity.py` | 校验 `SKILL.md` 引用的 `roles/*.md` 与 `scripts/*.py` 全部真实存在，防悬空引用 |

## CI

GitHub Actions 已配置于 `.github/workflows/ci.yml`：push/PR 到 `main` 时自动跑全部 pytest，
外加一次 Tectonic 中文模板编译冒烟（ctex 首次需联网下载，compile step 预留 ≥ 15 分钟）。