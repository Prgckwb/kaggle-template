# Competition Name

> Kaggle コンペティション用テンプレート。Hydra + wandb で実験管理、Claude Code / Codex のスキルでコンペの進行を支援する。
> エージェント向けの規約と全コマンドは [CLAUDE.md](CLAUDE.md)（= `AGENTS.md`）。

## Prerequisites

| ツール | 用途 | 準備 |
|--------|------|------|
| [uv](https://docs.astral.sh/uv/) | パッケージ管理 | `curl -LsSf https://astral.sh/uv/install.sh \| sh` |
| Kaggle API トークン | データ取得・LB 確認 | https://www.kaggle.com/settings → API → Create New Token → `~/.kaggle/kaggle.json` |
| wandb アカウント | 実験管理 | `uv run wandb login` |

## Quick Start

```bash
git clone <repo-url> && cd <repo-name>
uv sync --extra torch        # NN（PyTorch + Lightning）。GBDT なら --extra tabular

# サンプルで学習 → 推論が通ることを確認（合成データ・wandb 無効）
uv run python -m src.exp000_sample.make_synthetic
uv run python -m src.exp000_sample.train run_mode=debug
uv run python -m src.exp000_sample.inference run_mode=debug

# コンペのセットアップ（Claude Code / Codex で）
/kaggle:init
```

コンペ固有の設定（評価指標・wandb project・エージェントの働き方など）は `docs/competition-profile.yaml` に集約されている。

## 進め方

1. `/kaggle:init` — profile・競技指標（`src/metric.py`）・fold 設計・`docs/official/` を埋める
2. `/kaggle:past-solutions` — 類似過去コンペの上位解法を集めて初期仮説を作る
3. `/kaggle:new-experiment` — exp / run を設計・作成 → `run_mode=debug` → `fold0`（有望なら `full`）
4. `/kaggle:record-result` — `run_summary.json` から結果を記録し、知見を振り分ける
5. `/kaggle:review-strategy` — 探索マップと停滞を見て次の一手を考える
6. `/kaggle:ensemble` → `/kaggle:create-inference-notebook` → 提出（提出はユーザーが行う）

実験の記録は [EXP_SUMMARY.md](EXP_SUMMARY.md)、提出の記録は [docs/submissions.md](docs/submissions.md)。

## エージェントのガード

`.claude/hooks/guard.py`（PreToolUse hook）が、併走セッションの作業を巻き込む git 操作（`git add -A` 等）と
Kaggle への提出を止める。どの規則を有効にするかは profile の `workflow.concurrent_sessions` / `submission_by` で決まる。
規則の一覧は guard.py の docstring。
