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

## フェーズ 2: Kaggle Dataset メタデータ準備

1. **既存メタデータの確認**
   - `src/{exp_name}/output/{run_name}/dataset-metadata.json` が存在するか確認
   - 存在する場合はその内容を表示し、更新するか確認

2. **メタデータ作成（存在しない場合）**
   - ユーザーに以下を確認:
     - Kaggle ユーザー名（既存メタデータがあればそこから取得）
     - コンペティションスラグ（`docs/competition-profile.yaml` の `competition.slug` を既定値として提示）
   - slug を決定: `{kaggle_user}/{comp_slug}-{exp_name_kebab}`
     - **注意**: Kaggle の dataset slug に使えるのは英数字とハイフンのみ。実験名のアンダースコアはハイフンに変換する（例: `exp001_baseline` → `exp001-baseline`）
   - `dataset-metadata.json` を作成:
     ```json
     {
       "title": "{comp_slug} {exp_name}",
       "id": "{kaggle_user}/{comp_slug}-{exp_name_kebab}",
       "licenses": [{"name": "CC0-1.0"}]
     }
     ```
   - ライセンスはデフォルト CC0-1.0 だが、チーム戦略上問題ないかユーザーに確認する（`kaggle datasets create` のデフォルトは非公開 Dataset）

3. **ユーザーに確認**
   - メタデータの内容を表示
   - slug が正しいか確認
   - 承認を得てから次のフェーズに進む
   - **注意**: `dataset-metadata.json` は gitignore 対象の `output/{run_name}/` 配下に置かれるため、再学習で上書き・消失し得る。作成した slug は実験 README.md にも記録しておく

## フェーズ 3: アップロード実行

1. **既存 Dataset の確認**
   - `kaggle datasets status {id}` で既に Dataset が存在するか確認

2. **アップロード**
   - **初回**: `kaggle datasets create -p src/{exp_name}/output/{run_name}/`
   - **更新**: `kaggle datasets version -p src/{exp_name}/output/{run_name}/ -m "{message}"`
     - message はユーザーに確認（例: "fold0 学習完了", "全 fold 追加"）

3. **結果確認**
   - アップロードが成功したか確認
   - エラーがあれば原因を説明し対処法を案内

## フェーズ 4: 完了報告

- アップロードした Dataset の情報:
  - slug: `{kaggle_user}/{comp_slug}-{exp_name_kebab}`
  - Kaggle Notebook 上のマウントパス: 通常 `/kaggle/input/{dataset-slug}/`（**Add Data 後に Notebook のサイドバーで実際のパスを必ず確認する**。Kaggle の UI 更新でパス形式が変わることがある）
- アップロード内容（fold 数、チェックポイントファイル一覧）
- Notebook から参照する際のパス例
