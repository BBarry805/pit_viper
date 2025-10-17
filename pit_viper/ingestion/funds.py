"""Mutual fund and ETF ingestion leveraging yahoo finance."""
from __future__ import annotations

from typing import Iterable, List

import pandas as pd

from .base import IngestionResult, _generate_mock_prices, safe_call
from ..utils.config import AppConfig

DEFAULT_FUND_SYMBOLS = ("VTI", "VXUS", "BND")


def _yfinance_funds(symbols: Iterable[str]) -> pd.DataFrame:
    import yfinance as yf

    frames: List[pd.DataFrame] = []
    for symbol in symbols:
        ticker = yf.Ticker(symbol)
        info = ticker.info or {}
        nav = info.get("navPrice") or info.get("regularMarketPrice")
        if nav is None:
            raise ValueError(f"No NAV for {symbol}")
        frames.append(
            pd.DataFrame(
                {
                    "asset_id": [symbol],
                    "asset_type": ["fund"],
                    "currency": [info.get("currency", "USD")],
                    "close": [float(nav)],
                    "open": [float(info.get("regularMarketOpen", nav))],
                    "high": [float(info.get("regularMarketDayHigh", nav))],
                    "low": [float(info.get("regularMarketDayLow", nav))],
                    "volume": [float(info.get("regularMarketVolume", 0.0))],
                    "as_of": [pd.Timestamp.utcnow()],
                }
            )
        )
    return pd.concat(frames, ignore_index=True)


def fetch_funds(config: AppConfig, symbols: Iterable[str] | None = None) -> IngestionResult:
    symbols = tuple(symbols or DEFAULT_FUND_SYMBOLS)
    fallback = _generate_mock_prices(symbols, "fund")
    data, used_fallback = safe_call(lambda: _yfinance_funds(symbols), fallback)
    return IngestionResult(
        asset_type="fund",
        data=data,
        metadata={"source": "yfinance" if not used_fallback else "mock", "count": str(len(data))},
    )


__all__ = ["fetch_funds"]
