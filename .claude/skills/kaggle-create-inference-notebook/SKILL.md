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
   - 通常は `/kaggle/input/{competition-slug}`（slug は `docs/competition-profile.yaml` の `competition.slug`）
   - **注意**: マウントパスの形式は Kaggle の UI 更新で変わることがある。Notebook で **Add Data** した後、サイドバーに表示される実際のパスで必ず確認・修正するようユーザーに案内する

2. **Kaggle モデル Dataset のパス**
   - 通常は `/kaggle/input/{dataset-slug}`（例: `/kaggle/input/{comp_slug}-{exp_name_kebab}`）
   - `dataset-metadata.json` が存在すればそこから slug を取得

**Notebook 先頭セルのパス設定パターン**:

```python
from pathlib import Path

# ==== Path Configuration ====
# Kaggle 環境のパス（Add Data 後にサイドバーの実パスを確認して修正してください）
KAGGLE_COMP_DIR = "/kaggle/input/{competition-slug}"
KAGGLE_MODEL_DIR = "/kaggle/input/{dataset-slug}"

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

1. **タイトルセル**（Markdown）
   - `# {exp_name} Inference`
   - 実験の概要を日本語で記述:
     - アプローチの概要
     - 主な工夫点の箇条書き
     - バリデーション戦略の概要

2. **設定セルの説明**（Markdown） + **設定セル**（Code）
   - マークダウン: パス設定の説明、ハイパーパラメータの概要
   - コード: import 文、パス設定（フェーズ 2 のパターン）、モデル・データ・推論パラメータ、DEVICE 検出

3. **モデル定義の説明**（Markdown） + **モデル定義セル**（Code）
   - マークダウン: モデルアーキテクチャの日本語説明
     - backbone の選択理由
     - 分類ヘッドの構造
     - 推論時の処理フロー
   - コード: `nn.Module` としてインライン化、`load_model()` 関数

4. **データ処理の説明**（Markdown） + **データ処理セル**（Code）
   - マークダウン: 前処理パイプラインの日本語説明
     - データの変換方法や前処理パラメータの選択理由
     - テストデータの読み込み・分割方法
   - コード: Transform クラス、Dataset クラス

5. **推論の説明**（Markdown） + **推論セル**（Code）
   - マークダウン: 推論フローの説明
     - fold アンサンブルの有無
     - 確率値の計算方法
   - コード: テストデータ取得、バッチ推論ループ、submission.csv 保存

6. **後処理の説明**（Markdown） + **後処理セル**（Code、該当する場合のみ）
   - マークダウン: 後処理の手法と効果の説明
   - コード: `inference.py` の後処理をインライン化（デフォルト OFF ならコメントアウト）

### 注意点

- GPU/CPU 自動切り替え: `torch.device("cuda" if torch.cuda.is_available() else "cpu")`
- Kaggle 上のファイル名: `=` が除去される場合がある。チェックポイント名に `=` を含む場合は `glob("*.ckpt")` で検索するパターンも検討
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
