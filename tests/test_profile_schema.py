"""docs/competition-profile.yaml のスキーマ検証。

/kaggle:init と各スキルが参照するキーが存在し、既定値が想定どおりであることを守る。
"""

from pathlib import Path

import yaml

PROFILE_PATH = Path(__file__).resolve().parents[1] / "docs" / "competition-profile.yaml"


def _load() -> dict:
    return yaml.safe_load(PROFILE_PATH.read_text(encoding="utf-8"))


def test_metric_noise_keys_exist_and_default_to_null() -> None:
    noise = _load()["metric"]["noise"]

    assert set(noise) == {"seed_spread", "fold0_resolution", "proxy_resolution"}
    assert all(v is None for v in noise.values()), "テンプレート状態では未測定（null）"


def test_workflow_defaults() -> None:
    workflow = _load()["workflow"]

    assert workflow["default_run_mode"] == "fold0"
    assert workflow["submission_by"] == "user"
    assert workflow["branching"] == "main-only"
    assert workflow["concurrent_sessions"] is True
    assert workflow["remote_training"] == "none"
    assert workflow["max_runs_per_exp"] == 8


def test_workflow_enums_are_documented() -> None:
    """列挙値は yaml のコメントに書いてあること（/kaggle:init が選択肢として提示する）。"""
    text = PROFILE_PATH.read_text(encoding="utf-8")

    for token in ("main-only", "feature-branches", "herdr", "user", "agent"):
        assert token in text
