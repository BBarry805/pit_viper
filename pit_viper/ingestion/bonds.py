"""Bond ingestion using FRED yields with deterministic fallback."""
from __future__ import annotations

from typing import Iterable

import pandas as pd

from .base import IngestionResult, _generate_mock_prices, safe_call
from ..utils.config import AppConfig

DEFAULT_BOND_SERIES = {
    "DGS10": "10Y Treasury",
    "DGS2": "2Y Treasury",
    "BAMLH0A0HYM2": "High Yield OAS",
}


def _fred_series(series_ids: Iterable[str]) -> pd.DataFrame:
    from fredapi import Fred

    fred = Fred()
    frames = []
    for series_id in series_ids:
        series = fred.get_series_latest_release(series_id)
        if series is None or series.empty:
            raise ValueError(f"No FRED data for {series_id}")
        latest_value = float(series.iloc[-1])
        frames.append(
            {
                "asset_id": series_id,
                "asset_type": "bond",
                "currency": "USD",
                "close": latest_value,
                "open": latest_value,
                "high": latest_value,
                "low": latest_value,
                "volume": 0.0,
                "as_of": pd.Timestamp.utcnow(),
                "description": DEFAULT_BOND_SERIES.get(series_id, series_id),
            }
        )
    return pd.DataFrame(frames)


def fetch_bonds(config: AppConfig, series_ids: Iterable[str] | None = None) -> IngestionResult:
    series_ids = tuple(series_ids or DEFAULT_BOND_SERIES.keys())
    fallback = _generate_mock_prices(series_ids, "bond")
    data, used_fallback = safe_call(lambda: _fred_series(series_ids), fallback)
    return IngestionResult(
        asset_type="bond",
        data=data,
        metadata={"source": "fred" if not used_fallback else "mock", "count": str(len(data))},
    )


__all__ = ["fetch_bonds"]
