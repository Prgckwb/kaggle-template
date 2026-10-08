---
name: kaggle:create-inference-notebook
description: 提出用の Kaggle notebook を作る・更新するときに使う（「提出 notebook を作って」「inference notebook を更新」など）。実験コードを読み、Hydra や src に依存しない自己完結型の inference_notebook.ipynb を生成する。
argument-hint: [実験名（例: exp001_baseline）]
allowed-tools: Bash, Read, Write, Edit, Glob, Grep, NotebookEdit
---

# 提出用 inference notebook を生成する

**規約の正本は `docs/training-conventions.md`**。生成前に次の節を読み、それに従う（このスキルには規約を書き写さない）。

- 「提出 notebook の規約」: 置き場所・説明セル・ログ・実行機の性能を落とさない決め事・エラー処理
- 「チェックポイント」: ckpt の命名規則
- 「実行環境」: Kaggle のマウントパスと `INPUT_DIR`

設計原則（このスキル固有のもの）:

- **Hydra と `src.*` に依存しない**: 必要なコードはすべて notebook 内にインライン化する
  - `src/metric.py` は不要（推論で指標は計算しない）
  - `src/utils/submission_manifest.py` の `parse_ckpt_name` / `build_manifest` / `write_manifest` / `describe_manifest` はインライン化して使う
- **モデルは `nn.Module` に簡略化**: LightningModule から学習用メソッドを除き、`forward()` だけにする。ckpt の `state_dict` を読む
  - Lightning の接頭辞（`model.` など）は、キー名を確認して剥がす
- **置き場所**
  - 単一実験: `src/{exp}/inference_notebook.ipynb`
  - アンサンブル: そのアンサンブル実験 `src/exp{NNN}_ensemble/inference_notebook.ipynb`
- **パスは先頭セルの変数にまとめる**: `INPUT_DIR` と `MODEL_DIR` 以下のサブパスはローカルと同じにする（`MODEL_DIR/fold{k}/*.ckpt`）

## フェーズ 1: 対象と前提の確認

1. 対象の実験を決める。`$ARGUMENTS` に無ければ `src/exp*/` を Glob して候補を出し、ユーザーに選んでもらう
2. 次のファイルを Read して把握する
   - `README.md`: 目的と工夫点
   - `model.py` / `data.py`: 推論に要る前処理。学習側と同じ関数を使う（train/serve skew を防ぐ）
   - `inference.py`: 推論フローと後処理
   - `config/config.yaml`
3. `src/{exp}/logs/{run}/run_summary.json` で、どの fold が学習済みか（`fold_scores`）と `metric.mode` を確認する
4. 重みの Dataset id を確認する。順に実験 README の記録 → `/kaggle:upload-checkpoints` の出力を見て、無ければユーザーに聞く
   - 未アップロードなら、先に `/kaggle:upload-checkpoints` を案内する

## フェーズ 2: 生成

コードセルの直前には必ず日本語の markdown セルを置き、何をするか（実験固有の工夫は、なぜそうするか）を書く。

| # | 内容 |
|---|---|
| 1 | 概要（実験・ckpt 構成・前提・環境要件・提出手順） |
| 2 | パス設定。Kaggle かローカルかを `Path("/kaggle/input").exists()` で自動判定する。Kaggle 側のパスは `training-conventions.md`「実行環境」の形式で書き、「Add Data 後にサイドバーの実パスを確認」と注記する |
| 3 | 環境記録: GPU 名・主要パッケージ版・`INPUT_DIR`・code_sha。ckpt を fold / epoch / score にパースした表。ログファイルを開く |
| 4 | モデル構築（internet off なので `pretrained=False`）と、fold ごとの best ckpt の読み込み |
| 5 | 推論ループ（レコード単位の try/except、N 件ごとの進捗、逐次 append） |
| 6 | 検証と書き出し（`sample_submission.csv` と列名・行数を突合、`submission.csv`、`submission_manifest.json`、`describe_manifest` の 1 行、失敗件数） |

**best ckpt の選び方**（`src/utils/checkpoint.select_best_ckpt` と同じ考え方をインラインで書く）:

```python
refs = [(p, parse_ckpt_name(p.name)) for p in (MODEL_DIR / f"fold{k}").glob("*.ckpt")]
scored = [(r.score, p) for p, r in refs if r and r.score is not None]
if not scored:
    raise RuntimeError(f"fold{k}: スコア入りの ckpt 名がありません")  # 黙って任意の 1 個を読まない
best = (max if METRIC_MODE == "max" else min)(scored, key=lambda x: x[0])[1]
```

- `METRIC_MODE` には profile の `metric.mode` を書き込む
- スコアは負になることがあるので、`abs()` で比較しない
- GPU と CPU は `torch.device("cuda" if torch.cuda.is_available() else "cpu")` で切り替える。Kaggle 上の `num_workers` は 2 程度にする

生成後は `uv run --with nbstripout nbstripout <path>` で出力を消してからコミット対象にする。

## フェーズ 3: 完了報告

- notebook のパスと、Kaggle 上での使い方を伝える
  - Add Data でコンペデータと重みの Dataset を追加し、先頭セルのパスを確認する
- `describe_manifest` が出す 1 行を報告に載せる（提出時の description にそのまま貼れる形）
- `docs/competition-profile.yaml` の `workflow.submission_by` が `user` の間は、**notebook の commit と出力確認までで止めて**引き渡す（提出はしない）
