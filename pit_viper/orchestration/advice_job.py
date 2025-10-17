"""Nightly orchestration job for Pit Viper."""
from __future__ import annotations

import logging
from datetime import datetime
from typing import Dict

from ..ingestion.bonds import fetch_bonds
from ..ingestion.commodities import fetch_commodities
from ..ingestion.crypto import fetch_crypto
from ..ingestion.equities import fetch_equities
from ..ingestion.funds import fetch_funds
from ..processing.feature_pipeline import run_feature_pipeline
from ..processing.portfolio import load_holdings, reconcile
from ..processing.scoring import summarize_recommendations, score_assets
from ..sentiment.news import collect_news_sentiment
from ..sentiment.social import collect_social_sentiment
from ..utils.config import AppConfig, load_config
from ..utils.storage import DataStore
from .chatgpt import AdviceRequest, ChatGPTClient

logger = logging.getLogger(__name__)


def run_daily_advice(config: AppConfig | None = None) -> Dict[str, Dict[str, object]]:
    """Run the end-to-end ingestion, scoring, and advice workflow."""

    config = config or load_config()
    store = DataStore(config.storage.data_dir)

    ingestions = [
        fetch_crypto(config),
        fetch_equities(config),
        fetch_funds(config),
        fetch_bonds(config),
        fetch_commodities(config),
    ]

    feature_result = run_feature_pipeline(ingestions)
    scored = score_assets(feature_result.features)
    recommendations = summarize_recommendations(scored, top_n=10)

    portfolio_snapshot = load_holdings()
    reconciled = reconcile(portfolio_snapshot.holdings, recommendations)

    tickers = recommendations["asset_id"].tolist() if not recommendations.empty else []
    news_sentiment = collect_news_sentiment(config, tickers)
    social_sentiment = collect_social_sentiment(config, tickers)

    market_overview = {
        "generated_at": datetime.utcnow().isoformat(),
        "assets_considered": len(feature_result.combined),
        "asset_breakdown": feature_result.combined["asset_type"].value_counts().to_dict(),
    }

    sentiment_summary = {
        "news": news_sentiment.aggregated.to_dict(orient="records"),
        "social": social_sentiment.aggregated.to_dict(orient="records"),
    }

    request = AdviceRequest(
        market_overview=market_overview,
        recommendations={"top": recommendations.to_dict(orient="records")},
        portfolio={
            "holdings": portfolio_snapshot.holdings.to_dict(orient="records"),
            "reconciled": reconciled.to_dict(orient="records"),
        },
        sentiment=sentiment_summary,
    )
    chatgpt = ChatGPTClient(api_key=config.credentials.openai)
    advice = chatgpt.generate_advice(request)

    store.write_frame(feature_result.combined, config.storage.processed_subdir, f"market_{datetime.utcnow().date()}")
    store.write_frame(news_sentiment.aggregated, config.storage.sentiment_subdir, f"news_{datetime.utcnow().date()}")
    store.write_frame(social_sentiment.aggregated, config.storage.sentiment_subdir, f"social_{datetime.utcnow().date()}")
    store.write_json(advice, config.storage.advice_subdir, f"advice_{datetime.utcnow().date()}")

    output = {
        "market_overview": market_overview,
        "recommendations": request.recommendations,
        "portfolio": request.portfolio,
        "sentiment": sentiment_summary,
        "advice": advice,
    }
    logger.info("Generated daily advice packet", extra={"summary": advice.get("summary")})
    return output


__all__ = ["run_daily_advice"]
