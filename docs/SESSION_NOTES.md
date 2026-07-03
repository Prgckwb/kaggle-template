# Session Notes

This file tracks context across Claude Code sessions. Update at the end of each session.

## Current Focus

テンプレート自体の品質改善フェーズ（コンペ未参加）。PR #6〜#10 で大規模リファクタリングを実施し、すべて main にマージ済み。

## Recent Decisions

- **competition-profile 方式（PR #6）**: コンペ固有値（slug・評価指標の名前/方向/meaningful_delta・wandb project）は `docs/competition-profile.yaml` に一元管理。CLAUDE.md やスキルはコンペごとに書き換えない。`/kaggle:init` が書くのは profile + 実験 config のみ
- **メトリクス方向の明示（PR #6）**: best 判定・停滞検出はすべて `metric.mode`（max/min）を参照する。「最高 LB = best」という決めつけは廃止（RMSE 等の最小化指標対策）
- **Python 3.13 / requires-python `>=3.12,<3.14`（PR #6）**: torch の wheel 対応範囲に合わせた上限
- **フロントエンドはセルフホスト（PR #8）**: Tailwind はビルド済み CSS をコミット（`make css` で再ビルド、動的色クラスは safelist）。残る CDN は Mermaid のみ
- **タスクランナーは make に統一（PR #9）**: justfile 廃止。前提ツール削減のため
- **提出ガード**: `.claude/settings.json` で提出系 MCP ツールを ask（確認必須）に設定
- **unonao/kaggle-template 由来の改善（PR #10）**: config スキーマ検証（`config_schema.py` の dataclass、タイポ・型違いを起動時検出。config.yaml とキーを同期する規約）、`INPUT_DIR` 環境変数によるパス切替、`tools/` スタンドアロン CLI（提出監視・チェックポイントアップロード。`/kaggle:upload-checkpoints` はラッパー化）、wandb notes への Hydra オーバーライド自動記録、`utils/env.py`・`logger.py`・`timing.py` 追加。**Docker 導入はユーザー判断で見送り**

## Open Questions

- Kaggle Notebook のマウントパス形式（`/kaggle/input/{slug}` を採用中）は実環境で未検証。`/kaggle:upload-checkpoints` / `create-inference-notebook` 初回実行時にサイドバーの実パスを確認すること
- 外部スキル（`.agents/skills/`）は commit/tag のピンがなく陳腐化検知はハッシュのみ。更新運用は未整備

## Next Steps

- 実コンペ開始時: `/kaggle:init` を実行（profile 書き込み → ダッシュボードのセットアップ状況カードが 4/4 になることを確認）
- UI 改善の残提案（低優先）: Mermaid のローカル化、検索結果の aria-activedescendant 対応、text-gray-400 小テキストの全面コントラスト改善

## Known Issues

- ty の型チェックは未配線のまま既知の警告が多数（`make typecheck` はあるが CI に含めていない）
- `docs/official/` のプレースホルダ docs が Home の「最近更新されたドキュメント」に出る（実コンペで init すれば実データに置き換わるため許容）
- CLAUDE.md は ARS プラグインの scope guard により Edit/Write 不可。ユーザー許可のうえ Bash 経由で更新する運用（本セッションで2回実施）
