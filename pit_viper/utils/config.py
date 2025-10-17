"""Configuration helpers for the Pit Viper investment intelligence pipeline."""
from __future__ import annotations

import json
import os
from dataclasses import dataclass, field
from datetime import time
from pathlib import Path
from typing import Dict, Optional


def _load_json_env(var_name: str) -> Dict[str, str]:
    raw_value = os.getenv(var_name)
    if not raw_value:
        return {}
    try:
        return json.loads(raw_value)
    except json.JSONDecodeError:
        return {}


@dataclass
class ApiCredentials:
    """Container for optional API credentials used across the pipeline."""

    coinbase: Optional[str] = field(default=None)
    alpha_vantage: Optional[str] = field(default=None)
    finnhub: Optional[str] = field(default=None)
    fmp: Optional[str] = field(default=None)
    newsapi: Optional[str] = field(default=None)
    openai: Optional[str] = field(default=None)
    reddit: Optional[str] = field(default=None)
    twitter: Optional[str] = field(default=None)
    stocktwits: Optional[str] = field(default=None)


@dataclass
class SchedulingConfig:
    """Represents the timing requirements for the nightly orchestration job."""

    window_start: time = field(default=time(0, 0))
    window_end: time = field(default=time(6, 0))
    timezone: str = field(default=os.getenv("PIT_VIPER_TZ", "America/Los_Angeles"))


@dataclass
class StorageConfig:
    """Holds locations for persisting raw, intermediate, and curated data."""

    data_dir: Path = field(default=Path("data"))
    raw_subdir: str = field(default="raw")
    processed_subdir: str = field(default="processed")
    sentiment_subdir: str = field(default="sentiment")
    advice_subdir: str = field(default="advice")

    def path_for(self, category: str) -> Path:
        target = self.data_dir / category
        target.mkdir(parents=True, exist_ok=True)
        return target


@dataclass
class NotificationConfig:
    email_recipients: tuple[str, ...] = field(
        default_factory=lambda: tuple(filter(None, os.getenv("PIT_VIPER_EMAIL_RECIPIENTS", "").split(",")))
    )
    slack_webhook: Optional[str] = field(default=os.getenv("PIT_VIPER_SLACK_WEBHOOK"))


@dataclass
class AppConfig:
    """Top-level application configuration."""

    credentials: ApiCredentials
    scheduling: SchedulingConfig
    storage: StorageConfig
    notification: NotificationConfig
    sentiment_sources: Dict[str, Dict[str, str]]


def load_config() -> AppConfig:
    """Load configuration and secrets from environment variables."""

    credentials = ApiCredentials(
        coinbase=os.getenv("COINBASE_API_KEY"),
        alpha_vantage=os.getenv("ALPHA_VANTAGE_API_KEY"),
        finnhub=os.getenv("FINNHUB_API_KEY"),
        fmp=os.getenv("FMP_API_KEY"),
        newsapi=os.getenv("NEWSAPI_API_KEY"),
        openai=os.getenv("OPENAI_API_KEY"),
        reddit=os.getenv("REDDIT_API_SECRET"),
        twitter=os.getenv("TWITTER_BEARER_TOKEN"),
        stocktwits=os.getenv("STOCKTWITS_API_TOKEN"),
    )

    sentiment_sources = _load_json_env("PIT_VIPER_SENTIMENT_SOURCES")

    data_dir = Path(os.getenv("PIT_VIPER_DATA_DIR", "data"))
    data_dir.mkdir(parents=True, exist_ok=True)

    return AppConfig(
        credentials=credentials,
        scheduling=SchedulingConfig(),
        storage=StorageConfig(data_dir=data_dir),
        notification=NotificationConfig(),
        sentiment_sources=sentiment_sources,
    )


__all__ = ["AppConfig", "ApiCredentials", "load_config"]
