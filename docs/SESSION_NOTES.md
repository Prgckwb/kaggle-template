# Session Notes

This file tracks context across Claude Code sessions. Update at the end of each session.

## Current Focus

テンプレート自体の品質改善フェーズ（コンペ未参加）。PR #6〜#10 で大規模リファクタリングを実施し、すべて main にマージ済み。直近セッションでスキル・CLAUDE.md の整合性レビューを実施し、以下を修正（コミット前）。

## Recent Decisions

- **ダッシュボード UI/UX 再設計: Guides 機構の導入（2026-07-04）**:
  - **Guides = ファイルベースの成果物レジストリ**: `docs/guides/{slug}/`（guide.json + index.html + assets/）を置くだけで Knowledge → Guides に自動表示（アプリのコード変更不要）。ガイド・EDA・OOF 分析・リプレイビューアを単一レジストリ + タグ（guide/eda/analysis/viewer）で統合
  - render 2形態: `iframe`（自己完結 HTML。独自 CSS/JS/TS 成果物可、`?theme=` + postMessage でテーマ連携、`guide-height` で高さ通知。実装例 = `docs/guides/sample-guide/`）と `fragment`（Tailwind 断片、`make css` のスキャン対象に `docs/guides/**/*.html` を追加済み）
  - `/kaggle:create-guide` スキル新設。kaggle-analyst の出力先を `app/static/analysis/`（廃止）から `docs/guides/` に変更
  - **Data ページ補修**: Parquet プレビューが壊れていたのを修正（`pl.read_csv` 固定 → parquet/tsv 分岐）、wavesurfer.js を unpkg CDN からローカル vendor 化、長文向け「レコード表示」（1行=1カード、NLP コンペ用）を追加
  - **重大バグ修正: Tailwind ビルド環境の復元**: `.gitignore` の `build/` が `app/static/build/` にマッチし、ビルド環境一式が git に入っていなかった（`make css` が全クローンで壊れていた）。`/build/` に修正し、環境を再構築してコミット。safelist は旧 CSS の解析から復元（8色 × bg/text/border × hover/dark/dark:hover）+ `group-hover:text-{color}` を追加（従来サイレントに壊れていた）。**safelist の正規表現は必ず `^...$` でアンカーする**（未アンカーだと不透明度修飾が全展開され CSS が 80KB → 1MB に肥大化する。検証済み）。再ビルド後の旧 CSS とのクラスカバレッジ差分はノイズ2件のみ
  - app/README の技術スタック表を実態（セルフホスト）に合わせて修正。CDN 残は Mermaid のみ

- **整合性レビューに基づく一括修正（2026-07-04）**:
  - `docs/guardrails.md` 新設: コンペ固有ガードレール（評価関数の正誤・禁止事項）の SSOT。ai-agent-guidelines.md の「CLAUDE.md に蓄積」という矛盾した指示を修正し、CLAUDE.md・error-analyzer・new-experiment・review-strategy から参照
  - `docs/submissions.md` 新設: 提出ログの SSOT（record-result が LB 記録時に追記、kaggle-analyst の CV-LB 分析の元データ）
  - **selection.policy 導入**: best run 判定を「最良 LB」から profile の `selection.policy`（デフォルト `cv` = Trust your CV）に変更。CV best と LB best の食い違いは必ず警告。`public_test_ratio` も profile に追加
  - **competition.type の SSOT 統一**: init のタイプ判定ソースを EXP_SUMMARY.md から profile に変更（EXP_SUMMARY は表示用複製）。scout/review-strategy も profile を先に読む
  - **停滞判定のノイズフロア自動推定**: meaningful_delta 未設定時は run_summary.json の folds から `std/√n_folds` を計算して基準にする（record-result / review-strategy）
  - **competition.deadline 追加**: review-strategy が残り時間で序盤/中盤/終盤の戦略を出し分け
  - **`/kaggle:ensemble` スキル新設**: OOF ブレンド（utils/ensemble.py）→ 重み最適化（numpy のみ、等重み比較で過剰最適化を抑止）→ validate_submission → exp{NNN}_ensemble として記録
  - 細部: `src/exp000-sample`（ハイフン残骸）削除、init が exp000_sample の metric を書き換えない方針に変更（サンプルは loss/min が正）、scout の多様性スコアをトップレベルカテゴリ粒度に統一、Runs テーブルは実行順追記の規約を experiment-formats.md に明文化、init チェックリストに extra 依存確認を追加

（以前の決定）

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
