# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

AI エージェントがこのリポジトリで作業する際のガイドライン。

## プロジェクト概要

Kaggle コンペティション用テンプレート。Hydra + Wandb で実験管理、FastAPI + htmx でダッシュボード。

## 技術スタック

- **パッケージ管理**: uv
- **実験管理**: Hydra, Wandb
- **データ処理**: Polars（推奨）, Pandas
- **モデル学習**: PyTorch Lightning（最新版）、wandb logger
  - Trainer 内蔵ライブラリ（transformers 等）はその Trainer 利用も検討
  - MPS / CUDA / CPU を想定（`pin_memory` は GPU 時のみ有効化、`accelerator="auto"` を使用）
- **Web アプリ**: FastAPI, htmx, Jinja2
- **オプション依存**: `torch`（PyTorch + Lightning + scikit-learn）、`tabular`（LightGBM, XGBoost, CatBoost + scikit-learn）
  - `src/utils/cv.py` 等は scikit-learn に依存するため、実験前に `uv sync --extra torch` or `--extra tabular` が必要
- **pre-commit**: ruff による lint/format を自動実行

## コマンド

```bash
uv sync                        # 依存関係インストール（コア依存のみ）
uv sync --extra torch          # PyTorch 系を含めてインストール
uv sync --extra tabular        # GBDT 系を含めてインストール
just app                       # Web アプリ起動（空きポート自動選択）

# Lint / Format
uv run ruff check src/ app/    # Lint
uv run ruff format src/ app/   # Format

# 実験実行
uv run python -m src.exp001_xxx.train                           # fold0（デフォルト）
uv run python -m src.exp001_xxx.train run_mode=debug            # デバッグモード
uv run python -m src.exp001_xxx.train run_mode=full             # 全 fold
uv run python -m src.exp001_xxx.train --config-name=run001-yyy  # 小実験指定
```

## ディレクトリ構成

```
kaggle-template/
├── input/              # データ格納（gitignore）
├── sandbox/            # AI Agent 検証用スクリプト（gitignore）
├── app/                # Web アプリ → 詳細は app/README.md
├── docs/               # コンペ情報・知見・仕様
│   ├── official/       # Kaggle 公式情報
│   ├── discussion/     # Discussion（YYYY-MM-DD_topic.md）
│   └── insights/       # 実験知見（YYYY-MM-DD_topic.md）
├── src/
│   ├── exp000_sample/  # サンプル実験（テンプレート）
│   └── utils/          # 共有ユーティリティ
├── .claude/
│   ├── skills/         # Claude Code スキル
│   └── agents/         # Claude Code エージェント
└── .agents/skills/     # 外部スキル（wandb-primary, runpodctl, flash）
```

### src/utils（共有ユーティリティ）

| モジュール | 用途 |
|-----------|------|
| `cv.py` | K-fold 分割（stratified, group, timeseries 等） |
| `metrics_logger.py` | wandb 並行のローカルメトリクスログ |
| `ensemble.py` | 予測のブレンド・ランク平均アンサンブル |
| `postprocess.py` | クリッピング・閾値最適化 |
| `submission.py` | sample_submission.csv との形式バリデーション |
| `seeding.py` | 再現性のためのシード固定（random, numpy, torch） |

## Kaggle 情報の取得

**Kaggle 公式 MCP サーバー（`.mcp.json` で定義済み）を優先使用**。Web 検索より最新かつ正確。

- 一次情報は MCP から取得し、要点をまとめて `docs/official/` or `docs/discussion/` に保存する
- ダウンロード物は `input/` or `sandbox/` に保存（gitignore）
- 提出系ツール（`submit_to_competition` 等）は明示的な指示があるまで呼ばない
- **MCP 不通時のフォールバック**: `kaggle`（dev 依存に同梱）→ `WebFetch`

## 実験ディレクトリの規則

### 命名・構成

`exp{番号}_{subtitle}` 形式（大実験）。各実験は独立し、他の実験ディレクトリからインポートしない。安定した共有コードは `src/utils/` に置く。

