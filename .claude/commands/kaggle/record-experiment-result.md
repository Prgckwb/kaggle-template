# 実験結果を記録

実験の結果を README.md と docs/insights/ に記録してください。

## 手順

1. ユーザーに以下を質問（$ARGUMENTS で渡されていない場合）:
   - 実験番号（例: `001`）
   - CV スコア
   - LB スコア（未提出の場合は `-`）
   - 実験の概要・結果・考察

2. `README.md` の Experiments テーブルを更新
   - 該当する実験の CV, LB, Description を更新

3. `README.md` の Experiment Tree（mermaid）を確認
   - 親実験からの派生関係があれば矢印を追加
   - スコアをノードに含めることを検討

4. `docs/insights/` に知見ファイルを作成
   - ファイル名: `YYYY-MM-DD_exp{番号}-{subtitle}.md`
   - 内容:
     - 実験の目的
     - 変更内容
     - 結果（CV, LB）
     - 考察
     - 次に試すべきこと

## 引数

$ARGUMENTS に実験番号が渡される場合があります（例: `001`）。

## 完了後

- 更新したファイルの一覧を報告
- git commit を提案（`kaggle:commit-and-push` の使用を案内）
