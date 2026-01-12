# CLAUDE.md - AI アシスタント向けガイドライン

## 基本方針

- コメント・ドキュメントは日本語で記述
- 疑問点は解消されるまでユーザに質問（AskUserQuestion ツールを使用）
- 疑問点や実装ポイントは GitHub Issue を作成して参照

## 開発フロー

### ブランチ戦略
- 細かな機能ごとに branch を切る
- ブランチ名: `feature/{機能名}`, `fix/{修正内容}`, `exp/{実験番号}`
- commit + push を細かく行う

### コミットメッセージ
- gitmoji を使用する
- 例:
  - `:sparkles:` 新機能
  - `:bug:` バグ修正
  - `:recycle:` リファクタリング
  - `:memo:` ドキュメント
  - `:art:` コードスタイル
  - `:test_tube:` 実験追加
  - `:fire:` ファイル削除
  - `:wrench:` 設定変更

### GitHub 操作
- `gh` コマンドを使用
- Issue 作成: `gh issue create`
- PR 作成: `gh pr create`

## パッケージ管理

- `uv add {パッケージ名}` で依存追加
- `uv run {コマンド}` でスクリプト実行
- `uv sync` で環境同期

## リポジトリルール

### 実験の追加
1. `experiments/exp{番号}_{名前}/` フォルダを作成
2. `run.py`, `config.yaml`, `exp/` を配置
3. `README.md` を作成（テンプレート参照）
4. Issue を作成して実験目的を記録

### ノートブック
- `notebooks/` は公開用（Kaggle Discussion/Notebooks 投稿用）
- 探索的分析は `experiments/` 内で行う

### コード品質
- `uv run ruff check .` で lint
- `uv run ruff format .` でフォーマット
- pre-commit が自動実行される

## TDD（テスト駆動開発）

- 原則として TDD で進める
- 期待される入出力に基づきテストを作成
- テスト失敗を確認してからコミット
- テストをパスする実装を進める
