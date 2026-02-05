---
name: kaggle:record-experiment-result
description: 実験結果を README と docs/insights に記録する。CV/LB スコアと知見を保存。
argument-hint: [exp-name] [cv] [lb]
disable-model-invocation: true
allowed-tools: Read, Edit, Write, Bash
---

# 実験結果を記録

実験の結果（CV, LB スコア）と知見を記録する。

## 手順

1. **情報を収集**
   - $ARGUMENTS から実験名、CV、LB を取得
   - 不足している情報があればユーザーに確認:
     - 実験名（例: exp001-baseline）
     - CV スコア（例: 0.85）
     - LB スコア（例: 0.83、未提出なら "-"）
     - 簡潔な説明（1行）
     - 知見（何を試したか、結果、考察、次に試すべきこと）

2. **README.md の Experiments テーブルを更新**
   - 該当する実験の行を探す
   - CV, LB, Description を更新

3. **README.md の Experiment Tree を更新**
   - mermaid グラフに新しい実験を追加
   - 親となる実験（派生元）を確認してエッジを追加

4. **docs/insights/ に知見ファイルを作成**
   - ファイル名: `YYYY-MM-DD_{exp-name}.md`
   - 内容:
     ```markdown
     # {exp-name}

     ## 概要
     - CV: {cv}
     - LB: {lb}

     ## 試したこと
     {内容}

     ## 結果
     {内容}

     ## 考察
     {内容}

     ## 次に試すべきこと
     {内容}
     ```

5. **完了報告**
   - 更新したファイルの一覧を表示
