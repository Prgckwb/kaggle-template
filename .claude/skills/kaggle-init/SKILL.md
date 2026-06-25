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
| 1 | コンペティションタイプが選択済み | `EXP_SUMMARY.md` に `Competition Type: supervised/optimization/simulation` が記載されていること |
| 2 | コンペ名がドキュメント・アプリに反映済み | README.md のタイトルがデフォルト（`Competition Name`）でないこと |
| 3 | `uv sync` が実行済み | `.venv/` ディレクトリが存在すること |
| 4 | `input/` にデータがダウンロード済み | `input/` に `.gitkeep` 以外のファイルがあること |
| 5 | `docs/official/overview.md` が記入済み | テンプレートのプレースホルダーでないこと |
| 6 | `docs/official/data.md` が記入済み | テンプレートのプレースホルダーでないこと |
| 7 | Validation Strategy が記載済み（supervised のみ） | `supervised` タイプの場合、EXP_SUMMARY.md の該当セクションがプレースホルダーでないこと |
| 8 | `app/config.py` の `COMPETITION_ID` が設定済み | デフォルト値でないこと |
| 9 | 評価指標名が CLAUDE.md の wandb テーブルに反映済み | `{評価指標名}` プレースホルダーが実際の指標名に置換されていること |

## フェーズ 1: 現在の状態を診断

1. 上記チェックリストの各項目を自動的に確認する:
   - `EXP_SUMMARY.md` に `Competition Type:` の記載があるか確認
   - `README.md` の1行目を Read し、`Competition Name` のままか確認
   - `.venv/` の存在を Bash で確認
   - `input/` の内容を Glob で確認
   - `docs/official/overview.md` の内容を Read し、プレースホルダー（`- **Competition Name**:` が空）か確認
   - `docs/official/data.md` の内容を Read し、プレースホルダーか確認
   - `EXP_SUMMARY.md` の Validation Strategy セクションがプレースホルダーか確認（`supervised` タイプのみ）

2. 結果をサマリーとして表示:
   ```
   セットアップ状況:
   ❌ コンペティションタイプ — 未選択
   ✅ uv sync — 完了
   ❌ コンペ名の反映 — 未完了
   ❌ input/ データ — 未完了
   ❌ docs/official/overview.md — 未完了
   ❌ docs/official/data.md — 未完了
   ❌ Validation Strategy — 未完了（supervised のみ）
   ```

## フェーズ 2: 未完了項目の実行

未完了の項目を順番に対話的に進める。完了済みの項目はスキップする。
ユーザーが「後でやる」と言った項目もスキップする。

### 2-0. コンペティションタイプの選択

**他の全ステップよりも先に実行する。** タイプによって以降のセットアップ内容が変わるため。

1. ユーザーに質問:
   ```
   コンペティションのタイプを選んでください:
   1. supervised（デフォルト）— 予測コンペ（train/predict/submit CSV）
   2. optimization — 最適化コンペ（スコアがイテレーションで改善、train/test 分割なし）
   3. simulation — エージェント/RL コンペ（ゲームやシステムを制御するエージェント）
   ```

2. 選択されたタイプを `EXP_SUMMARY.md` の先頭付近に記載:
   ```markdown
   **Competition Type**: `supervised` | `optimization` | `simulation`
   ```

3. タイプに応じて以降のステップを適応:
   - **`supervised`**: 既存の動作と同じ（変更なし）
   - **`optimization`**:
     - 2-5 の Validation Strategy はスキップ（fold/CV の概念がないため）
     - 評価指標名は `score` など最適化スコア名を推奨
     - CLAUDE.md の wandb セクションは iteration ベースのログに適応
   - **`simulation`**:
     - 2-5 の Validation Strategy はスキップ（fold/CV の概念がないため）
     - 評価指標名は `reward` などエピソード報酬名を推奨
     - CLAUDE.md の wandb セクションは episode ベースのログに適応
     - 実験テンプレートで `model.py` の代わりに `agent.py` を案内

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

### 2-4. 評価指標名の設定

1. **指標名の確認**
   - `docs/official/overview.md` の Evaluation セクションから評価指標を確認
   - ユーザーに確認: 「メトリクスキー名を決めてください（例: `auc`, `f1`, `accuracy`, `map`, `rmse`）。wandb ログやチェックポイント名に使われます」
   - 短い英小文字の名前を推奨

2. **CLAUDE.md の更新**
   - wandb メトリクスキー名規則テーブルの `{評価指標名}` を実際の指標名に一括置換
   - コードサンプル内の `{評価指標名}` も同様に置換
   - チェックポイントファイル名パターンの `val_{評価指標名}` を置換（例: `val_auc`）
   - `wandb.summary` のキー名も置換

3. **確認**
   - 置換後のテーブルをユーザーに提示して確認を得る

### 2-5. Validation Strategy（supervised タイプのみ）

**注意**: `optimization` / `simulation` タイプではこのステップをスキップする（fold/CV の概念がないため）。

1. データの特性（件数、ターゲットの分布、時系列かどうか等）を確認
2. ユーザーと議論しながら分割戦略を決定
3. `EXP_SUMMARY.md` の Validation Strategy セクションに記載

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
