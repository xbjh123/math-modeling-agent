"""
cluster_bootstrap.py
基于主体 ID 的簇级 Bootstrap 置信区间与 MAD 噪声扰动模拟器

改进：
- point_est 改为原始完整样本的点估计（bootstrap 中位数仅作对照输出）；
- 记录失败重采样次数与失败率（fit_and_eval_fn 抛异常时静默跳过会低估方差）；
- 支持 random_state 保证可复现。
"""
from typing import Callable, Dict, Any, List
import numpy as np
import pandas as pd


def cluster_bootstrap_ci(
    df: pd.DataFrame,
    cluster_col: str,
    fit_and_eval_fn: Callable[[pd.DataFrame], float],
    n_boot: int = 500,
    ci: float = 0.95,
    random_state: Any = None,
    max_failure_rate: float = 0.2
) -> Dict[str, Any]:
    """对同一对象的重复测量进行簇级重采样，获得估计值的置信区间

    返回字段：point_estimate（原始样本点估计）、ci_lower/ci_upper、
    bootstrap_median、failed_replications、failure_rate、warning。
    """
    unique_clusters = df[cluster_col].unique()
    n_clusters = len(unique_clusters)
    rng = np.random.default_rng(random_state)

    estimates: List[float] = []
    failed = 0

    for _ in range(n_boot):
        sampled_clusters = rng.choice(unique_clusters, size=n_clusters, replace=True)
        boot_sample = pd.concat(
            [df[df[cluster_col] == cid] for cid in sampled_clusters],
            ignore_index=True
        )
        try:
            val = fit_and_eval_fn(boot_sample)
            if not np.isnan(val):
                estimates.append(float(val))
            else:
                failed += 1
        except Exception:
            failed += 1

    alpha = (1.0 - ci) / 2.0
    result: Dict[str, Any] = {
        "point_estimate": np.nan,
        "ci_lower": np.nan,
        "ci_upper": np.nan,
        "bootstrap_median": np.nan,
        "successful_replications": len(estimates),
        "failed_replications": failed,
    }

    if not estimates:
        result["warning"] = "all replications failed"
        return result

    lower = float(np.percentile(estimates, alpha * 100))
    upper = float(np.percentile(estimates, (1.0 - alpha) * 100))

    try:
        raw_point = float(fit_and_eval_fn(df))
    except Exception:
        raw_point = float(np.median(estimates))

    failure_rate = failed / float(n_boot)
    result.update({
        "point_estimate": round(raw_point, 3),
        "ci_lower": round(lower, 3),
        "ci_upper": round(upper, 3),
        "bootstrap_median": round(float(np.median(estimates)), 3),
        "failure_rate": round(failure_rate, 3)
    })

    if failure_rate > max_failure_rate:
        result["warning"] = (
            f"failure rate {failure_rate:.1%} exceeds {max_failure_rate:.0%}; "
            "CI may be biased — inspect fit_and_eval_fn stability"
        )
    return result


def mad_perturbation_analysis(
    df: pd.DataFrame,
    value_cols: List[str],
    fit_and_eval_fn: Callable[[pd.DataFrame], float],
    n_sims: int = 200,
    scale: float = 1.4826,
    random_state: Any = None
) -> Dict[str, Any]:
    """对指定列注入 MAD 尺度噪声，评估估计值的稳健性分布"""
    rng = np.random.default_rng(random_state)
    base = df.copy()
    ests: List[float] = []
    for _ in range(n_sims):
        perturbed = df.copy()
        for c in value_cols:
            med = np.nanmedian(base[c])
            mad = np.nanmedian(np.abs(base[c] - med))
            sigma = scale * mad
            perturbed[c] = perturbed[c] + rng.normal(0, sigma, len(perturbed))
        try:
            v = fit_and_eval_fn(perturbed)
            if not np.isnan(v):
                ests.append(float(v))
        except Exception:
            continue
    if not ests:
        return {"base_estimate": np.nan, "perturb_median": np.nan, "perturb_iqr": np.nan}
    try:
        base_est = float(fit_and_eval_fn(base))
    except Exception:
        base_est = float(np.median(ests))
    return {
        "base_estimate": round(base_est, 4),
        "perturb_median": round(float(np.median(ests)), 4),
        "perturb_iqr": round(float(np.percentile(ests, 75) - np.percentile(ests, 25)), 4),
        "n_valid": len(ests)
    }
