"""Regression tests for src/exp000_sample/data.create_folds.

sklearn の splitter は位置インデックスを返すため、.loc（ラベルベース）で
fold を代入すると index が 0 始まりでない DataFrame で壊れる。
.iloc ベースの実装が非連続 index でも全行に fold を割り当てることを確認する。
"""

import numpy as np
import pandas as pd
import pytest

from src.exp000_sample.data import create_folds

pytest.importorskip("sklearn")


def _make_df(n: int = 40) -> pd.DataFrame:
    return pd.DataFrame(
        {
            "id": np.arange(n),
            "target": np.tile([0, 1], n // 2),
            "group": np.arange(n) // 4,
        }
    )


def test_create_folds_assigns_all_rows_default_index() -> None:
    df = _make_df()
    result = create_folds(df, n_folds=5, seed=42, strategy="stratified")
    assert (result["fold"] >= 0).all()
    assert set(result["fold"]) == {0, 1, 2, 3, 4}


def test_create_folds_non_contiguous_index() -> None:
    """index が 0 始まりでない（df.iloc[5:35]）場合の回帰テスト。"""
    df = _make_df().iloc[5:35]
    assert df.index[0] == 5  # 前提: 位置とラベルがずれている

    result = create_folds(df, n_folds=5, seed=42, strategy="stratified")

    assert len(result) == 30
    assert (result["fold"] >= 0).all(), "fold 未割り当ての行がある（.loc/.iloc バグ）"
    assert set(result["fold"]) == {0, 1, 2, 3, 4}


def test_create_folds_shuffled_index() -> None:
    """index がシャッフルされていても全行に fold が付くこと。"""
    df = _make_df().sample(frac=1, random_state=0)

    result = create_folds(df, n_folds=5, seed=42, strategy="stratified")

    assert (result["fold"] >= 0).all()
    # fold ごとの行数がほぼ均等
    counts = result["fold"].value_counts()
    assert counts.min() >= len(df) // 5 - 1


def test_create_folds_does_not_mutate_input() -> None:
    df = _make_df()
    create_folds(df, n_folds=5, seed=42, strategy="stratified")
    assert "fold" not in df.columns
