"""
robust_qc_3zone.py
非参数数据质控、MAD 稳健质量指数与高特异度三区判定算法

注意：三区阈值的"Sp>=99%"为经验近似——以各 QI 层内信号分布的
上尾经验分位数作为阈值，在层内阳性稀薄的前提下近似控制假阳性率；
若层内阳性占比不可忽略，应以独立阴性对照样本重新标定阈值。
"""
from typing import Dict, Any, List
import numpy as np
import pandas as pd


def robust_mad_scale(x: np.ndarray) -> np.ndarray:
    """基于中位数与中位绝对偏差(MAD)的稳健标准化（NaN 安全）"""
    x = np.asarray(x, dtype=float)
    med = np.nanmedian(x) if np.any(np.isfinite(x)) else 0.0
    mad = np.nanmedian(np.abs(x - med)) if np.any(np.isfinite(x)) else 0.0
    if not np.isfinite(mad) or mad < 1e-8:
        return np.where(np.isfinite(x), x - (med if np.isfinite(med) else 0.0), 0.0)
    return np.where(np.isfinite(x), (x - med) / (1.4826 * mad), 0.0)


def non_parametric_quality_control(
    df: pd.DataFrame,
    higher_better_cols: List[str],
    lower_better_cols: List[str],
    trim_pct: float = 0.05
) -> pd.DataFrame:
    """双侧非参数质控截断（保留中心纯净样本）

    higher_better_cols：过低（< trim_pct 分位）判为可疑剔除；
    lower_better_cols：过高（> 1-trim_pct 分位）判为可疑剔除。
    """
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
    sp_hi: float = 0.995,
    min_tier_n: int = 30
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

    tier_thresholds: Dict[str, Any] = {}
    for tier_name in ['good', 'typ', 'marg']:
        sub_sig = df.loc[df['tier'] == tier_name, signal_col].dropna().values
        if len(sub_sig) < min_tier_n:
            tier_thresholds[tier_name] = {
                "n_samples": int(len(sub_sig)),
                "status": f"skipped: n < {min_tier_n}, thresholds unreliable"
            }
            continue
        z_lo = float(np.percentile(sub_sig, sp_lo * 100))
        z_hi = float(np.percentile(sub_sig, sp_hi * 100))
        z_hi = max(z_hi, z_lo + 0.05)

        tier_thresholds[tier_name] = {
            "n_samples": int(len(sub_sig)),
            "z_lo": round(z_lo, 3),
            "z_hi": round(z_hi, 3),
            "specificity_targets": {"lo": sp_lo, "hi": sp_hi},
            "decision_rule": (
                f"Z < {z_lo:.3f}: 阴性 | "
                f"{z_lo:.3f} <= Z < {z_hi:.3f}: 灰区复检 | "
                f"Z >= {z_hi:.3f}: 阳性"
            )
        }

    return {
        "qi_cutoffs": {"q20": round(float(q20), 3), "q80": round(float(q80), 3)},
        "tier_thresholds": tier_thresholds
    }
