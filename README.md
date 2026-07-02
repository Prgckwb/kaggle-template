# Competition Name

> Kaggle コンペティション用テンプレート。Hydra + Wandb で実験管理、FastAPI + htmx でダッシュボード。

## Prerequisites

| ツール | 用途 | インストール |
|--------|------|-------------|
| [uv](https://docs.astral.sh/uv/) | パッケージ管理 | `curl -LsSf https://astral.sh/uv/install.sh \| sh` |
| [just](https://github.com/casey/just) | タスクランナー（`just app` 等） | `brew install just` |
| Kaggle API トークン | データ取得・提出 | https://www.kaggle.com/settings → API → Create New Token → `~/.kaggle/kaggle.json` |
| wandb アカウント | 実験管理 | `uv run wandb login` |

## Quick Start

```bash
# 1. クローン
git clone <repo-url> && cd <repo-name>

# 2. 依存関係インストール（コア + 開発ツール）
uv sync

# 3. モデル学習に使うフレームワークに応じて extras を追加
uv sync --extra torch     # PyTorch + Lightning + scikit-learn
uv sync --extra tabular   # LightGBM / XGBoost / CatBoost + scikit-learn
# ※ src/utils/cv.py 等は scikit-learn に依存するため、実験前にどちらかが必要

# 4. Claude Code でコンペ情報をセットアップ
/kaggle:init
```

コンペ固有の設定（コンペ名・評価指標・wandb project）は `docs/competition-profile.yaml` に集約されており、`/kaggle:init` が書き込む。

## Directory Structure

```
kaggle-template/
├── input/          # データ格納（gitignore）
├── sandbox/        # AI Agent 検証用（gitignore）
├── app/            # Web アプリ（FastAPI + htmx）
├── docs/           # ドキュメント
│   ├── official/   # Kaggle 公式情報
│   ├── discussion/ # Kaggle Discussion 情報
│   └── insights/   # 実験から得た知見
└── src/            # 実験ディレクトリ
    └── exp000_sample/
        ├── config/     # ベース config + 小実験 config
        └── output/     # 学習出力（gitignore）
```

## Commands

```bash
# 依存関係インストール
uv sync

# Web ダッシュボード起動
just app

# Lint / Format / Test
just lint
just format
just test

# 実験実行
uv run python -m src.exp001_xxx.train                              # fold0（デフォルト）
uv run python -m src.exp001_xxx.train run_mode=debug               # デバッグモード
uv run python -m src.exp001_xxx.train run_mode=full                # 全 fold

# 小実験（Run）を指定して実行
uv run python -m src.exp001_xxx.train --config-name=run001-yyy
uv run python -m src.exp001_xxx.train --config-name=run001-yyy run_mode=debug
```

## Skills (Claude Code)

| スキル | 説明 |
|--------|------|
| `/kaggle:init` | テンプレート初期化（コンペ名・データ・docs セットアップ） |
| `/kaggle:new-experiment` | 新しい実験を対話的に設計・作成 |
| `/kaggle:record-result` | 実験結果を記録（README・EXP_SUMMARY・insights 更新） |
| `/kaggle:commit` | 変更を論理単位でコミット＆プッシュ |
| `/kaggle:check-commands` | 実行コマンドの確認 |
| `/kaggle:add-app-page` | ダッシュボードに新ページ追加 |
| `/kaggle:upload-checkpoints` | チェックポイントを Kaggle Datasets にアップロード |
| `/kaggle:create-inference-notebook` | Kaggle 用推論ノートブック作成 |
| `/kaggle:review-strategy` | 実験ポートフォリオの俯瞰レビュー（探索多様性・停滞検出） |
| `/kaggle:scout-approaches` | 手法チェックリスト生成・探索率追跡 |
| `/kaggle:past-solutions` | Kaggle MCP 経由で類似過去コンペの上位解法を `docs/insights/past_solutions_{slug}.md` に収集 |

## Experiment Workflow

1. `/kaggle:new-experiment` で実験を設計・作成
2. `run_mode=debug` でパイプラインの動作確認
3. `run_mode=fold0` で性能確認
4. `run_mode=full` で全 fold 実行・CV スコア算出
5. `/kaggle:record-result` で結果を記録

## Experiments

実験の記録は [EXP_SUMMARY.md](EXP_SUMMARY.md) を参照。