```
src/exp001_xxx/
├── README.md       # 目的・仮説・結果・Runs テーブル・考察
├── train.py        # 学習スクリプト
├── inference.py    # 推論スクリプト（sample_submission.csv と同形式の CSV を出力）
├── model.py        # モデル定義
├── data.py         # データ処理
├── inference_notebook.ipynb  # Kaggle 推論 notebook（/kaggle:create-inference-notebook で生成）
├── config/
│   ├── config.yaml           # ベース設定（run_name: run000-base）
│   └── run001-yyy.yaml       # 小実験（defaults: [config] で継承、差分のみ）
├── logs/                     # ローカルメトリクスログ（gitignore）
└── output/                   # 学習出力（gitignore）
```

### 大実験 vs 小実験（Run）

- **大実験**: アプローチ・アーキテクチャ・データパイプライン・バリデーション戦略が根本的に異なる場合に新規作成
- **小実験**: 既存大実験のコードを共有し、config の差分のみで表現できる変更 → `config/run{NNN}-{subtitle}.yaml`

小実験 config は Hydra defaults でベース config を継承し、差分のみ記述:

```yaml
defaults:
  - config    # config.yaml を継承
run_name: run001-bert
model:
  name: bert-base-uncased
training:
  lr: 2e-5
```

### 実行モード

| モード | 動作 | 用途 |
|--------|------|------|
| `debug` | 少数データ・1epoch・1fold・wandb disabled | パイプライン動作確認 |
| `fold0`（デフォルト） | fold0 のみ、通常量 | 性能確認 |
| `full` | 全 fold | CV スコア算出・OOF 生成 |

`debug` → `fold0` → `full` の順で進める。非 supervised コンペでの解釈は `docs/competition-types.md` を参照。

### wandb ログ

詳細は `docs/wandb-spec.md`。要点:

- fold ごとに独立した wandb run を作成し、`group` で束ねる
- メトリクスキー名は `{split}/{metric}` 形式（例: `train/loss`, `val/auc`）で全実験統一
- `{評価指標名}` は `/kaggle:init` 実行時にユーザーに確認し、実際のメトリクス名に置換する
- `debug`: wandb disabled / `fold0`: fold_0 のみ / `full`: 全 fold + summary run

### MetricsLogger（ローカルメトリクスログ）

wandb と並行してローカルにメトリクスを保存。ダッシュボードの Logs タブで閲覧可能。

```python
from src.utils.metrics_logger import MetricsLogger
metrics_logger = MetricsLogger(cfg)
metrics_logger.log_epoch(fold_idx, {"epoch": epoch, "train/loss": train_loss, "val/loss": val_loss})
metrics_logger.finish()
```

### チェックポイントと出力

```
src/{exp_name}/output/{run_name}/
├── fold0/
│   ├── {exp_name}-val_{評価指標名}={score}.ckpt
│   ├── train.csv / val.csv    # OOF 再現性のための split 記録
├── fold1/ ...
└── oof_predictions.csv        # full モードで生成
```

再実行時は上書き。パラメータを変えて比較したい場合は小実験を追加する。

### 実験後の更新（必須）

