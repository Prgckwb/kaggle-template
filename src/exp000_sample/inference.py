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
from src.utils.submission_manifest import parse_ckpt_name

register_config_schema()


def select_best_ckpt(fold_dir: Path, mode: str) -> Path:
    """fold ディレクトリから best の ckpt を 1 つ選ぶ。

    ckpt 名は `{exp番号}-{run_name}-f{k}[-ep{NN}][-val_{評価指標名}-{score}].ckpt`
    （`docs/training-conventions.md`）。スコアを含む名前だけを候補にし、
    `cfg.metric.mode`（max/min）に従って選ぶ。スコアは負にもなり得る（R2・相関係数）。

    ⚠ `next(fold_dir.glob("*.ckpt"))` で任意の 1 個を読んではいけない。
    `save_top_k` が 2 以上なら best 以外を掴み、「best という名前の非 best」で提出することになる。

    Raises:
        FileNotFoundError: ckpt が 1 つも無い。
        RuntimeError: 規約どおりに解析できスコアを持つ ckpt が 1 つも無い
            （黙って任意の 1 個を選ばず、命名を直すよう促す）。
    """
    ckpts = sorted(fold_dir.glob("*.ckpt"))
    if not ckpts:
        raise FileNotFoundError(f"ckpt が見つかりません: {fold_dir}")

    scored = [
        (ref.score, path)
        for path in ckpts
        if (ref := parse_ckpt_name(path.name)) and ref.score is not None
    ]
    if not scored:
        names = ", ".join(p.name for p in ckpts)
        raise RuntimeError(
            f"スコア入りの ckpt 名が {fold_dir} にありません（見つかったのは {names}）。"
            "docs/training-conventions.md の命名規約に合わせてから再実行してください。"
        )

    pick = max if mode == "max" else min
    return pick(scored, key=lambda item: item[0])[1]


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
    #     ckpt_path = select_best_ckpt(fold_dir, cfg.metric.mode)
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
