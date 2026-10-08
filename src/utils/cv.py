"""fold 割当。fold は実験ごとに作らず、`data/folds/folds_{version}.csv` を全実験で共有する。

共有しないと実験間で OOF の分割が食い違い、アンサンブルの重み最適化や
実験間のスコア比較にリークと交絡が入る。既存の fold ファイルは不変（上書きしない）。
戦略を変えるときは fold_version を上げて新しいファイルを作る。
"""

from __future__ import annotations

from pathlib import Path

import numpy as np
import pandas as pd


def assign_folds(
    df: pd.DataFrame,
    *,
    n_folds: int,
    strategy: str,
    target_col: str | None,
    group_col: str | None,
    seed: int,
) -> np.ndarray:
    """各行の fold 番号を返す。strategy: kfold / stratified / group / stratified_group / timeseries。"""
    from sklearn.model_selection import (
        GroupKFold,
        KFold,
        StratifiedGroupKFold,
        StratifiedKFold,
        TimeSeriesSplit,
    )

    y = df[target_col] if target_col else None
    groups = df[group_col] if group_col else None
    splitters = {
        "kfold": KFold(n_splits=n_folds, shuffle=True, random_state=seed),
        "stratified": StratifiedKFold(
            n_splits=n_folds, shuffle=True, random_state=seed
        ),
        "group": GroupKFold(n_splits=n_folds),
        "stratified_group": StratifiedGroupKFold(
            n_splits=n_folds, shuffle=True, random_state=seed
        ),
        "timeseries": TimeSeriesSplit(n_splits=n_folds),
    }
    if strategy not in splitters:
        raise ValueError(f"Unknown CV strategy: {strategy}")
    if strategy in ("group", "stratified_group") and groups is None:
        raise ValueError(f"{strategy} には group_col が必要です")

    folds = np.full(len(df), -1, dtype=int)
    for fold_idx, (_, val_idx) in enumerate(splitters[strategy].split(df, y, groups)):
        folds[val_idx] = fold_idx
    return folds


def load_or_create_folds(
    df: pd.DataFrame,
    *,
    path: str | Path,
    id_col: str,
    n_folds: int,
    strategy: str,
    target_col: str | None,
    group_col: str | None,
    seed: int,
) -> np.ndarray:
    """fold ファイルがあれば読んで df の行順に揃え、無ければ作って保存する。

    fold ファイルと df の ID 集合が一致しなければエラーにする（データ差し替えの検出）。
    timeseries の先頭区間など、どの fold にも入らない行は -1 になる。
    """
    path = Path(path)
    if path.exists():
        folds_df = pd.read_csv(path)
        mapping = dict(zip(folds_df[id_col], folds_df["fold"], strict=True))
        missing = [i for i in df[id_col] if i not in mapping]
        if missing or len(mapping) != len(df):
            raise ValueError(
                f"{path} の ID が学習データと一致しません（欠落 {len(missing)} 件）。"
                "データが変わったなら fold_version を上げて新しい fold ファイルを作ってください"
            )
        return df[id_col].map(mapping).to_numpy(dtype=int)

    folds = assign_folds(
        df,
        n_folds=n_folds,
        strategy=strategy,
        target_col=target_col,
        group_col=group_col,
        seed=seed,
    )
    path.parent.mkdir(parents=True, exist_ok=True)
    pd.DataFrame({id_col: df[id_col], "fold": folds}).to_csv(path, index=False)
    print(f"fold ファイルを作成しました: {path}（git にコミットしてください）")
    return folds
