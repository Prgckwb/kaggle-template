"""Tests for src/utils/metrics_logger.py."""

import csv
import json
from pathlib import Path

import pytest
from omegaconf import OmegaConf

from src.utils.metrics_logger import MetricsLogger


def make_cfg(tmp_path: Path, run_mode: str = "fold0", metric_mode: str = "min"):
    return OmegaConf.create(
        {
            "exp_name": "exp_test",
            "run_name": "run000-test",
            "run_mode": run_mode,
            "logs_dir": str(tmp_path / "logs" / "run000-test"),
            "metric": {"name": "loss", "mode": metric_mode},
        }
    )


def test_min_mode_zero_value_becomes_best(tmp_path: Path) -> None:
    """min モードで 0.0 が falsy 扱いされず best になること（or バグの回帰）。"""
    logger = MetricsLogger(make_cfg(tmp_path, metric_mode="min"))
    logger.log_epoch(0, {"epoch": 0, "val/loss": 0.5})
    logger.log_epoch(0, {"epoch": 1, "val/loss": 0.0})
    logger.finish()

    summary = json.loads(
        (tmp_path / "logs" / "run000-test" / "run_summary.json").read_text()
    )
    fold0 = summary["folds"]["fold0"]
    assert fold0["best_val_score"] == 0.0
    assert fold0["best_epoch"] == 1


def test_later_epoch_keys_appear_in_csv_header(tmp_path: Path) -> None:
    logger = MetricsLogger(make_cfg(tmp_path))
    logger.log_epoch(0, {"epoch": 0, "train/loss": 1.0})
    logger.log_epoch(0, {"epoch": 1, "train/loss": 0.8, "val/auc": 0.9})

    csv_path = tmp_path / "logs" / "run000-test" / "fold0_metrics.csv"
    with open(csv_path, newline="") as f:
        rows = list(csv.DictReader(f))

    assert "val/auc" in rows[0]  # 後から増えたキーがヘッダに含まれる
    assert rows[0]["val/auc"] == ""  # 最初のエポックでは空
    assert rows[1]["val/auc"] == "0.9"


def test_debug_mode_writes_to_debug_dir(tmp_path: Path) -> None:
    logger = MetricsLogger(make_cfg(tmp_path, run_mode="debug"))
    logger.log_epoch(0, {"epoch": 0, "val/loss": 0.5})
    logger.finish()

    debug_dir = tmp_path / "logs" / "run000-test-debug"
    assert (debug_dir / "fold0_metrics.csv").exists()
    assert (debug_dir / "run_summary.json").exists()
    # fold0/full 用のディレクトリを汚さない
    assert not (tmp_path / "logs" / "run000-test" / "run_summary.json").exists()

    summary = json.loads((debug_dir / "run_summary.json").read_text())
    assert summary["cv_score"] is None  # debug では CV スコアを算出しない


def test_run_summary_contains_cv_score_and_metric_name(tmp_path: Path) -> None:
    logger = MetricsLogger(make_cfg(tmp_path, metric_mode="min"))
    logger.log_epoch(0, {"epoch": 0, "val/loss": 0.5})
    logger.log_epoch(0, {"epoch": 1, "val/loss": 0.2})
    logger.log_epoch(1, {"epoch": 0, "val/loss": 0.4})
    logger.finish()

    summary = json.loads(
        (tmp_path / "logs" / "run000-test" / "run_summary.json").read_text()
    )
    assert summary["metric_name"] == "loss"
    assert summary["metric_mode"] == "min"
    assert summary["cv_score"] == pytest.approx((0.2 + 0.4) / 2)
    assert summary["run_name"] == "run000-test"
