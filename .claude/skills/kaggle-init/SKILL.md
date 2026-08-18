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
| 1 | コンペティションタイプが選択済み | `docs/competition-profile.yaml` の `competition.type` が意図したタイプであること（SSOT。EXP_SUMMARY.md の記載は表示用の複製） |
| 2 | コンペ名がドキュメント・アプリに反映済み | README.md のタイトルがデフォルト（`Competition Name`）でないこと |
| 3 | `uv sync` が実行済み | `.venv/` ディレクトリが存在すること |
| 4 | `input/` にデータがダウンロード済み | `input/` に `.gitkeep` 以外のファイルがあること |
| 5 | `docs/official/overview.md` が記入済み | テンプレートのプレースホルダーでないこと |
| 6 | `docs/official/data.md` が記入済み | テンプレートのプレースホルダーでないこと |
| 7 | Validation Strategy が記載済み（supervised のみ） | `supervised` タイプの場合、EXP_SUMMARY.md の該当セクションがプレースホルダーでないこと |
| 8 | `docs/competition-profile.yaml` が設定済み | `competition.slug` と `metric.name` / `metric.mode` が空・デフォルトでないこと |
| 9 | 実験 config の wandb project が設定済み | `src/exp000_sample/config/config.yaml` の `wandb.project` が `kaggle-competition` のままでないこと（`metric` はサンプル動作用に `loss`/`min` のままでよい） |
| 10 | 実験用 extra 依存がインストール済み | `uv pip list` に torch（`--extra torch`）または lightgbm 等（`--extra tabular`）があること。`src/utils/cv.py` 等は scikit-learn に依存するため、コア依存のみでは実験を実行できない |
| 11 | `workflow` が設定済み | `docs/competition-profile.yaml` の `workflow` が全キー埋まっていること（2-A で対話的に確認する） |
| 12 | per-competition ドキュメントがテンプレート状態 or 記入済み | `docs/guardrails.md` 等（1 行目が `<!-- lifecycle: per-competition -->` のファイル）に前のコンペの内容が残っていないこと |

## フェーズ 1: 現在の状態を診断

1. 上記チェックリストの各項目を自動的に確認する:
   - `docs/competition-profile.yaml` の `competition.type` を確認（SSOT。`EXP_SUMMARY.md` の `Competition Type:` は表示用の複製）
   - `README.md` の1行目を Read し、`Competition Name` のままか確認
   - `.venv/` の存在を Bash で確認
   - `input/` の内容を Glob で確認
   - `docs/official/overview.md` の内容を Read し、プレースホルダー（`- **コンペ名**:` が空）か確認
   - `docs/official/data.md` の内容を Read し、プレースホルダーか確認
   - `docs/competition-profile.yaml` を Read し、`competition.slug` / `metric.name` が設定済みか確認
   - `EXP_SUMMARY.md` の Validation Strategy セクションがプレースホルダーか確認（`supervised` タイプのみ）
   - `docs/competition-profile.yaml` の `workflow` が全キー埋まっているか確認
   - `head -1 docs/*.md` で lifecycle マーカーを確認し、`per-competition` のファイルに前のコンペの内容が残っていないか確認（残っていれば 2-1 の 5 で扱う）

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

2. 選択されたタイプを記録する:
   - **`docs/competition-profile.yaml` の `competition.type` に書き込む（これが SSOT。他のスキルはここを読む）**
   - あわせて `EXP_SUMMARY.md` の先頭付近にも表示用の複製として記載:
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

### 2-A. 運用の合意（workflow）の設定

**コンペの中で口頭指示として蓄積される「働き方」を、最初に機械可読な形で置く。**
ここを飛ばすと合意がエージェントの memory にしか残らず、セッションが変わるたびに失われる。

`docs/competition-profile.yaml` の `workflow` をユーザーに 1 問ずつ確認して埋める。
既定値をそのまま採るなら「既定でよい」と答えてもらう。各項目の理由は
`docs/ai-agent-guidelines.md` の「運用の合意」に書いてある（そこも併せて提示する）。