1. 各実験の **README.md**: 目的・仮説（開始時）、結果・Runs テーブル・考察（完了時）
2. **EXP_SUMMARY.md**: Experiments テーブルと Experiment Tree を更新 → フォーマットは `docs/experiment-formats.md`
3. **docs/insights/**: `YYYY-MM-DD_exp{番号}_{subtitle}.md` で知見を記録

### コンペティションタイプ

デフォルトは `supervised`（予測コンペ）。`simulation` / `optimization` タイプは `docs/competition-types.md` を参照。

### 再現性

シード固定（random, numpy, torch）、シード値は `config.yaml` に記録、環境は `uv.lock` で管理。

## Web アプリ（ダッシュボード）

- **ナビゲーション**: サイドバーは Home + Experiments / Data / Knowledge で構成
- 新ページはまず既存セクションのサブページとして追加を検討し、トップレベル追加は最終手段
- 2重サイドバー禁止（Data のファイルツリーは例外）
- スタイル・コンポーネント・htmx パターンの詳細: `app/README.md`

### sandbox → app/static パイプライン

sandbox/ で生成した分析画像を `app/static/analysis/` にコピーしてダッシュボードで表示（ディレクトリは必要に応じて `mkdir -p` で作成）。`app/static/` は単一の StaticFiles マウント — 別途マウントを追加しない。

## Git 規則

- **ブランチ**: `main`（デフォルト）、`exp/{番号}_{subtitle}`、`feature/{名前}`、`fix/{内容}`
- **コミット**: gitmoji + 日本語。1コミット = 1つの論理的な変更。例: `🧪 exp001_baseline を追加`
- **push**: 作業の区切りごと、実験完了時

## TDD 適用除外

このプロジェクトでは TDD は適用しない。`run_mode=debug` でパイプライン全体の動作確認を行うことで代替する。

## AI エージェントへの注意

### 探索の独立性

LLM は過去の実験結果に引きずられ探索空間を狭めがち。

- **引き継いでよい**: データ前処理の実装上の工夫、バグ修正、`docs/insights/` の実装知見
- **引き継いではいけない**: 「うまくいかない」という結論、手法への偏り、探索範囲の絞り込み
- **新しい実験では**: 問題の本質・データの特性・ドメイン知識から仮説をゼロベースで立てる

### 疑問点の確認

不明点や曖昧な点がある場合は、推測で進めずにユーザに質問すること。一度の質問で解消しない場合は、理解できるまで繰り返し質問する。特に以下の場面では必ず確認する:

- 実験の方針・仮説の妥当性に自信がないとき
- 複数のアプローチが考えられ、どれを選ぶべきか判断できないとき
- コンペ固有のドメイン知識が必要なとき

## セッション管理

セッション終了時は `docs/SESSION_NOTES.md` を更新し、次のセッションに引き継ぐべきコンテキストを記録する:
- 現在の作業フォーカス
- 直近の判断とその理由
- 未解決の疑問点
- 次のステップ

## スキル・MCP・エージェント

### Kaggle スキル（プロジェクト固有）

| スキル | 説明 |
|--------|------|
| `/kaggle:init` | テンプレート初期化（コンペ名・データ・docs セットアップ） |
| `/kaggle:new-experiment` | 新しい実験を対話的に設計・作成 |
| `/kaggle:record-result` | 実験結果を記録（README・EXP_SUMMARY・insights 更新） |
| `/kaggle:commit` | 変更を論理単位でコミット＆プッシュ |
| `/kaggle:check-commands` | 実行コマンドの確認 |
| `/kaggle:add-app-page` | ダッシュボードに新ページ追加 |
| `/kaggle:upload-checkpoints` | チェックポイントを Kaggle Datasets にアップロード |
| `/kaggle:create-inference-notebook` | 推論ノートブック作成 |
| `/kaggle:review-strategy` | 実験ポートフォリオの俯瞰レビュー（探索多様性・停滞検出） |
| `/kaggle:scout-approaches` | 手法チェックリスト生成・探索率追跡 |
| `/kaggle:past-solutions {slug}` | 過去コンペ上位解法を収集 → `docs/insights/` に保存 |

### 外部スキル

| スキル | 説明 |
|--------|------|
| `/wandb-primary` | W&B プロジェクト概要・Runs・Artifacts・Weave traces・Reports・Launch |
| `/runpodctl` | RunPod CLI で GPU ワークロード管理 |
| `/flash` | runpod-flash SDK で Serverless GPU/CPU にデプロイ |

### MCP サーバー

| サーバー | 用途 | 設定 |
|---------|------|------|
| `kaggle` | Kaggle 公式情報・Discussion・LB・Dataset 取得 | `.mcp.json`（リポジトリ同梱） |
| `runpod` | Pod・Endpoint・Template・GPU の管理 | claude.ai 統合（外部） |
| `runpod-docs` | RunPod ドキュメント検索 | claude.ai 統合（外部） |

### エージェント（.claude/agents/）

| エージェント | 用途 |
|-------------|------|
| `kaggle-researcher` | コンペリサーチ（論文・過去解法・Discussion 調査） |
| `kaggle-analyst` | データ分析（EDA・OOF エラー分析・CV-LB 相関分析） |
| `kaggle-error-analyzer` | エラー診断（学習失敗・スコア劣化・CV-LB 乖離の調査） |
