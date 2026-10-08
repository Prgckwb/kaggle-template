---
name: kaggle:ensemble
description: 複数の実験を混ぜたいとき（「アンサンブルして」「ブレンドして」「OOF で重みを決めて」など）に使う。OOF で混ぜ方と重みを決め、同じ重みでテスト予測を合成して、独立したアンサンブル実験 src/exp{NNN}_ensemble/ を作る。
argument-hint: [素材の実験名/run名のリスト（省略可）]
allowed-tools: Bash, Read, Write, Edit, Glob, Grep
---

# アンサンブル: OOF でブレンドを決めて submission を作る

使うもの:

- `src/utils/ensemble.py`
  - `load_aligned(paths, id_col)`: id で行を揃え、ID が一致しなければエラーにする
  - `blend(paths, weights=None, method="mean"|"rank", id_col, pred_cols)`
- `src/metric.py` の `score(y_true, y_pred)`: 競技指標。OOF の再計算にはこれだけを使い、別実装を書かない
- `src/utils/submission.py` の `validate_submission`
- `src/utils/submission_manifest.py`

素材は、実験の出力契約（`docs/training-conventions.md`）にある次の 2 ファイル。

- `src/{exp}/output/{run}/oof_predictions.csv`: 全 fold 走った run だけが持つ
- `src/{exp}/output/{run}/submission.csv`: `inference.py` が書くテスト予測

## 原則

- **素材は全 fold 走った run に限る**（`run_summary.json` の `oof_score` が null でないもの）
  - fold0 だけの run は OOF が train の一部しか覆っていないので、素材にしない
- **全素材が同じ fold ファイルを使っていること**（config の `data.fold_version` が一致）
  - fold が違う OOF 同士で重みを最適化すると、リークを含んだ値になる
- **重みを細かく最適化しすぎない**: 等重みをベースラインにする
  - 最適化した重みとの差が `metric.meaningful_delta`（無ければ `metric.noise.seed_spread`）に満たなければ、等重みを採る
- 指標の名前と向きは profile の `metric` に従う

## フェーズ 1: 素材の収集

1. `$ARGUMENTS` に無ければ `src/exp*/output/*/oof_predictions.csv` を Glob する
   - 対応する `run_summary.json` の `oof_score` と、`EXP_SUMMARY.md` の Key Change を並べて提示し、ユーザーに選んでもらう
2. 各素材について確認する。欠けていれば、何を実行すればよいかを案内する
   - `oof_predictions.csv` と `submission.csv` がそろっているか
   - `data.fold_version` と id 列が一致しているか
3. **アプローチの多様性**を確認する。同系統のモデルばかりではブレンドが伸びにくい

## フェーズ 2: OOF の健全性確認

`sandbox/ensemble_YYYYMMDD.py` に書いて実行する。

1. 各素材の OOF を `src/metric.score` で再計算し、`run_summary.json` の `oof_score` と一致するか確認する
   - 一致しなければ、列名や後処理が食い違っている兆候
2. 素材間の予測の相関行列を出す。相関が非常に高い（> 0.98 など）ペアは、混ぜる効果が薄いと伝える
3. 混ぜ方をユーザーと決める
   - `method="mean"`: 回帰・確率出力の基本
   - `method="rank"`: スケールの違う素材同士や、AUC 系の指標に向く

## フェーズ 3: 重みの決定

1. 等重みでブレンドした OOF スコアを出す（これがベースライン）
2. 重みを探すのは、改善を狙う場合だけにする。scipy は使わず numpy で行う
   - 0.1 刻みのグリッド、または Dirichlet サンプリング（数千点）
   - 制約は「重み ≥ 0、合計 1」
3. 等重みとの差を原則の閾値と比べて結論を出し、方式・重み・OOF スコアを提示して**承認を得る**
4. 後処理（クリッピング・閾値など）を入れたい場合は、このアンサンブル実験の中に実装する
   - OOF で効果を確認できたものだけを入れる（共有の後処理ユーティリティは無い）

## フェーズ 4: アンサンブル実験として出力

1. `src/exp{NNN}_ensemble/` を作る（番号は既存の最大 + 1）
   - `blend.py`: 素材のパス・方式・重みを定数で持ち、`oof_predictions.csv` と `submission.csv` を出す
   - `README.md`: 素材ごとの exp / run / `oof_score`、方式、最終的な重み、ブレンド OOF（= この実験の CV）と等重み比、後処理、再現コマンド
2. `uv run python -m src.exp{NNN}_ensemble.blend` を実行する。出力先は `src/exp{NNN}_ensemble/output/`
3. `validate_submission` でエラーが空であることを確認する
4. Kaggle 提出用の notebook が必要なら、`/kaggle:create-inference-notebook` で **同じディレクトリ** に `inference_notebook.ipynb` を作る
   - manifest の `blend` に方式と重みを渡す

## フェーズ 5: 記録

- `EXP_SUMMARY.md` の Experiments 表とツリーに追加する
  - 各素材からエッジを張り、Key Change は例えば「exp001+exp003 加重ブレンド」とする
- 提出した後は `/kaggle:record-result` で LB を記録する
  - `docs/submissions.md` の Exp/Run 欄には、**`describe_manifest()` の出力をそのまま貼る**（素材を手で列挙しない）

## 完了報告

- 素材・方式・重み・OOF スコア（等重みとの比較）、submission のパス、検証結果
- 素材の多様性が低ければ、系統の違う実験を足してからもう一度ブレンドすることを提案する
  - 実際に足すかどうかはユーザーが決める
