<!-- lifecycle: per-competition -->
# 学習実験の規約（コンペ固有）

> 学習コードを書く・修正する AI エージェントは、`docs/guardrails.md` と
> `docs/experiment-methodology.md` と併せて**実装前に必ず読む**。
> wandb の詳細は `docs/wandb-spec.md`、リモート学習は `docs/remote-training-ops.md`。

## 原則

1. **学習コードは PyTorch Lightning で書く**（全 `src/exp*/train.py`）。素の training loop を書かない
2. **確かなベースラインから 1 変数ずつ**: 最初の実験は「確実に動く最小構成」から始め、
   盛り込み最強モデルから始めない。各 exp・各 run は親との差分を 1 つに絞る
   （差分の宣言は config の `lineage.varied`。詳細は `docs/experiment-methodology.md`「効果の帰属」）
3. **バリデーション戦略はモデリング開始前に確定する**。適当な fold で走らせたスコアは
   意味を持たないため、fold 設計前の学習実験は作らない
4. **判断に迷ったら勝手に決めずユーザーに確認する**。特に fold 設計・ラベルの使い方・
   メトリクス定義・実験の分岐方針
5. **最初のベースラインが完走したら、seed のみ変えた run をもう 1 本焼く**。
   その差が `metric.noise.seed_spread` になり、以後すべての判定の分母になる
6. **train/serve skew を防ぐ**: 学習データを作る変換関数と、提出用推論の前処理関数は**同一の実装を共有する**
   （`src/utils/` に置いて両方から import する）。前処理済みデータで学習した実験は、推論側も同じ関数で
   生データから同じテンソルを作ること。別実装にすると、学習では正常に loss が下がるのに提出でだけ崩れる

## exp / run の切り分け

`docs/ai-agent-guidelines.md` の `max_runs_per_exp` と、`/kaggle:new-experiment` の
昇格トリガー表に従う。**迷ったら新しい exp を切る**（大きく分ける方向に倒す）。

- 一意識別子は `{exp番号}-{run_name}-f{fold}`。wandb run 名・チェックポイント名の接頭辞として全箇所で統一する
- コードを直した再実行も「変更」なので新しい run を切る（同じ run 名で上書き再実行しない）
- 各実験の README にアーキテクチャ図（mermaid）と**全 run の実行コマンド**を載せる

## バリデーション戦略

- **fold 割当は `data/folds/folds_v{N}.csv` として git にコミットする**。生成スクリプトとシードも同時にコミットする
- 既存の `folds_v{N}.csv` は**不変**（上書き・再生成禁止）。戦略を変えるなら v{N+1} を追加する
- 実験 config は `data.fold_version` で参照し、wandb の config / tags に記録する。
  **異なる fold_version 間で CV スコアを比較しない**

<!-- 埋める: fold 設計時のチェックリスト（リークの軸・stratification・test との分布差） -->

## ロギング

`docs/wandb-spec.md` に従う。本コンペでの要点:

<!-- 埋める: 必須ログ一覧（クラス別メトリクス・診断メトリクス） -->

- **「多めにログ」原則**: 後から「学習のどこかがおかしくなっていないか」を検証できる証拠を残す
- **情報を隠さない**: 例外は full traceback ごとログに残す。警告を握りつぶさない。
  fold ごとのサンプル数・クラス別件数・除外/スキップ件数・NaN 検出を逐一出力する

## チェックポイント

- Lightning の `ModelCheckpoint` を使い、ファイル名に **exp / run / fold / epoch / スコアを全て入れる**:
  `{exp番号}-{run_name}-f{k}-ep{epoch:02d}-val_{評価指標名}{score:.4f}.ckpt`。
  `auto_insert_metric_name=False` を必ず指定する（`val/xxx` の `/` がディレクトリを作るため）
  - この命名は `src/utils/submission_manifest.py` がパースして提出構成を復元するので、**規則を崩さない**
- **上書き禁止**: epoch とスコア入りの命名なので同名衝突は起きない。同期に削除系フラグを使わない
- **prune は best を絶対に削除しない**（resume 用の最新 N 個の外にあっても残す）。
  best を消すと「best という名前の非 best」で提出・比較してしまう
- 掃除は結果を記録した後に行い、**削除前にユーザー確認**。best と last は恒久保持

## 提出 notebook の規約

各実験は次の推論成果物を持つ:

| ファイル | 役割 |
|---|---|
| `inference.py` | 全レコード推論 → `submission.csv`（ローカル / VM 用、Hydra） |
| `debug_inference.py` | 学習済み ckpt を読んで 1 レコードだけ推論する動作確認。学習が終わるたびに実行する |
| `inference_notebook.ipynb` | 提出用 notebook（自己完結・日本語 markdown 説明つき） |

**置き場所**: 単一実験なら `src/exp{N}_{subtitle}/inference_notebook.ipynb`。
**複数実験のアンサンブルは、構成員のうち実験番号が大きい方のディレクトリに置く**
（番号がより大きい実験を新たに混ぜたら notebook をそちらへ移す）。

**説明**: 各コードセルの直前に**日本語の markdown で「何をするか」**を書く。
先頭に概要セル（どの実験・どの ckpt 構成・前提条件・環境要件）。

**ログ**（何を残すか）:

| タイミング | 残すもの |
|---|---|
| 先頭 | ckpt 一覧を fold / epoch / score にパースした表、GPU 名、デコーダの状態、主要パッケージ版、`INPUT_DIR`、code_sha |
| 推論中 | N レコードごとに 1 行の進捗（既定 50）。失敗レコードは理由 1 行 |
| 末尾 | 失敗件数と ID 一覧、`sample_submission.csv` との列名・行数の突合結果、manifest、貼り付け用 description |

**実行機の性能を落とさないための決め事**:

- ログは `print(..., flush=True)` + ファイル append で逐次書き出す。メモリに溜めない
- **1 レコード 1 行のログを出さない**（出力が膨らんで notebook が重くなる）。N 間隔にする
- 配列・画像をログに残さない。形状と min/max/mean のみ
- 予測は確定したら即座に行として吐き出す。全レコードを辞書で抱えず、DataFrame は最後に組む
- ループ末尾で `del` + `gc.collect()`
- ログの実体は `/kaggle/working/submission_log.txt`（Kaggle の出力に残るので、
  後から Version を開いて「どの ckpt でどこで落ちたか」を読める）

**エラー処理**: レコード単位の try/except を必須とし、失敗レコードは中立値で埋めて
submission から欠落させない（行が欠けると採点エラー）。失敗件数を最後に明示的に表示する。

<!-- 埋める: 実行環境の実測メモ（マウントパス・GPU 種別・追加パッケージ・internet off の制約） -->

## チェックポイントの配布（Internet off での重み配布）

<!-- 埋める: Dataset slug・アップロード手順・notebook 側の探索パス -->
