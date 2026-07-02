"""Ensemble and blending utilities."""

from __future__ import annotations

from pathlib import Path

import numpy as np
import pandas as pd


def _load_aligned(
    paths: list[Path | str],
    id_col: str,
) -> list[pd.DataFrame]:
    """予測ファイル群を読み込み、id_col で先頭ファイルの行順に揃える。

    行順が異なるファイルを位置で混ぜてしまう事故を防ぐ。ID 集合が一致しない
    場合はエラーにする。
    """
    dfs = [pd.read_csv(p) for p in paths]
    base = dfs[0]
    if id_col not in base.columns:
        raise ValueError(f"id_col '{id_col}' not found in {paths[0]}")

    aligned = [base]
    base_ids = base[id_col]
    for path, df in zip(paths[1:], dfs[1:], strict=True):
        if id_col not in df.columns:
            raise ValueError(f"id_col '{id_col}' not found in {path}")
        if not df[id_col].equals(base_ids):
            df = df.set_index(id_col).reindex(base_ids).reset_index()
            if df.isna().any().any():
                raise ValueError(
                    f"IDs in {path} do not match {paths[0]} (missing rows after align)"
                )
        aligned.append(df)
    return aligned


def _normalize_weights(weights: list[float] | None, n: int) -> list[float]:
    if weights is None:
        weights = [1.0 / n] * n
    if len(weights) != n:
        raise ValueError(f"Expected {n} weights, got {len(weights)}")
    w_sum = sum(weights)
    return [w / w_sum for w in weights]


def blend_predictions(
    oof_paths: list[Path | str],
    weights: list[float] | None = None,
    id_col: str = "id",
    pred_cols: list[str] | None = None,
) -> pd.DataFrame:
    """Weighted average of multiple OOF prediction files (aligned by id_col)."""
    dfs = _load_aligned(oof_paths, id_col)
    weights = _normalize_weights(weights, len(dfs))

    if pred_cols is None:
        pred_cols = [c for c in dfs[0].columns if c != id_col]

    result = dfs[0][[id_col]].copy()
    for col in pred_cols:
        result[col] = sum(
            w * df[col].values for w, df in zip(weights, dfs, strict=True)
        )

    return result


def rank_average(
    submission_paths: list[Path | str],
    weights: list[float] | None = None,
    id_col: str = "id",
    pred_cols: list[str] | None = None,
) -> pd.DataFrame:
    """Rank-average ensemble of multiple submission files (aligned by id_col)."""
    dfs = _load_aligned(submission_paths, id_col)
    weights = _normalize_weights(weights, len(dfs))

    if pred_cols is None:
        pred_cols = [c for c in dfs[0].columns if c != id_col]

    result = dfs[0][[id_col]].copy()
    for col in pred_cols:
        ranked = np.zeros(len(dfs[0]))
        for w, df in zip(weights, dfs, strict=True):
            ranked += w * df[col].rank(pct=True).values
        result[col] = ranked

    return result
