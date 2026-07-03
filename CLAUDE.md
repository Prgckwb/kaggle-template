# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

AI エージェントがこのリポジトリで作業する際のガイドライン。

## プロジェクト概要

Kaggle コンペティション用テンプレート。Hydra + Wandb で実験管理、FastAPI + htmx でダッシュボード。

## コンペティションプロファイル（Single Source of Truth）

コンペ固有の値は **`docs/competition-profile.yaml`** に一元管理する。`/kaggle:init` が書き込むのはこのファイル（+ 実験 config）であり、**CLAUDE.md やスキル定義はコンペごとに書き換えない**。

- 本ドキュメントやスキル中の `{評価指標名}` は profile の `metric.name` を指す
- スコアの「良い/悪い」「改善/停滞」の判断は必ず `metric.mode`（max/min）と `metric.meaningful_delta` に従う
- best run / 最終提出の判定基準は `selection.policy`（デフォルト `cv` = CV を信頼。public LB はノイジーな参考値）に従う
- ダッシュボード（`app/config.py`）も profile の `competition.slug` を読む

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
- **pre-commit**: ruff lint/format、大容量ファイル・秘密鍵チェック、notebook 出力除去（nbstripout）を自動実行

## コマンド

```bash
uv sync                        # 依存関係インストール（コア依存のみ）
uv sync --extra torch          # PyTorch 系を含めてインストール
uv sync --extra tabular        # GBDT 系を含めてインストール
make app                       # Web アプリ起動（空きポート自動選択）

# Lint / Format / Test
make lint                      # ruff check
make format                    # ruff format
make fix                       # ruff check --fix + format
make typecheck                 # ty check
make test                      # pytest（src/utils の単体テスト）

# 実験実行
uv run python -m src.exp001_xxx.train                           # fold0（デフォルト）
uv run python -m src.exp001_xxx.train run_mode=debug            # デバッグモード
uv run python -m src.exp001_xxx.train run_mode=full             # 全 fold
uv run python -m src.exp001_xxx.train --config-name=run001-yyy  # 小実験指定

# Kaggle CLI ツール（詳細は tools/README.md。提出は行わない読み取り専用の監視あり）
uv run python tools/check_submission.py                         # 最新提出のステータス監視・LB 表示
uv run python tools/upload_checkpoints.py {exp} {run} -m "..."  # チェックポイントを Dataset 化
```

## ディレクトリ構成

