---
name: kaggle:init
description: テンプレートリポジトリのセットアップ。コンペ名の記載、docs/official の作成、環境確認を対話的に行う。
argument-hint: [コンペティション名またはURL（省略可）]
disable-model-invocation: true
allowed-tools: Bash, Read, Write, Edit, Glob, Grep
---

# テンプレートリポジトリを初期化する

テンプレートリポジトリをクローンした直後に実行するセットアップスキル。
コンペティション固有の情報を記載し、環境が正しくセットアップされているかを確認する。

## セットアップチェックリスト

| # | 項目 | 確認方法 |
|---|------|---------|
| 1 | コンペ名がドキュメント・アプリに反映済み | README.md のタイトルがデフォルト（`Competition Name`）でないこと |
| 2 | `uv sync` が実行済み | `.venv/` ディレクトリが存在すること |
| 3 | `input/` にデータがダウンロード済み | `input/` に `.gitkeep` 以外のファイルがあること |
| 4 | `docs/official/overview.md` が記入済み | テンプレートのプレースホルダーでないこと |
| 5 | `docs/official/data.md` が記入済み | テンプレートのプレースホルダーでないこと |
| 6 | Validation Strategy が記載済み | README.md の該当セクションがプレースホルダーでないこと |
| 7 | `app/config.py` の `COMPETITION_ID` が設定済み | デフォルト値でないこと |

## フェーズ 1: 現在の状態を診断

1. 上記チェックリストの各項目を自動的に確認する:
   - `README.md` の1行目を Read し、`Competition Name` のままか確認
   - `.venv/` の存在を Bash で確認
   - `input/` の内容を Glob で確認
   - `docs/official/overview.md` の内容を Read し、プレースホルダー（`- **Competition Name**:` が空）か確認
   - `docs/official/data.md` の内容を Read し、プレースホルダーか確認
   - `README.md` の Validation Strategy セクションがプレースホルダーか確認

2. 結果をサマリーとして表示:
   ```
   セットアップ状況:
   ✅ uv sync — 完了
   ❌ コンペ名の反映 — 未完了
   ❌ input/ データ — 未完了
   ❌ docs/official/overview.md — 未完了
   ❌ docs/official/data.md — 未完了
   ❌ Validation Strategy — 未完了
   ```

## フェーズ 2: 未完了項目の実行

未完了の項目を順番に対話的に進める。完了済みの項目はスキップする。
ユーザーが「後でやる」と言った項目もスキップする。

### 2-1. コンペティション情報の収集と反映

1. **情報収集**: $ARGUMENTS または質問でコンペティション情報を取得
   - コンペティション名（正式名称）
   - コンペ略称（サイドバー表示用、短い英語名）
   - URL
   - 期間
   - ホスト

2. **以下の箇所にコンペ名を反映する**:

   | ファイル | 変更箇所 | 変更内容 |
   |---------|---------|---------|
   | `README.md` | 1行目 | `# Competition Name` → `# {正式名称}` |
   | `pyproject.toml` | `name` | `kaggle-template` → `kaggle-{略称}` |
   | `app/main.py` | FastAPI `title` | `Kaggle Competition Dashboard` → `{略称} Dashboard` |
   | `app/templates/base.html` | サイドバー Brand | `Kaggle` → `{略称}` |
   | `app/templates/base.html` | フッター | `Kaggle Competition Dashboard` → `{略称} Dashboard` |
   | `app/templates/index.html` | ヒーロータイトル | `Kaggle Dashboard` → `{略称} Dashboard` |
   | `CLAUDE.md` | wandb project | `kaggle-competition` → `kaggle-{略称}` |
   | `app/config.py` | `COMPETITION_ID` | `"titanic"` → `"{competition-slug}"` |

### 2-2. 環境セットアップ

1. **uv sync の確認**
   - `.venv/` が存在しなければ `uv sync` の実行を案内
   - 実行するかユーザーに確認し、承認があれば実行

2. **input/ データの確認**
   - `input/` に `.gitkeep` 以外のファイルがなければ、ダウンロード方法を案内:
     ```
     kaggle competitions download -c {competition-slug} -p input/
     unzip input/{competition-slug}.zip -d input/
     ```
   - 手動でデータを配置する場合はパスを案内

### 2-3. docs/official/ の作成

#### overview.md

1. ユーザーに情報ソースを確認:
   - 「Kaggle のコンペページの内容を貼り付けてもらえますか？（Overview, Evaluation, Timeline 等）」
   - または URL を提供してもらう

2. 提供された情報を `docs/official/overview.md` のフォーマットに整形:
   - Competition（名前、URL、期間、ホスト）
   - Evaluation（指標、計算式）
   - Rules
   - Notes

#### data.md

1. `input/` 配下のファイル構成を Glob で確認
2. CSV ファイルがあれば先頭行を Read してカラム一覧を取得
3. ユーザーに Kaggle Data ページの説明を確認
4. `docs/official/data.md` のフォーマットに整形:
   - Files テーブル
   - Columns テーブル（各カラムの型・説明）
   - Notes

### 2-4. Validation Strategy

1. データの特性（件数、ターゲットの分布、時系列かどうか等）を確認
2. ユーザーと議論しながら分割戦略を決定
3. `README.md` の Validation Strategy セクションに記載

## フェーズ 3: 完了チェック

全チェックリスト項目を再確認し、結果を表示する。

**全て完了の場合**:
```
🎉 セットアップが完了しました！

次のステップ:
1. `/new-experiment` で最初の実験を設計・作成する
2. `run_mode=debug` でパイプラインの動作確認
3. `run_mode=fold0` で性能確認
```

**未完了がある場合**:
```
⚠️ 以下の項目が未完了です:

❌ input/ データ — `kaggle competitions download -c xxx -p input/` を実行してください
❌ Validation Strategy — データを確認してから記載してください

準備ができたら再度 `/init` を実行してください。
```
