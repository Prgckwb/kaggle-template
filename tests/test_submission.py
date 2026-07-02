"""Tests for src/utils/submission.py."""

from pathlib import Path

import pandas as pd
import pytest

from src.utils.submission import validate_submission


@pytest.fixture
def sample_path(tmp_path: Path) -> Path:
    path = tmp_path / "sample_submission.csv"
    pd.DataFrame({"id": [1, 2, 3], "target": [0.0, 0.0, 0.0]}).to_csv(path, index=False)
    return path


def _write_sub(tmp_path: Path, df: pd.DataFrame) -> Path:
    path = tmp_path / "submission.csv"
    df.to_csv(path, index=False)
    return path


def test_valid_submission_returns_no_errors(tmp_path: Path, sample_path: Path) -> None:
    sub = _write_sub(
        tmp_path, pd.DataFrame({"id": [1, 2, 3], "target": [0.1, 0.5, 0.9]})
    )
    assert validate_submission(sub, sample_path) == []


def test_column_mismatch(tmp_path: Path, sample_path: Path) -> None:
    sub = _write_sub(
        tmp_path, pd.DataFrame({"id": [1, 2, 3], "prediction": [0.1, 0.5, 0.9]})
    )
    errors = validate_submission(sub, sample_path)
    assert len(errors) == 1
    assert "Column mismatch" in errors[0]


def test_row_count_and_missing_ids(tmp_path: Path, sample_path: Path) -> None:
    sub = _write_sub(tmp_path, pd.DataFrame({"id": [1, 2], "target": [0.1, 0.5]}))
    errors = validate_submission(sub, sample_path)
    assert any("Row count mismatch" in e for e in errors)
    assert any("Missing 1 IDs" in e for e in errors)


def test_null_values_detected(tmp_path: Path, sample_path: Path) -> None:
    sub = _write_sub(
        tmp_path, pd.DataFrame({"id": [1, 2, 3], "target": [0.1, None, 0.9]})
    )
    errors = validate_submission(sub, sample_path)
    assert any("Null values" in e for e in errors)


def test_extra_ids_detected(tmp_path: Path, sample_path: Path) -> None:
    sub = _write_sub(
        tmp_path, pd.DataFrame({"id": [1, 2, 9], "target": [0.1, 0.5, 0.9]})
    )
    errors = validate_submission(sub, sample_path)
    assert any("extra IDs" in e for e in errors)
    assert any("Missing 1 IDs" in e for e in errors)
