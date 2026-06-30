# コンペティションタイプ別ガイド

コンペティションタイプが `simulation` または `optimization` の場合、通常の train/predict/submit パイプラインは適用されない。`/kaggle:init` 実行時にタイプを選択する。

## タイプ一覧

| タイプ | 説明 | パイプライン |
|--------|------|-------------|
| `supervised`（デフォルト） | 予測コンペ | train → predict → submit CSV |
| `optimization` | 反復最適化コンペ | スコアがイテレーションごとに改善、train/test 分割なし |
| `simulation` | エージェント/RL コンペ | ゲームやシステムを制御するエージェントを作成 |

## simulation タイプの実験構成

`model.py` の代わりに `agent.py` を作成する。`BaseAgent` を継承し、`act(observation)` を実装する。

```
src/exp001_xxx/
├── agent.py        # エージェント定義（model.py の代わり）
├── env.py          # 環境ラッパー（必要に応じて）
├── train.py        # 学習・評価ループ
├── data.py         # リプレイデータ等の処理
├── config/
│   └── config.yaml
└── output/
```

- **トラッキング**: エピソード報酬（episode reward）で評価
- **評価方法**: セルフプレイまたはアリーナ形式

## optimization タイプの実験構成

`model.py` の代わりに `solver.py` を作成する。fold/CV の概念がなく、スコアをイテレーションごとに記録する。

```
src/exp001_xxx/
├── solver.py       # 最適化ソルバー（model.py の代わり）
├── train.py        # 最適化ループ
├── config/
│   └── config.yaml
└── output/
```

- **トラッキング**: イテレーションごとのスコア改善
- **評価方法**: テストケースに対するスコア

## 実行モードの対応

`run_mode` は全タイプで有効だが、名称の解釈が変わる:

| run_mode | supervised | simulation / optimization |
|----------|-----------|--------------------------|
| `debug` | 少数データ・1epoch・1fold | 少数エピソード/イテレーション・短時間で動作確認 |
| `fold0` | fold0 のみ学習 | `eval_once`: 単一評価（1エピソード or 1テストケース） |
| `full` | 全 fold 学習 | `eval_full`: 完全評価（全エピソード or 全テストケース） |

config 上は `run_mode` のまま統一し、コード内で解釈を切り替える。

## wandb ログの適応

| supervised | simulation | optimization |
|-----------|-----------|-------------|
| epoch | episode | iteration |
| train/loss, val/loss | episode/reward, episode/length | iteration/score, iteration/best_score |
| cv/{metric} | mean_reward | best_score |
| fold ごとの run | 単一 run（長期学習） | 単一 run |
