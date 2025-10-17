from __future__ import annotations

import json
from pathlib import Path

from pit_viper.orchestration.advice_job import run_daily_advice
from pit_viper.utils.config import load_config


def test_run_daily_advice(tmp_path: Path, monkeypatch):
    data_dir = tmp_path / "data"
    monkeypatch.setenv("PIT_VIPER_DATA_DIR", str(data_dir))
    config = load_config()
    payload = run_daily_advice(config)

    assert "advice" in payload
    assert "summary" in payload["advice"]

    advice_files = list((data_dir / config.storage.advice_subdir).glob("*.json"))
    assert advice_files, "Advice output should be persisted"

    loaded = json.loads(advice_files[0].read_text())
    assert "summary" in loaded
