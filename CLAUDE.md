# CLAUDE.md

このファイルは AI エージェント（Claude など）がこのリポジトリで作業する際のガイドラインです。

## プロジェクト概要

Kaggle コンペティション用のテンプレートリポジトリ。Hydra + Wandb で実験管理を行い、FastAPI + htmx でダッシュボードを構築する。

## ディレクトリ構成

```
kaggle-template/
├── input/          # データ格納（gitignore）
├── output/         # 出力格納（gitignore）
├── sandbox/        # AI Agent 検証用（gitignore）
├── notebook/       # Jupyter Notebook（公開Code、検証用）
├── app/            # Web アプリ（FastAPI + htmx）
├── docs/           # ドキュメント
│   ├── official/   # Kaggle 公式情報
│   ├── discussion/ # Kaggle Discussion 情報
│   └── insights/   # 実験から得た知見
└── src/            # 実験ディレクトリ
    └── exp000-sample/
```

## 実験ディレクトリの規則

### 命名規則

`exp{番号}-{subtitle}` の形式を使用する。

- `exp000-sample` - サンプル実験
- `exp001-baseline` - ベースライン
- `exp002-feature-engineering` - 特徴量エンジニアリング

### ディレクトリ構成

各実験ディレクトリは独立しており、他の実験に依存しない。

```
src/exp001-xxx/
├── train.py        # 学習スクリプト
├── model.py        # モデル定義
├── data.py         # データ処理
└── config/         # Hydra 設定
    └── config.yaml
```

### 依存関係

- 実験ディレクトリ内のコードは、同じディレクトリ内のファイルにのみ依存する
- 共通ライブラリが必要な場合は、各実験ディレクトリにコピーする

## docs ディレクトリの規則

### official/

Kaggle 公式から提供される情報を記載。

### discussion/

Kaggle Discussion から得られた情報を記載。命名規則: `YYYY-MM-DD_topic.md`

### insights/

自分の実験から得られた知見を記載。命名規則: `YYYY-MM-DD_topic.md`

## sandbox ディレクトリ

AI Agent が Python/Bash スクリプトを書いて検証を行うためのディレクトリ。このディレクトリの内容は gitignore される。

## Git 規則

### ブランチ

- デフォルトブランチ: `main`

### コミットメッセージ

gitmoji を使用し、日本語で記述する。

例:
- `🎉 初期コミット`
- `✨ 新機能を追加`
- `🐛 バグを修正`
- `📝 ドキュメントを更新`
- `♻️ コードをリファクタリング`
- `🔧 設定ファイルを変更`

## 技術スタック

- **実験管理**: Hydra, Wandb
- **Web アプリ**: FastAPI, htmx, Jinja2
- **パッケージ管理**: uv

## コマンド

```bash
# 依存関係インストール
uv sync

# Web アプリ起動
uv run uvicorn app.main:app --reload

# 実験実行
cd src/exp000-sample
uv run python train.py
```
