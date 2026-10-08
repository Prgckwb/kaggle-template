"""予測ファイル（OOF / submission）のブレンド。

ID 列で先頭ファイルの行順に揃えてから混ぜる（行順の違うファイルを位置で混ぜる事故を防ぐ）。
OOF のブレンドは全素材が同じ fold ファイル（data.fold_version）を使っていることが前提。
"""

from __future__ import annotations

from pathlib import Path

import numpy as np
import pandas as pd


def load_aligned(paths: list[Path | str], id_col: str) -> list[pd.DataFrame]:
    dfs = [pd.read_csv(p) for p in paths]
    base_ids = dfs[0][id_col]
    aligned = []
    for path, df in zip(paths, dfs, strict=True):
        if id_col not in df.columns:
            raise ValueError(f"id_col '{id_col}' が {path} にありません")
        if set(df[id_col]) != set(base_ids) or len(df) != len(base_ids):
            raise ValueError(f"{path} の ID 集合が {paths[0]} と一致しません")
        aligned.append(df.set_index(id_col).loc[base_ids].reset_index())
    return aligned


def blend(
    paths: list[Path | str],
    weights: list[float] | None = None,
    *,
    method: str = "mean",
    id_col: str = "id",
    pred_cols: list[str] | None = None,
) -> pd.DataFrame:
    """加重平均（method="mean"）または加重ランク平均（method="rank"）でブレンドする。"""
    if method not in ("mean", "rank"):
        raise ValueError(f"Unknown blend method: {method}")
    dfs = load_aligned(paths, id_col)
    w = np.full(len(dfs), 1.0 / len(dfs)) if weights is None else np.asarray(weights)
    if len(w) != len(dfs):
        raise ValueError(f"重みは {len(dfs)} 個必要です（{len(w)} 個）")
    w = w / w.sum()

    cols = pred_cols or [c for c in dfs[0].columns if c != id_col]
    result = dfs[0][[id_col]].copy()
    for col in cols:
        values = [
            df[col].rank(pct=True).to_numpy()
            if method == "rank"
            else df[col].to_numpy()
            for df in dfs
        ]
        result[col] = np.average(np.vstack(values), axis=0, weights=w)
    return result