```
kaggle-template/
├── input/              # データ格納（gitignore）
├── sandbox/            # AI Agent 検証用スクリプト（gitignore）
├── app/                # Web アプリ → 詳細は app/README.md
├── docs/               # コンペ情報・知見・仕様
│   ├── competition-profile.yaml  # コンペ固有設定（SSOT、/kaggle:init が書く）
│   ├── guardrails.md   # コンペ固有ガードレール（評価関数の正誤・禁止事項。実装前に必読）
│   ├── submissions.md  # 提出ログ（全提出の SSOT。CV-LB 分析・最終提出選定の元データ）
│   ├── guides/         # ガイド・分析レポート（ダッシュボードの Guides に自動表示）→ docs/guides/README.md
│   ├── official/       # Kaggle 公式情報
│   ├── discussion/     # 外部情報（Discussion・論文サーベイ、YYYY-MM-DD_topic.md）
│   └── insights/       # 実験知見（YYYY-MM-DD_topic.md。例外: past_solutions_{slug}.md）
├── tools/              # スタンドアロン CLI（提出監視・チェックポイントアップロード）→ tools/README.md
├── src/
│   ├── exp000_sample/  # サンプル実験（テンプレート）
│   └── utils/          # 共有ユーティリティ
├── tests/              # src/utils の単体テスト（make test）
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
| `ensemble.py` | 予測のブレンド・ランク平均アンサンブル（id 列でアライン） |
| `postprocess.py` | クリッピング・閾値最適化・argmax・許容値スナップ |
| `submission.py` | sample_submission.csv との形式バリデーション |
| `seeding.py` | 再現性のためのシード固定（random, numpy, torch） |
| `checkpoint.py` | チェックポイントの軽量化・重み読み込み |
| `env.py` | 実行環境検出・パス解決（INPUT_DIR / Kaggle Notebook 判定） |
| `logger.py` | ファイル + 標準出力ロガー（logs_dir にタイムスタンプ付き保存） |
| `timing.py` | 処理時間・メモリ使用量の計測（`timer` / `trace`） |

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
├── model.py        # モデル定義（simulation/optimization タイプでは agent.py / solver.py。docs/competition-types.md 参照）
├── data.py         # データ処理
├── config_schema.py # config.yaml のスキーマ（dataclass。タイポ・型違いを実行時に検出）
├── inference_notebook.ipynb  # Kaggle 推論 notebook（/kaggle:create-inference-notebook で生成）
├── config/
│   ├── config.yaml           # ベース設定（run_name: run000-base、metric は profile と揃える）
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

### config のスキーマ検証とパス

- ベース config は `defaults: [base_schema, _self_]` で `config_schema.py` の dataclass を継承しており、yaml・CLI オーバーライドのタイポや型違いは起動時にエラーになる
- **config.yaml にキーを追加・削除したら `config_schema.py` も同期する**（不一致は ConfigKeyError になる）
- 実験を新規作成する際は `config_schema` の import パスを新実験のものに更新する
- データパスは `data.input_dir`（環境変数 `INPUT_DIR` で上書き可能）を経由する。未設定時はローカルの `input/`、Kaggle Notebook では `INPUT_DIR=/kaggle/input/{slug}` を指定

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
- `{評価指標名}` = `docs/competition-profile.yaml` の `metric.name`。実験 config の `metric.name` / `metric.mode` も profile と揃える
- `debug`: wandb disabled / `fold0`: fold_0 のみ / `full`: 全 fold + summary run

### MetricsLogger（ローカルメトリクスログ）

wandb と並行してローカルにメトリクスを保存。ダッシュボードの Logs タブで閲覧可能。

```python
from src.utils.metrics_logger import MetricsLogger
metrics_logger = MetricsLogger(cfg)
metrics_logger.log_epoch(fold_idx, {"epoch": epoch, "train/loss": train_loss, f"val/{cfg.metric.name}": val_score})
metrics_logger.finish()
```

- best 値の追跡は `cfg.metric.name` / `cfg.metric.mode`（min/max）に従う
- `run_mode=debug` のログは `logs/{run_name}-debug/` に書かれ、fold0/full のログを上書きしない

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

`/kaggle:record-result` スキルの利用をユーザーに提案する。更新対象:

1. 各実験の **README.md**: 目的・仮説（開始時）、結果・Runs テーブル・考察（完了時）
2. **EXP_SUMMARY.md**: Experiments テーブルと Experiment Tree を更新 → フォーマットは `docs/experiment-formats.md`
3. **docs/insights/**: `YYYY-MM-DD_exp{番号}_{subtitle}.md` で知見を記録

### コンペティションタイプ

デフォルトは `supervised`（予測コンペ）。`simulation` / `optimization` タイプは `docs/competition-types.md` を参照。

### 再現性

シード固定は `src/utils/seeding.py` の `seed_everything` を使う（random, numpy, torch を自動検出）。シード値は `config.yaml` に記録、環境は `uv.lock` で管理。

## Web アプリ（ダッシュボード）

- **ナビゲーション**: サイドバーは Home + Experiments / Data / Knowledge で構成
- **可視化・説明・レポートはガイド（`docs/guides/`）に置く**: `/kaggle:create-guide` で作成し、Knowledge → Guides に自動表示される（アプリのコード変更不要）。ページ追加が必要なのはアプリのロジックが要る場合のみ
- 新ページはまず既存セクションのサブページとして追加を検討し、トップレベル追加は最終手段
- 2重サイドバー禁止（Data のファイルツリーは例外）
- スタイル・コンポーネント・htmx パターン・実験ディレクトリとの契約: `app/README.md`

### sandbox → docs/guides パイプライン

sandbox/ で生成した分析画像・図は `docs/guides/{slug}/assets/` に置き、`index.html`（+ `guide.json`）のレポートとしてまとめる（旧 `app/static/analysis/` への配置は廃止）。ダッシュボードの Knowledge → Guides に自動表示される。`app/static/` は単一の StaticFiles マウント — 別途マウントを追加しない（ガイドのアセットは `/knowledge/guides/{slug}/raw/{path}` ルートが配信する）。

## Git 規則

- **ブランチ**: `main`（デフォルト）、`exp/{番号}_{subtitle}`、`feature/{名前}`、`fix/{内容}`
- **コミット**: gitmoji + 日本語。1コミット = 1つの論理的な変更。例: `🧪 exp001_baseline を追加`
- **push**: 作業の区切りごと、実験完了時

## テスト方針

- `src/utils/` の共有ユーティリティは `tests/` に単体テストを置く（`make test`）。ユーティリティを変更したらテストも更新する
- 実験コード（`src/exp*`）には TDD を適用しない。`run_mode=debug` でパイプライン全体の動作確認を行うことで代替する

## AI エージェントへの注意

### 探索の独立性

LLM は過去の実験結果に引きずられ探索空間を狭めがち。

- **引き継いでよい**: データ前処理の実装上の工夫、バグ修正、`docs/insights/` の実装知見
- **引き継いではいけない**: 「うまくいかない」という結論、手法への偏り、探索範囲の絞り込み
- **新しい実験では**: 問題の本質・データの特性・ドメイン知識から仮説をゼロベースで立てる

人間と AI の役割分担・失敗履歴の読ませ方の詳細は `docs/ai-agent-guidelines.md` を参照。

### ガードレール（コンペ固有）

評価関数の正誤・既知のバグパターン・「やってはいけないこと」は `docs/guardrails.md` に蓄積する（CLAUDE.md はコンペごとに書き換えないため、ここには書かない）。**実験の実装・修正・提案の前に必ず参照すること。**

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
| `/kaggle:create-guide` | ガイド・分析レポートを作成（docs/guides/ → ダッシュボードに自動表示） |
| `/kaggle:upload-checkpoints` | チェックポイントを Kaggle Datasets にアップロード |
| `/kaggle:create-inference-notebook` | 推論ノートブック作成 |
| `/kaggle:ensemble` | 複数実験の OOF をブレンドしアンサンブル submission を作成 |
| `/kaggle:review-strategy` | 実験ポートフォリオの俯瞰レビュー（探索多様性・停滞検出） |
| `/kaggle:scout-approaches` | 手法チェックリスト生成・探索率追跡 |
| `/kaggle:past-solutions {slug}` | 過去コンペ上位解法を収集 → `docs/insights/` に保存 |

### 外部スキル

| スキル | 説明 |
|--------|------|
| `/wandb-primary` | W&B プロジェクト概要・Runs・Artifacts・Weave traces・Reports・Launch |
| `/runpodctl` | RunPod CLI で GPU ワークロード管理 |
| `/flash` | runpod-flash SDK で Serverless GPU/CPU にデプロイ |

外部スキルは `.agents/skills/` にベンダーコピーされ、`.claude/skills/` から symlink されている。`skills-lock.json` が取得元リポジトリと内容ハッシュを記録する（コミット固定はないため、更新時は取得元から再取得して `computedHash` を更新する）。

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
