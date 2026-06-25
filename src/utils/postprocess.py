"""Post-processing utilities for submission refinement."""

from __future__ import annotations

from collections.abc import Callable

import numpy as np
import pandas as pd


def clip_predictions(
    df: pd.DataFrame,
    pred_col: str,
    lower: float | None = None,
    upper: float | None = None,
) -> pd.DataFrame:
    """Clip prediction values to a valid range."""
    result = df.copy()
    result[pred_col] = result[pred_col].clip(lower=lower, upper=upper)
    return result


def optimize_threshold(
    y_true: np.ndarray,
    y_pred: np.ndarray,
    metric_fn: Callable,
    thresholds: np.ndarray | None = None,
    greater_is_better: bool = True,
) -> tuple[float, float]:
    """Find the optimal classification threshold by grid search.

    Returns (best_threshold, best_score).
    """
    if thresholds is None:
        thresholds = np.arange(0.01, 1.0, 0.01)

    best_score = float("-inf") if greater_is_better else float("inf")
    best_threshold = 0.5

    for t in thresholds:
        preds = (y_pred >= t).astype(int)
        score = metric_fn(y_true, preds)
        if greater_is_better and score > best_score:
            best_score = score
            best_threshold = t
        elif not greater_is_better and score < best_score:
            best_score = score
            best_threshold = t

    return float(best_threshold), float(best_score)
