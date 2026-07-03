# tools/

Claude Code なしでも直接使えるスタンドアロン CLI ツール群。
`kaggle` パッケージ（dev 依存）と Kaggle API トークン（`~/.kaggle/kaggle.json`）が必要。

| ツール | 用途 |
|--------|------|
| `check_submission.py` | 最新提出のステータスを監視し、完了したら LB スコアを表示（読み取り専用） |
| `upload_checkpoints.py` | 実験の output ディレクトリを Kaggle Dataset としてアップロード（`/kaggle:upload-checkpoints` スキルの実体） |

```bash
# 提出ステータスの監視（コンペは docs/competition-profile.yaml の slug を使用）
uv run python tools/check_submission.py
uv run python tools/check_submission.py -c titanic -i 30

# チェックポイントのアップロード（初回）
uv run python tools/upload_checkpoints.py exp001_baseline run000-base --user your-name --new

# チェックポイントのアップロード（バージョン更新）
uv run python tools/upload_checkpoints.py exp001_baseline run000-base -m "全 fold 追加"
```
