<!-- lifecycle: invariant -->
# wandb の k-fold ログ方針

**基本原則**: fold ごとに独立した wandb run を作成し、`group` で束ねる。
run 名は project 全体で一意にする。

**run 構造**（例: `exp001_baseline` / `run001-lr2e4` / `run_mode=full`, 5-fold）:

```
Group: exp001_baseline/run001-lr2e4_full

├── exp001-run001-lr2e4-f0       (job_type: "train")  ← 各 fold の学習曲線を記録
├── exp001-run001-lr2e4-f1       (job_type: "train")
├── ...
├── exp001-run001-lr2e4-f4       (job_type: "train")
└── exp001-run001-lr2e4-summary  (job_type: "summary") ← CV スコアのみ記録（学習曲線なし）
```

- **run 名を `fold_{k}` にしない**: 全実験で同名になり、run 一覧・検索・レポートで
  見分けがつかなくなる。`{exp番号}-{run_name}-f{k}` で一意化する
- `fold0` モードでは f0 の run のみ作成。summary run は作成しない
- `debug` モードでは wandb 自体が disabled

**実装の正本は `src/exp000_sample/train.py`**（ここにコードを複製しない）。押さえるべき約束だけを書く:

- fold ごとに `wandb.init(group=..., name=..., id=..., job_type="train", tags=..., config=...)` し、
  Lightning には `WandbLogger(experiment=wandb.run)` と `CSVLogger`（ローカルの `logs/{run_name}/fold{k}/metrics.csv`）を
  **両方**渡す。`self.log()` が両方に記録されるので、wandb を見られない環境でも曲線が残る
- `group = "{exp_name}/{run_name}_{run_mode}"`、`name = "{exp番号}-{run_name}-f{k}"`
- `tags` に `exp番号 / run_name / fold{k} / run_mode` と、設定されていれば
  `data.fold_version` / `data_version` / `label_version` を入れる（世代跨ぎの比較を後からフィルタで防ぐ）
- `config` には解決済みの config に加え、`lineage`（`src/utils/lineage.py` が自動計算した親と変えたキー）を入れる
- `define_metric` で `val/*` の x 軸を `epoch` に固定し、`val/{評価指標名}` の summary を `metric.mode`（max/min）、
  `val/loss` の summary を min にする（run テーブルの列が「最後の値」ではなく best になる）
- `debug` は wandb disabled。`fold0` は f0 の run のみ。`full` かつ 2 fold 以上のときだけ summary run を作る
  （1 fold の値を「CV」として並べない）
- summary run（`job_type="summary"`、`name = "{exp番号}-{run_name}-summary"`）の `wandb.summary` に
  `oof/{評価指標名}`・`cv/{評価指標名}`・`cv/{評価指標名}_std`・`fold{i}/best_val_{評価指標名}` を書く。
  同じ値はローカルの `run_summary.json`（スキーマは `src/utils/run_summary.py`）にも書かれる
- **CV の代表値は `oof/{評価指標名}`**（全 fold の予測を pooled して `src/metric.py` の `score` で 1 回計算した値）。
  `cv/{評価指標名}` と `_std`（fold ごとの best の平均と標準偏差）は**ばらつき幅の把握**に使う
  （fold 平均は fold ごとのサンプル数差・指標の非線形性で pooled とずれる）
- ⚠ **決定的 `id` + `resume="allow"` が安全なのは「同じ試行の継続」だけ**である。
  中断されたジョブを別マシンで再実行する用途には正しく効くが、**既存 id への resume は同じ history に追記される**。
  設定やコードを変えて焼き直すなら新しい run 名を切る（`docs/training-conventions.md`「exp / run の切り分け」）。
  同じ run 名でやり直す必要があるときは id に attempt を足す（`...-f{k}-a2`）。
  投入直後に設定を見直す手順は `docs/remote-training-ops.md` の「投入前チェック」

**メトリクスキー名規則**: `{split}/{metric}` 形式で全実験統一し、表記揺れ（`acc` vs `accuracy`、`valid` vs `val`）を避ける。wandb UI は `/` の前でパネルをグルーピングするため、`train` / `val` / `perf` / `time` / `cv` / `oof` の欄に自動整理される。本ドキュメント中の `{評価指標名}` は `docs/competition-profile.yaml` の `metric.name`（`/kaggle:init` で設定。例: `auc`, `f1`, `rmse`）を指す。実験 config は `${profile:metric.name}` / `${profile:metric.mode}` で profile を読むので、手で揃える必要はない。

