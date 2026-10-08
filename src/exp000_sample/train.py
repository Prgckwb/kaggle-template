"""学習スクリプト（実験の出力契約は docs/training-conventions.md）。

Run: uv run python -m src.exp000_sample.train [run_mode=debug|fold0|full] [--config-name=run001-xxx]
"""

from __future__ import annotations

from datetime import UTC, datetime
from pathlib import Path
from typing import Any, cast

import hydra
import lightning as L
import pandas as pd
import torch
import wandb
from hydra.core.hydra_config import HydraConfig
from lightning.pytorch.callbacks import ModelCheckpoint
from lightning.pytorch.loggers import CSVLogger, WandbLogger
from omegaconf import DictConfig, OmegaConf

from src.exp000_sample.data import feature_columns, make_loader, preprocess
from src.exp000_sample.model import TabularMLP
from src.metric import score
from src.utils.cv import load_or_create_folds
from src.utils.lineage import run_lineage
from src.utils.logger import get_logger
from src.utils.profile import register_profile_resolver
from src.utils.run_summary import build_run_summary, write_run_summary
from src.utils.seeding import seed_everything

register_profile_resolver()
CONFIG_DIR = Path(__file__).parent / "config"


def mode_settings(cfg: DictConfig) -> dict[str, Any]:
    """run_mode ごとの実行パラメータ。debug は出力先を *-debug に隔離し本番の出力を上書きしない。"""
    if cfg.run_mode == "debug":
        return {
            "epochs": cfg.debug.epochs,
            "max_samples": cfg.debug.samples,
            "limit_train_batches": cfg.debug.limit_train_batches,
            "limit_val_batches": cfg.debug.limit_val_batches,
            "wandb_mode": "disabled",
            "folds": [0],
            "suffix": "-debug",
        }
    if cfg.run_mode in ("fold0", "full"):
        return {
            "epochs": cfg.training.epochs,
            "max_samples": None,
            "limit_train_batches": 1.0,
            "limit_val_batches": 1.0,
            "wandb_mode": cfg.wandb.mode,
            "folds": [0] if cfg.run_mode == "fold0" else list(range(cfg.data.n_folds)),
            "suffix": "",
        }
    raise ValueError(f"Unknown run_mode: {cfg.run_mode}")


