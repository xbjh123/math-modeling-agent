"""
lmm_variance_decomp.py
线性混合效应模型（LMM）拟合、方差分解与边际/条件 R² 计算器

注意：
- 随机效应方差取协方差矩阵对角线之和（各 RE 项边际方差），
  正确支持 re_formula="1+x" 等多随机效应结构；
- 默认 BFGS 不收敛时自动以 lbfgs 重启一次。
"""
from typing import Dict, Any, Optional
import numpy as np
import pandas as pd
import statsmodels.formula.api as smf


def _fit_lmm(df: pd.DataFrame, formula: str, group_col: str, re_formula: str):
    md = smf.mixedlm(formula, df, groups=df[group_col], re_formula=re_formula)
    mdf = md.fit(reml=True)
    if not mdf.converged:
        mdf = md.fit(reml=True, method="lbfgs", start_params=mdf.params)
    return mdf


def fit_lmm_with_variance_decomposition(
    df: pd.DataFrame,
    formula: str,
    group_col: str,
    re_formula: str = "1"
) -> Dict[str, Any]:
    """拟合 LMM 并输出标准方差分解表（含各随机效应项的边际方差）"""
    df = df.copy()
    mdf = _fit_lmm(df, formula, group_col, re_formula)

    var_fixed = float(np.var(mdf.predict(df)))

    # 各随机效应项的边际方差 = 协方差矩阵对角线元素之和
    if hasattr(mdf.cov_re, "values"):
        re_diag = np.diag(mdf.cov_re.values.astype(float))
        re_names = list(mdf.cov_re.index)
    elif hasattr(mdf.cov_re, "iloc"):
        re_diag = np.diag(mdf.cov_re.iloc[:, :].values.astype(float))
        re_names = list(mdf.cov_re.index)
    else:
        re_diag = np.array([float(mdf.scale)])
        re_names = ["Group"]

    var_resid = float(mdf.scale)
    var_random = float(np.sum(re_diag))
    var_total = var_fixed + var_random + var_resid

    r2_marginal = var_fixed / var_total
    r2_conditional = (var_fixed + var_random) / var_total

    coef_summary = []
    for name in mdf.params.index:
        coef_summary.append({
            "param": name,
            "estimate": float(mdf.params[name]),
            "std_err": float(mdf.bse[name]),
            "z_val": float(mdf.tvalues[name]),
            "p_val": float(mdf.pvalues[name])
        })

    return {
        "coefficients": coef_summary,
        "variance_decomposition": {
            "fixed_variance": round(var_fixed, 4),
            "random_variance": round(var_random, 4),
            "residual_variance": round(var_resid, 4),
            "total_variance": round(var_total, 4),
            "marginal_r2": round(r2_marginal, 4),
            "conditional_r2": round(r2_conditional, 4)
        },
        "random_effect_components": {
            name: round(float(v), 4) for name, v in zip(re_names, re_diag)
        },
        "log_likelihood": float(mdf.llf),
        "converged": bool(mdf.converged)
    }
