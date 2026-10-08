# tools/

Claude Code なしでも使えるスタンドアロン CLI。リポジトリのルートで `uv run python -m tools.<name>` として実行する。
Kaggle を叩くものは `kaggle` パッケージ（dev 依存）と API トークン（`~/.kaggle/kaggle.json`）が必要。

| ツール | 用途 |
|--------|------|
| `check_submission` | 最新提出のステータスを監視し、完了したら public LB を表示（読み取り専用） |
| `upload_checkpoints` | run の各 fold の best ckpt を slim 化して Kaggle Dataset に新規作成 / バージョン更新 |
| `sync_codex_agents` | `.claude/agents/*.md` から `.codex/agents/*.toml` を生成 |

```bash
uv run python -m tools.check_submission [-c <slug>] [-i 30]
uv run python -m tools.upload_checkpoints exp001_baseline run000-base --user your-name   # 初回
uv run python -m tools.upload_checkpoints exp001_baseline run000-base -m "全 fold 追加"  # 2 回目以降
uv run python -m tools.sync_codex_agents
```
