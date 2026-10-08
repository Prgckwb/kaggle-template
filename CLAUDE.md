# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.
（`AGENTS.md` はこのファイルへの symlink。Codex も同じ内容を読む）

AI エージェントがこのリポジトリで作業する際のガイドライン。

## プロジェクト概要

Kaggle コンペティション用テンプレート。Hydra + wandb で実験管理、PyTorch Lightning（NN）/ GBDT で学習する。

## 正本の所在（1 つの事実は 1 か所にだけ書く）

ここに無い場所へ同じ事実を書き写さない。迷ったら正本へのリンク 1 行で済ませる。

| 事実 | 正本 |
|---|---|
| コンペ固有値（slug・評価指標名と向き・meaningful_delta・noise・selection・wandb project・workflow） | `docs/competition-profile.yaml`（実験 config は `${profile:...}` で参照し、転記しない） |
| 競技指標の実装 | `src/metric.py` の `score()`（全実験・アンサンブル・OOF 再計算が共有） |
| fold 割当 | `data/folds/folds_{fold_version}.csv`（全実験で共有・不変・git 管理） |
| 実験の設定 | 各 exp の `config/config.yaml`（小実験は差分 yaml。スキーマ dataclass は持たない） |
| run の系譜（親・変えたキー） | 自動計算（`src/utils/lineage.py`）→ `run_summary.json` と wandb config。手で宣言しない |
| run の結果 | `src/{exp}/logs/{run}/run_summary.json`（スキーマは `src/utils/run_summary.py`） |
| 学習・出力・ckpt・提出 notebook の規約、Kaggle のマウントパス | `docs/training-conventions.md` |
| 判定の作法・停滞の定義 | `docs/experiment-methodology.md` |
| コンペ固有の罠 | `docs/guardrails.md` |
| 実験一覧・ツリー・探索マップ・バックログ・ノイズ較正 | `EXP_SUMMARY.md` |
| 提出ログ | `docs/submissions.md` |
| 知見の振り分け先 | `docs/README.md` の「知見の routing」 |
| git / 提出のガード | `.claude/hooks/guard.py`（profile の `workflow` を読んで有効化） |
| スキル | `.agents/skills/kaggle-*/SKILL.md`（`.claude/skills/` は symlink） |
| エージェント定義 | `.claude/agents/*.md`（`.codex/agents/*.toml` は `uv run python -m tools.sync_codex_agents` で生成） |

本ドキュメントやスキル中の `{評価指標名}` は profile の `metric.name`。スコアの良し悪しは `metric.mode`、
改善/停滞は `metric.meaningful_delta` と `metric.noise.seed_spread`、best の判定は `selection.policy`（既定 `cv`）に従う。

## 技術スタック

- **パッケージ管理**: uv（`requires-python >=3.12,<3.14`）
- **実験管理**: Hydra, wandb（+ Lightning CSVLogger によるローカルログ）
- **データ処理**: pandas（`src/utils` の API は pandas）。大きいデータの前処理は polars も可
- **学習**: NN は PyTorch Lightning（`accelerator="auto"`、MPS / CUDA / CPU）、GBDT は各ライブラリを直接使う。
  どちらも `docs/training-conventions.md` の出力契約に従う
- **オプション依存**: `torch`（PyTorch + Lightning + scikit-learn）、`tabular`（LightGBM / XGBoost / CatBoost + scikit-learn）。
  `src/utils/cv.py` と `src/metric.py` は scikit-learn を使うので、実験前にどちらかを入れる

## コマンド

```bash
uv sync --extra torch          # PyTorch 系込みでインストール（GBDT なら --extra tabular）

# 実験（exp000_sample は先に合成データを作る: uv run python -m src.exp000_sample.make_synthetic）
uv run python -m src.exp001_xxx.train run_mode=debug            # パイプライン確認（出力は *-debug/ に隔離）
uv run python -m src.exp001_xxx.train                           # fold0（既定）
uv run python -m src.exp001_xxx.train run_mode=full             # 全 fold + OOF
uv run python -m src.exp001_xxx.train --config-name=run001-yyy  # 小実験
uv run python -m src.exp001_xxx.inference                       # submission.csv + manifest

# tools（用途は tools/README.md）
uv run python -m tools.check_submission                         # 最新提出の監視・LB 表示（読み取り専用）
uv run python -m tools.upload_checkpoints {exp} {run} -m "..."  # best ckpt を slim 化して Dataset 化
uv run python -m tools.sync_codex_agents                        # .codex/agents を再生成
```

## 必読ドキュメント（作業の前に読む）

| これをする前に | 読む |
|---|---|
| 実験を実装・修正・提案する | `docs/guardrails.md` + `docs/experiment-methodology.md` の「要約」 |
| 学習コード・提出 notebook を書く | `docs/training-conventions.md` |
| 結果を「効いた/効かない」と判定する | `docs/experiment-methodology.md`（効果の帰属・判定の資格） |
| 学習ジョブをリモートに投入する | `docs/remote-training-ops.md` |
| エージェントの既定の振る舞いを確認する | profile の `workflow` + `docs/ai-agent-guidelines.md` |

