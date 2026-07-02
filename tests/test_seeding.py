"""Tests for src/utils/seeding.py."""

import os
import random

import numpy as np

from src.utils.seeding import seed_everything


def test_random_is_reproducible() -> None:
    seed_everything(123)
    first = [random.random() for _ in range(5)]
    seed_everything(123)
    second = [random.random() for _ in range(5)]
    assert first == second


def test_numpy_is_reproducible() -> None:
    # seed_everything はレガシー global state を固定するため、レガシー API で検証する
    seed_everything(123)
    first = np.random.rand(5)  # noqa: NPY002
    seed_everything(123)
    second = np.random.rand(5)  # noqa: NPY002
    assert np.array_equal(first, second)


def test_sets_pythonhashseed() -> None:
    seed_everything(7)
    assert os.environ["PYTHONHASHSEED"] == "7"


def test_does_not_crash_without_torch() -> None:
    """torch 未インストール環境（base 依存のみ）でも例外なく動作する。"""
    seed_everything(0)  # ImportError が握りつぶされることの確認
