# -*- coding: utf-8 -*-
"""pytest 移植版：scripts/ 四个算法模块的冒烟回归测试。

源自 C:\\Users\\姜世骥\\math_modeling_test\\test_scripts.py，将原先的
record() 断言逐一改写为独立 test_ 函数，保留全部场景与随机种子，
确保结果仍可复现。公共合成数据构造已提取到 conftest.py 的 module 级 fixture。
"""
import numpy as np
import pandas as pd

from greedy_segmentation import greedy_ordered_partition
from lmm_variance_decomp import fit_lmm_with_variance_decomposition
from robust_qc_3zone import non_parametric_quality_control, compute_quality_index_and_zones
from cluster_bootstrap import cluster_bootstrap_ci


# =========================== greedy_segmentation ===========================

def test_greedy_recovers_real_cutpoint(greedy_recover_data):
    """场景 A：真实切点 split=50，应找回且只切一刀。"""
    df = greedy_recover_data
    out = greedy_ordered_partition(
        df, split_col="split", x_col="x", y_col="y",
        min_leaf_size=30, random_state=7)
    cuts = out["optimal_cuts"]
    assert len(cuts) == 1 and abs(cuts[0] - 50) <= 8, (
        f"cuts={cuts} (true=50), tests={out.get('significance_tests')}")


def test_greedy_no_false_split_on_homogeneous(greedy_homogeneous_data):
    """场景 B：同质数据不应切分（控制假阳性 / 假切点 bug）。"""
    out2 = greedy_ordered_partition(
        greedy_homogeneous_data, "split", "x", "y", random_state=7)
    assert len(out2["optimal_cuts"]) == 0, (
        f"cuts={out2['optimal_cuts']} on homogeneous data")


def test_greedy_scale_invariance(greedy_recover_data):
    """场景 C：y*1000 后切点结果应与原始一致（量纲缩放不变性）。"""
    df = greedy_recover_data
    cuts = greedy_ordered_partition(df, "split", "x", "y", random_state=7)["optimal_cuts"]

    df3 = df.copy()
    df3["y"] = df3["y"] * 1000
    out3 = greedy_ordered_partition(df3, "split", "x", "y", random_state=7)
    c3 = out3["optimal_cuts"]

    assert len(c3) == len(cuts) and all(abs(a - b) < 1e-6 for a, b in zip(c3, cuts)), (
        f"cuts(y*1000)={c3} vs cuts(y)={cuts}")


def test_greedy_three_segments(greedy_three_segment_data):
    """场景 D：三段真实区段（切点 33 / 66）。"""
    out4 = greedy_ordered_partition(
        greedy_three_segment_data, "split", "x", "y", random_state=11)
    c4 = out4["optimal_cuts"]
    assert len(c4) == 2 and abs(c4[0] - 33) < 6 and abs(c4[1] - 66) < 6, (
        f"cuts={c4} (true=33/66)")


# ========================= lmm_variance_decomp =========================

def test_lmm_random_intercept(lmm_data):
    """随机截距项方差应被分解为 ~4.0，残差 ~1.0。"""
    res = fit_lmm_with_variance_decomposition(
        lmm_data, formula="y ~ visit", group_col="subject")
    vd = res["variance_decomposition"]
    assert res["converged"], "LMM did not converge"
    assert abs(vd["random_variance"] - 4.0) < 1.5
    assert abs(vd["residual_variance"] - 1.0) < 0.4


def test_lmm_random_slope(lmm_data):
    """re_formula='1+visit' 时斜率方差进入分解且总随机方差 > 4。"""
    res2 = fit_lmm_with_variance_decomposition(
        lmm_data, formula="y ~ visit", group_col="subject", re_formula="1+visit")
    assert res2["converged"], "LMM(random slope) did not converge"
    rv2 = res2["variance_decomposition"]["random_variance"]
    assert rv2 > 4.0, f"total_rand_var={rv2:.3f} expected > 4"


# ========================== robust_qc_3zone ==========================

def test_robust_qc_3zone(robust_data):
    """三区键齐全且每层含必需键。"""
    qc = non_parametric_quality_control(
        robust_data, higher_better_cols=["aux"], lower_better_cols=["lowgood"])
    zones = compute_quality_index_and_zones(
        qc, signal_col="signal",
        higher_better_cols=["aux"], lower_better_cols=["lowgood"], gc_col="gc")
    tt = zones["tier_thresholds"]

    required = {"n_samples", "z_lo", "z_hi", "decision_rule"}
    assert set(tt.keys()) == {"good", "typ", "marg"}, f"tiers={sorted(tt.keys())}"
    assert all(required.issubset(v.keys()) for v in tt.values())


def test_robust_qc_nan_safe(robust_data):
    """信号列含 NaN 不应崩溃，且三区仍完整。"""
    dfa_nan = robust_data.copy()
    dfa_nan.loc[dfa_nan.index[:20], "signal"] = np.nan
    qc = non_parametric_quality_control(
        dfa_nan, higher_better_cols=["aux"], lower_better_cols=["lowgood"])
    zones_nan = compute_quality_index_and_zones(
        qc, signal_col="signal",
        higher_better_cols=["aux"], lower_better_cols=["lowgood"], gc_col="gc")
    assert set(zones_nan["tier_thresholds"].keys()) == {"good", "typ", "marg"}


# ========================== cluster_bootstrap ==========================

def test_bootstrap_point_matches_raw(bootstrap_data):
    """点估计应等于原始完整样本的均值（四舍五入到 3 位）。"""
    est = cluster_bootstrap_ci(
        bootstrap_data, cluster_col="sid",
        fit_and_eval_fn=lambda d: d["val"].mean(),
        n_boot=400, random_state=42)
    assert abs(est["point_estimate"]
               - round(bootstrap_data["val"].mean(), 3)) < 1e-9, (
        f"raw_mean={bootstrap_data['val'].mean():.4f}, point={est['point_estimate']}")


def test_bootstrap_counts_failures(bootstrap_data):
    """半数重采样抛异常时应记录 failed_replications 且仍能输出 CI。"""
    def flaky(d):
        if np.random.rand() < 0.5:
            raise ValueError("boom")
        return d["val"].mean()

    est2 = cluster_bootstrap_ci(bootstrap_data, "sid", flaky,
                                n_boot=200, random_state=1)
    assert not np.isnan(est2["ci_lower"])
    assert est2.get("failed_replications", -1) > 50
    assert est2.get("failure_rate", 0) > 0.2