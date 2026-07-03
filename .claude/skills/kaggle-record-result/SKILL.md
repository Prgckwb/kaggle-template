---
name: kaggle:record-result
description: 実験結果を対話的に確認・記録する。CV/LB スコア、考察、知見を README と docs/insights に保存。
argument-hint: [実験名（例: exp001_baseline）]
disable-model-invocation: true
allowed-tools: Bash, Read, Write, Edit, Glob
---

# 実験結果を確認・記録する

このスキルはユーザーと対話しながら実験結果を確認し、記録する。
機械的に記録するのではなく、ユーザーから学びを引き出す対話を行う。

## best run の決定ルール

**必ず先に `docs/competition-profile.yaml` を Read し、`metric.mode` と `selection.policy` を確認すること。**

- 「最良」の方向は `metric.mode` に従う（`max` なら最大、`min`（RMSE 等）なら最小が best）
- best の判定基準は `selection.policy` に従う:
  - `cv`（デフォルト）: **最良 CV の run** が best。public LB はノイジーな参考値として扱う
  - `lb`: 最良 public LB の run が best（LB が未提出の run しかない場合は CV で判定）
  - `hybrid`: CV best と LB best の両方を提示し、ユーザーに判断を委ねる
- **CV best と LB best の run が食い違う場合は、policy に関わらず必ず両方を提示して警告する**（CV-LB 乖離のサイン。`docs/submissions.md` の履歴で相関を確認し、必要なら `kaggle-analyst` での分析を提案する）

EXP_SUMMARY.md の Experiments テーブルには大実験の best run のスコアを記載する。

## フェーズ 1: 実験の特定と状況確認

1. **対象実験を特定する**
   - $ARGUMENTS があればその実験名を使用
   - なければ `src/exp*/` を Glob で検索し、ユーザーに選択肢を提示
   - 対象実験の README.md を Read して目的・仮説を確認

2. **対象 run を特定する**
   - `src/{exp-name}/config/run*.yaml` を Glob で検索し、小実験の一覧を把握
   - `config/config.yaml` の `run_name` も確認（ベース run）
   - ユーザーに「どの run の結果ですか？」と確認
   - 複数 run がある場合は一覧を提示して選択してもらう

3. **現在の実験状況を確認する**
   - 対象 run の config を Read
   - `src/{exp-name}/output/{run_name}/` 配下に学習済みの出力があるか確認
   - EXP_SUMMARY.md の Experiments テーブルで既存のスコアを確認

## フェーズ 2: スコアの収集（ローカルログ優先）

**ユーザーに聞く前に、まず機械可読なログから自動取得する:**

1. **CV スコアの自動取得**
   - `src/{exp-name}/logs/{run_name}/run_summary.json` を Read し、`cv_score`・`folds`（fold ごとの best）・`metric_name`・`run_mode` を取得
   - `fold{N}_metrics.csv` があれば fold ごとの推移も確認できる
   - 取得できた場合: 「run_summary.json によると CV は {cv_score}（{metric_name}）ですね。この値で記録しますか？」と**確認だけ**行う
   - ログが存在しない・値が欠けている場合のみ「CV スコアはいくつでしたか？」と質問する

2. **LB スコア**
   - 「Kaggle に submit しましたか？LB スコアはいくつでしたか？」
   - Kaggle MCP が利用可能なら submission 一覧からの取得を試みてもよい
   - `uv run python tools/check_submission.py` でも最新提出のステータス・public LB を取得できる（読み取り専用）
   - 未提出の場合は `-` として記録し、「後で submit したら教えてください、更新します」と伝える
   - **提出があった場合は提出日・提出ファイル名・提出理由も確認する**（4-3 で `docs/submissions.md` に追記するため）

3. **Split 方法**
   - README.md にすでに記載があればそれを確認
   - なければ質問する

## フェーズ 3: 考察のヒアリング（最重要）

ユーザーから以下を引き出す。答えが薄い場合は掘り下げる質問をする:

1. **結果の評価**
   - 「仮説は正しかったですか？結果をどう評価しますか？」
   - 仮説と結果のギャップがあれば、その理由を一緒に考える

2. **学んだこと**
   - 「この実験から何がわかりましたか？」
   - 「予想外だったことはありますか？」

3. **次のアクション**
   - 「この結果を踏まえて、次に何を試したいですか？」
   - ただし、具体的な次の実験の設計には踏み込まない（それは `kaggle:new-experiment` の役割）

## フェーズ 4: 記録の実行

### 4-1. 実験 README.md の更新

`src/{exp-name}/README.md` を更新する:

- **結果テーブル**（大実験全体の best スコアを記載）:
```markdown
| Metric | Value |
|--------|-------|
| Split  | {split方法} |
| CV     | {cv_score} |
| LB     | {lb_score} |
```

- **Runs テーブル**の該当行を更新:
```markdown
| Run | Key Change | CV | LB |
|-----|-----------|----|----|
| run000-base | ベースライン | {cv} | {lb} |
| run001-xxx | XXX | {cv} | {lb} |
```

- **考察**セクションを記述

各 Fold のスコアが判明している場合は追記:
```markdown
| Fold | Score |
|------|-------|
| 0    | x.xxx |
| ...  | ...   |
```

