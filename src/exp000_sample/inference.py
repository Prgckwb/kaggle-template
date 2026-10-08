"""推論スクリプト: 各 fold の best ckpt でテストを推論し、平均して submission.csv を書く。

Run: uv run python -m src.exp000_sample.inference [run_mode=debug] [--config-name=run001-xxx]
- 対象 fold は学習時の run_summary.json に記録された fold（fold0 の run なら fold0 だけ）
- run_mode=debug は *-debug の出力を読み、先頭数行だけ推論して形式を確認する
提出 notebook はこのファイルを自己完結に書き直したもの（/kaggle:create-inference-notebook）。
"""

from __future__ import annotations

from pathlib import Path

import hydra
import lightning as L
import pandas as pd
import torch
from omegaconf import DictConfig

from src.exp000_sample.data import feature_columns, make_loader, preprocess
from src.exp000_sample.model import TabularMLP
from src.utils.checkpoint import select_best_ckpt
from src.utils.profile import register_profile_resolver
from src.utils.run_summary import read_run_summary
from src.utils.seeding import seed_everything
from src.utils.submission import validate_submission
from src.utils.submission_manifest import (
    build_manifest,
    describe_manifest,
    write_manifest,
)

register_profile_resolver()


@hydra.main(version_base=None, config_path="config", config_name="config")
def main(cfg: DictConfig) -> None:
    seed_everything(cfg.seed)
    debug = cfg.run_mode == "debug"
    suffix = "-debug" if debug else ""
    output_dir = Path(f"{cfg.output_dir}{suffix}")
    summary = read_run_summary(Path(f"{cfg.logs_dir}{suffix}") / "run_summary.json")
    folds = [int(k) for k in summary["fold_scores"]]

    test_df = preprocess(pd.read_csv(cfg.data.test_path), cfg)
    sample_sub = pd.read_csv(cfg.data.sample_submission_path)
    if debug:
        test_df = test_df.head(cfg.debug.samples)
        sample_sub = sample_sub.head(cfg.debug.samples)
    loader = make_loader(
        test_df, cfg, features=feature_columns(test_df, cfg), train=False
    )

    trainer = L.Trainer(accelerator="auto", logger=False, enable_progress_bar=False)
    ckpts, fold_preds = [], []
    for fold_idx in folds:
        ckpt = select_best_ckpt(output_dir / f"fold{fold_idx}", cfg.metric.mode)
        model = TabularMLP.load_from_checkpoint(ckpt)
        fold_preds.append(torch.cat(trainer.predict(model, loader)).float().numpy())
        ckpts.append(ckpt)
        print(f"fold{fold_idx}: {ckpt.name}")

    submission = sample_sub.copy()
    submission[cfg.data.target_col] = sum(fold_preds) / len(fold_preds)
    submission_path = output_dir / "submission.csv"
    submission.to_csv(submission_path, index=False)

    manifest = build_manifest(
        ckpts,
        notebook=f"{cfg.exp_name}/inference.py",
        notebook_version=0,
        code_sha=summary["git_sha"],
        exp_names={cfg.exp_name.split("_")[0]: cfg.exp_name},
    )
    write_manifest(manifest, output_dir / "submission_manifest.json")

    if debug:
        print(
            f"debug: {len(submission)} 行だけ推論しました（形式確認のみ）: {submission_path}"
        )
        return
    errors = validate_submission(submission_path, cfg.data.sample_submission_path)
    if errors:
        raise SystemExit(
            "Submission validation errors:\n" + "\n".join(f"  - {e}" for e in errors)
        )
    print(f"Submission saved: {submission_path} (validated OK)")
    print(f"description: {describe_manifest(manifest)}")


if __name__ == "__main__":
    main()
