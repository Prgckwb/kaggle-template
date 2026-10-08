---
name: kaggle:upload-checkpoints
description: ユーザーが学習済み重みの Kaggle Dataset 化を頼んだときだけ使う（「ckpt をアップロードして」「重みを Dataset にして」など）。各 fold の best ckpt を軽量化して、Kaggle Dataset を新規作成またはバージョン更新する。
argument-hint: [実験名 run名（例: exp001_baseline run000-base）]
allowed-tools: Bash, Read, Glob, Grep
---

# チェックポイントを Kaggle Dataset にアップロードする

実体は `tools/upload_checkpoints.py`（スタンドアロンの CLI）で、このスキルはヒアリングと実行のラッパー。CLI がやることは次のとおり。

- 各 fold の best ckpt を選ぶ。選び方は `src/utils/checkpoint.select_best_ckpt` で、ckpt 名のスコアと profile の `metric.mode` を使う
- 選んだ ckpt を `export_slim_checkpoint` で推論に必要なキーだけに軽量化し、ステージング用ディレクトリに `fold{k}/` の構造で並べる
- そのステージング用ディレクトリをアップロードする（optimizer の状態や OOF などはアップロードしない）
- `dataset-metadata.json` の有無で、新規作成かバージョン更新かを自動で判定する

Notebook 側のマウントパスと読み込み方は `docs/training-conventions.md`（「実行環境」と「提出 notebook の規約」）が正本。

## フェーズ 1: 対象の特定

1. `$ARGUMENTS` から実験名と run 名を取る。無ければ `src/exp*/output/*/` を Glob して候補を出し、ユーザーに選んでもらう
2. `src/{exp}/output/{run}/fold*/` の ckpt を `ls -lh` で示す
3. `src/{exp}/logs/{run}/run_summary.json` を読み、何 fold 走った run か（`n_folds_run`）とスコアを示す
   - fold0 だけの run なら、Dataset に入るのも fold0 だけだと伝える
4. `-debug` サフィックスの付いた出力は候補にしない

## フェーズ 2: 実行内容の確認

- **初回**（ステージング先に `dataset-metadata.json` が無い場合）
  - Kaggle ユーザー名（`--user`）を確認する
  - slug は profile の `competition.slug` と実験名から CLI が生成する。英数字とハイフンのみで、`_` は `-` に変わる
  - 非公開・CC0-1.0 で作られる。チーム戦略上問題ないか確認する
- **2 回目以降**: バージョン更新のメッセージ（`-m`）を確認する（例:「全 fold 追加」）
- 実行するコマンドを提示し、**承認を得てから**実行する
  - Dataset の作成と更新は外部への公開操作にあたる

```bash
# 初回
uv run python -m tools.upload_checkpoints {exp} {run} --user {kaggle_user}
# 2 回目以降
uv run python -m tools.upload_checkpoints {exp} {run} -m "{message}"
```

## フェーズ 3: 実行と完了報告

- CLI の出力（アップロードしたファイル、Dataset の id、想定されるマウントパス）をそのまま示す。失敗した場合は原因と対処を説明する
- Dataset の id（`{user}/{slug}`）を実験の README に記録する
  - ステージング先と metadata は gitignore された `output/` の配下にあり、再学習で消える可能性があるため
- 次の一手として `/kaggle:create-inference-notebook` を案内する
