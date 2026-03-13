---
name: kaggle:run-experiment
description: 実験を debug → 本番 → 推論の順に実行する。
argument-hint: [exp-name]
allowed-tools: Bash, Read, Write, Edit, Glob
---

# 実験を実行

$ARGUMENTS を実験名として、以下の順序で実行する。

## 手順

1. **実験ディレクトリの確認**
   - `src/{exp-name}/` の存在を確認
   - `config/config.yaml` を Read で確認

2. **デバッグモードで実行**
   - `cd src/{exp-name} && uv run python train.py`
   - 出力を確認し、パイプラインが通ることを確認
   - エラーがあれば修正して再実行

3. **本番モードで実行**
   - `cd src/{exp-name} && uv run python train.py debug=false`
   - 学習が完了することを確認

4. **推論を実行**
   - `cd src/{exp-name} && uv run python inference.py`
   - submission ファイルが生成されたことを確認

5. **結果を報告**
   - CV スコア、各 fold のスコアを表示
   - submission ファイルのパスを表示
   - `kaggle:record-experiment-result` での記録を案内
