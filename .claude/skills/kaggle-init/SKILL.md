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
| 8 | `docs/competition-profile.yaml` が設定済み | `competition.slug` と `metric.name` / `metric.mode` が空・デフォルトでないこと |
| 9 | 実験 config の wandb project / metric が設定済み | `src/exp000_sample/config/config.yaml` の `wandb.project` が `kaggle-competition` のままでなく、`metric` が profile と一致すること |

## フェーズ 1: 現在の状態を診断

1. 上記チェックリストの各項目を自動的に確認する:
   - `EXP_SUMMARY.md` に `Competition Type:` の記載があるか確認
   - `README.md` の1行目を Read し、`Competition Name` のままか確認
   - `.venv/` の存在を Bash で確認
   - `input/` の内容を Glob で確認
   - `docs/official/overview.md` の内容を Read し、プレースホルダー（`- **コンペ名**:` が空）か確認
   - `docs/official/data.md` の内容を Read し、プレースホルダーか確認
   - `docs/competition-profile.yaml` を Read し、`competition.slug` / `metric.name` が設定済みか確認
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
     - wandb ログは iteration ベースで解釈する（`docs/competition-types.md` 参照）
   - **`simulation`**:
     - 2-5 の Validation Strategy はスキップ（fold/CV の概念がないため）
     - 評価指標名は `reward` などエピソード報酬名を推奨
     - wandb ログは episode ベースで解釈する（`docs/competition-types.md` 参照）
     - 実験テンプレートで `model.py` の代わりに `agent.py` を案内

### 2-1. コンペティション情報の収集と反映

1. **情報収集**: $ARGUMENTS または質問でコンペティション情報を取得
   - コンペティション名（正式名称）
   - コンペ略称（サイドバー表示用、短い英語名）
   - URL
   - 期間
   - ホスト

2. **`docs/competition-profile.yaml` に反映する**（コンペ固有値の Single Source of Truth）:

   ```yaml
   competition:
     name: "{正式名称}"
     slug: "{competition-slug}"
     abbreviation: "{略称}"
     url: "https://www.kaggle.com/competitions/{competition-slug}"
     type: {2-0 で選択したタイプ}
   wandb:
     project: kaggle-{略称の小文字}
   ```

   ダッシュボード（`app/config.py`）は profile の `competition.slug` を自動で読むため、app 側の変更は不要。

3. **以下の表示箇所にもコンペ名を反映する**:

   | ファイル | 変更箇所 | 変更内容 |
   |---------|---------|---------|
   | `README.md` | 1行目 | `# Competition Name` → `# {正式名称}` |
   | `pyproject.toml` | `name` | `kaggle-template` → `kaggle-{略称}` |
   | `app/main.py` | FastAPI `title` | `Kaggle Competition Dashboard` → `{略称} Dashboard` |
   | `app/templates/base.html` | サイドバー Brand | `Kaggle` → `{略称}` |
   | `app/templates/index.html` | ヒーロータイトル | `Kaggle Dashboard` → `{略称} Dashboard` |
   | `src/exp000_sample/config/config.yaml` | `wandb.project` | `kaggle-competition` → profile の `wandb.project` と同じ値 |

   **注意**: CLAUDE.md・docs/wandb-spec.md・スキル定義はコンペごとに書き換えない（profile を参照する設計）。

4. **ローカルキャッシュの掃除**: 前のコンペの残骸があれば `.cache/` ディレクトリを削除する（gitignore 済みのローカルキャッシュ）。

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

2. 提供された情報を `docs/official/overview.md` の既存テンプレート構造に沿って整形:
   - コンペティション概要（名前、URL、期間、ホスト）
   - タスク定義（タスクの種類、入力、出力、パイプライン概要図）
   - 背景・ドメイン知識
   - 評価指標（指標名、計算方法、最適化の考慮点）
   - 提出形式
   - コード要件（Code Competition かどうか、ランタイム制限等）
   - タイムライン

#### data.md

1. `input/` 配下のファイル構成を Glob で確認
2. CSV ファイルがあれば先頭行を Read してカラム一覧を取得
3. ユーザーに Kaggle Data ページの説明を確認
4. `docs/official/data.md` のフォーマットに整形:
   - Files テーブル
   - Columns テーブル（各カラムの型・説明）
   - Notes

### 2-4. 評価指標の設定

1. **指標名と方向の確認**
   - `docs/official/overview.md` の評価指標セクションから評価指標を確認
   - ユーザーに確認: 「メトリクスキー名を決めてください（例: `auc`, `f1`, `accuracy`, `map`, `rmse`）。wandb ログやチェックポイント名に使われます」（短い英小文字を推奨）
   - **方向も必ず確認**: 大きいほど良い（`max`）か、小さいほど良い（`min`）か
   - 可能なら「意味のある改善幅」（`meaningful_delta`）も確認する。停滞検出や best 判定の基準になる（例: AUC なら 0.001）。不明なら `null` のままでよい

2. **`docs/competition-profile.yaml` の `metric` セクションに記録**

   ```yaml
   metric:
     name: {指標名}
     mode: {max|min}
     meaningful_delta: {数値 or null}
   ```

3. **実験 config への反映**
   - `src/exp000_sample/config/config.yaml` の `metric.name` / `metric.mode` を profile と同じ値に更新
   - CLAUDE.md や docs/wandb-spec.md は置換しない（`{評価指標名}` は profile の `metric.name` を指す設計）

4. **確認**
   - 設定内容をユーザーに提示して確認を得る

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
1. `/kaggle:new-experiment` で最初の実験を設計・作成する
2. `run_mode=debug` でパイプラインの動作確認
3. `run_mode=fold0` で性能確認
```

**未完了がある場合**:
```
⚠️ 以下の項目が未完了です:

❌ input/ データ — `kaggle competitions download -c xxx -p input/` を実行してください
❌ Validation Strategy — データを確認してから記載してください

準備ができたら再度 `/kaggle:init` を実行してください。
```
