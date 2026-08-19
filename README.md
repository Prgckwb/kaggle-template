# Competition Name

> Kaggle コンペティション用テンプレート。Hydra + Wandb で実験管理、FastAPI + htmx でダッシュボード。

## Prerequisites

| ツール | 用途 | インストール |
|--------|------|-------------|
| [uv](https://docs.astral.sh/uv/) | パッケージ管理 | `curl -LsSf https://astral.sh/uv/install.sh \| sh` |
| make | タスクランナー（`make app` 等） | macOS / Linux は標準搭載（macOS は Xcode CLT） |
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

コンペ固有の設定（コンペ名・評価指標・wandb project・エージェントの働き方）は `docs/competition-profile.yaml` に集約されており、`/kaggle:init` が書き込む。

### エージェントのガードレール（hooks）

危険な操作は **2 層**で止めている。`.claude/settings.json` の `permissions.deny`（宣言的。
コマンド文字列の先頭一致 glob）と、`PreToolUse` hook（`.claude/hooks/guard.py`。
正規表現で判定し、理由を添えて deny を返す）。

**2 層が必要な理由**: hook は fail-open（スクリプトに届かなければ黙って通る）なので
deny が外側の網になる。一方 deny の glob は先頭一致なので
`git -C <path> add -A` のように**グローバルオプションが挟まった形**を拾えず、
そこは hook の正規表現だけが見ている。

| パターン | 止める場所 | 理由 |
|---|---|---|
| `git add -A` / `git add .` / `git add --all` | deny + hook | 併走セッションの未コミット作業を巻き込む。常にパスを明示する |
| `git add -u` / `git add --update` | deny + hook | 追跡中の全変更をステージする（`git commit -a` と同じ危険）。短く打ちやすいぶん事故りやすい |
| `git add -Av` / `git add -vu` 等、まとめたショートオプション束 | deny + hook | 同上。hook は束の中の `A` / `u` を見る（`-A\b` だけでは `-Av` の境界が立たない） |
| `git -C <path> add -A` 等、オプションが挟まった形 | hook のみ（deny の glob は先頭一致で拾えない） | 同上。`/kaggle:harvest-template` が `git -C` の書き方を教えているため実際に起きる |
| `git commit -a` / `git commit -am` / `git commit --all` | deny + hook | 追跡中の全変更を巻き込む（`git add -A` と同じ危険）。`--amend` は素通しする |
| `git stash` / `git reset --hard` / `git checkout -- <file>` | deny + hook | 相手の未コミット作業を即座に消す |
| `kaggle competitions submit` | deny + hook | 提出はユーザーの専管。notebook の commit までで止める |
| `mcp__kaggle__submit_to_competition` / `mcp__kaggle__create_code_competition_submission` | deny のみ（hook は Bash 専用） | 同上。`mcp__kaggle__upload_dataset_file` は重みの Dataset 化に必要なので `ask` のまま |

`docs/competition-profile.yaml` の `workflow.concurrent_sessions` が `false` なら git 系、
`workflow.submission_by` が `agent` なら提出のパターンを外してよい
（理由は `docs/ai-agent-guidelines.md` の「運用の合意」）。

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
├── tools/          # スタンドアロン CLI（提出監視・チェックポイントアップロード）
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
make app

# Lint / Format / Test
make lint
make format
make test

# 実験実行
uv run python -m src.exp001_xxx.train                              # fold0（デフォルト）
uv run python -m src.exp001_xxx.train run_mode=debug               # デバッグモード
uv run python -m src.exp001_xxx.train run_mode=full                # 全 fold

# 小実験（Run）を指定して実行
uv run python -m src.exp001_xxx.train --config-name=run001-yyy
uv run python -m src.exp001_xxx.train --config-name=run001-yyy run_mode=debug

# Kaggle CLI ツール（詳細は tools/README.md）
uv run python tools/check_submission.py       # 最新提出のステータス監視 + LB 表示
uv run python tools/upload_checkpoints.py exp001_xxx run000-base -m "更新"  # チェックポイントを Dataset 化
```

データパスは `INPUT_DIR` 環境変数で切り替えられる（未設定時はローカルの `input/`）:

```bash
# Kaggle Notebook: コンペデータは /kaggle/input/competitions/{slug} にマウントされる
INPUT_DIR=/kaggle/input/competitions/{slug} uv run python -m src.exp001_xxx.train
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
| `/kaggle:create-guide` | ダッシュボードの Guides に表示するガイド・分析レポート（HTML）を作成 |
| `/kaggle:ensemble` | 複数実験の OOF をブレンドし、重みを最適化して submission を作成 |
| `/kaggle:harvest-template` | コンペで得た汎用知見をテンプレートリポジトリへ還流する PR を作る |

## Experiment Workflow

1. `/kaggle:new-experiment` で実験を設計・作成
2. `run_mode=debug` でパイプラインの動作確認
3. `run_mode=fold0` で性能確認
4. `run_mode=full` で全 fold 実行・CV スコア算出
5. `/kaggle:record-result` で結果を記録

## Experiments

実験の記録は [EXP_SUMMARY.md](EXP_SUMMARY.md) を参照。
