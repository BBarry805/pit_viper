# Pit Viper Investment Intelligence

Pit Viper is an end-to-end, locally runnable investment intelligence pipeline. It ingests cross-asset market data, enriches it with portfolio context and sentiment analytics, and generates curated daily guidance using ChatGPT. The system is designed for a single user running overnight batches (00:00–06:00 PST) with optional intraday refreshes.

## Features

- **Multi-asset ingestion** covering crypto (Coinbase), equities/ETFs/mutual funds (Yahoo Finance, Alpha Vantage), bonds (FRED), and commodities.
- **Robust fallbacks**: deterministic mock data keeps the pipeline operable without API connectivity—helpful for development and testing.
- **Feature engineering** deriving valuation, momentum, risk, and liquidity proxies.
- **Portfolio reconciliation** for Coinbase/Fidelity holdings via CSV or secure aggregators.
- **Sentiment analytics** across news (NewsAPI) and social sources (Reddit, X, StockTwits) with Vader-based scoring.
- **Recommendation engine** producing ranked opportunities with diversification-aware scoring.
- **ChatGPT-5 handoff** packaging structured prompts and persisting advice summaries, ready for email/Slack/dashboard distribution.
- **Audit-friendly storage** of raw, processed, sentiment, and advice artifacts as Parquet/JSON.

## Project layout

```
pit_viper/
  ingestion/        # Asset-class connectors
  processing/       # Cleaning, features, scoring, portfolio utilities
  sentiment/        # News and social collectors
  orchestration/    # ChatGPT integration and nightly job
  utils/            # Configuration and storage helpers
```

## Getting started

### 1. Prerequisites

- Python 3.11+
- Optional: PostgreSQL/MinIO if you plan to swap out the default Parquet storage
- API credentials stored as environment variables (see below). During development you can omit them and rely on mock data.

### 2. Installation

```bash
python -m venv .venv
source .venv/bin/activate
pip install -e .[dev]
```

### 3. Environment variables

Create a `.env` file (or export variables) with the secrets you have provisioned:

| Variable | Purpose |
| --- | --- |
| `COINBASE_API_KEY` | Coinbase Advanced Trade key (read-only) |
| `ALPHA_VANTAGE_API_KEY` | Optional equity/forex redundancy |
| `FINNHUB_API_KEY` | Optional fundamentals/news |
| `FMP_API_KEY` | Optional fundamentals and holdings |
| `NEWSAPI_API_KEY` | News sentiment |
| `OPENAI_API_KEY` | ChatGPT-5 access |
| `REDDIT_API_SECRET` | Reddit client secret (paired with script app) |
| `TWITTER_BEARER_TOKEN` | X/Twitter API |
| `STOCKTWITS_API_TOKEN` | StockTwits API |
| `PIT_VIPER_EMAIL_RECIPIENTS` | Comma-separated list for email notifications |
| `PIT_VIPER_SLACK_WEBHOOK` | Optional Slack webhook |
| `PIT_VIPER_DATA_DIR` | Target directory for Parquet/JSON outputs |

### 4. Running the nightly job

Once the environment is configured, trigger the pipeline locally:

```bash
python -m pit_viper --output advice.json
```

The command ingests market/sentiment data, scores opportunities, reconciles holdings, and stores artifacts under `data/` (or the directory specified by `PIT_VIPER_DATA_DIR`). The generated advice JSON is printed to stdout and optionally written to `advice.json`.

### 5. Scheduling

For an overnight run (00:00–06:00 PST) on a Unix-like system, add a cron entry:

```
0 6 * * * /path/to/project/.venv/bin/python -m pit_viper --output /path/to/project/data/advice/latest.json
```

Alternatively, use `systemd` timers or Prefect/Dagster if you later migrate to orchestrated workflows.

### 6. Portfolio data

- **Coinbase**: supply API credentials and extend `processing/portfolio.py` to call the API for balances and fills.
- **Fidelity**: integrate via Plaid/Finicity or import OFX/CSV statements into the `load_holdings` helper.
- **Manual override**: place a CSV with columns `asset_id,asset_type,quantity,cost_basis,source` and point `load_holdings` to it.

### 7. Extending sentiment & delivery

- Replace the placeholder social collector with live Reddit/X/StockTwits integrations using PRAW, Tweepy, and StockTwits REST.
- Configure email (SMTP/SendGrid) and Slack notifications using the stored advice payloads.
- Introduce a lightweight dashboard (Streamlit, Dash) that reads the persisted Parquet files for historical analysis.

## Testing

Run the automated test suite:

```bash
pytest
```

Tests leverage the deterministic mock data path so they pass without network access. When running in production, ensure outbound connectivity and rate-limit management for all APIs.

## Roadmap

- Plug in live brokerage integrations and reconcile trades automatically.
- Expand the scoring model with additional factors (quality, macro regime detection).
- Add backtesting harnesses and performance attribution reporting.
- Implement notification channels (email/Slack) and a dashboard UI.

## License

MIT (pending confirmation). Adapt as needed for personal use.
