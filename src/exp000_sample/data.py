"""データの読み込みと Dataset / DataLoader。

学習（train.py）と推論（inference.py・提出 notebook）は同じ前処理関数を通す（train/serve skew 防止）。
"""

from __future__ import annotations

import pandas as pd
import torch
from omegaconf import DictConfig
from torch.utils.data import DataLoader, TensorDataset


def feature_columns(df: pd.DataFrame, cfg: DictConfig) -> list[str]:
    excluded = {cfg.data.id_col, cfg.data.target_col}
    return [c for c in df.columns if c not in excluded]


def preprocess(df: pd.DataFrame, cfg: DictConfig) -> pd.DataFrame:
    """学習・推論で共有する前処理（コンペごとに書き換える）。"""
    return df


def make_loader(
    df: pd.DataFrame, cfg: DictConfig, *, features: list[str], train: bool
) -> DataLoader:
    x = torch.tensor(df[features].to_numpy(), dtype=torch.float32)
    tensors = [x]
    if cfg.data.target_col in df.columns:
        tensors.append(
            torch.tensor(df[cfg.data.target_col].to_numpy(), dtype=torch.float32)
        )
    return DataLoader(
        TensorDataset(*tensors),
        batch_size=cfg.training.batch_size,
        shuffle=train,
        num_workers=cfg.training.num_workers,
        pin_memory=torch.cuda.is_available(),
        persistent_workers=cfg.training.num_workers > 0,
    )
