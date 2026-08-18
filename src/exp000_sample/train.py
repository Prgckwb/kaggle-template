from pathlib import Path
from typing import Any, cast

import hydra

# import numpy as np
# import pandas as pd
import wandb
from hydra.core.hydra_config import HydraConfig
from omegaconf import DictConfig, OmegaConf

from src.exp000_sample.config_schema import register_config_schema
from src.utils.logger import get_logger, resolve_logs_dir
from src.utils.metrics_logger import MetricsLogger
from src.utils.seeding import seed_everything

register_config_schema()


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

    # 実行ログ（進捗・警告）は logs_dir にタイムスタンプ付きで保存される
    logger = get_logger(cfg.exp_name, resolve_logs_dir(cfg.logs_dir, cfg.run_mode))

    # 評価指標（config.yaml の metric セクション。docs/competition-profile.yaml と揃える）
    metric_name = cfg.metric.name
    metric_mode = cfg.metric.mode  # "max" | "min"
    metric_key = (
        f"val/{metric_name}"  # wandb / MetricsLogger のキー名（{split}/{metric} 形式）
    )

    logger.info("Experiment: %s", cfg.exp_name)
    logger.info("Run: %s", cfg.run_name)
    logger.info("Run mode: %s", cfg.run_mode)
    logger.info("Config:\n%s", OmegaConf.to_yaml(cfg))

    # wandb group name（全 fold を束ねるキー）
    group_name = f"{cfg.exp_name}/{cfg.run_name}_{cfg.run_mode}"
    exp_short = cfg.exp_name.split("_")[0]  # "exp000_sample" -> "exp000"
    wandb_config = cast(dict[str, Any], OmegaConf.to_container(cfg, resolve=True))
    # CLI オーバーライド（例: "training.lr=5e-4, run_mode=full"）を wandb の
    # notes に記録し、run 一覧で「何を変えたか」を一目でわかるようにする
    wandb_notes = ", ".join(HydraConfig.get().overrides.task) or None

    # Initialize local metrics logger
    metrics_logger = MetricsLogger(cfg)

    # TODO: Load data
    # 行を絞ったら必ず reset_index(drop=True) すること（fold 割り当ては位置ベース）
    # df = pd.read_csv(cfg.data.train_path)
    # if run_cfg["max_samples"]:
    #     df = df.head(run_cfg["max_samples"]).reset_index(drop=True)

    # TODO: Create folds (e.g., StratifiedKFold)
    # from sklearn.model_selection import StratifiedKFold
    # skf = StratifiedKFold(n_splits=run_cfg["n_folds"], shuffle=True, random_state=cfg.seed)

    fold_scores: dict[int, float] = {}

    for fold_idx in run_cfg["folds_to_run"]:
        logger.info("=" * 50)
        logger.info("Fold %d", fold_idx)
        logger.info("=" * 50)

        # Initialize wandb fold run
        wandb.init(
            project=cfg.wandb.project,
            entity=cfg.wandb.entity,
            group=group_name,
            name=f"{exp_short}-{cfg.run_name}-f{fold_idx}",
            # 決定的 id + resume="allow": 中断しても別マシンで同じ run に続きが記録される。
            # ⚠ 設定を変えて仕切り直すときは新しい id を取る（docs/wandb-spec.md 参照）
            id=f"{exp_short}-{cfg.run_name}-{cfg.run_mode}-f{fold_idx}",
            resume="allow",
            job_type="train",
            config=wandb_config,
            notes=wandb_notes,
            tags=[
                t
                for t in (
                    exp_short,
                    cfg.run_name,
                    f"fold{fold_idx}",
                    cfg.run_mode,
                    cfg.data.fold_version,
                    cfg.data.data_version,
                    cfg.data.label_version,
                )
                if t
            ],
            mode=run_cfg["wandb_mode"],
            reinit=True,
        )
        # run テーブルの列を「最後の値」ではなく best にし、val 系の x 軸を epoch に固定する
        wandb.define_metric("epoch")
        wandb.define_metric("val/*", step_metric="epoch")
        wandb.define_metric(
            f"val/{metric_name}", step_metric="epoch", summary=cfg.metric.mode
        )
        wandb.define_metric("val/loss", step_metric="epoch", summary="min")

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
        # チェックポイント名は docs/training-conventions.md の規約
        #   {exp番号}-{run_name}-f{k}[-ep{NN}][-val_{評価指標名}-{score}].ckpt
        # に従う（src/utils/submission_manifest.py がこの形をパースして提出構成を復元する）。
        # ⚠ メトリクス名とスコアの区切りの "-" は必須（区切りが無いと f1 のような
        #    数字入りメトリクス名でスコアの境界が決まらず、静かに誤った値になる）。
        # ⚠ "=" は使わない（Kaggle がファイル名の "=" を除去することがあり、
        #    Dataset 経由の重み配布が壊れる）。
        # monitor には学習ループで log しているキー（metric_key = "val/{metric}"）を渡すこと。
        # キーに "/" を含むため auto_insert_metric_name=False が必須。
        #
        # from lightning.pytorch.callbacks import ModelCheckpoint
        # checkpoint_callback = ModelCheckpoint(
        #     dirpath=str(fold_dir),
        #     filename=(
        #         f"{exp_short}-{cfg.run_name}-f{fold_idx}"
        #         f"-ep{{epoch:02d}}-val_{metric_name}-{{{metric_key}:.4f}}"
        #     ),
        #     auto_insert_metric_name=False,
        #     monitor=metric_key,
        #     mode=metric_mode,
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
        # メトリクスの向き（metric_mode）に応じて best を更新する
        best_score = float("-inf") if metric_mode == "max" else float("inf")
        for epoch in range(run_cfg["epochs"]):
            train_loss = 1.0 / (epoch + 1)
            val_score = 1.1 / (epoch + 1)  # サンプルではダミー損失をスコアとして扱う
            if metric_mode == "max":
                best_score = max(best_score, val_score)
            else:
                best_score = min(best_score, val_score)

            epoch_metrics = {
                "epoch": epoch,
                "train/loss": train_loss,
                metric_key: val_score,
            }
            wandb.log(epoch_metrics)
            metrics_logger.log_epoch(fold_idx, epoch_metrics)

            logger.info(
                "  Epoch %d: train_loss=%.4f, %s=%.4f",
                epoch,
                train_loss,
                metric_key,
                val_score,
            )

        fold_scores[fold_idx] = best_score
        wandb.finish()

    # Save OOF predictions (full mode)
    # if run_cfg["folds_to_run"] == list(range(run_cfg["n_folds"])) and oof_predictions:
    #     oof_df = pd.concat(oof_predictions, ignore_index=True)
    #     oof_df.to_csv(output_dir / "oof_predictions.csv", index=False)
    #     print(f"\nOOF predictions saved to {output_dir / 'oof_predictions.csv'}")

    # Summary run（full モード && wandb 有効 && fold >= 2 のときだけ。docs/wandb-spec.md 参照）
    # 1 fold しか回っていない CV に summary run を作ると、fold run と同じ値が
    # "CV スコア" として並び、単一 fold の値を CV と見誤る。
    if (
        cfg.run_mode == "full"
        and run_cfg["wandb_mode"] != "disabled"
        and len(fold_scores) >= 2
    ):
        wandb.init(
            project=cfg.wandb.project,
            entity=cfg.wandb.entity,
            group=group_name,
            name=f"{exp_short}-{cfg.run_name}-summary",
            id=f"{exp_short}-{cfg.run_name}-{cfg.run_mode}-summary",
            resume="allow",
            job_type="summary",
            config=wandb_config,
            notes=wandb_notes,
            mode=run_cfg["wandb_mode"],
            reinit=True,
        )
        scores = list(fold_scores.values())
        cv_mean = sum(scores) / len(scores)
        cv_std = (
            (sum((s - cv_mean) ** 2 for s in scores) / (len(scores) - 1)) ** 0.5
            if len(scores) > 1
            else 0.0
        )
        wandb.summary[f"cv/{metric_name}"] = cv_mean
        wandb.summary[f"cv/{metric_name}_std"] = cv_std
        # CV の代表値は OOF pooled スコア（docs/wandb-spec.md）。
        # OOF を算出したら wandb.summary[f"oof/{metric_name}"] に記録する
        for fi, score in fold_scores.items():
            wandb.summary[f"fold{fi}/best_val_{metric_name}"] = score
        wandb.finish()
        logger.info("CV score: %.4f ± %.4f", cv_mean, cv_std)

    metrics_logger.finish()
    logger.info("Training complete. Output dir: %s", output_dir)


if __name__ == "__main__":
    main()
