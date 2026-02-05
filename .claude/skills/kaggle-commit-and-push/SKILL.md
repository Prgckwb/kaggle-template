---
name: kaggle:commit-and-push
description: 変更を gitmoji + 日本語でコミットし、push する。
disable-model-invocation: true
allowed-tools: Bash, Read
---

# コミット & プッシュ

変更を gitmoji + 日本語でコミットし、リモートにプッシュする。

## 手順

1. **変更を確認**
   - `git status` で変更ファイルを確認
   - `git diff` で変更内容を確認

2. **gitmoji を選択**
   変更内容に応じて適切な gitmoji を選択:
   - 🎉 `:tada:` - 初期コミット
   - ✨ `:sparkles:` - 新機能を追加
   - 🐛 `:bug:` - バグを修正
   - 📝 `:memo:` - ドキュメントを更新
   - ♻️ `:recycle:` - コードをリファクタリング
   - 🔧 `:wrench:` - 設定ファイルを変更
   - 🧪 `:test_tube:` - 新しい実験を追加
   - 📊 `:bar_chart:` - 実験結果を記録
   - 🎨 `:art:` - コードの構造/フォーマットを改善
   - 🔥 `:fire:` - コードやファイルを削除
   - 🚀 `:rocket:` - デプロイ関連
   - ➕ `:heavy_plus_sign:` - 依存関係を追加
   - ➖ `:heavy_minus_sign:` - 依存関係を削除

3. **コミットメッセージを生成**
   - 日本語で簡潔に変更内容を説明
   - フォーマット: `{gitmoji} {説明}`
   - 例: `✨ exp001-baseline を追加`
   - 例: `📊 exp001 の結果を記録（CV: 0.85, LB: 0.83）`

4. **コミット & プッシュを実行**
   ```bash
   git add <変更ファイル>
   git commit -m "{gitmoji} {メッセージ}

   Co-Authored-By: Claude <noreply@anthropic.com>"
   git push
   ```

5. **完了報告**
   - コミットハッシュを表示
   - プッシュ先を表示

## 注意事項

- 機密情報（.env, credentials など）がステージングされていないか確認
- 大きなバイナリファイルがないか確認
- コミットする前にユーザーに確認を取る
