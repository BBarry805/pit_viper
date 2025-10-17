"""Social sentiment collectors for Reddit, X, and StockTwits."""
from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, Iterable, List

import pandas as pd
from vaderSentiment.vaderSentiment import SentimentIntensityAnalyzer

from ..utils.config import AppConfig


@dataclass
class SocialSentiment:
    posts: pd.DataFrame
    aggregated: pd.DataFrame


_ANALYZER = SentimentIntensityAnalyzer()


def _mock_posts() -> pd.DataFrame:
    return pd.DataFrame(
        [
            {"platform": "reddit", "ticker": "SPY", "text": "SPY looks strong into earnings", "sentiment": 0.6},
            {"platform": "twitter", "ticker": "BTC-USD", "text": "Bitcoin consolidating before breakout", "sentiment": 0.4},
            {"platform": "stocktwits", "ticker": "AAPL", "text": "AAPL might be overvalued", "sentiment": -0.3},
        ]
    )


def _score_posts(posts: pd.DataFrame) -> pd.DataFrame:
    if posts.empty:
        return posts
    scores = []
    for _, row in posts.iterrows():
        text = str(row.get("text", ""))
        score = _ANALYZER.polarity_scores(text)["compound"]
        scores.append(score)
    scored = posts.copy()
    scored["sentiment"] = scores
    return scored


def collect_social_sentiment(config: AppConfig, tickers: Iterable[str]) -> SocialSentiment:
    # Placeholder: in production use praw/tweepy/StockTwits API
    posts = _mock_posts()
    try:
        scored = _score_posts(posts)
    except Exception:
        scored = posts
    aggregated = (
        scored.groupby("ticker")["sentiment"].mean().reset_index().rename(columns={"sentiment": "sentiment_score"})
    )
    aggregated["source"] = "social"
    return SocialSentiment(posts=scored, aggregated=aggregated)


__all__ = ["collect_social_sentiment", "SocialSentiment"]
