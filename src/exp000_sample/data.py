"""Data loading and preprocessing.

Replace the TODO sections with your competition-specific implementation.
For PyTorch Lightning, use LightningDataModule.
For GBM/tabular, use pandas/polars directly.
"""

from __future__ import annotations

from pathlib import Path

import pandas as pd


def load_data(
    train_path: str | Path, test_path: str | Path
) -> tuple[pd.DataFrame, pd.DataFrame]:
    """Load train and test data."""
    train_df = pd.read_csv(train_path)
    test_df = pd.read_csv(test_path)
    return train_df, test_df


def preprocess(df: pd.DataFrame) -> pd.DataFrame:
    """Preprocess dataframe. Override per competition."""
    return df


def create_folds(
    df: pd.DataFrame,
    n_folds: int,
    seed: int,
    strategy: str = "stratified",
    target_col: str = "target",
    group_col: str | None = None,
) -> pd.DataFrame:
    """Add a 'fold' column to the dataframe using src/utils/cv.py.

    Note: sklearn の splitter が返す val_idx は「位置」インデックスなので、
    ラベルベースの .loc ではなく .iloc で代入する（行をフィルタした
    DataFrame でも正しく動作させるため）。
    """
    from src.utils.cv import create_folds as _create_folds

    df = df.copy()
    df["fold"] = -1
    fold_col = df.columns.get_loc("fold")
    for fold_idx, (_, val_idx) in enumerate(
        _create_folds(
            df,
            n_folds=n_folds,
            strategy=strategy,
            target_col=target_col,
            group_col=group_col,
            seed=seed,
        )
    ):
        df.iloc[val_idx, fold_col] = fold_idx
    return df


# ---------------------------------------------------------------------------
# PyTorch Lightning DataModule example (uncomment and adapt):
# ---------------------------------------------------------------------------
#
# import lightning as L
# from torch.utils.data import DataLoader, Dataset
#
# class CompetitionDataModule(L.LightningDataModule):
#     def __init__(self, cfg, train_df, val_df):
#         super().__init__()
#         self.cfg = cfg
#         self.train_df = train_df
#         self.val_df = val_df
#
#     def setup(self, stage=None):
#         self.train_ds = CompetitionDataset(self.train_df)
#         self.val_ds = CompetitionDataset(self.val_df)
#
#     def train_dataloader(self):
#         return DataLoader(
#             self.train_ds,
#             batch_size=self.cfg.training.batch_size,
#             shuffle=True,
#             num_workers=self.cfg.data.get("num_workers", 4),
#             pin_memory=self.cfg.data.get("pin_memory", True),
#         )
#
#     def val_dataloader(self):
#         return DataLoader(
#             self.val_ds,
#             batch_size=self.cfg.training.batch_size,
#             shuffle=False,
#             num_workers=self.cfg.data.get("num_workers", 4),
#             pin_memory=self.cfg.data.get("pin_memory", True),
#         )
