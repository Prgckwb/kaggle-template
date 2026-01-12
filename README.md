# Kaggle コンペティション用実験テンプレート

## 特徴
- uv によるパッケージ管理
- Hydra による実験管理
- Ruff + pre-commit によるコード品質管理
- dataclass を用いた config 定義によるエディタ補完
- 実験スクリプトとパラメータを同一フォルダで管理

### Hydra による Config 管理
- Config は yamlとdictではなく、dataclass を用いて定義
- エディタの補完機能を活用してタイポを防止
- 共通設定は utils/env.py の EnvConfig で定義
- 実験ごとの設定は `conf/{minor_exp_name}.yaml` で管理
- `{major_exp_name}` と `{minor_exp_name}` の組み合わせで実験を再現

## セットアップ

### uv のインストール

```bash
# uv のインストール（未導入の場合）
curl -LsSf https://astral.sh/uv/install.sh | sh
```

### 依存関係のインストール

```bash
# 基本依存関係のインストール
uv sync

# 開発用依存関係も含める
uv sync --extra dev

# GPU 環境の場合
uv sync --extra gpu
```

### pre-commit のセットアップ

```bash
# pre-commit フックをインストール
uv run pre-commit install
```

## ディレクトリ構成

```text
.
├── experiments/       # 実験スクリプト（Hydra ベース）
│   ├── exp000_sample/
│   │   ├── README.md
│   │   ├── run.py
│   │   ├── config.yaml
│   │   └── conf/
│   │       ├── 000.yaml
│   │       └── 001.yaml
│   └── README_TEMPLATE.md
├── input/             # 入力データ
├── notebooks/         # 公開用ノートブック
├── output/            # 出力ファイル
├── tools/             # ユーティリティスクリプト
├── utils/             # 共通モジュール
├── pyproject.toml     # プロジェクト設定
├── CLAUDE.md          # AI アシスタント向けガイドライン
├── AGENTS.md          # CLAUDE.md へのリンク
└── README.md
```

## 実験の実行

```bash
# デフォルト設定で実行
uv run python experiments/exp000_sample/run.py

# 設定を指定して実行
uv run python experiments/exp000_sample/run.py conf=001

# デバッグモード
uv run python experiments/exp000_sample/run.py conf.debug=true
```

## コード品質管理

```bash
# lint チェック
uv run ruff check .

# 自動フォーマット
uv run ruff format .

# pre-commit 手動実行
uv run pre-commit run --all-files
```

## JupyterLab の起動

```bash
uv run jupyter lab
```

## 新しい実験の追加

1. experiments/ 内に新しいフォルダを作成
2. README_TEMPLATE.md を参考に README.md を作成
3. run.py, config.yaml, conf/ を配置
4. GitHub Issue で実験目的を記録
