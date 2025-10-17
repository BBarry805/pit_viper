"""Portfolio reconciliation helpers for Coinbase/Fidelity holdings."""
from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Dict, Iterable, Optional

import pandas as pd


@dataclass
class PortfolioSnapshot:
    holdings: pd.DataFrame
    metadata: Dict[str, str]


DEFAULT_COLUMNS = ("asset_id", "asset_type", "quantity", "cost_basis", "source")


def load_holdings(csv_path: Optional[Path] = None) -> PortfolioSnapshot:
    if csv_path and csv_path.exists():
        holdings = pd.read_csv(csv_path)
    else:
        holdings = pd.DataFrame(
            [
                {
                    "asset_id": "SPY",
                    "asset_type": "equity",
                    "quantity": 10,
                    "cost_basis": 4000,
                    "source": "mock",
                },
                {
                    "asset_id": "BTC-USD",
                    "asset_type": "crypto",
                    "quantity": 0.5,
                    "cost_basis": 15000,
                    "source": "mock",
                },
            ]
        )
    for column in DEFAULT_COLUMNS:
        if column not in holdings.columns:
            holdings[column] = 0
    return PortfolioSnapshot(holdings=holdings[list(DEFAULT_COLUMNS)], metadata={"source": "file" if csv_path else "mock"})


def reconcile(holdings: pd.DataFrame, recommendations: pd.DataFrame) -> pd.DataFrame:
    if holdings.empty or recommendations.empty:
        return pd.DataFrame()
    merged = recommendations.merge(holdings, how="left", on=["asset_id", "asset_type"], suffixes=("", "_held"))
    merged["position_delta"] = merged["quantity"].fillna(0)
    merged["in_portfolio"] = merged["quantity"].notna()
    return merged


__all__ = ["PortfolioSnapshot", "load_holdings", "reconcile"]
