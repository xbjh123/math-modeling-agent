"""
robust_qc_3zone.py
非参数数据质控、MAD 稳健质量指数与高特异度三区判定算法
"""
from typing import Dict, Any, List
import numpy as np
import pandas as pd


def robust_mad_scale(x: np.ndarray) -> np.ndarray:
    """基于中位数与中位绝对偏差(MAD)的稳健标准化"""
    med = np.nanmedian(x)
    mad = np.nanmedian(np.abs(x - med))
    if mad < 1e-8:
        return x - med
    return (x - med) / (1.4826 * mad)


def non_parametric_quality_control(
    df: pd.DataFrame,
    higher_better_cols: List[str],
    lower_better_cols: List[str],
    trim_pct: float = 0.05
) -> pd.DataFrame:
    """双侧非参数质控截断 (保留中心 90% 纯净样本)"""
    valid_mask = pd.Series(True, index=df.index)
    for col in higher_better_cols:
        valid_mask &= (df[col] >= df[col].quantile(trim_pct))
    for col in lower_better_cols:
        valid_mask &= (df[col] <= df[col].quantile(1.0 - trim_pct))
    return df[valid_mask].copy()


def compute_quality_index_and_zones(
    df_qc: pd.DataFrame,
    signal_col: str,
    higher_better_cols: List[str],
    lower_better_cols: List[str],
    gc_col: str,
    sp_lo: float = 0.99,
    sp_hi: float = 0.995
) -> Dict[str, Any]:
    """计算综合质量指数 QI，划分 Good/Typ/Marginal 三档，并确定条件双阈值三区"""
    df = df_qc.copy()
    qi = np.zeros(len(df))
    for col in higher_better_cols:
        qi += robust_mad_scale(df[col].values)
    for col in lower_better_cols:
        qi -= robust_mad_scale(df[col].values)
    if gc_col in df.columns:
        qi -= np.abs(robust_mad_scale(df[gc_col].values))
        
    df['QI'] = qi
    q20, q80 = np.percentile(df['QI'], [20, 80])
    df['tier'] = 'typ'
    df.loc[df['QI'] <= q20, 'tier'] = 'marg'
    df.loc[df['QI'] >= q80, 'tier'] = 'good'
    
    tier_thresholds = {}
    for tier_name in ['good', 'typ', 'marg']:
        sub_sig = df.loc[df['tier'] == tier_name, signal_col].dropna().values
        if len(sub_sig) == 0:
            continue
        z_lo = float(np.percentile(sub_sig, sp_lo * 100))
        z_hi = float(np.percentile(sub_sig, sp_hi * 100))
        z_hi = max(z_hi, z_lo + 0.05)
        
        tier_thresholds[tier_name] = {
            "n_samples": len(sub_sig),
            "z_threshold_lo (Sp>=99%)": round(z_lo, 3),
            "z_threshold_hi (Sp>=99.5%)": round(z_hi, 3),
            "decision_rule": f"Z < {z_lo:.3f}: 阴性 | {z_lo:.3f} <= Z < {z_hi:.3f}: 灰区复检 | Z >= {z_hi:.3f}: 阳性"
        }
        
    return {
        "qi_cutoffs": {"q20": round(q20, 3), "q80": round(q80, 3)},
        "tier_thresholds": tier_thresholds
    }