| キー名 | 意味 | 記録場所 |
|--------|------|----------|
| `train/loss` | 学習ロス（step + epoch 平均） | fold run |
| `train/lr` | 学習率（scheduler の挙動確認用） | fold run |
| `train/grad_norm` | 勾配ノルム（発散・勾配消失の検出） | fold run |
| `train/{評価指標名}` | 学習メトリクス（train-val ギャップ = 過学習の監視） | fold run |
| `val/loss` | 検証ロス（epoch 平均） | fold run |
| `val/{評価指標名}` | 検証メトリクス | fold run |
| `val/{評価指標名}_{class}` | **per-class メトリクス**（クラス別の課題では毎 epoch 記録する） | fold run |
| `val/pred_std` | 予測値の標準偏差（≈0 = 事前確率への collapse の早期検出） | fold run |
| `val/attn_entropy` | 集約機構の注視分布の正規化エントロピー（1 に張り付き = 拡散） | fold run（集約機構を持つ実験） |
| `val/attn_query_js` | クエリ間の pairwise JS divergence（≈0 = クエリ退化） | fold run（同上） |
| `cv/{評価指標名}` | 全 fold の best `val/{評価指標名}` の平均（ばらつき把握用） | summary run の `wandb.summary` |
| `cv/{評価指標名}_std` | 同標準偏差 | summary run の `wandb.summary` |
| `fold{i}/best_val_{評価指標名}` | 各 fold の best `val/{評価指標名}` | summary run の `wandb.summary` |
| `oof/{評価指標名}` | OOF 全体を pooled したスコア（**CV の代表値**） | summary run の `wandb.summary` |
| `oof/{評価指標名}_{class}` | OOF pooled の per-class メトリクス | summary run の `wandb.summary` |

- **per-class メトリクスがある課題では、マクロ平均だけでなくクラス別も毎 epoch ログする。**
  マクロだけでは「どのクラスが動いたのか」が分からず、改善とノイズを区別できない
- `val/pred_std` は**予測が事前確率に潰れる collapse** を最も安く検出する。
  loss は中程度で下がり止まる（プラトー）だけなので loss 監視では気づけない
  → 機序は `docs/experiment-methodology.md` の「collapse は獲得させたい軸で層別する」

**「多めにログ」原則**: 学習が終わったあとで**「学習のどこかがおかしくなっていないか」を
検証できる証拠を残す**のが目的である。ロスの遷移・学習率・勾配ノルム・スループットは
「今は見ていないから」という理由で削らない。あとから足しても過去の run には遡れない。

**パフォーマンスメトリクス（推奨）**:

学習効率の把握と異なる実験間の比較のために、以下のスループット系メトリクスの記録を推奨する:

| キー名 | 意味 | 記録タイミング |
|--------|------|---------------|
| `perf/steps_per_second` | 1秒あたりの学習ステップ数 | epoch 終了時 |
| `perf/samples_per_second` | 1秒あたりの処理サンプル数 | epoch 終了時 |
| `perf/tokens_per_second` | 1秒あたりの処理トークン数（NLP の場合） | epoch 終了時 |
| `perf/gpu_memory_mb` | GPU メモリ使用量（MB） | epoch 終了時 |
| `time/epoch_seconds` | epoch あたりの所要時間（秒） | epoch 終了時 |
| `time/total_seconds` | 学習開始からの累計時間（秒） | epoch 終了時 |

```python
import time
import torch

epoch_start = time.perf_counter()
# ... training loop ...
epoch_seconds = time.perf_counter() - epoch_start

perf_metrics = {
    "perf/steps_per_second": num_steps / epoch_seconds,
    "perf/samples_per_second": num_samples / epoch_seconds,
    "time/epoch_seconds": epoch_seconds,
}
if torch.cuda.is_available():
    perf_metrics["perf/gpu_memory_mb"] = torch.cuda.max_memory_allocated() / 1e6
wandb.log(perf_metrics)
```

**run_mode ごとの挙動**:

| run_mode | wandb_mode | fold 数 | 作成される run | summary run |
|----------|------------|---------|---------------|-------------|
| `debug` | disabled | 1（fold0。出力は `-debug` に隔離） | なし | なし |
| `fold0` | online | 1 | `...-f0` のみ | なし |
| `full` | online | N | `...-f0` 〜 `...-f{N-1}` | あり |
