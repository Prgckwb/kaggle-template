"""Model definitions.

Replace this with your competition-specific model.
For PyTorch Lightning: subclass LightningModule.
For GBM: use lightgbm/xgboost/catboost directly in train.py.
"""

from __future__ import annotations

from typing import Any


class BaselineModel:
    """Framework-agnostic model skeleton.

    For PyTorch Lightning, replace with::

        import lightning as L
        import torch
        import torch.nn as nn

        class BaselineModel(L.LightningModule):
            def __init__(self, cfg):
                super().__init__()
                self.save_hyperparameters()
                self.model = nn.Linear(cfg.model.input_dim, cfg.model.output_dim)
                self.criterion = nn.MSELoss()

            def forward(self, x):
                return self.model(x)

            def training_step(self, batch, batch_idx):
                x, y = batch
                pred = self(x)
                loss = self.criterion(pred, y)
                self.log("train/loss", loss, prog_bar=True)
                return loss

            def validation_step(self, batch, batch_idx):
                x, y = batch
                pred = self(x)
                loss = self.criterion(pred, y)
                self.log("val/loss", loss, prog_bar=True)

            def configure_optimizers(self):
                return torch.optim.Adam(self.parameters(), lr=self.hparams.cfg.training.lr)
    """

    def __init__(self, config: Any) -> None:
        self.config = config

    def forward(self, x: Any) -> Any:
        raise NotImplementedError

    def predict(self, x: Any) -> Any:
        raise NotImplementedError
