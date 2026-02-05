---
name: kaggle:create-experiment
description: 新しい実験ディレクトリを作成する。exp000-sample をコピーして番号を自動採番。
argument-hint: [subtitle]
disable-model-invocation: true
allowed-tools: Bash, Read, Write, Glob, Edit
---

# 新しい実験を作成

$ARGUMENTS をサブタイトルとして新しい実験ディレクトリを作成する。

## 手順

1. **既存の実験番号を取得**
   - `src/exp*/` を Glob で検索
   - 最大の番号を特定（exp000, exp001 など）

2. **新しい実験ディレクトリを作成**
   - 次の番号を決定（最大番号 + 1）
   - `src/exp{番号:03d}-{subtitle}/` を作成
   - `src/exp000-sample/` の内容をコピー:
     - `train.py`
     - `model.py`
     - `data.py`
     - `config/config.yaml`

3. **config.yaml を更新**
   - `exp_name` を新しい実験名に変更

4. **README.md を更新**
   - Experiments テーブルに新しい行を追加:
     ```
     | exp{番号} | {subtitle} | - | - | 説明を追加してください |
     ```

5. **完了報告**
   - 作成したディレクトリパスを表示
   - 次のステップ（コードの編集、学習の実行など）を案内
