"""Submission file validation utilities."""

from __future__ import annotations

from pathlib import Path

import pandas as pd


def validate_submission(
    submission_path: Path | str,
    sample_submission_path: Path | str,
) -> list[str]:
    """Validate a submission file against the sample submission.

    Returns a list of error messages (empty = valid).
    """
    errors: list[str] = []

    sub = pd.read_csv(submission_path)
    sample = pd.read_csv(sample_submission_path)

    if list(sub.columns) != list(sample.columns):
        errors.append(
            f"Column mismatch: expected {list(sample.columns)}, got {list(sub.columns)}"
        )
        return errors

    if len(sub) != len(sample):
        errors.append(f"Row count mismatch: expected {len(sample)}, got {len(sub)}")

    if sub.isnull().any().any():
        null_cols = [c for c in sub.columns if sub[c].isnull().any()]
        errors.append(f"Null values found in columns: {null_cols}")

    id_col = sample.columns[0]
    if id_col in sub.columns and id_col in sample.columns:
        sub_ids = set(sub[id_col])
        sample_ids = set(sample[id_col])
        missing = sample_ids - sub_ids
        extra = sub_ids - sample_ids
        if missing:
            errors.append(f"Missing {len(missing)} IDs from submission")
        if extra:
            errors.append(f"Found {len(extra)} extra IDs in submission")

    return errors
