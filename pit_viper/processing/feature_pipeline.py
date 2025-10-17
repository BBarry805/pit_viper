"""Data cleaning and feature engineering for market data."""
from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable, List

import numpy as np
import pandas as pd

from ..ingestion.base import IngestionResult


@dataclass
class FeaturePipelineResult:
    combined: pd.DataFrame
    features: pd.DataFrame


def clean_and_combine(results: Iterable[IngestionResult]) -> pd.DataFrame:
    frames: List[pd.DataFrame] = []
    for result in results:
        frame = result.data.copy()
        frame["asset_type"] = result.asset_type
        frame["asset_id"] = frame["asset_id"].astype(str)
        frame["close"] = pd.to_numeric(frame["close"], errors="coerce")
        frame["volume"] = pd.to_numeric(frame.get("volume", np.nan), errors="coerce")
        frame["as_of"] = pd.to_datetime(frame.get("as_of", pd.Timestamp.utcnow()), utc=True, errors="coerce").dt.tz_localize(None)
        frames.append(frame)
    if not frames:
        return pd.DataFrame()
    combined = pd.concat(frames, ignore_index=True)
    combined.dropna(subset=["asset_id", "close"], inplace=True)
    combined.sort_values(["asset_id", "as_of"], inplace=True)
    combined.reset_index(drop=True, inplace=True)
    return combined


def engineer_features(combined: pd.DataFrame) -> pd.DataFrame:
    if combined.empty:
        return pd.DataFrame()
    feature_frame = combined.copy()
    feature_frame["log_close"] = np.log(feature_frame["close"].clip(lower=1e-6))
    feature_frame["liquidity_score"] = np.log1p(feature_frame.get("volume", 0)).fillna(0)
    feature_frame["volatility_proxy"] = (
        (feature_frame.get("high", feature_frame["close"]) - feature_frame.get("low", feature_frame["close"]))
        / feature_frame["close"].replace(0, np.nan)
    ).fillna(0)
    feature_frame["momentum_proxy"] = (
        feature_frame["close"].pct_change().fillna(0)
    )
    feature_frame["valuation_proxy"] = 1 / feature_frame["log_close"].replace(0, np.nan)
    feature_frame.replace([np.inf, -np.inf], np.nan, inplace=True)
    feature_frame.fillna(0, inplace=True)
    return feature_frame


def run_feature_pipeline(results: Iterable[IngestionResult]) -> FeaturePipelineResult:
    combined = clean_and_combine(results)
    features = engineer_features(combined)
    return FeaturePipelineResult(combined=combined, features=features)


__all__ = ["FeaturePipelineResult", "run_feature_pipeline"]
