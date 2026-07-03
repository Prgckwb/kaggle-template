"""Lightweight local metrics logger for experiment tracking.

Writes per-fold CSV metrics and a run summary JSON alongside wandb logging,
so that training results can be reviewed without wandb access.
"""

from __future__ import annotations

import csv
import json
from datetime import UTC, datetime
from typing import Any

from omegaconf import DictConfig, OmegaConf

from src.utils.logger import resolve_logs_dir


class MetricsLogger:
    """Local metrics logger that writes CSV + JSON to logs/{run_name}/.

    - run_mode=debug のときは logs/{run_name}-debug/ に書き、fold0/full の
      ログを上書きしない。
    - 追跡する評価指標は cfg.metric.name / cfg.metric.mode（min/max）に従う。
    - 途中のエポックで新しいメトリクスキーが増えても CSV に反映される
      （行をメモリに保持し、毎回ファイル全体を書き直す）。
    """

    def __init__(self, cfg: DictConfig) -> None:
        self.exp_name: str = cfg.exp_name
        self.run_name: str = cfg.run_name
        self.run_mode: str = cfg.run_mode

        self.logs_dir = resolve_logs_dir(cfg.logs_dir, self.run_mode)
        self.logs_dir.mkdir(parents=True, exist_ok=True)

        # 評価指標（未設定の古い config でも動くようにフォールバックする）
        self.metric_name: str = OmegaConf.select(cfg, "metric.name", default="score")
        self.metric_mode: str = OmegaConf.select(cfg, "metric.mode", default="max")

        self._fold_rows: dict[int, list[dict[str, Any]]] = {}
        self._fold_fieldnames: dict[int, list[str]] = {}
        self._fold_best: dict[int, dict[str, Any]] = {}
        self._started_at = datetime.now(UTC).isoformat()
        self._config_snapshot = OmegaConf.to_container(cfg, resolve=True)

    def log_epoch(self, fold_idx: int, metrics: dict[str, Any]) -> None:
        """Log one epoch of metrics for a given fold."""
        rows = self._fold_rows.setdefault(fold_idx, [])
        fieldnames = self._fold_fieldnames.setdefault(fold_idx, [])
        self._fold_best.setdefault(fold_idx, {})

        rows.append(dict(metrics))
        for key in metrics:
            if key not in fieldnames:
                fieldnames.append(key)

        self._write_fold_csv(fold_idx)
        self._update_best(fold_idx, metrics)

    def finish(self) -> None:
        """Write run_summary.json."""
        # CV score = 各 fold の best スコアの平均（debug では None）
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
                # 評価指標が未記録の場合は val_loss にフォールバック
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
            "metric_name": self.metric_name,
            "metric_mode": self.metric_mode,
            "started_at": self._started_at,
            "finished_at": datetime.now(UTC).isoformat(),
            "folds": {f"fold{k}": v for k, v in sorted(self._fold_best.items())},
            "cv_score": cv_score,
            "config_snapshot": self._config_snapshot,
        }

        with open(self.logs_dir / "run_summary.json", "w") as f:
            json.dump(summary, f, indent=2, ensure_ascii=False)

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    def _write_fold_csv(self, fold_idx: int) -> None:
        path = self.logs_dir / f"fold{fold_idx}_metrics.csv"
        fieldnames = self._fold_fieldnames[fold_idx]
        with open(path, "w", newline="") as f:
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            writer.writeheader()
            for row in self._fold_rows[fold_idx]:
                writer.writerow({k: row.get(k) for k in fieldnames})

    def _metric_value(self, metrics: dict[str, Any]) -> Any:
        """評価指標の値を取り出す（val/{metric} を優先、旧キーにフォールバック）。"""
        for key in (f"val/{self.metric_name}", "val/score", "val_score"):
            value = metrics.get(key)
            if value is not None:
                return value
        return None

    def _is_better(self, value: float, current_best: float | None) -> bool:
        if current_best is None:
            return True
        if self.metric_mode == "min":
            return value < current_best
        return value > current_best

    def _update_best(self, fold_idx: int, metrics: dict[str, Any]) -> None:
        best = self._fold_best[fold_idx]
        epoch = metrics.get("epoch", 0)

        val_score = self._metric_value(metrics)
        if val_score is not None and self._is_better(
            val_score, best.get("best_val_score")
        ):
            best["best_epoch"] = epoch
            best["best_val_score"] = val_score

        # val/loss は補助情報として常に追跡する（0.0 も有効値として扱う）
        val_loss = metrics.get("val/loss")
        if val_loss is None:
            val_loss = metrics.get("val_loss")
        if val_loss is not None and (
            "best_val_loss" not in best or val_loss < best["best_val_loss"]
        ):
            best["best_val_loss"] = val_loss
            if val_score is None:
                best["best_epoch"] = epoch

        best["total_epochs"] = epoch + 1
