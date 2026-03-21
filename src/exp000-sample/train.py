import os
import random
from pathlib import Path

import hydra

# import numpy as np
# import pandas as pd
# import torch
import wandb
from omegaconf import DictConfig, OmegaConf

from src.utils.metrics_logger import MetricsLogger


def seed_everything(seed: int) -> None:
    """シード固定。実験で torch/numpy を使う場合は追加すること。"""
    random.seed(seed)
    os.environ["PYTHONHASHSEED"] = str(seed)
    # np.random.seed(seed)
    # torch.manual_seed(seed)
    # torch.cuda.manual_seed_all(seed)
    # torch.backends.cudnn.deterministic = True
    # torch.backends.cudnn.benchmark = False


def resolve_run_config(cfg: DictConfig) -> dict:
    """run_mode に応じて実行パラメータを決定する。"""
    mode = cfg.run_mode
    if mode == "debug":
        return {
            "epochs": cfg.debug.epochs,
            "n_folds": cfg.debug.n_folds,
            "max_samples": cfg.debug.samples,
            "limit_train_batches": cfg.debug.limit_train_batches,
            "limit_val_batches": cfg.debug.limit_val_batches,
            "wandb_mode": "disabled",
            "folds_to_run": [0],
        }
    elif mode == "fold0":
        return {
            "epochs": cfg.training.epochs,
            "n_folds": cfg.data.n_folds,
            "max_samples": None,
            "limit_train_batches": 1.0,
            "limit_val_batches": 1.0,
            "wandb_mode": cfg.wandb.mode,
            "folds_to_run": [0],
        }
    elif mode == "full":
        return {
            "epochs": cfg.training.epochs,
            "n_folds": cfg.data.n_folds,
            "max_samples": None,
            "limit_train_batches": 1.0,
            "limit_val_batches": 1.0,
            "wandb_mode": cfg.wandb.mode,
            "folds_to_run": list(range(cfg.data.n_folds)),
        }
    else:
        raise ValueError(f"Unknown run_mode: {mode}")


