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
        if (
            greater_is_better
            and score > best_score
            or not greater_is_better
            and score < best_score
        ):
            best_score = score
            best_threshold = t

    return float(best_threshold), float(best_score)


def probs_to_labels(
    probs: np.ndarray,
    class_labels: list | None = None,
) -> np.ndarray:
    """Convert multiclass probabilities (n_samples, n_classes) to labels via argmax."""
    indices = np.asarray(probs).argmax(axis=1)
    if class_labels is None:
        return indices
    return np.asarray(class_labels)[indices]


def snap_to_values(
    y_pred: np.ndarray,
    allowed_values: np.ndarray | list,
) -> np.ndarray:
    """Snap continuous predictions to the nearest allowed value.

    順序ラベル（QWK 等）や離散値しか許されない提出形式の後処理に使う。
    """
    allowed = np.sort(np.asarray(allowed_values, dtype=float))
    pred = np.asarray(y_pred, dtype=float)
    idx = np.searchsorted(allowed, pred)
    idx = np.clip(idx, 1, len(allowed) - 1)
    left = allowed[idx - 1]
    right = allowed[idx]
    snapped = np.where(pred - left <= right - pred, left, right)
    # 範囲外は端に寄せる
    snapped = np.clip(snapped, allowed[0], allowed[-1])
    return snapped
