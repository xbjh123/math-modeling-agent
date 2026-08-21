"""
greedy_segmentation.py
有序协变量异质性贪心切分算法 (Greedy Ordered Segmentation with Penalty)
"""
from typing import List, Tuple, Dict, Any
import numpy as np
import pandas as pd


def fit_group_linear(x_c: np.ndarray, y: np.ndarray) -> Tuple[float, float, int]:
    """组内拟合中心化后的线性趋势: y = alpha + beta * x_c"""
    n = len(y)
    if n < 3:
        return np.nan, np.nan, n
    x_mean = np.mean(x_c)
    y_mean = np.mean(y)
    ss_xx = np.sum((x_c - x_mean) ** 2)
    beta = np.sum((x_c - x_mean) * (y - y_mean)) / ss_xx if ss_xx > 1e-8 else 0.0
    alpha = y_mean - beta * x_mean
    return float(alpha), float(beta), n


def compute_heterogeneity(groups_data: List[Tuple[np.ndarray, np.ndarray]]) -> Tuple[float, List[Dict[str, float]]]:
    """计算各组的异质性加权指标 D(K)"""
    alphas, betas, weights = [], [], []
    for x_c, y in groups_data:
        a, b, w = fit_group_linear(x_c, y)
        alphas.append(a)
        betas.append(b)
        weights.append(w)
    
    weights = np.array(weights, dtype=float)
    total_w = np.sum(weights)
    if total_w == 0:
        return 0.0, []
    
    alpha_bar = np.sum(weights * np.array(alphas)) / total_w
    beta_bar = np.sum(weights * np.array(betas)) / total_w
    d_k = np.sum(weights * ((np.array(alphas) - alpha_bar) ** 2 + (np.array(betas) - beta_bar) ** 2))
    
    group_stats = [
        {"alpha": a, "beta": b, "n": int(w)} for a, b, w in zip(alphas, betas, weights)
    ]
    return float(d_k), group_stats


def greedy_ordered_partition(
    df: pd.DataFrame,
    split_col: str,
    x_col: str,
    y_col: str,
    penalty_lambda: float = 0.0055,
    min_leaf_size: int = 30,
    max_groups: int = 6
) -> Dict[str, Any]:
    """贪心迭代寻找最优切点集合 K"""
    data = df[[split_col, x_col, y_col]].dropna().copy()
    data['x_c'] = data[x_col] - data[x_col].mean()
    best_cuts: List[float] = []
    
    def get_groups_by_cuts(cuts: List[float]) -> List[Tuple[np.ndarray, np.ndarray]]:
        sorted_cuts = sorted(cuts)
        bins = [-np.inf] + sorted_cuts + [np.inf]
        cats = pd.cut(data[split_col], bins=bins)
        return [(group['x_c'].values, group[y_col].values) for _, group in data.groupby(cats, observed=False)]

    d0, stats0 = compute_heterogeneity(get_groups_by_cuts(best_cuts))
    current_obj = d0
    history = [{"step": 1, "cuts": [], "D_K": d0, "objective": current_obj}]

    for step in range(2, max_groups + 1):
        candidate_cuts = np.percentile(data[split_col], np.linspace(5, 95, 50))
        best_candidate = None
        best_cand_obj = -np.inf
        best_cand_dk = 0.0

        for cand in candidate_cuts:
            if any(abs(cand - existing) < 0.5 for existing in best_cuts):
                continue
            test_cuts = sorted(best_cuts + [cand])
            test_groups = get_groups_by_cuts(test_cuts)
            if any(len(y) < min_leaf_size for _, y in test_groups):
                continue
                
            dk, _ = compute_heterogeneity(test_groups)
            k_groups = len(test_cuts) + 1
            obj = dk - penalty_lambda * (k_groups - 1)
            
            if obj > best_cand_obj:
                best_cand_obj = obj
                best_candidate = cand
                best_cand_dk = dk

        if best_candidate is not None and (best_cand_obj - current_obj) > 1e-6:
            best_cuts.append(best_candidate)
            current_obj = best_cand_obj
            history.append({
                "step": step,
                "cuts": sorted(best_cuts),
                "D_K": best_cand_dk,
                "objective": current_obj
            })
        else:
            break

    final_cuts = sorted(best_cuts)
    _, final_group_stats = compute_heterogeneity(get_groups_by_cuts(final_cuts))

    return {
        "optimal_cuts": [round(c, 2) for c in final_cuts],
        "num_groups": len(final_cuts) + 1,
        "max_objective": current_obj,
        "iteration_history": history,
        "group_parameters": final_group_stats
    }
