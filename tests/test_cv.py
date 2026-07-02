"""Tests for src/utils/cv.py."""

import numpy as np
import pandas as pd
import pytest

from src.utils.cv import create_folds, save_fold_split

pytest.importorskip("sklearn")

N_ROWS = 40
N_FOLDS = 5


@pytest.fixture
def df() -> pd.DataFrame:
    rng = np.random.default_rng(0)
    return pd.DataFrame(
        {
            "id": np.arange(N_ROWS),
            "target": np.tile([0, 1], N_ROWS // 2),
            "group": np.arange(N_ROWS) // 4,
            "feature": rng.normal(size=N_ROWS),
        }
    )


def _check_positional_splits(df: pd.DataFrame, splits: list) -> None:
    """val 集合が互いに素で、全行を位置インデックスでカバーすることを確認する。"""
    all_val: list[int] = []
    for train_idx, val_idx in splits:
        train_set, val_set = set(train_idx), set(val_idx)
        assert train_set.isdisjoint(val_set)
        assert train_set | val_set == set(range(len(df)))
        all_val.extend(val_idx)
    # 各行がちょうど 1 回だけ val に現れる（位置ベース）
    assert sorted(all_val) == list(range(len(df)))


@pytest.mark.parametrize("strategy", ["kfold", "stratified", "group"])
def test_create_folds_disjoint_full_coverage(df: pd.DataFrame, strategy: str) -> None:
    splits = list(
        create_folds(
            df,
            n_folds=N_FOLDS,
            strategy=strategy,
            target_col="target",
            group_col="group",
            seed=42,
        )
    )
    assert len(splits) == N_FOLDS
    _check_positional_splits(df, splits)


def test_stratified_preserves_class_ratio(df: pd.DataFrame) -> None:
    for _, val_idx in create_folds(
        df, n_folds=N_FOLDS, strategy="stratified", target_col="target", seed=42
    ):
        val_targets = df.iloc[val_idx]["target"]
        assert set(val_targets) == {0, 1}


def test_group_folds_do_not_split_groups(df: pd.DataFrame) -> None:
    for train_idx, val_idx in create_folds(
        df, n_folds=N_FOLDS, strategy="group", group_col="group", seed=42
    ):
        train_groups = set(df.iloc[train_idx]["group"])
        val_groups = set(df.iloc[val_idx]["group"])
        assert train_groups.isdisjoint(val_groups)


def test_group_strategy_requires_group_col(df: pd.DataFrame) -> None:
    with pytest.raises(ValueError, match="group_col"):
        list(create_folds(df, n_folds=N_FOLDS, strategy="group"))


def test_unknown_strategy_raises(df: pd.DataFrame) -> None:
    with pytest.raises(ValueError, match="Unknown CV strategy"):
        list(create_folds(df, strategy="bogus"))


def test_save_fold_split_writes_files(df: pd.DataFrame, tmp_path) -> None:
    train_idx, val_idx = next(
        create_folds(df, n_folds=N_FOLDS, strategy="kfold", seed=42)
    )
    fold_dir = tmp_path / "fold0"
    save_fold_split(df, train_idx, val_idx, fold_dir, id_col="id")

    train_csv = pd.read_csv(fold_dir / "train.csv")
    val_csv = pd.read_csv(fold_dir / "val.csv")
    assert list(train_csv.columns) == ["id"]
    assert len(train_csv) == len(train_idx)
    assert len(val_csv) == len(val_idx)
    assert set(val_csv["id"]) == set(df.iloc[val_idx]["id"])
