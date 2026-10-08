<!-- lifecycle: per-competition -->
# 学習実験の規約（コンペ固有）

> 学習コード・提出 notebook を書く前に、`docs/guardrails.md` と `docs/experiment-methodology.md` の「要約」と併せて読む。
> wandb は `docs/wandb-spec.md`、リモート学習は `docs/remote-training-ops.md`。
> 実装の正本は `src/exp000_sample/`（この規約どおりに動く最小パイプライン）。

## 原則

1. **確かなベースラインから 1 変数ずつ**: 最初の exp は確実に動く最小構成から。run は親から 1 キーだけ変える
   （親と変えたキーは自動計算され `run_summary.json` の `lineage` に入る）
2. **バリデーション戦略はモデリング前に確定する**。fold 設計前の学習実験は作らない
3. **判断に迷ったらユーザーに確認する**（fold 設計・ラベルの使い方・メトリクス定義・実験の分岐方針）
4. **最初のベースラインが完走したら seed だけ変えた run をもう 1 本焼く**。その差が `metric.noise.seed_spread`（profile）になり、
   以後の判定の分母になる。測り方の記録は `EXP_SUMMARY.md` の「ノイズ較正記録」
5. **train/serve skew を防ぐ**: 学習と推論（`inference.py`・提出 notebook）は同じ前処理関数を通す
6. **NN は Lightning、GBDT は各ライブラリを直接使う**。どちらも下の出力契約と共有 fold に従う

## exp / run の切り分け

- 大実験（exp）: アプローチ・アーキテクチャ・データパイプライン・バリデーション戦略が根本的に違うとき
- 小実験（run）: 同じコードで config の差分だけで表せる変更。`config/run{NNN}-{subtitle}.yaml`
- 1 exp の run が profile の `workflow.max_runs_per_exp` を超えたら exp を分ける。**迷ったら新しい exp を切る**
- 一意識別子は `{exp番号}-{run_name}-f{fold}`。wandb run 名・ckpt 名の接頭辞として全箇所で統一する
- コードを直した再実行も新しい run（同じ run_name で焼き直さない。wandb の決定的 id に追記されてしまう）
- 各 exp の README に目的・仮説・アーキテクチャ（mermaid）・Runs テーブル・全 run の実行コマンドを載せる

## バリデーション戦略

- **fold 割当は `data/folds/folds_{fold_version}.csv`（列: id, fold）として git にコミットし、全 exp で共有する**。
  初回の学習実行時に `src/utils/cv.py:load_or_create_folds` が config の `data.cv_strategy` / `n_folds` / `seed` で作る
- 既存の fold ファイルは**不変**。戦略やデータが変わったら `data.fold_version` を上げて新しいファイルを作る
  （ID が一致しない fold ファイルを読むとエラーになる）
- **異なる fold_version 間で CV を比較しない・OOF を混ぜない**（wandb の tags に fold_version が入る）
- debug の間引きは fold 割当の後に行う（fold の定義を変えない）

<!-- 埋める: fold 設計時のチェックリスト（リークの軸・stratification・test との分布差） -->

## 出力契約（NN / GBDT 共通。ensemble・record-result・提出 notebook が依存する）

```
src/{exp}/output/{run_name}[-debug]/
  fold{k}/{exp番号}-{run_name}-f{k}-ep{NN}-val_{metric}-{score}.ckpt   # NN。GBDT は fold{k}/model.* でよい
  fold{k}/val_ids.csv
  oof_predictions.csv          # 全 fold を回したときだけ。列 = id + sample_submission と同じ予測列
  submission.csv               # inference.py が書くテスト予測（アンサンブルの素材）
  submission_manifest.json     # 同上。構成は ckpt 名から復元
  kaggle_dataset/              # tools.upload_checkpoints のステージング（slim ckpt + dataset-metadata.json）
src/{exp}/logs/{run_name}[-debug]/
  run_summary.json             # スキーマは src/utils/run_summary.py
  fold{k}/metrics.csv          # Lightning CSVLogger（GBDT は同名で epoch/iteration ごとの値を書く）
  {YYYYmmdd_HHMMSS}.log
```

- `debug` は output / logs とも `-debug` サフィックスで隔離し、本番の出力を上書きしない
- 指標の計算は必ず `src/metric.py:score()` を使う（実験ごとに書き直さない）
- fold ごとのスコアは best モデルで val 全体を推論し直して計算する（学習中のログ値ではなく）

