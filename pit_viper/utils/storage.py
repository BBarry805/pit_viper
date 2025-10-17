"""Utility helpers for persisting pipeline artifacts to the local filesystem."""
from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict

import pandas as pd


@dataclass
class DataStore:
    """Lightweight Parquet-based persistence layer."""

    root: Path

    def write_frame(self, df: pd.DataFrame, category: str, name: str) -> Path:
        path = self._build_path(category, name)
        df.to_parquet(path, index=False)
        return path

    def write_json(self, payload: Dict[str, Any], category: str, name: str) -> Path:
        path = self._build_path(category, name, suffix=".json")
        import json

        path.write_text(json.dumps(payload, indent=2, default=str))
        return path

    def read_frame(self, category: str, name: str) -> pd.DataFrame:
        path = self._build_path(category, name)
        return pd.read_parquet(path)

    def _build_path(self, category: str, name: str, suffix: str = ".parquet") -> Path:
        target_dir = self.root / category
        target_dir.mkdir(parents=True, exist_ok=True)
        if not name.endswith(suffix):
            name = f"{name}{suffix}"
        return target_dir / name


__all__ = ["DataStore"]
