"""Lightweight local metrics logger for experiment tracking.

Writes per-fold CSV metrics and a run summary JSON alongside wandb logging,
so that training results can be reviewed without wandb access.
"""

from __future__ import annotations

import csv
import json
from datetime import datetime, timezone
from io import TextIOWrapper
from pathlib import Path
from typing import Any

from omegaconf import DictConfig, OmegaConf


class MetricsLogger:
    """Local metrics logger that writes CSV + JSON to logs/{run_name}/."""

    def __init__(self, cfg: DictConfig) -> None:
        self.exp_name: str = cfg.exp_name
        self.run_name: str = cfg.run_name
        self.run_mode: str = cfg.run_mode
        self.logs_dir = Path(cfg.logs_dir)
        self.logs_dir.mkdir(parents=True, exist_ok=True)

        self._fold_writers: dict[int, csv.DictWriter] = {}
        self._fold_files: dict[int, TextIOWrapper] = {}
        self._fold_fieldnames: dict[int, list[str]] = {}
        self._fold_best: dict[int, dict[str, Any]] = {}
        self._started_at = datetime.now(timezone.utc).isoformat()
        self._config_snapshot = OmegaConf.to_container(cfg, resolve=True)

    def log_epoch(self, fold_idx: int, metrics: dict[str, Any]) -> None:
        """Log one epoch of metrics for a given fold."""
        if fold_idx not in self._fold_writers:
            self._open_fold(fold_idx, list(metrics.keys()))

        writer = self._fold_writers[fold_idx]
        row = {k: metrics.get(k) for k in self._fold_fieldnames[fold_idx]}
        writer.writerow(row)
        self._fold_files[fold_idx].flush()

        self._update_best(fold_idx, metrics)

    def finish(self) -> None:
        """Close all files and write run_summary.json."""
        for f in self._fold_files.values():
            f.close()

        # Compute CV score (mean of best val_score across folds; fallback to best val_loss)
        cv_score = None
        if self.run_mode != "debug":
            scores = [
                b["best_val_score"]
                for b in self._fold_best.values()
                if b.get("best_val_score") is not None
            ]
            if scores:
                cv_score = sum(scores) / len(scores)
            else:
                losses = [
                    b["best_val_loss"]
                    for b in self._fold_best.values()
                    if b.get("best_val_loss") is not None
                ]
                if losses:
                    cv_score = sum(losses) / len(losses)

        summary = {
            "exp_name": self.exp_name,
            "run_name": self.run_name,
            "run_mode": self.run_mode,
            "started_at": self._started_at,
            "finished_at": datetime.now(timezone.utc).isoformat(),
            "folds": {
                f"fold{k}": v for k, v in sorted(self._fold_best.items())
            },
            "cv_score": cv_score,
            "config_snapshot": self._config_snapshot,
        }

        with open(self.logs_dir / "run_summary.json", "w") as f:
            json.dump(summary, f, indent=2, ensure_ascii=False)

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    def _open_fold(self, fold_idx: int, fieldnames: list[str]) -> None:
        path = self.logs_dir / f"fold{fold_idx}_metrics.csv"
        f = open(path, "w", newline="")  # noqa: SIM115
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        self._fold_writers[fold_idx] = writer
        self._fold_files[fold_idx] = f
        self._fold_fieldnames[fold_idx] = fieldnames
        self._fold_best[fold_idx] = {}

    def _update_best(self, fold_idx: int, metrics: dict[str, Any]) -> None:
        best = self._fold_best[fold_idx]

        # Track best val_score (higher is better)
        if "val_score" in metrics and metrics["val_score"] is not None:
            if not best or metrics["val_score"] > best.get("best_val_score", float("-inf")):
                best["best_epoch"] = metrics.get("epoch", 0)
                best["best_val_score"] = metrics["val_score"]

        # Track best val_loss (lower is better)
        if "val_loss" in metrics and metrics["val_loss"] is not None:
            if "best_val_loss" not in best or metrics["val_loss"] < best["best_val_loss"]:
                best["best_val_loss"] = metrics["val_loss"]
                if "val_score" not in metrics:
                    best["best_epoch"] = metrics.get("epoch", 0)

        best["total_epochs"] = metrics.get("epoch", 0) + 1
