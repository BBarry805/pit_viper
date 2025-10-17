"""CLI entrypoint for running the Pit Viper nightly job."""
from __future__ import annotations

import argparse
import json

from .orchestration.advice_job import run_daily_advice
from .utils.config import load_config


def main() -> None:
    parser = argparse.ArgumentParser(description="Run the Pit Viper daily advice pipeline")
    parser.add_argument("--output", help="Optional path to write the advice JSON payload")
    args = parser.parse_args()

    config = load_config()
    payload = run_daily_advice(config)

    if args.output:
        with open(args.output, "w", encoding="utf-8") as handle:
            json.dump(payload, handle, indent=2, default=str)
    else:
        print(json.dumps(payload, indent=2, default=str))


if __name__ == "__main__":
    main()
