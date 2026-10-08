---
name: kaggle:new-experiment
description: 新しい実験（大実験 exp または小実験 run）を対話で設計・作成する。仮説の批判的レビュー、exp/run の判定、ディレクトリと config の作成まで。「次の実験を作りたい」「〜を試したい」「新しい run を追加」と言われたら使う。
argument-hint: [試したいこと（省略可）]
allowed-tools: Bash, Read, Write, Glob, Edit
---

# 新しい実験を設計・作成する

ユーザーと対話しながら進める。各フェーズで確認を取り、一方的に作らない。

- **大実験（exp）**: `src/exp{NNN}_{subtitle}/` を新規作成
- **小実験（run）**: 既存 exp に `config/run{NNN}-{subtitle}.yaml` を追加（親 config から **1 キーだけ**変える）

## フェーズ 1: コンテキスト収集

1. 読む: `EXP_SUMMARY.md`（実験一覧・探索マップ・バックログ）、`docs/guardrails.md`（必ず引き継ぐ）、
   `docs/competition-profile.yaml`（metric・workflow）、`docs/official/`、各 exp の README（Runs）
2. `docs/insights/` は**実装知見だけ**参考にする。「〜は効かない」という結論は引き継がない
   （CLAUDE.md「探索の独立性」）
3. ユーザーに聞く:「何を試したいか」「仮説は何か」「比較する変数は何か」

## フェーズ 2: 批判的レビュー

1. **多様性チェック**: EXP_SUMMARY.md の探索マップと照らし、提案が既存ファミリーの延長なら
   それを明示して意図的か確認する（意図的な深掘りは止めない。無意識の偏りだけを防ぐ）
2. **メリット・リスク・期待値**を中立に整理する。改善幅は profile の `metric.mode` と
   `meaningful_delta` のスケールで表現する
3. **変数の数**: 一度に変える要素が複数なら分割を提案する
4. **対案を 1 つ示す**: ユーザー案と性格の違う案（堅実型なら挑戦型、逆も）を 1 つ添える。
   対案は**問題設定・データ特性・公開情報から作り、失敗履歴からは作らない**
   （`docs/ai-agent-guidelines.md`「分析とアイデアの役割分担」）。採否はユーザーが決める

## フェーズ 3: exp か run か

判定基準は「config で書けるか」ではなく「比較可能性が保てるか」。1 つでも該当したら新 exp:

| トリガー | 理由 |
|---|---|
| backbone / モデル族の変更 | lr 等の再調整が要り 1 変数差分にならない |
| 入力の変更（解像度・系列長・特徴量セット・チャネル構成） | コスト構造とキャッシュが変わる |
| ラベル・ターゲット定義の世代変更 | スコアの土俵が変わる |
| アーキ構成要素の追加・交換 | 早期打ち切りゲート等の較正が流用できない |
| 2 変数以上を同時に変える | 効果を帰属できない（中間 run で分解できるなら分解） |
| fold 定義の変更（`data.fold_version`） | 既存 run と CV を比較できない |
| `train.py` / `model.py` / `data.py` のコード変更が必要 | config 差分で表現できていない |

run に留めてよいのはスカラー 1 個（lr / epochs / seed / dropout / augmentation 強度 1 種 /
実効バッチを保った batch 分割）。**迷ったら新 exp**。
profile の `workflow.max_runs_per_exp` を超える exp に run を足すなら、まず分割を提案する。

決めること:
- exp: 番号（既存最大 + 1、3 桁）、サブタイトル（英語）、Key Change、ベースにする exp
- run: 対象 exp、親（`config` か既存 run）、run 番号（`grep -rnE "run[0-9]{3}" docs src` で予約も確認して最大 + 1）、変えるキー 1 つ

## フェーズ 4: 作成

### 大実験

1. ベースを決める（既存 exp の発展ならその exp、新規なら `src/exp000_sample/`）
2. `src/exp{NNN}_{subtitle}/` にコピーする（`output/` `logs/` は除く）。ファイル構成はベースに縛られない
3. 必ず直す:
   - [ ] `config/config.yaml` の `exp_name` と `run_name: run000-base`
   - [ ] exp000 から作った場合: `make_synthetic.py` を消し、`data:` ブロックを config 内コメントに従って
         **実データ用**（`input_dir` は `INPUT_DIR` か `input/`、`folds_path` は `data/folds/folds_${data.fold_version}.csv`）に戻す。
         `id_col` / `target_col` / `cv_strategy` / `group_col` / `n_folds` は init で決めた fold 設計と揃える
   - [ ] `train.py` / `inference.py` の import が `src.exp000_sample` 等のコピー元を指していない
   - [ ] metric と wandb project は `${profile:...}` のまま（手で値を書かない）
   - [ ] simulation / optimization なら `model.py` を `agent.py` / `solver.py` に置き換える（`docs/competition-types.md`）
   - [ ] GBDT の exp なら Lightning 部分を各ライブラリ直に置き換え、出力契約
         （`docs/training-conventions.md`「出力契約」）は維持する
4. `README.md` を作る（目的・仮説・手法・比較変数・アーキ図・Runs テーブル・実行コマンド。
   要件は `docs/training-conventions.md`「exp / run の切り分け」）
5. `EXP_SUMMARY.md` に行と `wip` ノードを追加する（書式は EXP_SUMMARY.md 冒頭のコメントに従う）

### 小実験

1. `config/run{NNN}-{subtitle}.yaml` を作る。親を `defaults` に書き、**変えるキーだけ**を書く:

   ```yaml
   defaults:
     - config          # 親（ベース config か既存 run 名）
   run_name: run{NNN}-{subtitle}
   training:
     lr: 5e-4
   ```

   系譜は宣言しない。train.py が起動時に `src/utils/lineage.py:run_lineage` で親と変えたキーを自動計算し、
   ログ・wandb config・`run_summary.json` の `lineage` に記録する。親に存在しないキーを書くと
   タイポとしてエラーになる。
2. README の Runs テーブルに行を追加する（実行順に追記。並び替えない）
3. EXP_SUMMARY.md は更新不要

## フェーズ 5: 動作確認と報告

1. debug で起動する:
   - exp: `uv run python -m src.{exp}.train run_mode=debug`
   - run: `uv run python -m src.{exp}.train --config-name={run_name} run_mode=debug`
2. 冒頭ログの `lineage.changed` を確認する。**2 個以上なら警告**し、run を分けるか新 exp にするかを
   ユーザーに問う（`docs/experiment-methodology.md`「効果の帰属」）
3. 作成ファイル一覧・目的・仮説・比較変数・実行コマンドを報告し、
   次の段取り（debug → fold0 → 有望なら full。昇格は profile の `workflow.default_run_mode` に従う）を案内する
