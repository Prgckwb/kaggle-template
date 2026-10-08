---
name: kaggle:record-result
description: 学習が終わった run や提出の結果を記録する。run_summary.json から CV を読み、exp README・EXP_SUMMARY.md・docs/submissions.md を更新し、考察を聞いて知見を routing 表に従って振り分ける。「結果を記録して」「CV/LB を書いて」「学習が終わった」「LB が出た」と言われたら使う。
argument-hint: [実験名（例: exp001_baseline）]
allowed-tools: Bash, Read, Write, Edit, Glob
---

# 実験結果を確認・記録する

スコアは手で写さず機械可読な出力から読む。そのうえでユーザーから学びを引き出す。

## 判定の前提（最初に読む）

`docs/competition-profile.yaml` の `metric.mode` / `meaningful_delta` / `noise` / `selection.policy`。

- best の方向は `metric.mode`、best の基準は `selection.policy`（`cv` 既定 / `lb` / `hybrid`）
- **CV best と LB best が食い違ったら policy に関わらず両方を提示して警告する**
- 「棄却」「dead-end」「確定」を言えるかは `docs/experiment-methodology.md`「判定の資格」に従う
  （`noise.seed_spread` が null の間は言わない）

## フェーズ 1: 対象の特定

1. $ARGUMENTS か `src/exp*/` の一覧から exp を決め、README（目的・仮説）を読む
2. run を決める（`config/config.yaml` = run000-base と `config/run*.yaml`）。複数あれば選んでもらう

## フェーズ 2: スコアの収集

1. **`src/{exp}/logs/{run_name}/run_summary.json` を読む**（スキーマは `src/utils/run_summary.py`）
   - `oof_score` があればそれが **CV の代表値**（全 fold の OOF pooled）。`cv_mean ± cv_std` はばらつきの参考
   - fold0 モードなら値は `fold_scores["0"]`。**CV と呼ばず `(f0)` を付けて記録する**
   - `lineage.parent` / `lineage.changed`（自動計算された親と変えたキー）、`git_sha` も控える
   - ファイルが無い・壊れている場合だけユーザーに聞く。`-debug` の summary は記録しない
2. **系譜の確認**: `lineage.changed` が 2 個以上なら、README・EXP_SUMMARY.md に
   「この Δ は N 変数の合計」と明記し、1 変数の名前で呼ばない（`docs/experiment-methodology.md`「効果の帰属」）
3. **LB**（提出があった場合）: `uv run python -m tools.check_submission` か
   `uv run kaggle competitions submissions -c {slug}` で取得する（読み取りのみ）。
   提出日・提出理由と、notebook が出した `submission_manifest.json` の場所を確認する
4. Split 方法は README か EXP_SUMMARY.md の Validation Strategy から取る

## フェーズ 3: 考察のヒアリング

答えが薄ければ掘り下げる。次の実験の設計には踏み込まない（`/kaggle:new-experiment` の役割）。

- 仮説は当たったか。外れたならなぜか
- 何が分かったか。予想外だったことは
- 次に試したいこと（EXP_SUMMARY.md の探索バックログに入れる）

## フェーズ 4: 知見の routing

出てきた学びを **`docs/README.md` の「知見の routing」表**に従って振り分け、表にしてユーザーに確認する
（分類と書き込み先はその表が正本。ここに写さない）。

- 迷ったら問う:「次のコンペが別ドメインでも、この文は意味を持つか」
- invariant 層に書くときは固有名詞を落とし、実測値は「あるコンペでの実測例」と匿名化して
  `<!-- harvest -->` を付ける（`/kaggle:harvest-template` が回収する）
- 働き方の合意（ユーザーの指示）は profile の `workflow` の該当キーも同時に書き換える

## フェーズ 5: 記録

1. **exp README**: Runs テーブルの該当行（CV・LB・Key Change）、結果テーブル（exp の best run）、考察。
   fold 別スコアは `fold_scores` から表にしてよい
2. **EXP_SUMMARY.md**（書式は冒頭のコメントに従う）:
   - Experiments テーブルの該当行（exp の best run のスコア）
   - Experiment Tree のノードとクラス（`wip`→`good`、全体 best なら `best` にして旧 best を降格）
   - 探索バックログにフェーズ 3 の「次に試したいこと」を追加
   - seed 違いの run を測った場合は「ノイズ較正記録」に追記し、profile の `metric.noise` も更新する
3. **docs/submissions.md**（提出があった場合）: 構成は manifest から読む（推測しない）。

   ```bash
   uv run python -c "import json,sys; from src.utils.submission_manifest import describe_manifest; print(describe_manifest(json.load(open(sys.argv[1]))))" path/to/submission_manifest.json
   ```

   - 出力を **Exp / Run 列にそのまま貼る**。manifest が無い提出は「構成不明」と書き、
     次回から notebook が manifest を出すよう `/kaggle:create-inference-notebook` を案内する
   - `manifest["unparsed"]` が空でなければ ckpt 名が規約外。命名を直して manifest を作り直す
   - 「CV-LB の写像」にも追記する。較正点は `lineage.changed` が 1 個の比較からだけ採る
   - 初回はプレースホルダー行を消す。過去の記録漏れに気づいたら追記を提案する
4. **docs/insights/**: routing で「実装知見」に分類したものがあれば
   `YYYY-MM-DD_exp{番号}_{subtitle}.md` に書く（概要・試したこと・結果・考察・実装上の知見）

## フェーズ 6: 停滞チェック

`docs/experiment-methodology.md` の「停滞の定義」に従って判定する（計算方法・基準値の優先順位は
そこが正本。ここで独自に定義しない）。

- `noise.seed_spread` が null なら停滞・dead-end を判定せず、
  **同一設定で seed だけ変えた run を 1 本焼く**ことを提案する（その差が分母になる）
- 停滞に該当したら、差・基準値・`差 / seed_spread` を示して、exp を `dead-end` にするか尋ねる
  - 承認されたら README の結果テーブルに `| Status | dead-end |` を足し、Tree のクラスを `dead` にし、
    `/kaggle:review-strategy` を案内する
  - 続行なら状態は変えない
- 判定に必要な run 数が揃わなければ、スキップした旨を報告する

## フェーズ 7: 報告

更新したファイル、スコアのサマリー（CV の代表値か f0 かを明記）、現在の best、
routing の結果（どこへ何を書いたか。invariant に書いたものはコンペ終了時に `/kaggle:harvest-template` で還流）、
停滞チェックの結果。最後に `docs/SESSION_NOTES.md` の更新を提案する。
