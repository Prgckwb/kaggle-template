<!-- lifecycle: per-competition -->
# 実験台帳（Experiment Log）

> **役割**: exp ごとの「試したいこと」「アーキテクチャの要点」「スコアの変遷」を
> 1 箇所で時系列に追うための台帳。
>
> - `EXP_SUMMARY.md` = 一覧表 + Experiment Tree（現在地のスナップショット）
> - 各 `src/exp*/README.md` = 実験単体の詳細（仮説・アーキ図・runs・考察）
> - **本ファイル = 時系列の物語 + 探索バックログ**。`/kaggle:record-result` 実行時に更新する

## スコア変遷（時系列）

CV の代表値は `oof/{評価指標名}`（OOF pooled）。単一 fold の場合は `val/{評価指標名}` に `(f0)` を付す。
⚠ fold 定義・前処理・ラベルのバージョンを跨いだ比較は不可（`docs/guardrails.md`）。

| 日付 | exp / run | 親 run | 変えた変数の数 | CV | LB | 一言 |
|---|---|---|---:|---|---|---|

<!-- 「変えた変数の数」は config の lineage.varied の長さ。
     2 以上なら Δ を 1 変数の名前で呼ばない（docs/experiment-methodology.md「効果の帰属」）。 -->

## 探索バックログ（試したいことと根拠）

優先度は `/kaggle:review-strategy` と相談しつつ随時入れ替える。着手したら exp / run 番号を記入。

| # | アイデア | 種別（exp / run） | 根拠 | 状態 |
|---|---|---|---|---|

## ノイズの較正記録

`docs/competition-profile.yaml` の `metric.noise` に書いた値の出典を残す。

| 測った量 | 値 | 測り方 |
|---|---|---|
| `seed_spread` | | 同一設定・seed のみ変更した run 2 本の差 |
| `fold0_resolution` | | |
| `proxy_resolution` | | |

⚠ **`seed_spread` が空のままで「棄却」「dead-end」「確定」を書いてはいけない**
（`docs/experiment-methodology.md`「判定の資格」）。