@hydra.main(version_base=None, config_path="config", config_name="config")
def main(cfg: DictConfig) -> None:
    started_at = datetime.now(UTC).isoformat()
    mode = mode_settings(cfg)
    output_dir = Path(f"{cfg.output_dir}{mode['suffix']}")
    logs_dir = Path(f"{cfg.logs_dir}{mode['suffix']}")
    logger = get_logger(cfg.exp_name, logs_dir)
    seed_everything(cfg.seed)

    metric_key = f"val/{cfg.metric.name}"
    exp_short = cfg.exp_name.split("_")[0]  # "exp000_sample" -> "exp000"
    overrides = list(HydraConfig.get().overrides.task)
    lineage = run_lineage(CONFIG_DIR, HydraConfig.get().job.config_name, overrides)
    if len(lineage["changed"]) >= 2:
        logger.warning(
            "親 %s から %d 変数を変えています %s。この run の Δ は単一の変数に帰属できません",
            lineage["parent"],
            len(lineage["changed"]),
            lineage["changed"],
        )
    logger.info(
        "Run %s/%s (%s) lineage=%s", cfg.exp_name, cfg.run_name, cfg.run_mode, lineage
    )
    logger.info("Config:\n%s", OmegaConf.to_yaml(cfg, resolve=True))

    # fold は全行に対して共有ファイルから割り当ててから間引く（debug でも fold の定義を変えない）
    df = preprocess(pd.read_csv(cfg.data.train_path), cfg)
    df["fold"] = load_or_create_folds(
        df,
        path=cfg.data.folds_path,
        id_col=cfg.data.id_col,
        n_folds=cfg.data.n_folds,
        strategy=cfg.data.cv_strategy,
        target_col=cfg.data.target_col,
        group_col=cfg.data.group_col,
        seed=cfg.seed,
    )
    if mode["max_samples"]:
        df = df.sample(n=min(mode["max_samples"], len(df)), random_state=cfg.seed)
        df = df.reset_index(drop=True)
    features = feature_columns(df.drop(columns="fold"), cfg)

    wandb_config = cast(dict[str, Any], OmegaConf.to_container(cfg, resolve=True))
    wandb_config["lineage"] = lineage
    group = f"{cfg.exp_name}/{cfg.run_name}_{cfg.run_mode}"
    tags = [
        t
        for t in (
            exp_short,
            cfg.run_name,
            cfg.run_mode,
            cfg.data.fold_version,
            cfg.data.data_version,
            cfg.data.label_version,
        )
        if t
    ]

    fold_scores: dict[int, float] = {}
    oof_parts: list[pd.DataFrame] = []
    for fold_idx in mode["folds"]:
        logger.info("===== Fold %d =====", fold_idx)
        train_df = df[df["fold"] != fold_idx].reset_index(drop=True)
        val_df = df[df["fold"] == fold_idx].reset_index(drop=True)
        logger.info("train=%d val=%d", len(train_df), len(val_df))
        fold_dir = output_dir / f"fold{fold_idx}"
        fold_dir.mkdir(parents=True, exist_ok=True)
        val_df[[cfg.data.id_col]].to_csv(fold_dir / "val_ids.csv", index=False)

        # 決定的 id + resume="allow" は「同じ試行の継続」用。設定を変えたら新しい run_name を切る
        run = wandb.init(
            project=cfg.wandb.project,
            entity=cfg.wandb.entity,
            group=group,
            name=f"{exp_short}-{cfg.run_name}-f{fold_idx}",
            id=f"{exp_short}-{cfg.run_name}-{cfg.run_mode}-f{fold_idx}",
            resume="allow",
            job_type="train",
            config=wandb_config | {"fold_idx": fold_idx},
            notes=", ".join(overrides) or None,
            tags=[*tags, f"fold{fold_idx}"],
            mode=mode["wandb_mode"],
            reinit="finish_previous",
        )
        run.define_metric(metric_key, summary=cfg.metric.mode)
        run.define_metric("val/loss", summary="min")

        checkpoint = ModelCheckpoint(
            dirpath=fold_dir,
            # 命名規約は docs/training-conventions.md「チェックポイント」（submission_manifest がパースする）
            filename=f"{exp_short}-{cfg.run_name}-f{fold_idx}-ep{{epoch:02d}}"
            f"-val_{cfg.metric.name}-{{{metric_key}:.4f}}",
            auto_insert_metric_name=False,
            monitor=metric_key,
            mode=cfg.metric.mode,
            save_top_k=cfg.training.save_top_k,
        )
        model = TabularMLP(
            n_features=len(features),
            hidden_dim=cfg.model.hidden_dim,
            dropout=cfg.model.dropout,
            lr=cfg.training.lr,
            metric_key=metric_key,
        )
        trainer = L.Trainer(
            max_epochs=mode["epochs"],
            accelerator="auto",
            limit_train_batches=mode["limit_train_batches"],
            limit_val_batches=mode["limit_val_batches"],
            callbacks=[checkpoint],
            logger=[
                WandbLogger(experiment=run),
                CSVLogger(save_dir=logs_dir, name=f"fold{fold_idx}", version=""),
            ],
            log_every_n_steps=10,
        )
        val_loader = make_loader(val_df, cfg, features=features, train=False)
        trainer.fit(
            model, make_loader(train_df, cfg, features=features, train=True), val_loader
        )

        # best ckpt で val 全体を推論し直し、競技指標を再計算する（ログの値は limit_val_batches の影響を受ける）
        best = TabularMLP.load_from_checkpoint(checkpoint.best_model_path)
        preds = torch.cat(trainer.predict(best, val_loader)).float().numpy()
        fold_scores[fold_idx] = score(val_df[cfg.data.target_col].to_numpy(), preds)
        logger.info(
            "Fold %d score=%.5f best=%s",
            fold_idx,
            fold_scores[fold_idx],
            checkpoint.best_model_path,
        )
        run.summary[f"best_{metric_key}"] = fold_scores[fold_idx]
        oof_parts.append(
            pd.DataFrame(
                {cfg.data.id_col: val_df[cfg.data.id_col], cfg.data.target_col: preds}
            )
        )
        run.finish()

    # OOF と CV の代表値（oof_score）は全 fold を回したときだけ。fold0 の値を CV と呼ばない
    oof_score = None
    if cfg.run_mode == "full":
        oof = pd.concat(oof_parts, ignore_index=True)
        oof.to_csv(output_dir / "oof_predictions.csv", index=False)
        truth = df.set_index(cfg.data.id_col).loc[
            oof[cfg.data.id_col], cfg.data.target_col
        ]
        oof_score = score(truth.to_numpy(), oof[cfg.data.target_col].to_numpy())

    summary = build_run_summary(
        exp_name=cfg.exp_name,
        run_name=cfg.run_name,
        run_mode=cfg.run_mode,
        metric_name=cfg.metric.name,
        metric_mode=cfg.metric.mode,
        fold_scores=fold_scores,
        n_folds=cfg.data.n_folds,
        oof_score=oof_score,
        lineage=lineage,
        overrides=overrides,
        started_at=started_at,
    )
    write_run_summary(summary, logs_dir)
    logger.info(
        "fold_scores=%s cv_mean=%s cv_std=%s oof=%s",
        summary["fold_scores"],
        summary["cv_mean"],
        summary["cv_std"],
        oof_score,
    )

    # summary run は全 fold を回し、wandb が有効なときだけ（1 fold の値を CV として並べない）
    if oof_score is not None and mode["wandb_mode"] != "disabled":
        run = wandb.init(
            project=cfg.wandb.project,
            entity=cfg.wandb.entity,
            group=group,
            name=f"{exp_short}-{cfg.run_name}-summary",
            id=f"{exp_short}-{cfg.run_name}-{cfg.run_mode}-summary",
            resume="allow",
            job_type="summary",
            config=wandb_config,
            tags=tags,
            mode=mode["wandb_mode"],
            reinit="finish_previous",
        )
        run.summary[f"oof/{cfg.metric.name}"] = oof_score
        run.summary[f"cv/{cfg.metric.name}"] = summary["cv_mean"]
        run.summary[f"cv/{cfg.metric.name}_std"] = summary["cv_std"]
        for k, v in fold_scores.items():
            run.summary[f"fold{k}/best_val_{cfg.metric.name}"] = v
        run.finish()

    logger.info("Done. output=%s logs=%s", output_dir, logs_dir)


if __name__ == "__main__":
    main()