`docs/` は lifecycle 二層（`invariant` はコンペを跨いで持ち越し、`per-competition` は `/kaggle:init` がリセット）。詳細は `docs/README.md`。

## 実験の規則（要点。詳細は `docs/training-conventions.md`）

- 大実験 `src/exp{NNN}_{subtitle}/` は互いに独立し、他の exp から import しない。安定した共有コードは `src/utils/`
- 小実験は `config/run{NNN}-{subtitle}.yaml`（`defaults: [<親>]` + 変えたキーだけ）。**1 run = 1 変数**。
  2 変数以上変わった run は train.py が警告し、その Δ を単一変数に帰属しない
- `debug` → `fold0` → `full` の順。`full` への昇格は profile の `workflow.default_run_mode` に従う
  （既定 `fold0`: fold0 で有望な run だけをユーザーの明示指示で full にする）
- fold0 の値は CV と呼ばない。CV の代表値は全 fold を回した `oof_score`
- コードを直した再実行も新しい run（同じ run_name で焼き直さない）
- 新しい exp は `src/exp000_sample` をコピーして作る（`/kaggle:new-experiment`）

## Kaggle 情報の取得

- LB・提出状況はまず `docs/submissions.md` を読み、`kaggle` CLI（dev 依存に同梱）で照合・更新する
- CLI で取れるもの（コンペ一覧・LB・提出履歴・データ・notebook）は CLI。Writeup / Discussion 本文は Kaggle MCP（`.mcp.json`。
  未認証だと公開ツールが `authenticate` だけになるので `/mcp` で認証する）。どちらも駄目なら WebFetch
- 一次情報の要点は `docs/official/` か `docs/discussion/` に保存。ダウンロード物は `input/` か `sandbox/`（gitignore）
- **提出は行わない**（`workflow.submission_by: user` の間）。notebook の commit・出力確認までで止め、
  `describe_manifest()` の description を添えて引き渡す。ガードは `.claude/hooks/guard.py`

## Git 規則

- ブランチは profile の `workflow.branching`（既定 `main-only` = main に直接コミット）
- `git add` は常にパスを明示する（`workflow.concurrent_sessions: true` の間、巻き込み系・破壊系の git は guard.py が止める）
- コミットは gitmoji + 日本語、1 コミット = 1 つの論理的な変更（例: `🧪 exp001_baseline を追加`）。手順は `/kaggle:commit`
- `inference_notebook.ipynb` はコミット前に出力を除去する（`uv run --with nbstripout nbstripout <path>`）

## 品質チェック方針

- CI・pre-commit・`tests/` は置かない。動作確認は `run_mode=debug` でパイプライン全体（学習 → 推論）を通す
- lint / format は都度: `uv run --with ruff ruff check src/ tools/ .claude/hooks/`（`ruff format` も同様）

## AI エージェントへの注意

- **探索の独立性**: 過去の結果に引きずられて探索空間を狭めない。引き継いでよいのは実装上の工夫・バグ修正・`docs/insights/` の実装知見。
  「うまくいかない」という結論や手法の偏りは引き継がない。新しい実験の仮説は問題の本質・データ特性・ドメイン知識からゼロベースで立てる
- **アイデアの役割分担**: AI は候補を出してよいが、失敗履歴ではなく問題設定・データ・公開情報から作り、採否は人間が決める（`docs/ai-agent-guidelines.md`）
- **疑問点は推測で進めず質問する**。特に実験方針・仮説の妥当性、複数アプローチの選択、コンペ固有のドメイン知識が要るとき
- 新しい知見は `/kaggle:record-result` が routing 表に従って書き分ける。コンペ終了時は `/kaggle:harvest-template` でテンプレートへ還流する
  （CLAUDE.md はコンペごとに書き換えない）

## セッション管理

セッション終了時は `docs/SESSION_NOTES.md` を更新する（現在のフォーカス・直近の判断と理由・未解決の疑問・次のステップ）。

## スキル・エージェント・MCP

- **Kaggle スキル**（`/kaggle:*`）: init / new-experiment / record-result / review-strategy / ensemble /
  create-inference-notebook / upload-checkpoints / past-solutions / commit / harvest-template。
  説明はセッション開始時のスキル一覧に載り、状況に応じて自動で起動する（commit・upload-checkpoints・harvest-template は依頼時のみ）
- **外部スキル**（`.agents/skills/` にベンダーコピー、取得元とハッシュは `skills-lock.json`）: `/wandb-primary`、`/runpodctl`、`/flash`
- **エージェント**: `kaggle-researcher`（論文・過去解法・Discussion 調査）、`kaggle-analyst`（EDA・OOF・CV-LB 分析）、
  `kaggle-error-analyzer`（学習失敗・スコア劣化・CV-LB 乖離の診断）
- **MCP**: `kaggle`（`.mcp.json`）、`runpod` / `runpod-docs`（claude.ai 統合）
