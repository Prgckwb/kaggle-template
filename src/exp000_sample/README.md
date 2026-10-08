# exp000_sample

## 目的

テンプレートのサンプル実験。`docs/training-conventions.md` の規約（共有 fold・ckpt 命名・出力契約・
`run_summary.json`・manifest）どおりに動く最小パイプラインを示す。合成データ（二値分類）を MLP で学習する。

## 仮説

（実験開始時に記載する）

> 例: XXX により、親 run の OOF スコアが meaningful_delta 以上改善すると考える。根拠: …

## 手法

- データ: `uv run python -m src.exp000_sample.make_synthetic` が `sandbox/synthetic/` に作る合成データ
- fold: `sandbox/synthetic/folds_v1.csv`（5-Fold Stratified。実コンペでは `data/folds/`）
- モデル: `TabularMLP`（Lightning。`model.py`）
- 指標: `src/metric.py:score()`

```mermaid
graph LR
    X["特徴量 f0..f7"] --> L1["Linear(8→hidden)"] --> R["ReLU + Dropout"] --> L2["Linear(hidden→1)"] --> S["sigmoid"]
```

## 結果

| Metric | Value |
|--------|-------|
| Split  | 5-Fold SKF (v1) |
| CV (oof_score) | - |
| LB     | - |

## Runs

| Run | Parent | Changed | Key Change | CV | LB | Command |
|-----|--------|---------|-----------|----|----|---------|
| run000-base | - | - | ベースライン | - | - | `uv run python -m src.exp000_sample.train run_mode=full` |
| run001-wider | config | model.hidden_dim | 隠れ層 64→256 | - | - | `uv run python -m src.exp000_sample.train --config-name=run001-wider` |

## 考察

（実験完了時に記載する）
