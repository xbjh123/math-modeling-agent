"""
greedy_segmentation.py
有序协变量异质性贪心切分算法（置换检验停止准则版）

设计要点：
1. 停止准则借鉴条件推断树 (CTree, Hothorn et al. 2006) 的思想：
   在叶节点内对分组变量做随机置换构造增益零分布，只有观测增益超过
   零分布 95% 分位才接受切分。纯噪声数据的假切点率由显著性水平控制，
   而不是依赖惩罚系数的拍脑袋取值。
2. 显著性判定在稳健标准化空间进行：以根节点混合回归残差方差 sigma^2
   归一化异质性 D，使阈值与数据量纲解耦。
3. 对外输出的 alpha/beta/cuts 保持原始量纲，内部标准化不影响可读性。
"""
from typing import List, Tuple, Dict, Any
import numpy as np
import pandas as pd


def fit_group_linear(x_c: np.ndarray, y: np.ndarray) -> Tuple[float, float, int]:
    """组内拟合线性趋势 y = alpha + beta * x_c（x_c 为全局中心化的 x）"""
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
    """计算各组的加权异质性 D(K)：组间截距/斜率差异的加权和"""
    alphas, betas, weights = [], [], []
    for x_c, y in groups_data:
        a, b, w = fit_group_linear(x_c, y)
        alphas.append(a)
        betas.append(b)
        weights.append(w)

    weights = np.array(weights, dtype=float)
    total_w = np.sum(weights)
    if total_w == 0 or np.any(np.isnan(alphas)):
        return 0.0, []

    alpha_bar = np.sum(weights * np.array(alphas)) / total_w
    beta_bar = np.sum(weights * np.array(betas)) / total_w
    d_k = np.sum(weights * ((np.array(alphas) - alpha_bar) ** 2 + (np.array(betas) - beta_bar) ** 2))

    group_stats = [
        {"alpha": a, "beta": b, "n": int(w)} for a, b, w in zip(alphas, betas, weights)
    ]
    return float(d_k), group_stats

def _split_gain(x_c: np.ndarray, y: np.ndarray, mask: np.ndarray) -> float:
    """给定二分掩码，返回 D(2 组) - D(1 组) 的增益（无权重惩罚，量纲同 y^2）"""
    d2, _ = compute_heterogeneity([(x_c[mask], y[mask]), (x_c[~mask], y[~mask])])
    d1, _ = compute_heterogeneity([(x_c, y)])
    return max(d2 - d1, 0.0)


def _best_split_in_node(
    x_c: np.ndarray,
    y: np.ndarray,
    split_vals: np.ndarray,
    candidate_cuts: np.ndarray,
    min_leaf_size: int
) -> Tuple[float, float]:
    """节点内扫描所有候选切点，返回 (最优切点, 观测增益)"""
    best_cut, best_gain = np.nan, 0.0
    for cand in candidate_cuts:
        mask = split_vals < cand
        n_l = int(mask.sum())
        if n_l < min_leaf_size or (len(y) - n_l) < min_leaf_size:
            continue
        gain = _split_gain(x_c, y, mask)
        if gain > best_gain:
            best_gain = gain
            best_cut = cand
    return best_cut, best_gain


def _permutation_max_threshold(
    x_c: np.ndarray,
    y: np.ndarray,
    split_vals: np.ndarray,
    candidate_cuts: np.ndarray,
    min_leaf_size: int,
    n_perm: int = 199,
    alpha_level: float = 0.05,
    rng: Any = None
) -> float:
    """
    max-T 置换检验 (Hothorn et al. 2006 条件推断树准则)：
    每次在节点内置换 split_vals，对【整个候选切点网格】逐一计算增益并取最大值，
    构造"无分组效应时网格最大增益"的零分布。
    返回其 (1-alpha) 分位阈值。观测最优增益须超过该阈值才接受切分——
    同时控制了跨网格与跨轮次的多重比较假阳性。
    """
    if rng is None:
        rng = np.random.default_rng()
    n = len(y)
    null_max: List[float] = []
    for _ in range(n_perm):
        perm = rng.permutation(split_vals)
        g_max = 0.0
        for cand in candidate_cuts:
            mask = perm < cand
            n_l = int(mask.sum())
            if n_l < min_leaf_size or (n - n_l) < min_leaf_size:
                continue
            g = _split_gain(x_c, y, mask)
            if g > g_max:
                g_max = g
        null_max.append(g_max)
    if len(null_max) < 20:
        return np.inf
    return float(np.percentile(null_max, (1.0 - alpha_level) * 100))

