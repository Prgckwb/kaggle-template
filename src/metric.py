# lifecycle: per-competition
"""競技指標（全実験・アンサンブル・OOF 再計算で共有する唯一の実装）。

lifecycle: per-competition。`/kaggle:init` がコンペの評価指標に書き換える。
名前と向き（max/min）は docs/competition-profile.yaml の metric.name / metric.mode。
正しい実装・間違いやすい実装の記録は docs/guardrails.md の「評価関数」。
"""

from __future__ import annotations

import numpy as np


def score(y_true: np.ndarray, y_pred: np.ndarray) -> float:
    """テンプレートの既定は二値分類の ROC AUC（exp000_sample の合成データ用）。"""
    from sklearn.metrics import roc_auc_score

    return float(roc_auc_score(y_true, y_pred))
