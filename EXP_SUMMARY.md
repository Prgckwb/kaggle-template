<!-- lifecycle: per-competition -->
<!--
書式（このファイルの書式の正本。書き換えるスキル・人はここに従う）
- Experiments Table: 1 exp 1 行。スコアはその exp の best run（selection.policy と metric.mode で判定）。
  CV は run_summary.json の oof_score。fold0 しか無い run は val 値に "(f0)" を付け、CV と呼ばない
  Parent / Vars は best run の run_summary.json の lineage.parent / len(lineage.changed)。
  Vars が 2 以上なら Key Change を単一の変数名で書かない
- Experiment Tree: ノード "exp名<br/>Split | CV: x.xxx | LB: x.xxx"、エッジラベル = Key Change（2 変数以上なら "(2 vars)" を併記）。
  全ノードに class を付ける: best（全実験中の best。太枠）/ good（完了）/ base（ベースライン）/ wip（進行中）/ dead（行き止まり）
- exp000_sample は exp001 ができたら表とツリーから外す
- 探索マップは /kaggle:review-strategy、探索バックログとノイズ較正記録は /kaggle:record-result も更新する
-->
# Experiments

## Validation Strategy

> 分割方法・fold_version・リークの軸・train/test の分布差（`/kaggle:init` で決める）

## Experiments Table

| Exp | Name | Split | Parent | Vars | Key Change | CV | LB |
|-----|------|-------|--------|-----:|------------|----|----|
| exp000 | sample | 5-Fold SKF | - | 0 | テンプレート（合成データ） | - | - |

## Experiment Tree

```mermaid
graph TD
    A["exp000_sample"]

    classDef best fill:#10b981,stroke:#059669,color:#fff,stroke-width:3px
    classDef good fill:#3b82f6,stroke:#2563eb,color:#fff
    classDef base fill:#64748b,stroke:#475569,color:#fff
    classDef wip fill:#f59e0b,stroke:#d97706,color:#fff,stroke-dasharray:5 5
    classDef dead fill:#ef4444,stroke:#dc2626,color:#fff

    class A base
```

## 探索マップ

> `/kaggle:review-strategy` が更新する（最終更新日・アプローチ・チェックリストとカバレッジ・未探索の候補）

## 探索バックログ

| # | アイデア | 種別（exp / run） | 根拠 | 状態 |
|---|---|---|---|---|

## ノイズ較正記録

profile の `metric.noise` に書いた値の出典。**`seed_spread` が空のまま「棄却」「dead-end」「確定」を書かない**。

| 測った量 | 値 | 測り方（比較した run） |
|---|---|---|
| `seed_spread` | | 同一設定・seed のみ変えた run 2 本の差 |
| `fold0_resolution` | | |
| `proxy_resolution` | | |
