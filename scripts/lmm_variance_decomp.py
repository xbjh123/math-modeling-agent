"""
lmm_variance_decomp.py
线性混合效应模型（LMM）拟合、方差分解与边际/条件 R² 计算器
"""
from typing import Dict, Any
import numpy as np
import pandas as pd
import statsmodels.formula.api as smf


def fit_lmm_with_variance_decomposition(
    df: pd.DataFrame,
    formula: str,
    group_col: str,
    re_formula: str = "1"
) -> Dict[str, Any]:
    """拟合 LMM 并输出标准方差分解表"""
    md = smf.mixedlm(formula, df, groups=df[group_col], re_formula=re_formula)
    mdf = md.fit(reml=True)
    
    var_fixed = float(np.var(mdf.predict(df)))
    var_random = float(mdf.cov_re.iloc[0, 0]) if hasattr(mdf.cov_re, 'iloc') else float(mdf.scale)
    var_resid = float(mdf.scale)
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
            "fixed_variance": var_fixed,
            "random_variance": var_random,
            "residual_variance": var_resid,
            "total_variance": var_total,
            "marginal_r2": round(r2_marginal, 4),
            "conditional_r2": round(r2_conditional, 4)
        },
        "log_likelihood": float(mdf.llf),
        "converged": bool(mdf.converged)
    }
