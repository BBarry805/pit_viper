"""Equity and ETF ingestion leveraging yfinance with Alpha Vantage fallback."""
from __future__ import annotations

from typing import Iterable, List

import pandas as pd

from .base import IngestionResult, _generate_mock_prices, safe_call
from ..utils.config import AppConfig

DEFAULT_EQUITY_SYMBOLS = ("AAPL", "MSFT", "SPY")


def _yfinance_prices(symbols: Iterable[str]) -> pd.DataFrame:
    import yfinance as yf

    frames: List[pd.DataFrame] = []
    for symbol in symbols:
        ticker = yf.Ticker(symbol)
        history = ticker.history(period="5d")
        if history.empty:
            raise ValueError(f"No history for {symbol}")
        latest = history.tail(1).reset_index(drop=False)
        frames.append(
            pd.DataFrame(
                {
                    "asset_id": [symbol],
                    "asset_type": ["equity"],
                    "currency": [ticker.info.get("currency", "USD")],
                    "close": [float(latest["Close"].iloc[0])],
                    "open": [float(latest["Open"].iloc[0])],
                    "high": [float(latest["High"].iloc[0])],
                    "low": [float(latest["Low"].iloc[0])],
                    "volume": [float(latest["Volume"].iloc[0])],
                    "as_of": [pd.Timestamp(latest["Date"].iloc[0])],
                }
            )
        )
    return pd.concat(frames, ignore_index=True)


def fetch_equities(config: AppConfig, symbols: Iterable[str] | None = None) -> IngestionResult:
    symbols = tuple(symbols or DEFAULT_EQUITY_SYMBOLS)
    fallback = _generate_mock_prices(symbols, "equity")
    data, used_fallback = safe_call(lambda: _yfinance_prices(symbols), fallback)
    return IngestionResult(
        asset_type="equity",
        data=data,
        metadata={"source": "yfinance" if not used_fallback else "mock", "count": str(len(data))},
    )


__all__ = ["fetch_equities"]
