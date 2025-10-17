"""Portfolio scoring and recommendation engine."""
from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, Iterable

import numpy as np
import pandas as pd


@dataclass
class ScoringWeights:
    valuation: float = 0.35
    momentum: float = 0.2
    liquidity: float = 0.15
    risk: float = 0.2
    diversification: float = 0.1


def _normalize(series: pd.Series) -> pd.Series:
    if series.empty:
        return series
    min_val = series.min()
    max_val = series.max()
    if min_val == max_val:
        return pd.Series(np.ones_like(series), index=series.index)
    return (series - min_val) / (max_val - min_val)


def score_assets(features: pd.DataFrame, weights: ScoringWeights | None = None) -> pd.DataFrame:
    if features.empty:
        return pd.DataFrame(columns=["asset_id", "score"])

    weights = weights or ScoringWeights()
    scored = features.copy()
    scored["valuation_score"] = _normalize(features.get("valuation_proxy", 0)).fillna(0)
    scored["momentum_score"] = _normalize(features.get("momentum_proxy", 0)).fillna(0)
    scored["liquidity_score_norm"] = _normalize(features.get("liquidity_score", 0)).fillna(0)
    scored["risk_score"] = 1 - _normalize(features.get("volatility_proxy", 0)).fillna(0)

    diversification_bonus = (
        scored.groupby("asset_type")["asset_id"].transform("count").rpow(-1).fillna(0)
    )

    scored["composite_score"] = (
        scored["valuation_score"] * weights.valuation
        + scored["momentum_score"] * weights.momentum
        + scored["liquidity_score_norm"] * weights.liquidity
        + scored["risk_score"] * weights.risk
        + diversification_bonus * weights.diversification
    )
    scored.sort_values("composite_score", ascending=False, inplace=True)
    scored.reset_index(drop=True, inplace=True)
    return scored


def summarize_recommendations(scored: pd.DataFrame, top_n: int = 10) -> pd.DataFrame:
    if scored.empty:
        return scored
    columns = [
        "asset_id",
        "asset_type",
        "composite_score",
        "close",
        "momentum_proxy",
        "volatility_proxy",
        "liquidity_score",
    ]
    available_columns = [col for col in columns if col in scored.columns]
    return scored.loc[: top_n - 1, available_columns].copy()


__all__ = ["ScoringWeights", "score_assets", "summarize_recommendations"]
