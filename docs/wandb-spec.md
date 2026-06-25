# wandb の k-fold ログ方針

**基本原則**: fold ごとに独立した wandb run を作成し、`group` で束ねる。

**run 構造**（例: `run_mode=full`, 5-fold）:

```
Group: {exp_name}/{run_name}_{run_mode}

├── fold_0  (job_type: "train")  ← 各 fold の学習曲線を記録
├── fold_1  (job_type: "train")
├── ...
├── fold_4  (job_type: "train")
└── summary (job_type: "summary") ← CV スコアのみ記録（学習曲線なし）
```

- `fold0` モードでは `fold_0` の run のみ作成。summary run は作成しない
- `debug` モードでは wandb 自体が disabled

**wandb.init パラメータ**:

```python
# fold run（各 fold の学習用）
wandb.init(
    project=cfg.wandb.project,
    entity=cfg.wandb.entity,
    group=f"{cfg.exp_name}/{cfg.run_name}_{cfg.run_mode}",
    name=f"fold_{fold_idx}",
    job_type="train",
    config=OmegaConf.to_container(cfg, resolve=True),
    mode=run_cfg["wandb_mode"],
    reinit=True,  # 同一プロセスで複数回 init するために必須
)

# summary run（full モード && wandb 有効 && fold≥2 の場合のみ）
wandb.init(
    ...,
    name="summary",
    job_type="summary",
)
wandb.summary["cv/{評価指標名}"] = cv_mean
wandb.summary["cv/{評価指標名}_std"] = cv_std
wandb.finish()
```

- `WandbLogger(experiment=wandb.run)` を Trainer に渡し、PL の `self.log()` を現在の fold run に記録

**メトリクスキー名規則**: `{split}/{metric}` 形式。全実験で統一し、表記揺れ（`acc` vs `accuracy`、`valid` vs `val`）を避ける。`{評価指標名}` は `/kaggle:init` 実行時にユーザーに確認し、実際のメトリクス名（例: `auc`, `f1`, `accuracy`）に置換する。以降変更しない。

| キー名 | 意味 | 記録場所 |
|--------|------|----------|
| `train/loss` | 学習ロス（epoch 平均） | fold run |
| `train/{評価指標名}` | 学習メトリクス（← `/kaggle:init` で置換） | fold run |
| `val/loss` | 検証ロス（epoch 平均） | fold run |
| `val/{評価指標名}` | 検証メトリクス（← `/kaggle:init` で置換） | fold run |
| `cv/{評価指標名}` | 全 fold の best `val/{評価指標名}` の平均 | summary run の `wandb.summary` |
| `cv/{評価指標名}_std` | 同標準偏差 | summary run の `wandb.summary` |
| `fold{i}/best_val_{評価指標名}` | 各 fold の best `val/{評価指標名}` | summary run の `wandb.summary` |

**ライフサイクル**:

```python
for fold_idx in folds:
    wandb.init(...)          # fold run 開始
    trainer.fit(...)         # PL が self.log() → WandbLogger 経由で記録
    wandb.finish()           # fold run 終了

# full モードのみ
wandb.init(...)              # summary run 開始
wandb.summary["cv/{評価指標名}"] = ...
wandb.finish()               # summary run 終了
```

**run_mode ごとの挙動**:

| run_mode | wandb_mode | fold 数 | 作成される run | summary run |
|----------|------------|---------|---------------|-------------|
| `debug` | disabled | 1 | なし | なし |
| `fold0` | online | 1 | `fold_0` のみ | なし |
| `full` | online | N | `fold_0` 〜 `fold_{N-1}` | あり |
