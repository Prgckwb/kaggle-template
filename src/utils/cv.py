"""Cross-validation split utilities."""

from __future__ import annotations

from pathlib import Path
from typing import Any, Iterator

import pandas as pd


def create_folds(
    df: pd.DataFrame,
    *,
    n_folds: int = 5,
    strategy: str = "stratified",
    target_col: str = "target",
    group_col: str | None = None,
    seed: int = 42,
) -> Iterator[tuple[Any, Any]]:
    """Generate train/val index splits.

    Args:
        strategy: "kfold", "stratified", "group", "stratified_group", "timeseries"
    """
    from sklearn.model_selection import (
        GroupKFold,
        KFold,
        StratifiedGroupKFold,
        StratifiedKFold,
        TimeSeriesSplit,
    )

    if strategy == "kfold":
        splitter = KFold(n_splits=n_folds, shuffle=True, random_state=seed)
        yield from splitter.split(df)
    elif strategy == "stratified":
        splitter = StratifiedKFold(n_splits=n_folds, shuffle=True, random_state=seed)
        yield from splitter.split(df, df[target_col])
    elif strategy == "group":
        if group_col is None:
            raise ValueError("group_col is required for group strategy")
        splitter = GroupKFold(n_splits=n_folds)
        yield from splitter.split(df, groups=df[group_col])
    elif strategy == "stratified_group":
        if group_col is None:
            raise ValueError("group_col is required for stratified_group strategy")
        splitter = StratifiedGroupKFold(
            n_splits=n_folds, shuffle=True, random_state=seed
        )
        yield from splitter.split(df, df[target_col], groups=df[group_col])
    elif strategy == "timeseries":
        splitter = TimeSeriesSplit(n_splits=n_folds)
        yield from splitter.split(df)
    else:
        raise ValueError(f"Unknown CV strategy: {strategy}")


def save_fold_split(
    df: pd.DataFrame,
    train_idx: Any,
    val_idx: Any,
    fold_dir: Path,
    id_col: str = "id",
) -> None:
    """Save train/val index files for reproducibility."""
    fold_dir.mkdir(parents=True, exist_ok=True)
    if id_col in df.columns:
        df.iloc[train_idx][[id_col]].to_csv(fold_dir / "train.csv", index=False)
        df.iloc[val_idx][[id_col]].to_csv(fold_dir / "val.csv", index=False)
    else:
        pd.DataFrame({"index": train_idx}).to_csv(fold_dir / "train.csv", index=False)
        pd.DataFrame({"index": val_idx}).to_csv(fold_dir / "val.csv", index=False)
