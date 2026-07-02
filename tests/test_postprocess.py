"""Tests for src/utils/postprocess.py."""

import numpy as np
import pandas as pd

from src.utils.postprocess import (
    clip_predictions,
    optimize_threshold,
    probs_to_labels,
    snap_to_values,
)


def test_clip_predictions() -> None:
    df = pd.DataFrame({"pred": [-1.0, 0.5, 2.0]})
    result = clip_predictions(df, "pred", lower=0.0, upper=1.0)
    assert result["pred"].tolist() == [0.0, 0.5, 1.0]
    # 元の DataFrame は変更しない
    assert df["pred"].tolist() == [-1.0, 0.5, 2.0]


def _accuracy(y_true: np.ndarray, y_pred: np.ndarray) -> float:
    return float((y_true == y_pred).mean())


def test_optimize_threshold_greater_is_better() -> None:
    y_true = np.array([0, 0, 1, 1])
    y_pred = np.array([0.1, 0.4, 0.6, 0.9])
    threshold, score = optimize_threshold(y_true, y_pred, _accuracy)
    assert score == 1.0
    assert 0.4 < threshold <= 0.6


def test_optimize_threshold_lower_is_better() -> None:
    y_true = np.array([0, 0, 1, 1])
    y_pred = np.array([0.1, 0.4, 0.6, 0.9])

    def error_rate(t, p):
        return 1.0 - _accuracy(t, p)

    threshold, score = optimize_threshold(
        y_true, y_pred, error_rate, greater_is_better=False
    )
    assert score == 0.0
    assert 0.4 < threshold <= 0.6


def test_probs_to_labels_indices() -> None:
    probs = np.array([[0.9, 0.1], [0.2, 0.8], [0.4, 0.6]])
    assert probs_to_labels(probs).tolist() == [0, 1, 1]


def test_probs_to_labels_with_class_labels() -> None:
    probs = np.array([[0.9, 0.1], [0.2, 0.8]])
    labels = probs_to_labels(probs, class_labels=["cat", "dog"])
    assert labels.tolist() == ["cat", "dog"]


def test_snap_to_values() -> None:
    snapped = snap_to_values(np.array([1.4, 1.6, 2.5]), [1, 2, 3])
    # 2.5 は等距離なので左（2）に寄る
    assert snapped.tolist() == [1.0, 2.0, 2.0]


def test_snap_to_values_out_of_range_clips() -> None:
    snapped = snap_to_values(np.array([-5.0, 0.2, 3.9, 100.0]), [1, 2, 3])
    assert snapped.tolist() == [1.0, 1.0, 3.0, 3.0]
