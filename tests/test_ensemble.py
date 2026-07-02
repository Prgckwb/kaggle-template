"""Tests for src/utils/ensemble.py."""

from pathlib import Path

import pandas as pd
import pytest

from src.utils.ensemble import blend_predictions, rank_average


@pytest.fixture
def pred_files(tmp_path: Path) -> tuple[Path, Path]:
    """id 順の揃った file1 と、行順をシャッフルした file2 を作る。"""
    file1 = tmp_path / "pred1.csv"
    file2 = tmp_path / "pred2.csv"
    pd.DataFrame({"id": [1, 2, 3, 4], "pred": [0.0, 0.1, 0.2, 0.3]}).to_csv(
        file1, index=False
    )
    # id 1..4 に対して pred = 0.2, 0.3, 0.4, 0.5（行順はシャッフル）
    pd.DataFrame({"id": [3, 1, 4, 2], "pred": [0.4, 0.2, 0.5, 0.3]}).to_csv(
        file2, index=False
    )
    return file1, file2


def test_blend_aligns_rows_by_id(pred_files: tuple[Path, Path]) -> None:
    file1, file2 = pred_files
    result = blend_predictions([file1, file2])

    assert list(result["id"]) == [1, 2, 3, 4]
    expected = [(0.0 + 0.2) / 2, (0.1 + 0.3) / 2, (0.2 + 0.4) / 2, (0.3 + 0.5) / 2]
    assert result["pred"].tolist() == pytest.approx(expected)


def test_blend_shuffled_equals_sorted(
    pred_files: tuple[Path, Path], tmp_path: Path
) -> None:
    """file2 をソートし直しても結果が同じ（位置混合していない）こと。"""
    file1, file2 = pred_files
    sorted_file2 = tmp_path / "pred2_sorted.csv"
    pd.read_csv(file2).sort_values("id").to_csv(sorted_file2, index=False)

    shuffled = blend_predictions([file1, file2])
    sorted_ = blend_predictions([file1, sorted_file2])
    pd.testing.assert_frame_equal(shuffled, sorted_)


def test_blend_weights(pred_files: tuple[Path, Path]) -> None:
    file1, file2 = pred_files
    result = blend_predictions([file1, file2], weights=[3.0, 1.0])
    expected = [
        0.75 * a + 0.25 * b
        for a, b in zip([0.0, 0.1, 0.2, 0.3], [0.2, 0.3, 0.4, 0.5], strict=True)
    ]
    assert result["pred"].tolist() == pytest.approx(expected)


def test_blend_mismatched_weights_length_raises(pred_files: tuple[Path, Path]) -> None:
    file1, file2 = pred_files
    with pytest.raises(ValueError, match="weights"):
        blend_predictions([file1, file2], weights=[1.0, 1.0, 1.0])


def test_blend_mismatched_ids_raise(tmp_path: Path) -> None:
    file1 = tmp_path / "a.csv"
    file2 = tmp_path / "b.csv"
    pd.DataFrame({"id": [1, 2, 3], "pred": [0.1, 0.2, 0.3]}).to_csv(file1, index=False)
    pd.DataFrame({"id": [1, 2, 5], "pred": [0.1, 0.2, 0.3]}).to_csv(file2, index=False)
    with pytest.raises(ValueError, match="do not match"):
        blend_predictions([file1, file2])


def test_rank_average_basic(pred_files: tuple[Path, Path]) -> None:
    file1, file2 = pred_files
    result = rank_average([file1, file2])
    # 両ファイルとも id 順に単調増加なので、rank 平均も単調増加
    assert result["pred"].is_monotonic_increasing
    assert list(result["id"]) == [1, 2, 3, 4]


def test_rank_average_mismatched_weights_length_raises(
    pred_files: tuple[Path, Path],
) -> None:
    file1, file2 = pred_files
    with pytest.raises(ValueError, match="weights"):
        rank_average([file1, file2], weights=[0.5])
