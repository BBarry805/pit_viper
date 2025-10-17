"""Shared ingestion utilities and base classes."""
from __future__ import annotations

import logging
from dataclasses import dataclass
from datetime import datetime
from typing import Callable, Dict, Iterable, List, Tuple

import numpy as np
import pandas as pd

logger = logging.getLogger(__name__)


@dataclass
class IngestionResult:
    """Represents the output of a single ingestion task."""

    asset_type: str
    data: pd.DataFrame
    metadata: Dict[str, str]


def _generate_mock_prices(symbols: Iterable[str], asset_type: str) -> pd.DataFrame:
    """Generate deterministic-yet-random-looking price data for tests/offline work."""

    now = datetime.utcnow()
    records: List[Dict[str, object]] = []
    for idx, symbol in enumerate(symbols):
        base_price = 10 + idx * 5
        rng = np.random.default_rng(seed=hash(symbol) % 2**32)
        close_price = base_price * rng.uniform(0.95, 1.05)
        records.append(
            {
                "asset_id": symbol,
                "asset_type": asset_type,
                "currency": "USD",
                "close": round(close_price, 2),
                "open": round(close_price * rng.uniform(0.98, 1.02), 2),
                "high": round(close_price * rng.uniform(1.00, 1.05), 2),
                "low": round(close_price * rng.uniform(0.95, 1.00), 2),
                "volume": int(rng.integers(1_000, 1_000_000)),
                "as_of": now,
            }
        )
    return pd.DataFrame.from_records(records)


def safe_call(callable_fn: Callable[[], pd.DataFrame], fallback: pd.DataFrame) -> Tuple[pd.DataFrame, bool]:
    """Execute an ingestion function and fall back to offline data when it fails."""

    try:
        result = callable_fn()
        if not isinstance(result, pd.DataFrame) or result.empty:
            raise ValueError("ingestion produced no data")
        return result, False
    except Exception as exc:  # noqa: BLE001 - we want to log any ingestion failure
        logger.warning("Falling back to offline data for ingestion: %s", exc, exc_info=True)
        return fallback.copy(), True


__all__ = ["IngestionResult", "safe_call", "_generate_mock_prices"]
