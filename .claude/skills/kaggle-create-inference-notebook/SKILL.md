---
name: kaggle:create-inference-notebook
description: 実験コードを読み取り、Kaggle 用の自己完結型 inference notebook を生成する。
argument-hint: [実験名（例: exp001_baseline）]
disable-model-invocation: true
allowed-tools: Bash, Read, Write, Edit, Glob, Grep, NotebookEdit
---

# Kaggle 用 Inference Notebook を生成する

実験の model.py / data.py / inference.py / config.yaml を読み取り、
Kaggle Notebooks 環境で動作する自己完結型の inference notebook を生成する。

## 重要な設計原則

- **Hydra / `src.*` への依存なし**: すべてのコードを notebook 内にインライン化する
- **パスは先頭セルで設定**: Kaggle 環境のパスはコンペ・データセットごとに異なるため、先頭セルで変数として定義し、ユーザーが簡単に変更できるようにする
- **サブパスはローカルと同一**: `INPUT_DIR` 以下（`sample_submission.csv` 等）、`MODEL_DIR` 以下（`fold0/{ckpt}` 等）のサブパスはローカルの構造と同一
- **nn.Module に簡略化**: LightningModule の training 関連メソッドを除外し、`forward()` のみの `nn.Module` として定義。Lightning checkpoint から `state_dict` を読み込む
- **置き場所**: 単一実験の推論は `src/exp{N}_{subtitle}/inference_notebook.ipynb`。
  **複数実験のアンサンブルは、構成員のうち実験番号が大きい方のディレクトリに置く**
  （番号がより大きい実験を新たに混ぜたら notebook をそちらへ移し、以後そこを更新する）。
  Kaggle 上のタイトルに最新の構成員が出るので、提出一覧で実験を取り違えない
- **説明を必ず入れる**: 各コードセルの直前に日本語の markdown で「何をするか」を書く。
  先頭は概要セル（どの実験・どの ckpt 構成・前提条件・環境要件）
- **manifest を必ず書く**: `src/utils/submission_manifest.py` の
  `build_manifest` / `write_manifest` / `describe_manifest` を使い、
  `submission.csv` と同じディレクトリに `submission_manifest.json` を出す。
  構成は ckpt 名から復元されるので追加入力は不要

## フェーズ 1: 対象実験の特定とコード確認

1. **対象実験を特定する**
   - $ARGUMENTS があればその実験名を使用
   - なければ `src/exp*/` を Glob で検索し、ユーザーに選択肢を提示

2. **実験コードを読み取る**（すべて Read で内容を把握すること）
   - `src/{exp_name}/README.md` — 実験の目的・仮説・工夫点の把握
   - `src/{exp_name}/model.py` — モデルアーキテクチャの把握
   - `src/{exp_name}/data.py` — 推論に必要なデータ処理クラス/関数の特定
   - `src/{exp_name}/inference.py` — 推論フロー、後処理の確認
   - `src/{exp_name}/config/config.yaml` — モデル・データのハイパーパラメータの取得

3. **実験の工夫点を整理する**
   - README.md やコードから、この実験のアプローチ・特徴・工夫を把握する
   - 例: モデル構造の特徴、損失関数の工夫、データ処理の特徴、後処理の手法 等
   - これらは Notebook のマークダウンセルに日本語で記述する（フェーズ 3 参照）

4. **チェックポイント情報の確認**
   - `src/{exp_name}/output/{run_name}/` 配下のチェックポイントファイル名を確認
   - Kaggle 上のファイル名では `=` が除去される場合があることに注意

## フェーズ 2: パス設定の確認

ユーザーに以下を確認する:

1. **Kaggle コンペデータのパス**
   - 通常は `/kaggle/input/competitions/{competition-slug}`（slug は `docs/competition-profile.yaml` の `competition.slug`。
     `{slug}` 直下ではなく `competitions/` が挟まる。実機で確認済み）
   - **注意**: マウントパスの形式は Kaggle の UI 更新で変わることがある。Notebook で **Add Data** した後、サイドバーに表示される実際のパスで必ず確認・修正するようユーザーに案内する

2. **Kaggle モデル Dataset のパス**
   - 通常は `/kaggle/input/datasets/{user}/{dataset-slug}`（例: `/kaggle/input/datasets/{user}/{comp_slug}-{exp_name_kebab}`）
   - `dataset-metadata.json` が存在すればそこから slug を取得

**Notebook 先頭セルのパス設定パターン**:

```python
from pathlib import Path

# ==== Path Configuration ====
# Kaggle 環境のパス（Add Data 後にサイドバーの実パスを確認して修正してください）
KAGGLE_COMP_DIR = "/kaggle/input/competitions/{competition-slug}"
KAGGLE_MODEL_DIR = "/kaggle/input/datasets/{user}/{dataset-slug}"

# 自動検出（変更不要）
if Path("/kaggle/input").exists():
    INPUT_DIR = Path(KAGGLE_COMP_DIR)
    MODEL_DIR = Path(KAGGLE_MODEL_DIR)
    OUTPUT_DIR = Path("/kaggle/working")
else:
    PROJECT_ROOT = Path(".").resolve().parent
    INPUT_DIR = PROJECT_ROOT / "input"
    MODEL_DIR = PROJECT_ROOT / "src/{exp_name}/output/{run_name}"
    OUTPUT_DIR = Path(".")
```

- `INPUT_DIR` 以下のサブパスはローカルの `input/` 構造と同一
- `MODEL_DIR` 以下のサブパス（`fold0/{ckpt}` 等）はアップロードした `output/{run_name}/` 構造と同一

## フェーズ 3: Notebook 生成

`src/{exp_name}/inference_notebook.ipynb` を作成する。

### セル構成

コードセルの前には必ず **マークダウンセル** を挿入し、そのセルで何をしているかを日本語で説明する。
特に実験固有の工夫（モデル構造、損失関数、データ処理、後処理等）がある場合は、**なぜそうしているか** を含めて説明する。

| # | 種類 | 内容 |
|---|---|---|
| 1 | markdown | タイトル + 概要（実験・ckpt 構成・前提・環境要件・提出手順） |
| 2 | markdown | 「環境と構成を記録する」 |
| 3 | code | パス設定 → ckpt を rglob → `parse_ckpt_name` で fold/epoch/score の表を print → GPU 名・主要パッケージ版・`INPUT_DIR`・code_sha を print → ログファイルを開く |
| 4 | markdown | 「モデルを構築して重みを読む」 |
| 5 | code | `pretrained=False` で構築（internet off）→ fold ごとに best ckpt をロード |
| 6 | markdown | 「推論する」 |
| 7 | code | レコードループ。try/except で失敗は中立値埋め + 理由 1 行、N 件ごとに進捗 1 行、確定した予測は即座に行として append、ループ末尾で `del` + `gc.collect()` |
| 8 | markdown | 「提出ファイルを検証して書き出す」 |
| 9 | code | `sample_submission.csv` と列名・行数を突合 → `submission.csv` を書く → `write_manifest` → `describe_manifest` の 1 行を print → 失敗件数と ID 一覧を print |

**実行機の性能を落とさないための決め事**（生成時に必ず守る）:

- ログは `print(..., flush=True)` + ファイル append で逐次書き出す。メモリに溜めない
- **1 レコード 1 行のログを出さない**（出力が膨らんで notebook が重くなる）。既定 50 件間隔
- 配列・画像をログに残さない。形状と min/max/mean のみ
- 全レコードの予測を辞書で抱えず、DataFrame は最後に組む
- ログの実体は `/kaggle/working/submission_log.txt`（Kaggle の出力に残る）

### 注意点

- GPU/CPU 自動切り替え: `torch.device("cuda" if torch.cuda.is_available() else "cpu")`
- チェックポイント名は `{exp番号}-{run_name}-f{k}[-ep{NN}][-val_{評価指標名}-{score}].ckpt`（`docs/training-conventions.md`）を前提にする。
  **`=` を含む名前は作らない** — Kaggle がファイル名の `=` を除去することがあり、Dataset 経由の重み配布が壊れる。
  fold ごとの best は `glob("*-f{k}-*.ckpt")` で引き、`src/utils/submission_manifest.parse_ckpt_name` でスコアを読んで選ぶ
- `num_workers`: Kaggle 環境では `2` 程度が安定

## フェーズ 4: 完了報告

- 生成した Notebook のパス: `src/{exp_name}/inference_notebook.ipynb`
- Kaggle 上での使い方:
  1. Kaggle Notebooks で新規 Notebook を作成（またはファイルをアップロード）
  2. **Add Data** から以下を追加:
     - コンペティションデータ
     - モデル Dataset（`{user}/{slug}`）
  3. 先頭セルのパスが正しいか確認
  4. **Submit** で提出
- パス設定の変更が必要な場合の案内
- **`describe_manifest` の 1 行をそのまま報告に載せる**（ユーザーが提出時の description に貼れる形）
- `docs/competition-profile.yaml` の `workflow.submission_by` が `user` の間は、
  **notebook の commit と出力確認までで止める**。`kaggle competitions submit` は呼ばない
