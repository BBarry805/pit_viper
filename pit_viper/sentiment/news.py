"""News sentiment collector using NewsAPI and fallback heuristics."""
from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable

import pandas as pd
from vaderSentiment.vaderSentiment import SentimentIntensityAnalyzer

from ..utils.config import AppConfig


@dataclass
class NewsSentiment:
    articles: pd.DataFrame
    aggregated: pd.DataFrame


_DEFAULT_HEADLINES = [
    {
        "title": "Tech stocks rally on strong earnings",
        "ticker": "AAPL",
        "sentiment": 0.4,
    },
    {
        "title": "Oil prices fall amid supply concerns",
        "ticker": "CL=F",
        "sentiment": -0.2,
    },
]


_ANALYZER = SentimentIntensityAnalyzer()


def _call_newsapi(api_key: str | None, tickers: Iterable[str]) -> pd.DataFrame:
    if not api_key:
        raise ValueError("NewsAPI key missing")
    import requests

    params = {
        "q": " OR ".join(set(tickers)) or "markets",
        "apiKey": api_key,
        "pageSize": 50,
        "language": "en",
        "sortBy": "publishedAt",
    }
    response = requests.get("https://newsapi.org/v2/everything", params=params, timeout=10)
    response.raise_for_status()
    articles = response.json().get("articles", [])
    records = []
    for article in articles:
        records.append(
            {
                "title": article.get("title"),
                "source": article.get("source", {}).get("name"),
                "url": article.get("url"),
                "published_at": article.get("publishedAt"),
                "ticker": article.get("symbol") or "",
                "sentiment": 0.0,
            }
        )
    return pd.DataFrame(records)


def _fallback_articles() -> pd.DataFrame:
    return pd.DataFrame(_DEFAULT_HEADLINES)


def _score_articles(articles: pd.DataFrame) -> pd.DataFrame:
    if articles.empty:
        return articles
    sentiments = []
    for _, row in articles.iterrows():
        text = str(row.get("title", ""))
        score = _ANALYZER.polarity_scores(text)["compound"]
        sentiments.append(score)
    scored = articles.copy()
    scored["sentiment"] = sentiments
    return scored


def collect_news_sentiment(config: AppConfig, tickers: Iterable[str]) -> NewsSentiment:
    fallback = _fallback_articles()
    used_fallback = False
    try:
        articles = _call_newsapi(config.credentials.newsapi, tickers)
        if articles.empty:
            raise ValueError("No articles from NewsAPI")
    except Exception:
        articles = fallback
        used_fallback = True

    try:
        scored = _score_articles(articles)
    except Exception:
        scored = articles.copy()
        scored["sentiment"] = scored.get("sentiment", 0.0)
        scored["sentiment"].fillna(0.0, inplace=True)

    aggregated = (
        scored.groupby("ticker", dropna=False)["sentiment"].mean().reset_index().rename(columns={"sentiment": "sentiment_score"})
    )
    aggregated["source"] = "newsapi" if not used_fallback else "mock"
    return NewsSentiment(articles=scored, aggregated=aggregated)


__all__ = ["collect_news_sentiment", "NewsSentiment"]
