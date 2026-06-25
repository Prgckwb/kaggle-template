# Competition Name

> Kaggle コンペティション用テンプレート。Hydra + Wandb で実験管理、FastAPI + htmx でダッシュボード。

## Quick Start

```bash
# 1. クローン
git clone <repo-url> && cd <repo-name>

# 2. 依存関係インストール
uv sync

# 3. Claude Code でコンペ情報をセットアップ
/kaggle:init
```

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

# 実験実行
uv run python -m src.exp001-xxx.train                              # fold0（デフォルト）
uv run python -m src.exp001-xxx.train run_mode=debug               # デバッグモード
uv run python -m src.exp001-xxx.train run_mode=full                # 全 fold

# 小実験（Run）を指定して実行
uv run python -m src.exp001-xxx.train --config-name=run001-yyy
uv run python -m src.exp001-xxx.train --config-name=run001-yyy run_mode=debug
```

## Skills (Claude Code)

| スキル | 説明 |
|--------|------|
| `/kaggle:init` | テンプレート初期化（コンペ名・データ・docs セットアップ） |
| `/kaggle:new-experiment` | 新しい実験を対話的に設計・作成 |
| `/kaggle:record-result` | 実験結果を記録 |
| `/kaggle:commit` | 変更を論理単位でコミット＆プッシュ |
| `/kaggle:check-commands` | 実行コマンドの確認 |
| `/kaggle:add-app-page` | ダッシュボードに新ページ追加 |
| `/kaggle:past-solutions` | Kaggle MCP 経由で類似過去コンペの上位解法を `docs/insights/past_solutions_{slug}.md` に収集 |

## Experiment Workflow

1. `/kaggle:new-experiment` で実験を設計・作成
2. `run_mode=debug` でパイプラインの動作確認
3. `run_mode=fold0` で性能確認
4. `run_mode=full` で全 fold 実行・CV スコア算出
5. `/kaggle:record-result` で結果を記録

## Experiments

実験の記録は [EXP_SUMMARY.md](EXP_SUMMARY.md) を参照。
