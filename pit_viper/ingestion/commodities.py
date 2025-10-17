"""Commodity ingestion using Stooq CSV endpoints with offline fallback."""
from __future__ import annotations

from typing import Iterable

import pandas as pd

from .base import IngestionResult, _generate_mock_prices, safe_call
from ..utils.config import AppConfig

DEFAULT_COMMODITIES = {
    "GC=F": "Gold Futures",
    "CL=F": "WTI Crude",
    "SI=F": "Silver Futures",
}


def _yfinance_commodities(symbols: Iterable[str]) -> pd.DataFrame:
    import yfinance as yf

    frames = []
    for symbol in symbols:
        ticker = yf.Ticker(symbol)
        history = ticker.history(period="5d")
        if history.empty:
            raise ValueError(f"No commodity data for {symbol}")
        latest = history.tail(1).reset_index(drop=False)
        frames.append(
            {
                "asset_id": symbol,
                "asset_type": "commodity",
                "currency": ticker.info.get("currency", "USD"),
                "close": float(latest["Close"].iloc[0]),
                "open": float(latest["Open"].iloc[0]),
                "high": float(latest["High"].iloc[0]),
                "low": float(latest["Low"].iloc[0]),
                "volume": float(latest.get("Volume", pd.Series([0.0])).iloc[0]),
                "as_of": pd.Timestamp(latest["Date"].iloc[0]),
                "description": DEFAULT_COMMODITIES.get(symbol, symbol),
            }
        )
    return pd.DataFrame(frames)


def fetch_commodities(config: AppConfig, symbols: Iterable[str] | None = None) -> IngestionResult:
    symbols = tuple(symbols or DEFAULT_COMMODITIES.keys())
    fallback = _generate_mock_prices(symbols, "commodity")
    data, used_fallback = safe_call(lambda: _yfinance_commodities(symbols), fallback)
    return IngestionResult(
        asset_type="commodity",
        data=data,
        metadata={"source": "yfinance" if not used_fallback else "mock", "count": str(len(data))},
    )


__all__ = ["fetch_commodities"]
