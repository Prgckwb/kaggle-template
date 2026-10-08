"""run の結果サマリ（`logs/{run_name}/run_summary.json`）。スキーマの唯一の定義。

/kaggle:record-result・/kaggle:review-strategy はスコアを手で写さず、このファイルを読む。

- `fold_scores`: fold ごとの best モデルで再計算した競技指標
- `cv_mean` / `cv_std`: 2 fold 以上走ったときだけ（fold 平均。ばらつきの把握用）
- `oof_score`: 全 fold 走ったときだけ。OOF を pooled して 1 回計算した値で、**CV の代表値**
- fold0 モードの値は `fold_scores["0"]` であり、CV と呼ばない
"""

from __future__ import annotations

import json
import statistics
import subprocess
from datetime import UTC, datetime
from pathlib import Path
from typing import Any


def git_sha() -> str | None:
    try:
        out = subprocess.run(
            ["git", "rev-parse", "--short", "HEAD"],
            capture_output=True,
            text=True,
            check=True,
        )
    except (OSError, subprocess.CalledProcessError):
        return None
    return out.stdout.strip() or None


def build_run_summary(
    *,
    exp_name: str,
    run_name: str,
    run_mode: str,
    metric_name: str,
    metric_mode: str,
    fold_scores: dict[int, float],
    n_folds: int,
    oof_score: float | None,
    lineage: dict[str, Any],
    overrides: list[str],
    started_at: str,
) -> dict[str, Any]:
    scores = list(fold_scores.values())
    multi = len(scores) >= 2
    return {
        "exp_name": exp_name,
        "run_name": run_name,
        "run_mode": run_mode,
        "metric": {"name": metric_name, "mode": metric_mode},
        "fold_scores": {str(k): v for k, v in sorted(fold_scores.items())},
        "n_folds_run": len(scores),
        "n_folds": n_folds,
        "cv_mean": statistics.mean(scores) if multi else None,
        "cv_std": statistics.stdev(scores) if multi else None,
        "oof_score": oof_score,
        "lineage": lineage,
        "overrides": overrides,
        "git_sha": git_sha(),
        "started_at": started_at,
        "finished_at": datetime.now(UTC).isoformat(),
    }


def write_run_summary(summary: dict[str, Any], logs_dir: str | Path) -> Path:
    path = Path(logs_dir) / "run_summary.json"
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(summary, indent=2, ensure_ascii=False) + "\n")
    return path


def read_run_summary(path: str | Path) -> dict[str, Any]:
    return json.loads(Path(path).read_text())