@hydra.main(version_base=None, config_path="config", config_name="config")
def main(cfg: DictConfig) -> None:
    seed_everything(cfg.seed)
    run_cfg = resolve_run_config(cfg)
    output_dir = Path(cfg.output_dir)

    print(f"Experiment: {cfg.exp_name}")
    print(f"Run: {cfg.run_name}")
    print(f"Run mode: {cfg.run_mode}")
    print(f"Config:\n{OmegaConf.to_yaml(cfg)}")

    # wandb group name（全 fold を束ねるキー）
    group_name = f"{cfg.exp_name}/{cfg.run_name}_{cfg.run_mode}"
    wandb_config = OmegaConf.to_container(cfg, resolve=True)

    # Initialize local metrics logger
    metrics_logger = MetricsLogger(cfg)

    # TODO: Load data
    # df = pd.read_csv(cfg.data.train_path)
    # if run_cfg["max_samples"]:
    #     df = df.head(run_cfg["max_samples"])

    # TODO: Create folds (e.g., StratifiedKFold)
    # from sklearn.model_selection import StratifiedKFold
    # skf = StratifiedKFold(n_splits=run_cfg["n_folds"], shuffle=True, random_state=cfg.seed)

    oof_predictions = []
    fold_scores: dict[int, float] = {}

    for fold_idx in run_cfg["folds_to_run"]:
        print(f"\n{'='*50}")
        print(f"Fold {fold_idx}")
        print(f"{'='*50}")

        # Initialize wandb fold run
        wandb.init(
            project=cfg.wandb.project,
            entity=cfg.wandb.entity,
            group=group_name,
            name=f"fold_{fold_idx}",
            job_type="train",
            config=wandb_config,
            mode=run_cfg["wandb_mode"],
            reinit=True,
        )

        fold_dir = output_dir / f"fold{fold_idx}"
        fold_dir.mkdir(parents=True, exist_ok=True)

        # TODO: Split data into train/val for this fold
        # train_idx, val_idx = list(skf.split(df, df["target"]))[fold_idx]
        # train_df = df.iloc[train_idx]
        # val_df = df.iloc[val_idx]

        # Save train/val split for reproducibility
        # train_df[["id"]].to_csv(fold_dir / "train.csv", index=False)
        # val_df[["id"]].to_csv(fold_dir / "val.csv", index=False)

        # TODO: Create DataLoaders
        # TODO: Create model
        # TODO: Create PyTorch Lightning Trainer with ModelCheckpoint
        #
        # from pytorch_lightning.callbacks import ModelCheckpoint
        # checkpoint_callback = ModelCheckpoint(
        #     dirpath=str(fold_dir),
        #     filename=f"{cfg.exp_name}-{{val_score:.4f}}",
        #     monitor="val_score",
        #     mode="max",
        #     save_top_k=1,
        # )
        #
        # trainer = pl.Trainer(
        #     max_epochs=run_cfg["epochs"],
        #     accelerator="auto",
        #     limit_train_batches=run_cfg["limit_train_batches"],
        #     limit_val_batches=run_cfg["limit_val_batches"],
        #     callbacks=[checkpoint_callback],
        #     logger=WandbLogger(experiment=wandb.run),
        # )
        #
        # trainer.fit(model, train_dataloader, val_dataloader)

        # TODO: Collect OOF predictions for this fold
        # oof_predictions.append(val_predictions_df)

        # Example: simulate training loop
        best_val_loss = float("inf")
        for epoch in range(run_cfg["epochs"]):
            train_loss = 1.0 / (epoch + 1)
            val_loss = 1.1 / (epoch + 1)
            best_val_loss = min(best_val_loss, val_loss)

            wandb.log({
                "epoch": epoch,
                "train/loss": train_loss,
                "val/loss": val_loss,
            })

            metrics_logger.log_epoch(fold_idx, {
                "epoch": epoch,
                "train_loss": train_loss,
                "val_loss": val_loss,
            })

            print(f"  Epoch {epoch}: train_loss={train_loss:.4f}, val_loss={val_loss:.4f}")

        fold_scores[fold_idx] = best_val_loss
        wandb.finish()

    # Save OOF predictions (full mode)
    # if run_cfg["folds_to_run"] == list(range(run_cfg["n_folds"])) and oof_predictions:
    #     oof_df = pd.concat(oof_predictions, ignore_index=True)
    #     oof_df.to_csv(output_dir / "oof_predictions.csv", index=False)
    #     print(f"\nOOF predictions saved to {output_dir / 'oof_predictions.csv'}")

    # Summary run（full モード && wandb 有効 && fold≥2）
    if len(run_cfg["folds_to_run"]) >= 2 and run_cfg["wandb_mode"] != "disabled":
        wandb.init(
            project=cfg.wandb.project,
            entity=cfg.wandb.entity,
            group=group_name,
            name="summary",
            job_type="summary",
            config=wandb_config,
            mode=run_cfg["wandb_mode"],
            reinit=True,
        )
        scores = list(fold_scores.values())
        cv_mean = sum(scores) / len(scores)
        cv_std = (sum((s - cv_mean) ** 2 for s in scores) / len(scores)) ** 0.5
        # TODO: Replace "loss" with your competition metric (e.g., "auc", "f1")
        wandb.summary["cv/loss"] = cv_mean
        wandb.summary["cv/loss_std"] = cv_std
        for fi, score in fold_scores.items():
            wandb.summary[f"fold{fi}/best_val_loss"] = score
        wandb.finish()
        print(f"\nCV score: {cv_mean:.4f} ± {cv_std:.4f}")

    metrics_logger.finish()
    print(f"\nTraining complete. Output dir: {output_dir}")


if __name__ == "__main__":
    main()
