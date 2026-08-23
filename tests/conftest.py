# -*- coding: utf-8 -*-
"""math-modeling-agent 测试公共配置与合成数据 fixture。

延续原回归脚本 C:\\Users\\姜世骥\\math_modeling_test\\test_scripts.py：
为保证结果完全复现，此处**忠实复现**原脚本的生成逻辑 —— 在模块导入时用
`np.random.seed(42)` 并严格按原脚本的 RNG 消费顺序（greedy A/B/D → lmm →
robust → bootstrap）一次性构造全部合成数据，再把各子集作为 module 级 fixture
暴露给测试。这样无论测试收集顺序如何，数据与原始回归一致。

同时把 scripts/ 目录挂到 sys.path 顶部，使测试可直接 import 算法模块。
"""
import sys
import warnings
import numpy as np
import pandas as pd
from pathlib import Path

import pytest

# 与原回归脚本一致的全局噪声抑制。
warnings.filterwarnings("ignore")

REPO_ROOT = Path(__file__).resolve().parents[1]
SCRIPTS_DIR = REPO_ROOT / "scripts"
TEMPLATES_DIR = REPO_ROOT / "templates"

if str(SCRIPTS_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPTS_DIR))


# ---------------------------------------------------------------------------
# 忠实复现原脚本的数据构造（seed 42，RNG 消费顺序与原脚本逐字一致）
# ---------------------------------------------------------------------------
np.random.seed(42)

# --- greedy 场景 A（并派生 B、C、D 共享的 split / xc 基向量）---
_n_g = 200
_split = np.random.uniform(0, 100, _n_g)
_xc = np.random.normal(0, 2, _n_g)
_y = np.where(_split < 50, 2 + 0.5 * _xc, 10 - 1.0 * _xc) + np.random.normal(0, 0.5, _n_g)
_dfA = pd.DataFrame({"split": _split, "x": _xc, "y": _y})

_y2 = 3 + 0.7 * _xc + np.random.normal(0, 0.5, _n_g)
_dfB = pd.DataFrame({"split": _split, "x": _xc, "y": _y2})

_y4 = (np.select([_split < 33, _split < 66], [1 + 0.2 * _xc, 5 + 0.2 * _xc],
                 default=9 + 0.2 * _xc) + np.random.normal(0, 0.3, _n_g))
_dfD = pd.DataFrame({"split": _split, "x": _xc, "y": _y4})

# --- lmm 场景 ---
_n_sub, _n_vis = 40, 4
_subj = np.repeat(np.arange(_n_sub), _n_vis)
_visit = np.tile(np.arange(_n_vis), _n_sub).astype(float)
_re_int = np.random.normal(0, 2.0, _n_sub)
_y_l = 5 + 0.8 * _visit + _re_int[_subj] + np.random.normal(0, 1.0, _n_sub * _n_vis)
_dfl = pd.DataFrame({"y": _y_l, "visit": _visit, "subject": _subj})

# --- robust 场景 ---
_n_r = 600
_sig = np.concatenate([
    np.random.normal(0.2, 0.15, int(_n_r * 0.85)),
    np.random.normal(3.0, 0.8, _n_r - int(_n_r * 0.85)),
])
_dfr = pd.DataFrame({
    "signal": _sig,
    "aux": np.random.normal(10, 2, _n_r),
    "lowgood": np.random.normal(50, 5, _n_r),
    "gc": np.random.normal(12, 1, _n_r),
})

# --- bootstrap 场景 ---
_brows = []
for s in range(25):
    m = np.random.normal(10, 1.5)
    for _ in range(np.random.randint(2, 6)):
        _brows.append((s, m + np.random.normal(0, 0.5)))
_dfb = pd.DataFrame(_brows, columns=["sid", "val"])


@pytest.fixture(scope="module")
def repo_root():
    return REPO_ROOT


@pytest.fixture(scope="module")
def greedy_recover_data():
    return _dfA.copy()


@pytest.fixture(scope="module")
def greedy_homogeneous_data():
    return _dfB.copy()


@pytest.fixture(scope="module")
def greedy_three_segment_data():
    return _dfD.copy()


@pytest.fixture(scope="module")
def lmm_data():
    return _dfl.copy()


@pytest.fixture(scope="module")
def robust_data():
    return _dfr.copy()


@pytest.fixture(scope="module")
def bootstrap_data():
    return _dfb.copy()