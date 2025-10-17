"""Crypto ingestion using Coinbase when available with offline fallbacks."""
from __future__ import annotations

from typing import Iterable, List

import pandas as pd

from .base import IngestionResult, _generate_mock_prices, safe_call
from ..utils.config import AppConfig

DEFAULT_CRYPTO_SYMBOLS = ("BTC-USD", "ETH-USD", "SOL-USD")


def _coinbase_prices(symbols: Iterable[str], api_key: str | None) -> pd.DataFrame:
    if not api_key:
        raise ValueError("Coinbase API key not provided")
    import requests

    frames: List[pd.DataFrame] = []
    for product_id in symbols:
        url = f"https://api.exchange.coinbase.com/products/{product_id}/ticker"
        response = requests.get(url, timeout=10)
        response.raise_for_status()
        payload = response.json()
        frames.append(
            pd.DataFrame(
                {
                    "asset_id": [product_id],
                    "asset_type": ["crypto"],
                    "currency": [payload.get("currency", "USD")],
                    "close": [float(payload.get("price", 0.0))],
                    "open": [float(payload.get("open", payload.get("price", 0.0)))],
                    "high": [float(payload.get("high", payload.get("price", 0.0)))],
                    "low": [float(payload.get("low", payload.get("price", 0.0)))],
                    "volume": [float(payload.get("volume", 0.0))],
                    "as_of": [pd.Timestamp.utcnow()],
                }
            )
        )
    return pd.concat(frames, ignore_index=True)


def fetch_crypto(config: AppConfig, symbols: Iterable[str] | None = None) -> IngestionResult:
    symbols = tuple(symbols or DEFAULT_CRYPTO_SYMBOLS)
    fallback = _generate_mock_prices(symbols, "crypto")
    data, used_fallback = safe_call(lambda: _coinbase_prices(symbols, config.credentials.coinbase), fallback)
    return IngestionResult(
        asset_type="crypto",
        data=data,
        metadata={"source": "coinbase" if not used_fallback else "mock", "count": str(len(data))},
    )


__all__ = ["fetch_crypto"]
