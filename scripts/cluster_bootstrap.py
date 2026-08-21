"""
cluster_bootstrap.py
基于主体 ID 的簇级 Bootstrap 置信区间与 MAD 噪声扰动模拟器
"""
from typing import Callable, Dict, Any, List
import numpy as np
import pandas as pd


def cluster_bootstrap_ci(
    df: pd.DataFrame,
    cluster_col: str,
    fit_and_eval_fn: Callable[[pd.DataFrame], float],
    n_boot: int = 500,
    ci: float = 0.95
) -> Dict[str, float]:
    """对同一对象的重复测量进行簇级重采样，获得估计值的 95% CI"""
    unique_clusters = df[cluster_col].unique()
    n_clusters = len(unique_clusters)
    estimates: List[float] = []
    
    for _ in range(n_boot):
        sampled_clusters = np.random.choice(unique_clusters, size=n_clusters, replace=True)
        boot_sample = pd.concat([df[df[cluster_col] == cid] for cid in sampled_clusters], ignore_index=True)
        try:
            val = fit_and_eval_fn(boot_sample)
            if not np.isnan(val):
                estimates.append(val)
        except Exception:
            continue
            
    if len(estimates) < 10:
        return {"point_est": np.nan, "ci_lower": np.nan, "ci_upper": np.nan}
        
    alpha = (1.0 - ci) / 2.0
    lower = float(np.percentile(estimates, alpha * 100))
    upper = float(np.percentile(estimates, (1.0 - alpha) * 100))
    point_est = float(np.median(estimates))
    
    return {
        "point_est": round(point_est, 3),
        "ci_lower": round(lower, 3),
        "ci_upper": round(upper, 3),
        "successful_replications": len(estimates)
    }
