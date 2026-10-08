---
name: kaggle:init
description: 新しいコンペを始めるときのセットアップ。competition-profile.yaml・競技指標（src/metric.py）・fold 設計・docs/official を対話で埋め、前コンペの per-competition 層をリセットする。「コンペを始めたい」「テンプレートを初期化」「init して」と言われたら使う。
argument-hint: [コンペティション名またはURL（省略可）]
allowed-tools: Bash, Read, Write, Edit, Glob, Grep
---

# テンプレートを新しいコンペ用に初期化する

コンペ固有値の正本は `docs/competition-profile.yaml`。このスキルが書くのは
profile・`src/metric.py`・`docs/official/`・`EXP_SUMMARY.md` の Validation Strategy と、
README / pyproject の名前だけ。CLAUDE.md・invariant の docs・スキル定義は書き換えない。

## フェーズ 1: 診断

次を確認し、✅/❌ の一覧で提示する。完了済みの項目は以降スキップする。

| # | 項目 | 確認方法 |
|---|------|---------|
| 1 | コンペタイプ | profile の `competition.type` |
| 2 | コンペ情報 | profile の `competition.slug` / `name` / `deadline` が空でない |
| 3 | 競技指標 | profile の `metric.name` / `mode` と、`src/metric.py` の `score()` がそのコンペの指標を実装している |
| 4 | workflow | profile の `workflow` が全キー埋まっている |
| 5 | 依存 | `.venv/` があり、`uv pip list` に torch（`--extra torch`）か lightgbm 等（`--extra tabular`）がある |
| 6 | データ | `input/` に `.gitkeep` 以外がある |
| 7 | docs/official | `overview.md` / `data.md` がプレースホルダーでない |
| 8 | fold 設計（supervised のみ） | `EXP_SUMMARY.md` の Validation Strategy がプレースホルダーでない |
| 9 | 前コンペの残骸 | per-competition 層に前コンペの内容が無い（フェーズ 2-6） |

## フェーズ 2: 未完了項目を順に埋める

ユーザーが「後でやる」と言った項目は飛ばす。

### 2-1. コンペタイプ（最初に決める）

`supervised`（既定・予測コンペ）/ `optimization` / `simulation` を選んでもらい、profile の
`competition.type` に書く。optimization / simulation では 2-5 の fold 設計を飛ばし、
解釈は `docs/competition-types.md` に従う（simulation は `model.py` の代わりに `agent.py`）。

### 2-2. コンペ情報

$ARGUMENTS か質問で取得し、`uv run kaggle competitions list -s <keyword>` で締切・slug を照合する。
profile に書く: `competition.{name, slug, abbreviation, url, deadline}`、`wandb.project: kaggle-{略称の小文字}`。
README.md の 1 行目（`# {正式名称}`）と pyproject.toml の `name`（`kaggle-{略称}`）も変える。
実験 config の wandb project・metric は `${profile:...}` で profile を読むので触らない。

### 2-3. workflow（運用の合意）

profile の `workflow` を 1 問ずつ確認する（既定でよければ「既定でよい」）。各キーの意味と理由は
`docs/ai-agent-guidelines.md` の「運用の合意」を提示する。
`concurrent_sessions` / `submission_by` は `.claude/hooks/guard.py` が profile を直接読むので、
値を変えるだけでガードの有効・無効が切り替わる（settings.json は触らない）。

### 2-4. 環境とデータ

- `.venv/` が無い、または extra が無ければ `uv sync --extra torch`（NN）/ `--extra tabular`（GBDT）を提案し、承認後に実行
- データ: `uv run kaggle competitions download -c {slug} -p input/ && unzip input/{slug}.zip -d input/`
- Kaggle Notebook 上のマウントパスは `docs/training-conventions.md` の「実行環境」節を参照（ここには書かない）

### 2-5. docs/official

- `overview.md`: ユーザーにコンペページ（Overview / Evaluation / Timeline / Code Requirements）を貼ってもらうか URL をもらい、既存テンプレート構造に整形する
- `data.md`: `input/` のファイル構成と CSV 先頭行からカラム表を作り、Data ページの説明で補う

### 2-6. 競技指標

1. `overview.md` の Evaluation から指標を確認し、ユーザーと決める:
   - `metric.name`: 短い英小文字。**ハイフン禁止**（`macro_f1`。ckpt 名のパースが壊れる）
   - `metric.mode`: `max` / `min`
   - `metric.meaningful_delta`: 分かれば。不明なら `null`
   - `selection.policy`（既定 `cv`）と `selection.public_test_ratio`
   - `metric.noise` は `null` のまま（最初のベースライン後に seed 違いの run で実測する。`/kaggle:record-result` が誘導する）
2. `src/metric.py` の `score(y_true, y_pred) -> float` をその指標で実装する。これが全実験・OOF 再計算・
   アンサンブルが共有する唯一の実装。公式の定義（Evaluation ページ・公開されている metric notebook）と
   小さな手計算例で一致を確認し、ユーザーに提示する
3. 実装上の落とし穴（NaN の扱い・平均の取り方の誤り等）が分かったら `docs/guardrails.md` の「評価関数」に
   **誤実装の罠だけ**書く（正しいコードは metric.py が正本なので写さない）

### 2-7. fold 設計（supervised のみ）

モデリング前に確定する（`docs/training-conventions.md`「バリデーション戦略」）。
データの件数・ターゲット分布・グループ（ユーザー・患者・時系列など）・train/test の分布差を確認し、
ユーザーと議論して決める:

- `cv_strategy`（kfold / stratified / group / stratified_group / timeseries）・`n_folds`・`id_col`・`target_col`・`group_col`・`seed`
- `fold_version: v1`

決定内容と根拠を `EXP_SUMMARY.md` の Validation Strategy に書く。値そのものは最初の実験の config の
`data:` ブロックに入れ、初回実行時に `src/utils/cv.py:load_or_create_folds` が
`data/folds/folds_v1.csv` を作る。**そのファイルをコミットし、以後上書きしない**（変えるなら v2）。

### 2-8. 前コンペの残骸のリセット

1. lifecycle マーカーで対象を決める（ファイル名をハードコードしない）:

   ```bash
   head -1 docs/*.md docs/competition-profile.yaml EXP_SUMMARY.md src/metric.py | grep -B1 "lifecycle:"
   ```

   - `invariant` は触らない（コンペ非依存の蓄積）
   - `per-competition`（`EXP_SUMMARY.md`・`src/metric.py` を含む）に前コンペの内容があれば、
     テンプレート状態の骨格へ戻すことをユーザーに確認する
   - ⚠ **リセットの前に必ず問う**:「汎用化して invariant 層へ移すべき節はありませんか？」。
     判定基準は `docs/README.md` の「知見の routing」表（移し忘れるとそのまま失われる）
   - マーカーが無いファイルは、どちらの層かを確認して 1 行目に付ける
2. 前コンペの `src/exp001*` 以降・`data/folds/*`・`docs/insights/`・`docs/discussion/`・`.cache/` が残っていれば、
   削除をユーザーに確認する（汎用知見の移送を先に問う）

## フェーズ 3: 完了チェック

チェックリストを再確認して表示する。全て完了なら次を案内する:

1. `/kaggle:new-experiment` で最初の実験（確実に動く最小構成のベースライン）を作る
2. `run_mode=debug` → `fold0` の順に動かす
3. ベースライン完走後、seed だけ変えた run で `metric.noise.seed_spread` を測る

未完了があれば、項目ごとに次の一手（コマンド・入力してほしい情報）を示す。
