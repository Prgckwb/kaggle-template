<!-- lifecycle: per-competition -->
# Submission Log

> 提出履歴の Single Source of Truth。**すべての提出を1行ずつ記録する**（実験単位の best しか残らない EXP_SUMMARY.md とは役割が異なる）。
> CV-LB 相関分析（`kaggle-analyst`）と終盤の final submission 選定はこのテーブルを元データにする。
> LB 取得には `uv run python tools/check_submission.py` が使える（読み取り専用）。
> `/kaggle:record-result` が LB スコアを記録する際にこのファイルにも追記する。
> **記録は推測しない。** notebook が出力する `submission_manifest.json` を
> `/kaggle:record-result` が読んで追記する（`src/utils/submission_manifest.py`）。

## Submissions

| Date | Exp / Run | Submission File | CV | Public LB | 提出理由・メモ |
|------|-----------|-----------------|----|-----------|---------------|
| - | - | - | - | - | （まだ提出なし） |

- `Date`: 提出日（YYYY-MM-DD）
- `Exp / Run`: **`describe_manifest()` の出力をそのまま貼る**（構成を手打ち・事後推測しない）。
  例: `V20 exp006-run004-effv2s(2f) + exp010-run000-base(1f) | mean w=0.5/0.5 | tta=off`
- `CV`: 提出物に対応する OOF/CV スコア（アンサンブルならブレンド OOF スコア）
- `Public LB`: 提出後に判明した public スコア
- 提出理由・メモ: なぜこの提出をしたか（仮説検証・LB プローブ・final 候補等）

## CV-LB の写像

Δ(LB − CV) の実測を蓄積する。写像が線形な区間と、破れる条件を書く。

| 提出 | CV | LB | Δ(LB−CV) | 備考 |
|---|---|---|---|---|

- 「CV が上がったのに LB が下がった」ケースは必ず交絡を分解して記録する
  （`docs/experiment-methodology.md` の「効果の帰属」）
- **較正点は統制された 1 変数差分からのみ採る**。交絡を含む比較から傾きを引かない

## Final Selection（コンペ終盤に記入）

- 選定方針: `docs/competition-profile.yaml` の `selection.policy` に従う
- 候補1: （Exp/Run・CV・LB・選定理由）
- 候補2: （同上）