1. `default_run_mode` — 既定 `fold0`（有望な run だけを明示指示で full に昇格）/ `full`
2. `submission_by` — 既定 `user`（エージェントは提出せず notebook の commit までで止める）/ `agent`
3. `branching` — 既定 `main-only` / `feature-branches`
4. `concurrent_sessions` — 既定 `true`（複数セッションが同じ作業ディレクトリを共有する）
5. `remote_training` — 既定 `none` / `herdr`（運用は `docs/remote-training-ops.md`）
6. `max_runs_per_exp` — 既定 `8`（超過は `/kaggle:review-strategy` が分割を提案する）

- `concurrent_sessions` を `false` にした場合は、`.claude/settings.json` の git 系ガード
  （`permissions.deny` の `git add -A` / `git commit -a` / `git stash` / `git reset --hard` /
  `git checkout --` と、`.claude/hooks/guard.py` の同等の git 規則）を
  外してよいことを案内する
- `submission_by` を `agent` にした場合は、同じく提出のガードを外してよいことを案内する
- **`metric.noise` は null のまま置く**。最初のベースラインが完走した後に
  「同一設定・seed のみ変更した run」で実測して埋める、と案内する
  （`/kaggle:record-result` が誘導する。`docs/experiment-methodology.md` の「判定の資格」）

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
     deadline: {最終提出締切 YYYY-MM-DD。Overview のタイムラインから取得}
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

5. **lifecycle マーカーでリセット対象を決める**（ファイル名をハードコードしない）:

   ```bash
   head -1 docs/*.md docs/competition-profile.yaml | grep -B1 "lifecycle:"
   ```

   - **`<!-- lifecycle: invariant -->` のファイルは編集しない。** 前のコンペで得た
     コンペ非依存の知見が入っているのが正しい状態（消すと蓄積がゼロに戻る）
   - **`<!-- lifecycle: per-competition -->` のファイルに前のコンペの内容が残っていたら、
     テンプレート状態へのリセットをユーザーに確認する**（各セクションを「（まだなし）」や
     見出しだけの骨格に戻す）
   - ⚠ **リセットの前に必ず問う**: 「この中に、汎用化して `docs/experiment-methodology.md`
     （invariant）へ移すべき節はありませんか？」。移し忘れるとそのまま失われる
     （実際にあった事故: 汎用の実験作法が per-competition 層に埋もれ、リセットで消えかけた）。
     移す判定は `/kaggle:harvest-template` の 4 分類と同じ基準を使う
   - マーカーが無いファイルを見つけたら、どちらの層かをユーザーに確認して 1 行目に付ける

6. **ガイドの掃除**: `docs/guides/` に前のコンペのガイドが残っていれば削除する（`README.md` と `sample-guide/` は残す）。`docs/insights/` の前コンペ分も同様に確認する（汎用知見の移送を先に問う）。

### 2-2. 環境セットアップ

1. **uv sync の確認**
   - `.venv/` が存在しなければ `uv sync` の実行を案内
   - **実験に使うモデル系統に応じて extra も同時に確認する**: PyTorch 系なら `uv sync --extra torch`、GBDT 系なら `uv sync --extra tabular`（`src/utils/cv.py` 等が scikit-learn に依存するため、コア依存のみでは実験を実行できない）
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

3. **選定方針（selection）の確認**
   - `docs/official/overview.md` から public LB に使われる test の割合を確認（記載があれば `selection.public_test_ratio` に記録）
   - `selection.policy` はデフォルト `cv`（Trust your CV）のままを推奨。public test が十分大きい等の理由でユーザーが `lb` / `hybrid` を選ぶ場合のみ変更する

   ```yaml
   selection:
     policy: {cv|lb|hybrid}
     public_test_ratio: {数値 or null}
   ```

4. **実験 config への反映**
   - `src/exp000_sample/config/config.yaml` の `metric` は**書き換えない**（サンプルはダミー損失を記録するため `loss`/`min` が正。実コンペの metric に変えると「metric 名で loss 値を記録する」半壊状態になる）。新実験を作成する際に `/kaggle:new-experiment` のチェックリストで profile と揃える
   - CLAUDE.md や docs/wandb-spec.md は置換しない（`{評価指標名}` は profile の `metric.name` を指す設計）

5. **確認**
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