## ロギング

`docs/wandb-spec.md` に従う。本コンペでの要点:

<!-- 埋める: 必須ログ一覧（クラス別メトリクス・診断メトリクス） -->

- **「多めにログ」**: 後から「学習のどこかがおかしくなっていないか」を検証できる証拠を残す
- **情報を隠さない**: 例外は full traceback ごと残す。fold ごとのサンプル数・クラス別件数・除外件数・NaN 検出を出す

## チェックポイント

- `ModelCheckpoint` のファイル名に exp / run / fold / epoch / スコアを全て入れる:
  `{exp番号}-{run_name}-f{k}-ep{epoch:02d}-val_{評価指標名}-{score:.4f}`、`auto_insert_metric_name=False`（`val/xxx` の `/` 対策）
  - `src/utils/submission_manifest.py` がこの名前をパースして提出構成を復元するので崩さない
  - メトリクス名とスコアの間の `-` は必須。`=` は使わない（Kaggle がファイル名から除去することがある）
  - メトリクス名にハイフンを使わない（`macro_f1`）。スコアは負になり得る（`val_r2--0.1234` は -0.1234）
- best の選択は `src/utils/checkpoint.py:select_best_ckpt`（ファイル名のスコアと `metric.mode`）。任意の 1 個を掴まない
- 残る個数は `training.save_top_k` が決める（Lightning が超過分を削除する）。prune・監査の前にその値を確認する
- 掃除は結果を記録した後に、削除前にユーザー確認。best は消さない

## 提出 notebook の規約

各 exp の推論成果物:

| ファイル | 役割 |
|---|---|
| `inference.py` | 全 fold の best ckpt で推論 → `submission.csv` + manifest（`run_mode=debug` は数行だけ推論して形式確認） |
| `inference_notebook.ipynb` | 提出用 notebook（Hydra / `src` に依存しない自己完結型。`/kaggle:create-inference-notebook` で生成） |

- **置き場所**: 単一 exp は `src/{exp}/inference_notebook.ipynb`。アンサンブルは独立した exp `src/exp{NNN}_ensemble/` に置く
- **説明**: 先頭に概要セル（どの exp・どの ckpt 構成・前提・環境要件）、各コードセルの直前に日本語 markdown
- **ログ**: 先頭で ckpt 一覧（fold / epoch / score）・GPU・主要パッケージ版・入力パス・code_sha、推論中は N レコードごとに進捗 1 行、
  末尾で失敗件数と ID・`sample_submission.csv` との列名・行数の突合・manifest・貼り付け用 description
- **実行機を重くしない**: `print(..., flush=True)` + `/kaggle/working/submission_log.txt` へ逐次追記。1 レコード 1 行のログ・配列の出力をしない。
  予測は確定したら即座に行として吐き出し、DataFrame は最後に組む。ループ末尾で `del` + `gc.collect()`
- **エラー処理**: レコード単位の try/except。失敗は中立値で埋めて行を欠落させない（欠けると採点エラー）。失敗件数を最後に表示
- コミット前に出力を除去する（`uv run --with nbstripout nbstripout <path>`）

## 実行環境（Kaggle Notebook）

- コンペデータ: `/kaggle/input/competitions/{slug}`（`{slug}` 直下ではない。実機で確認済み）
- Dataset: `/kaggle/input/datasets/{user}/{dataset-slug}`
- 出力: `/kaggle/working`
- マウントパスは Kaggle の UI 更新で変わり得る。**Add Data 後にサイドバーの実パスで必ず確認する**
  （誤ったパスで欠損値埋めのまま提出が静かに壊れた事例がある）
- ローカルの `inference.py` は `data.input_dir`（環境変数 `INPUT_DIR` で上書き可）を経由する

<!-- 埋める: 実行環境の実測メモ（GPU 種別・追加パッケージ・internet off の制約・実行時間上限） -->

## チェックポイントの配布（Internet off での重み配布）

`uv run python -m tools.upload_checkpoints {exp} {run} [--user U] [-m msg]` が各 fold の best ckpt を slim 化（state_dict と
hyper_parameters だけ）して Dataset にする。2 回目以降は自動でバージョン更新。

<!-- 埋める: Dataset slug・notebook 側の探索パス -->
