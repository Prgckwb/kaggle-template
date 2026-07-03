# Submission Log

> 提出履歴の Single Source of Truth。**すべての提出を1行ずつ記録する**（実験単位の best しか残らない EXP_SUMMARY.md とは役割が異なる）。
> CV-LB 相関分析（`kaggle-analyst`）と終盤の final submission 選定はこのテーブルを元データにする。
> LB 取得には `uv run python tools/check_submission.py` が使える（読み取り専用）。
> `/kaggle:record-result` が LB スコアを記録する際にこのファイルにも追記する。

## Submissions

| Date | Exp / Run | Submission File | CV | Public LB | 提出理由・メモ |
|------|-----------|-----------------|----|-----------|---------------|
| - | - | - | - | - | （まだ提出なし） |

- `Date`: 提出日（YYYY-MM-DD）
- `Exp / Run`: 例 `exp001_baseline / run002-lr5e4`。アンサンブルの場合は構成 run を列挙
- `CV`: 提出物に対応する OOF/CV スコア（アンサンブルならブレンド OOF スコア）
- `Public LB`: 提出後に判明した public スコア
- 提出理由・メモ: なぜこの提出をしたか（仮説検証・LB プローブ・final 候補等）

## Final Selection（コンペ終盤に記入）

- 選定方針: `docs/competition-profile.yaml` の `selection.policy` に従う
- 候補1: （Exp/Run・CV・LB・選定理由）
- 候補2: （同上）
