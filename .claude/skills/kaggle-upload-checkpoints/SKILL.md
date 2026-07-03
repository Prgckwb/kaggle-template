---
name: kaggle:upload-checkpoints
description: 実験の output ディレクトリを Kaggle Dataset としてアップロードする。
argument-hint: [実験名（例: exp001_baseline）]
disable-model-invocation: true
allowed-tools: Bash, Read, Write, Edit, Glob, Grep
---

# チェックポイントを Kaggle Dataset にアップロードする

実験の output ディレクトリをそのまま Kaggle Dataset としてアップロードする。
output ディレクトリの構造（`fold0/`, `fold1/`, ...）がそのまま Kaggle 上に反映される。

実体は `tools/upload_checkpoints.py`（Claude Code なしでも直接使えるスタンドアロン CLI）。
このスキルはヒアリング + CLI 実行のラッパー。

## フェーズ 1: 対象実験の特定と状況確認

1. **対象実験を特定する**
   - $ARGUMENTS があればその実験名を使用
   - なければ `src/exp*/` を Glob で検索し、ユーザーに選択肢を提示

2. **対象 run を特定する**
   - `src/{exp_name}/config/config.yaml` の `run_name` を確認
   - `src/{exp_name}/config/run*.yaml` を Glob で小実験の一覧を把握
   - ユーザーに「どの run をアップロードしますか？」と確認

3. **チェックポイントを確認する**
   - `src/{exp_name}/output/{run_name}/` 配下を `ls -lhR` で一覧表示
   - 各 fold のチェックポイントファイル名とサイズを表示
   - アップロード対象を確認（通常は全 fold）

## フェーズ 2: アップロード方法の確認

1. **既存メタデータの確認**
   - `src/{exp_name}/output/{run_name}/dataset-metadata.json` が存在するか確認
   - 存在する場合はその内容（Dataset の id）を表示し、バージョン更新でよいか確認
   - 存在しない場合は初回作成。ユーザーに Kaggle ユーザー名を確認する
     - dataset slug は CLI が profile の `competition.slug` + 実験名から自動生成する
       （英数字とハイフンのみ。アンダースコアはハイフンに変換される）
     - ライセンスはデフォルト CC0-1.0（非公開 Dataset として作成される）。チーム戦略上問題ないか確認する

2. **ユーザーに確認**
   - 実行する CLI コマンドを提示し、承認を得てから次のフェーズに進む
   - **注意**: `dataset-metadata.json` は gitignore 対象の `output/{run_name}/` 配下に置かれるため、再学習で上書き・消失し得る。作成した slug は実験 README.md にも記録しておく

## フェーズ 3: アップロード実行

`tools/upload_checkpoints.py` を実行する:

```bash
# 初回（Dataset 新規作成）
uv run python tools/upload_checkpoints.py {exp_name} {run_name} --user {kaggle_user} --new

# 2回目以降（バージョン更新。message はユーザーに確認。例: "fold0 学習完了", "全 fold 追加"）
uv run python tools/upload_checkpoints.py {exp_name} {run_name} -m "{message}"
```

- アップロードが成功したか確認
- エラーがあれば原因を説明し対処法を案内

## フェーズ 4: 完了報告

- アップロードした Dataset の情報:
  - slug: `{kaggle_user}/{comp_slug}-{exp_name_kebab}`
  - Kaggle Notebook 上のマウントパス: 通常 `/kaggle/input/{dataset-slug}/`（**Add Data 後に Notebook のサイドバーで実際のパスを必ず確認する**。Kaggle の UI 更新でパス形式が変わることがある）
- アップロード内容（fold 数、チェックポイントファイル一覧）
- Notebook から参照する際のパス例
