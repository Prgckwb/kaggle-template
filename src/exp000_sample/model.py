"""モデル定義（サンプル: 表形式データの MLP による二値分類）。"""

from __future__ import annotations

import lightning as L
import numpy as np
import torch
from torch import nn

from src.metric import score


class TabularMLP(L.LightningModule):
    def __init__(
        self,
        n_features: int,
        hidden_dim: int,
        dropout: float,
        lr: float,
        metric_key: str,
    ) -> None:
        super().__init__()
        self.save_hyperparameters()
        self.net = nn.Sequential(
            nn.Linear(n_features, hidden_dim),
            nn.ReLU(),
            nn.Dropout(dropout),
            nn.Linear(hidden_dim, 1),
        )
        self.criterion = nn.BCEWithLogitsLoss()
        self._val_preds: list[torch.Tensor] = []
        self._val_targets: list[torch.Tensor] = []

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        return self.net(x).squeeze(-1)

    def training_step(self, batch: list[torch.Tensor], batch_idx: int) -> torch.Tensor:
        x, y = batch
        loss = self.criterion(self(x), y)
        self.log("train/loss", loss, on_step=True, on_epoch=True, prog_bar=True)
        return loss

    def validation_step(self, batch: list[torch.Tensor], batch_idx: int) -> None:
        x, y = batch
        logits = self(x)
        self.log("val/loss", self.criterion(logits, y), on_epoch=True, prog_bar=True)
        self._val_preds.append(torch.sigmoid(logits).detach().cpu())
        self._val_targets.append(y.detach().cpu())

    def on_validation_epoch_end(self) -> None:
        preds = torch.cat(self._val_preds).numpy()
        targets = torch.cat(self._val_targets).numpy()
        self._val_preds.clear()
        self._val_targets.clear()
        value = score(targets, preds) if len(np.unique(targets)) > 1 else float("nan")
        self.log(self.hparams.metric_key, value, prog_bar=True)
        self.log("val/pred_std", float(preds.std()))

    def predict_step(self, batch: list[torch.Tensor], batch_idx: int) -> torch.Tensor:
        return torch.sigmoid(self(batch[0]))

    def configure_optimizers(self) -> torch.optim.Optimizer:
        return torch.optim.AdamW(self.parameters(), lr=self.hparams.lr)