### 4-2. EXP_SUMMARY.md の更新

1. **Experiments テーブル**: 該当行の Split, CV, LB を更新（大実験の best run のスコアを記載。判定は「best run の決定ルール」= profile の `selection.policy` と `metric.mode` に従う）
2. **Experiment Tree**: ノードにスコアを追加し、クラスを更新
   - スコアが入ったら `wip` → `good`（青）に変更
   - 全実験中の best（`selection.policy` に従って判定）なら `best`（緑）に変更
   - 他の実験が `best` → `good` に降格する必要があるかも確認
   - 行き詰まり検出でステータスが `dead-end` になった場合は `dead`（赤）に変更

   ノードのフォーマット:
   ```
   X["exp{番号}_{subtitle}<br/>{split} | CV: {cv} | LB: {lb}"]
   ```

### 4-3. docs/submissions.md への追記（提出があった場合）

LB スコアが得られた提出については、`docs/submissions.md` の Submissions テーブルに 1 行追記する:

```markdown
| {提出日} | {exp_name} / {run_name} | {submission ファイル名} | {cv} | {lb} | {提出理由・メモ} |
```

- 初回追記時はプレースホルダー行（「まだ提出なし」）を削除する
- 過去の提出の記録漏れに気づいた場合も、この機会に追記を提案する

### 4-4. docs/insights/ に知見ファイルを作成

ファイル名: `YYYY-MM-DD_exp{番号}_{subtitle}.md`（今日の日付。CLAUDE.md の命名規則と同じアンダースコア区切り）

```markdown
# exp{番号}_{subtitle}

## 概要

- **目的**: （実験の目的）
- **比較変数**: （何を変えたか）
- **CV**: {cv}
- **LB**: {lb}

## 試したこと

（実験の手法の要約）

## 結果

（定量的な結果と定性的な評価）

## 考察

（ユーザーとの議論から得られた洞察）

## 実装上の知見

（コードレベルで他の実験に役立つ発見。なければ省略。）

## 次に試すべきこと

（ユーザーが挙げたアイデア）
```

## フェーズ 5: 行き詰まり検出（Dead-End Detection）

記録完了後、この実験が行き詰まりに達していないかを自動検出する。

### 5-1. 停滞チェック

対象実験の Runs テーブル（README.md）を確認し、直近 3 run の CV スコアを比較する。
**改善の方向と基準は `docs/competition-profile.yaml` の `metric.mode` と `meaningful_delta` に従う**（`min` 指標では減少が改善であることに注意）:

1. CV スコアが数値として記録されている直近 3 run を取得（Runs テーブルは実行順に追記される前提。順序が怪しい場合はユーザーに確認する）
2. 最新 run の CV と 3 つ前の run の CV の「改善量」（mode を考慮した符号）を計算
3. **停滞判定の基準値**は次の優先順位で決める:
   1. `meaningful_delta`（profile に設定済みの場合）
   2. 未設定なら **fold 間ばらつきから自動推定する**: `src/{exp-name}/logs/{run_name}/run_summary.json` の `folds` から各 fold の best スコアの標準偏差 `std` を計算し、`ノイズフロア = std / sqrt(n_folds)` を基準値とする（CV 平均の標準誤差。これ未満の改善は fold 間ノイズと区別できない）。この値を profile の `meaningful_delta` に記録することをユーザーに提案する
   3. run_summary.json も取れなければ、そのコンペのスコアスケールで有意な差かをユーザーに確認する
4. **改善量が基準値未満の場合**、以下の警告を表示する:

```
⚠ 行き詰まり検出: この実験の直近 3 run の CV 改善量は {差分} です（meaningful_delta = {値} 未満）。
この実験は収穫逓減（diminishing returns）に達している可能性があります。

推奨アクション:
- この実験のステータスを「dead-end」に変更し、新しい大実験で根本的に異なるアプローチを検討する
- あるいは、この実験内でまだ試していない大きな変更がある場合は続行する

実験ステータスを「dead-end」に変更しますか？（yes/no）
```

### 5-2. 実験ステータスの記録

ユーザーの回答に応じて、実験 README.md のメタ情報を更新する:

- ユーザーが `dead-end` を承認した場合:
  - README.md の結果テーブルに `Status` 行を追加:
    ```markdown
    | Metric | Value |
    |--------|-------|
    | Status | dead-end |
    | Split  | {split方法} |
    | CV     | {cv_score} |
    | LB     | {lb_score} |
    ```
  - EXP_SUMMARY.md の Experiment Tree で該当ノードのクラスを `dead` に変更
  - 「`kaggle:review-strategy` で全体戦略を見直すことをお勧めします」と案内

- ユーザーが続行を選択した場合:
  - ステータスは変更しない
  - ただし警告は記録として残す

### 5-3. run が 3 未満の場合

直近 3 run の CV スコアが揃わない場合（run 数が不足、または CV が未記録）は、
行き詰まり検出はスキップし、その旨を報告する。

## フェーズ 6: 完了報告

- 更新・作成したファイルの一覧を表示
- スコアのサマリーを表示
- Experiment Tree の現在の状態を簡潔に説明（どの実験が best か等）
- 行き詰まり検出の結果（該当した場合）
