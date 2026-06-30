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

## simulation タイプのベストプラクティス

以下は過去の上位解法（Orbit Wars 1位等）から抽出した、simulation/RL コンペで有効なパターン。

### 環境の高速化

公式の Python 環境は RL 学習に必要なスループットが得られないことが多い。以下の選択肢を検討する:

| 手法 | 速度向上 | 実装コスト | 推奨場面 |
|------|---------|-----------|---------|
| Cython 化 | 5-20x | 中 | ホットパスが特定できている場合 |
| Rust + PyO3 | 10-100x | 高 | 大規模学習（数十億ステップ） |
| C++ + pybind11 | 10-100x | 高 | 既存 C++ コードがある場合 |
| Numba JIT | 2-10x | 低 | プロトタイピング段階 |

**Parity テスト**: 高速環境を実装したら、公式環境からリプレイを抽出して各ステップの出力が一致するかを検証する。

### Self-Play 戦略

| 戦略 | 説明 | 適用場面 |
|------|------|---------|
| Last-Best | 勝率 70% 超で過去最良を更新 | シンプルで安定 |
| League Play | 過去チェックポイントのプールから対戦相手を選択 | 戦略サイクル防止 |
| Fixed Teacher + KL | 固定教師モデルからの KL Distillation | 学習安定化 |
| Population-Based | 複数エージェントを並行学習 | 計算資源が豊富な場合 |

### 推論時間制約への対処

多くの simulation コンペには推論時間制約がある（例: 1秒/ターン + overage time）。

- **Fallback Model**: メインモデル + 軽量モデルの2段構成。時間が足りなくなったら軽量モデルに切り替え
- **INT8 量子化**: `torch.ao.quantization` で推論時に線形層を INT8 化
- **Entity Compaction**: 不活性なエンティティを推論テンソルから除去し、出力時に展開
- **Checkpoint 軽量化**: `src/utils/checkpoint.py` の `export_slim_checkpoint` で optimizer state を除去

### RL アルゴリズム選択の目安

| アルゴリズム | 長所 | 短所 |
|-------------|------|------|
| PPO | 実装が単純、GPU スケーリング容易 | サンプル効率が低い |
| IMPALA | Off-policy で高スループット | Collector/Trainer のバランス調整が必要 |
| AlphaZero/MuZero | 探索 (MCTS) を組み込める | 実装が複雑、推論が重い |
| DQN 系 | 離散行動空間に強い | 連続行動空間に不向き |

### Composite Optimizer パターン

Transformer ベースのモデルでは、trunk（Attention + MLP）と embedding/head で異なるオプティマイザ・学習率を使うと効果的な場合がある:

```python
# Muon for trunk, AdamW for embeddings/heads
trunk_params = [p for n, p in model.named_parameters() if "trunk" in n]
head_params = [p for n, p in model.named_parameters() if "trunk" not in n]
optimizer = torch.optim.AdamW([
    {"params": trunk_params, "lr": 2e-3, "weight_decay": 0.05},
    {"params": head_params, "lr": 1e-4, "weight_decay": 0.0},
])
```

### torch.compile 活用

PyTorch 2.0+ の `torch.compile` で無料の高速化が得られる:

| モード | 説明 | 推奨場面 |
|--------|------|---------|
| `trunk` | Transformer trunk 全体をコンパイル | 本番学習（最大スループット） |
| `mlp` | MLP ブロックのみコンパイル | 実験段階（互換性重視） |
| `none` | コンパイルなし | デバッグ・CPU テスト |

```python
if cfg.compile_mode == "trunk":
    model.trunk = torch.compile(model.trunk, mode="max-autotune-no-cudagraphs")
elif cfg.compile_mode == "mlp":
    for block in model.trunk.blocks:
        block.mlp = torch.compile(block.mlp, dynamic=True)
```

## wandb ログの適応

| supervised | simulation | optimization |
|-----------|-----------|-------------|
| epoch | episode | iteration |
| train/loss, val/loss | episode/reward, episode/length | iteration/score, iteration/best_score |
| cv/{metric} | mean_reward | best_score |
| fold ごとの run | 単一 run（長期学習） | 単一 run |