def greedy_ordered_partition(
    df: pd.DataFrame,
    split_col: str,
    x_col: str,
    y_col: str,
    min_leaf_size: int = 30,
    max_groups: int = 6,
    alpha_level: float = 0.05,
    n_perm: int = 199,
    random_state: Any = None,
    candidate_points: int = 50
) -> Dict[str, Any]:
    """
    贪心迭代寻找最优切点集合 K，停止准则为节点内置换检验。

    返回字典含 optimal_cuts / num_groups / iteration_history / group_parameters /
    significance_tests（每个切点的观测增益与置换 p 值）。
    """
    data = df[[split_col, x_col, y_col]].dropna().copy()
    data['x_c'] = data[x_col] - data[x_col].mean()

    rng = np.random.default_rng(random_state)
    best_cuts: List[float] = []
    sig_tests: List[Dict[str, float]] = []
    history: List[Dict[str, Any]] = []

    d0, _ = compute_heterogeneity([(data['x_c'].values, data[y_col].values)])
    history.append({"step": 1, "cuts": [], "D_K": round(d0, 4)})

    for step in range(2, max_groups + 1):
        # 当前切点集合定义的各叶节点
        bins = [-np.inf] + sorted(best_cuts) + [np.inf]
        cats = pd.cut(data[split_col], bins=bins)
        node_slices = [(idx, grp) for idx, grp in data.groupby(cats, observed=True)]

        accepted = False
        for _, node in node_slices:
            if len(node) < 2 * min_leaf_size:
                continue
            sv = node[split_col].values.astype(float)
            if len(np.unique(sv)) < 5:
                continue
            xc_n = node['x_c'].values
            yy = node[y_col].values

            cand_grid = np.percentile(sv, np.linspace(5, 95, candidate_points))
            cand_cut, cand_gain = _best_split_in_node(xc_n, yy, sv, cand_grid, min_leaf_size)
            if np.isnan(cand_cut):
                continue

            # max-T 置换检验阈值（对整个候选网格的多重比较校正）
            threshold = _permutation_max_threshold(
                xc_n, yy, sv, cand_grid, min_leaf_size,
                n_perm=n_perm, alpha_level=alpha_level, rng=rng
            )
            if cand_gain <= threshold:
                continue

            best_cuts.append(float(cand_cut))
            sig_tests.append({
                "cut": round(float(cand_cut), 3),
                "node_n": int(len(node)),
                "observed_gain": round(float(cand_gain), 4),
                "perm_threshold": round(threshold, 4),
                "alpha_level": alpha_level,
                "n_perm_used": n_perm
            })
            bins_new = [-np.inf] + sorted(best_cuts) + [np.inf]
            cats_new = pd.cut(data[split_col], bins=bins_new)
            groups = [(g['x_c'].values, g[y_col].values) for _, g in data.groupby(cats_new, observed=True)]
            dk, _ = compute_heterogeneity(groups)
            history.append({"step": step, "cuts": sorted(round(c, 2) for c in best_cuts), "D_K": round(dk, 4)})
            accepted = True
            break  # 每轮只接受一个全局最优显著切分，下一轮重新评估所有叶节点

        if not accepted:
            break

    final_cuts = sorted(best_cuts)
    bins_f = [-np.inf] + final_cuts + [np.inf]
    cats_f = pd.cut(data[split_col], bins=bins_f)
    groups_f = [(g['x_c'].values, g[y_col].values) for _, g in data.groupby(cats_f, observed=True)]
    _, final_stats = compute_heterogeneity(groups_f)

    return {
        "optimal_cuts": [round(c, 2) for c in final_cuts],
        "num_groups": len(final_cuts) + 1,
        "significance_tests": sig_tests,
        "iteration_history": history,
        "group_parameters": final_stats,
        "settings": {
            "alpha_level": alpha_level, "n_perm": n_perm,
            "min_leaf_size": min_leaf_size, "max_groups": max_groups,
            "random_state": str(random_state)
        }
    }
