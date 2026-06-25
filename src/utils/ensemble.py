"""Ensemble and blending utilities."""

from __future__ import annotations

from pathlib import Path

import numpy as np
import pandas as pd


def blend_predictions(
    oof_paths: list[Path | str],
    weights: list[float] | None = None,
    id_col: str = "id",
    pred_cols: list[str] | None = None,
) -> pd.DataFrame:
    """Weighted average of multiple OOF prediction files.

    All files must have the same ID column and be aligned by it.
    """
    dfs = [pd.read_csv(p) for p in oof_paths]
    n = len(dfs)

    if weights is None:
        weights = [1.0 / n] * n
    if len(weights) != n:
        raise ValueError(f"Expected {n} weights, got {len(weights)}")

    w_sum = sum(weights)
    weights = [w / w_sum for w in weights]

    if pred_cols is None:
        pred_cols = [c for c in dfs[0].columns if c != id_col]

    result = dfs[0][[id_col]].copy()
    for col in pred_cols:
        result[col] = sum(w * df[col].values for w, df in zip(weights, dfs))

    return result


def rank_average(
    submission_paths: list[Path | str],
    weights: list[float] | None = None,
    id_col: str = "id",
    pred_cols: list[str] | None = None,
) -> pd.DataFrame:
    """Rank-average ensemble of multiple submission files."""
    dfs = [pd.read_csv(p) for p in submission_paths]
    n = len(dfs)

    if weights is None:
        weights = [1.0 / n] * n

    w_sum = sum(weights)
    weights = [w / w_sum for w in weights]

    if pred_cols is None:
        pred_cols = [c for c in dfs[0].columns if c != id_col]

    result = dfs[0][[id_col]].copy()
    for col in pred_cols:
        ranked = np.zeros(len(dfs[0]))
        for w, df in zip(weights, dfs):
            ranked += w * df[col].rank(pct=True).values
        result[col] = ranked

    return result
