"""Inference script.

Loads trained checkpoints and generates submission.csv.
Run: uv run python -m src.exp000_sample.inference
"""

from __future__ import annotations

from pathlib import Path

import hydra
import pandas as pd
from omegaconf import DictConfig

from src.exp000_sample.config_schema import register_config_schema
from src.utils.seeding import seed_everything
from src.utils.submission import validate_submission

register_config_schema()


@hydra.main(version_base=None, config_path="config", config_name="config")
def main(cfg: DictConfig) -> None:
    seed_everything(cfg.seed)
    output_dir = Path(cfg.output_dir)
    sample_sub_path = Path(cfg.data.sample_submission_path)

    sample_sub = pd.read_csv(sample_sub_path)

    # TODO: Load model checkpoints per fold and average predictions
    # Example for fold-ensemble:
    #
    # predictions = []
    # for fold_idx in range(cfg.data.n_folds):
    #     fold_dir = output_dir / f"fold{fold_idx}"
    #     ckpt_path = next(fold_dir.glob("*.ckpt"))
    #     model = BaselineModel.load_from_checkpoint(ckpt_path)
    #     model.eval()
    #     preds = model.predict(test_dataloader)
    #     predictions.append(preds)
    #
    # final_preds = np.mean(predictions, axis=0)

    submission = sample_sub.copy()
    # TODO: Fill in predictions
    # submission["target"] = final_preds

    submission_path = output_dir / "submission.csv"
    submission.to_csv(submission_path, index=False)

    errors = validate_submission(submission_path, sample_sub_path)
    if errors:
        print("Submission validation errors:")
        for e in errors:
            print(f"  - {e}")
    else:
        print(f"Submission saved to {submission_path} (validated OK)")


if __name__ == "__main__":
    main()
