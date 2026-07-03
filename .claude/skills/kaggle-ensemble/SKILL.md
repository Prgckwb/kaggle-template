---
name: kaggle:ensemble
description: 複数実験の OOF 予測をブレンドし、OOF で重みを最適化してアンサンブル submission を作成する。
argument-hint: [対象実験名のリスト（省略可。例: exp001_baseline exp003_bert）]
disable-model-invocation: true
allowed-tools: Bash, Read, Write, Edit, Glob, Grep
---

# アンサンブル: OOF ブレンドと submission 生成

複数の大実験の OOF 予測（`oof_predictions.csv`）を素材に、OOF 上でブレンド重みを決定し、
同じ重みでテスト予測を合成して submission を作成する。
実装は `src/utils/ensemble.py`（`blend_predictions` / `rank_average`。id 列でアラインし、ID 不一致はエラー）と
`src/utils/submission.py`（`validate_submission`）を使う。

## 前提と原則

- **素材は `run_mode=full` の実験のみ**（OOF が全 train をカバーしている必要がある）
- **全素材が同一の CV 分割であること**（fold 数・分割方法・seed が同じ）。分割が違う OOF 同士の比較・重み最適化はリークを含み信頼できない。各実験の config（`data.n_folds`, `seed`）と `output/{run_name}/fold*/train.csv, val.csv` で確認する
- **重みの過剰最適化に注意**: OOF 上で重みを細かく最適化するほど OOF にオーバーフィットする。素材が 2〜4 個なら等重み or 粗い探索で十分。等重みとの差が `meaningful_delta`（またはノイズフロア）未満なら等重みを選ぶ
- 評価指標・方向は `docs/competition-profile.yaml` の `metric` に従う

## フェーズ 1: 素材の収集

1. $ARGUMENTS があればその実験を対象にする。なければ `src/exp*/output/*/oof_predictions.csv` を Glob で検索し、候補一覧（実験名・run 名・CV スコア）を提示してユーザーに選んでもらう
2. 各素材について確認する:
   - `oof_predictions.csv` が存在するか（なければ `run_mode=full` の再実行を案内）
   - 対応するテスト予測（`inference.py` の出力 submission CSV）が存在するか
   - CV 分割が一致しているか（fold 数・seed・分割方法）
3. `EXP_SUMMARY.md` で各素材のスコアと Key Change を確認し、**アプローチの多様性**を把握する（同系統モデルばかりのブレンドは伸びにくい）

## フェーズ 2: OOF 分析（ブレンド前の健全性確認）

sandbox/ に分析スクリプトを書いて実行する（`sandbox/ensemble_YYYYMMDD.py` 等）:

1. 各素材の OOF スコアを競技指標で再計算し、記録された CV と一致するか確認（不一致は列名や後処理の食い違いのサイン）
2. **素材間の予測相関行列**を計算して提示する。相関が非常に高い（例: > 0.98）ペアはブレンド効果が薄いことを伝える
3. ブレンド方式をユーザーと決める:
   - `blend_predictions`（加重平均）: 回帰・確率出力の基本
   - `rank_average`: スケールの異なるモデル同士や AUC 系指標で有効

## フェーズ 3: 重みの決定

1. まず**等重み**のブレンド OOF スコアを計算する（これがベースライン）
2. 改善を狙う場合のみ重み探索する。scipy は依存に含まれないため numpy のみで行う:
   - 粗いグリッド（0.1 刻み）または Dirichlet サンプリングによるランダム探索（数千点で十分）
   - 制約: 重み ≥ 0、合計 1
3. 最良重みと等重みの OOF スコア差を `meaningful_delta`（未設定なら fold 間ノイズフロア）と比較し、**有意でなければ等重みを推奨する**
4. 決定した重み・方式・OOF スコアをユーザーに提示して承認を得る

## フェーズ 4: submission の生成

1. 同じ方式・重みでテスト予測を合成する（`blend_predictions` / `rank_average` に submission CSV のパスを渡す）
2. 必要なら後処理を適用する（`src/utils/postprocess.py`: クリッピング・閾値・argmax 等。OOF で効果を確認したもののみ）
3. `validate_submission(submission_path, sample_submission_path)` で形式を検証する（エラーが空であること）
4. 出力先: `src/exp{NNN}_ensemble/output/`（フェーズ 5 で作る実験ディレクトリ配下）

## フェーズ 5: 実験としての記録

アンサンブルも1つの大実験として扱う:

1. `src/exp{NNN}_ensemble/`（番号は既存最大 + 1）を作成し、README.md に以下を記録する:
   - 素材（実験名 / run 名 / 各 OOF スコア）
   - 方式（加重平均 / ランク平均）と**最終的な重み**
   - ブレンド OOF スコア（= この実験の CV）と等重みとの比較
   - 使用した後処理
   - sandbox スクリプトのパス（再現手順）
2. `EXP_SUMMARY.md` の Experiments テーブルと Experiment Tree に追加する（素材の各実験からエッジを張る。Key Change 例: `exp001+exp003 加重ブレンド`）
3. 提出したら `/kaggle:record-result` で LB を記録する（`docs/submissions.md` にも追記される。Exp / Run 欄には素材 run を列挙する）

## フェーズ 6: 完了報告

- 素材・方式・重み・OOF スコア（等重み比）のサマリー
- 生成した submission のパスとバリデーション結果
- 次の一手の提案（素材の多様性が低ければ、未探索ファミリーの実験を `/kaggle:new-experiment` で追加してからの再ブレンドを提案する）
