"""exp000_sample 用の合成データを sandbox/synthetic/ に作る（実コンペのデータは input/）。

Run: uv run python -m src.exp000_sample.make_synthetic
"""

from __future__ import annotations

from pathlib import Path

import numpy as np
import pandas as pd

OUT_DIR = Path(__file__).resolve().parents[2] / "sandbox" / "synthetic"


def main(
    n_train: int = 2000, n_test: int = 500, n_features: int = 8, seed: int = 0
) -> None:
    rng = np.random.default_rng(seed)
    weights = rng.normal(size=n_features)

    def make(n: int, offset: int) -> pd.DataFrame:
        x = rng.normal(size=(n, n_features))
        logits = x @ weights + 0.5 * rng.normal(size=n)
        df = pd.DataFrame(x, columns=[f"f{i}" for i in range(n_features)])
        df.insert(0, "id", np.arange(offset, offset + n))
        df["target"] = (logits > 0).astype(int)
        return df

    OUT_DIR.mkdir(parents=True, exist_ok=True)
    make(n_train, 0).to_csv(OUT_DIR / "train.csv", index=False)
    test = make(n_test, n_train).drop(columns="target")
    test.to_csv(OUT_DIR / "test.csv", index=False)
    pd.DataFrame({"id": test["id"], "target": 0.5}).to_csv(
        OUT_DIR / "sample_submission.csv", index=False
    )
    print(f"合成データを作成しました: {OUT_DIR}")


if __name__ == "__main__":
    main()
