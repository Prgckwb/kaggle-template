<!-- lifecycle: invariant -->
# リモート GPU 学習の運用（herdr 前提）

> **クラウドの GPU / CPU に学習・前処理ジョブを投入する前に読む。**
> `docs/competition-profile.yaml` の `workflow.remote_training` が `none` のコンペでは不要。
>
> provider 固有のコマンドは末尾の付録に分けてある。本文は provider 非依存。
> プロジェクト ID・バケット名・インスタンス名は `{...}` の placeholder で書いてあるので、
> コンペ開始時に自分の値へ置き換える。

placeholder の一覧:

| placeholder | 意味 |
|---|---|
| `{PROJECT}` | クラウドのプロジェクト / アカウント ID |
| `{BUCKET}` | 成果物を置くオブジェクトストレージのバケット |
| `{REGION}` `{ZONE}` | データと同居させるリージョン / ゾーン |
| `{SA}` | インスタンスに付けるサービスアカウント |
| `{INSTANCE}` | GPU インスタンス名 |
| `{USER}` | リモート側のログインユーザー |
| `{repo}` | このリポジトリのディレクトリ名 |

## 原則

1. **永続ストレージはオブジェクトストレージのみ**。永続ディスクに常設コピーを持たない
2. **GPU インスタンスは完全エフェメラル**: 学習のたびに作成 → ステージング → 学習 →
   成果物を退避 → **インスタンスごと削除**（stop で放置しない）
3. **中断可能インスタンス（Spot / preemptible）が基本** → すべての学習スクリプトは
   **「チェックポイントの逐次同期 + resume 再開」が必須要件**。
   合格条件は「新しいインスタンスでステージングして**同一コマンドを再実行すると続きから走る**」
4. **リージョンはデータと同居させて固定する**。同一リージョン内のストレージ → インスタンス転送は
   無料だが、大陸を跨ぐと GiB 単価が乗る（数百 GiB のデータセットでは無視できない）
5. **環境再現は「ドライバ入りイメージ + `git clone` + lock ファイルによる同期」**。
   Docker は挟まない（lock ファイルがローカルと同一環境を保証する）
6. **成果物の置き場を 3 系統に分ける**:

| 置き場 | 何を | 用途 |
|---|---|---|
| wandb | メトリクス・config | 実験比較（`docs/wandb-spec.md`） |
| オブジェクトストレージ `experiments/` | チェックポイント・OOF・ログ | resume・再現・アンサンブル素材 |
| Kaggle Datasets | 提出に使う最終重みのみ | 推論 notebook から参照（`tools/upload_checkpoints.py`） |

7. **前処理の固定費は 1 回だけ払う**。毎 epoch 払う前処理（デコード・並べ替え・QC・正規化）は
   CPU インスタンスで 1 回だけ実行してアーカイブし、バージョン名（`v{NNN}_{短い説明}`）を刻む。
   バージョン直下に生成コードの git SHA と全パラメータを書いた `_meta.json`、
   全件完了時のみ `_SUCCESS` を置き、**`_SUCCESS` のないバージョンを学習に使わない**
8. **モデル固有の属性（解像度・crop）はストレージに焼き込まない**。
   焼き込むと、その属性を動かす実験のたびにアーカイブを作り直すことになる

## 投入前チェック

長時間ジョブ（単一 fold フル 1 本以上）を投入する前に、**必ず実測を取る**。
判定側の根拠は `docs/experiment-methodology.md` の「投入前のコスト実測」。

```bash
# 1. 1 epoch のコストを実測して総時間に換算する（見積りで投入しない）
#    分/epoch × epoch 数 × fold 数 が予算に入るか

# 2. ディスク: 前処理キャッシュは入力サイズ（解像度・系列長・特徴量数）に対して
#    超線形に増える。VRAM より先に律速する
du -sh input/cache/* ; df -h /

# 3. VRAM: 定常値ではなく「検証ループを 1 回通した後のピーク」を見る
nvidia-smi --query-gpu=memory.used,memory.total,utilization.gpu \
           --format=csv -l 30

# 4. CPU: worker 数をインスタンスの vCPU に合わせる（キャッシュ構築 epoch は CPU 律速）
nproc
```

- ⚠ **実効バッチ（micro-batch × 勾配累積）は変えない**で micro-batch を上げる。
  変えると ablation の比較可能性が壊れる
- 開始直後に VRAM を実測し、大幅に余っていれば（目安 **50% 未満**）序盤のうちに設定を上げて
  仕切り直す。序盤なら restart のコストは小さい
  ⚠ **設定を変えて仕切り直すときは wandb の id も新しく取る**（同じ id に resume すると
  捨てた試行の曲線が同じ history に残り、best が両試行を通した値になる）→ `docs/wandb-spec.md`
- 中断可能インスタンスの在庫は時間帯・ゾーンで変わる。**在庫確認 → 作成**の順にする

## 生存性

🔴 **長時間学習は、端末マルチプレクサ（tmux）のセッションごと消えて無警告に死ぬ。**

**症状の見分け方が独特で、原因調査を誤りやすい**:

- Python の例外トレースが**一切残らない**（SIGKILL 系）
- chain スクリプトの `echo "EXIT: $?"` にも到達しないので、**失敗マーカーも立たない**
- wandb の state は `crashed`
- **決定的な証拠はセッションの作成時刻**。`tmux ls` の `created` が学習開始時刻より新しければ、
  セッションは一度消えている（`tmux attach || tmux new` を使っていると後半が発火して新規作成される）
- `capture-pane` が空なのも「新セッションだから履歴ゼロ」であって、画面クリアではない
- 死亡時刻は**最後のチェックポイントの mtime** で確定できる。ssh 切断時刻と比べれば
  ssh 起因かを切り分けられる

**真因の実例**: 同型の消失が 2 度起きたインスタンスは `Linger=no` で、
同時に動いていた別インスタンスは `Linger=yes` で無事だった。
**新規作成したインスタンスでは linger の設定を忘れやすい**のが真因で、
症状（セッションごと消滅・OOM 痕跡なし・再起動なし・失敗マーカーなし）は上記と完全に一致した。

**投入前に両方入れる（片方では足りない）**:

1. **linger を有効化する** — ssh が全部切れてもユーザープロセスが kill されない
   ```bash
   sudo loginctl enable-linger {USER}
   loginctl show-user {USER} | grep Linger    # Linger=yes を確認
   ```
2. **chain の外側に supervisor ループを置く** — chain が完走マーカーを出さずに終了したら自動再投入。
   chain 側は**冪等**にする（最終 epoch のチェックポイントが既にあれば SKIP）ので
   完了済み run はやり直されない。**無限ループ防止に再投入回数の上限**（5 回程度）を付ける

- ⚠ **学習中のセッションに `attach` するのも危険**（attach 経由で同じ消滅が起きた実例がある）。
  監視は `tail -F` / `capture-pane` の**読み取り専用**にする
- `setsid` で切り離す手もあるが、**進捗バーが読めなくなる**（→「進捗の読み方」）ので
  tmux + supervisor の組み合わせを優先する

## 監視

🔴 **監視を「沈黙 = 正常」にしてはいけない。**

**なぜ**: 「epoch が変わったら通知」という設計は、**停滞すると黙り込む**。
沈黙は「順調」と「死亡」と「ハング」の区別がつかない。

**実測例（あるコンペ）**: 通知が epoch 遷移だけで、しかも失敗検出の grep が
`out of memory` しか見ていなかったため、実際のログ文字列（`OOM on device`）を拾えず
`errs=0` と報告していた。学習は OOM 警告を出しながら回っていた。

**学習監視には必ず 2 つを入れる**:

- **(a) 停滞検出**: N 分 epoch が進まなければ通知する（正常系でも定期的に生存を報告させる）
- **(b) 失敗シグネチャの網羅**: 1 つの文字列に賭けない
  ```bash
  grep -nE "Traceback|Killed|CUDA error|RuntimeError|OOM|out of memory|Segmentation fault" train.log
  ```

## 監視自体を検証する

🔴 **停滞検出と失敗シグネチャを入れても、監視スクリプトが最初から動いていなければ全部無意味。**

あるコンペでは同日に 2 件の実例が出た。どちらも「監視は黙っていた／異常を報告した」が、
**真因は監視側**だった。

| 症状 | 真因 | 危険 |
|---|---|---|
| 出力が 0 バイトで一度も通知が来ない | 参照先が存在しないパス（そのインスタンスにその階層が無い） | **沈黙を「順調」と誤読**。停滞検出も一度も走らない |
| 「ssh 応答なし — 中断の疑い」を報告 | 🔴 **監視側のシェルバグ**。インスタンスも学習も完全に無事（epoch 7 / GPU 99%） | **健全なインスタンスを止めて学習を焼き直す**恐れ |

- 🔴 **監視スクリプトを走らせるシェルの語彙を確認する。** zsh はクォートなしの変数展開を
  ワード分割しない。`SSH="<ssh コマンド> --command"` を `$SSH 'script'` で呼ぶと
  文字列全体が 1 個のコマンド名として扱われ **即 rc=127** で落ちる
  （bash なら動く書き方なので気づきにくい）。
  → **コマンドは変数に入れず直書きする**。どうしても変数化するなら zsh では `${=SSH}`
- 🔴 **`2>/dev/null` で stderr を捨てると、この種のバグが「応答なし」に化ける。**
  疑ったら**前景で同一コマンドを実行して rc と stderr を見る**（それで 30 秒で判明した）

**必須手順**:

1. **監視を張ったら、第 1 イベントが実際に出るまで確認する。**
   通知が来るまで「張れた」と見なさない（スクリプト側に `first` フラグを置いて
   初回は無条件に現状を出力させるのが確実）
2. **参照するパス・マーカー名は、前景の ssh で存在を確認してから監視に埋める**
3. 🔴 **監視の異常報告を単独で信じない。独立系統で照合する**
   （ssh 不通 → provider の CLI でインスタンスの STATUS を見る）。
   監視は「学習の状態」ではなく **「監視 + ssh + 学習の合成状態」**を見ている

## プロセスの停止

🔴 **ssh の `--command` で `pkill -f` を使うと、自分の ssh セッションを殺す。**

**なぜ**: `pkill -f` はプロセスのコマンドライン全体を照合する。リモートで実行されるシェルの
コマンドラインにはパターン文字列そのものが含まれるため、**自分自身がマッチ対象になる**。
ローカルシェルでも同じ罠があるが、ssh 経由だと**「接続エラー」に見えて原因を誤診しやすい**
（実例: `return code 255` で落ち、狙った学習プロセスまで到達せず止め損なった）。

**ブラケットトリックで回避する**:

```bash
pgrep -af "[s]upervisor_train"     # 確認
pkill -f  "[s]upervisor_train"     # 実行（自分にはマッチしない）
```

正規表現として `[s]` は `s` にマッチするが、自分のコマンドライン中のリテラル
`[s]upervisor_train` はパターン `[s]upervisor_train` にマッチしない。

⚠ **停止順序も重要**: **supervisor を先に止めてから学習プロセスを止める**
（逆順だと supervisor が再投入してしまう）。

## 進捗の読み方

🔴 **ステップ進捗はログではなく画面を読む。**

**なぜ**: Rich 系のプログレスバー（Lightning の `RichProgressBar` 等）は ANSI エスケープで
同じ行を書き換え続けるので、`> train.log` や `tmux pipe-pane` には**エスケープ断片しか残らない**。
`tail -f train.log` ではステップ進捗（`Epoch 3/11 ━━━ 49/869`）が見えない。
さらに **`| tee` でパイプすると Rich が「非対話」と判定して live バーの描画自体をやめる**ため、
tmux ペインにも何も出なくなる。

epoch 単位の検証メトリクスと `logger.info` は普通にログに残るので、
**「秒単位のステップ進捗が見たいときだけ画面を読む」**という使い分けが正しい。

```bash
# 学習は「パイプなしで」tmux に起動して stdout を pty のままにする
tmux new-session -d -s train "bash chain.sh"

# ログが欲しければ別アーカイブする（バーは残らないが logger.info は残る）
tmux pipe-pane -o -t train 'cat >> train.log'

# attach 不要のワンショット
tmux capture-pane -p -t train | tail -5
```

## herdr の使い方

**タブ名はマシン名で揃え、実験名はペイン名に入れる。**

- タブ名は学習マシンごとの**短いニックネーム 1 語**（例: `local` = 手元のマシン、
  `heron` / `otter` = クラウドの学習インスタンス）。長いとサイドバーで判別しづらい
- **実験名はタブ名ではなくペイン名**に入れる（例: `train: run007→run008 (heron)` / `gpu (heron)`）。
  実験が切り替わってもタブ名は変えず、ペイン名だけ更新する

```bash
herdr tab create --workspace {WS} --label "{nickname}"
herdr pane rename <PANE> "train: {run_name} ({nickname})"
```

**生画面をペインに映す（`-t` = TTY 割当が必須）**:

```bash
herdr pane run <PANE> "ssh -t -i ~/.ssh/id_ed25519 -o IdentitiesOnly=yes \
  -p {PORT} {USER}@{HOST} 'tmux attach -t train'"

herdr pane read <PANE> --source visible    # 今のバーがそのまま読める
```

- ⚠ `--source recent` は代替スクリーンを使うアプリだと**空になる**ので `visible` を使う
- ⚠ chain が run を切り替えるときに tmux session が kill → 再作成されると attach が exit する。
  **監視ループ側で自動再接続させる**（付録の `watch_train.sh` 相当）
- ⚠ 学習中セッションへの attach は生存性のリスクがある（→「生存性」）。
  長時間張り続けるなら `capture-pane` のポーリングに切り替える

## 付録: provider 別の手順

固有名詞はすべて placeholder。コンペ開始時に自分の値へ置き換える。

### GCP（Compute Engine）

**作成（デフォルト: 中位 GPU の Spot）**:

```bash
PROJECT_ID={PROJECT}
ZONE={ZONE}                 # 在庫がない場合は近隣ゾーンを試す
SERVICE_ACCOUNT={SA}

# ドライバ入りイメージの family 名は変わることがあるので実行前に確認する
gcloud compute images list --project=deeplearning-platform-release \
  --no-standard-images | grep -E "common|pytorch"

gcloud compute instances create {INSTANCE} \
  --project="$PROJECT_ID" --zone="$ZONE" \
  --machine-type={MACHINE_TYPE} \
  --provisioning-model=SPOT \
  --instance-termination-action=STOP \
  --image-family={IMAGE_FAMILY} \
  --image-project=deeplearning-platform-release \
  --metadata=install-nvidia-driver=True \
  --boot-disk-size={DISK}GB --boot-disk-type=pd-balanced \
  --service-account="$SERVICE_ACCOUNT" --scopes=cloud-platform
```

- データは boot disk（インスタンス削除と同時に消える）に置けば十分。
  容量は「前処理済みデータ + OS/環境 + キャッシュ」で見積もる
- Spot 中断時は STOP で残る → 在庫が戻れば `instances start`、戻らなければ削除して別ゾーンに作り直す
  （チェックポイントはオブジェクトストレージにあるので失うものはない）

**セットアップ + ステージング**（ssh 後、tmux 内で）:

```bash
tmux new -s train
git clone <repository-url> {repo} && cd {repo}
curl -LsSf https://astral.sh/uv/install.sh | sh && source ~/.local/bin/env
uv sync --extra torch

# ⚠ `uv sync --extra torch` 済みの環境なら、素の `uv run python -m ...` で extra は維持される
#   （他ドキュメントとスキルはこの素の形を使っている）。
#   `--extra torch` を明示するのは次の場合: extra を入れていない環境、
#   別のセッション・スクリプトが `uv sync`（extra なし）を打ち得る場合、
#   VM を作り直した直後で同期状態が不明な場合。迷うならこちらを使えば副作用はない

uv run wandb login

# 学習データのステージング（バージョンは実験 config と一致させる）
# ⚠ メタデータ CSV も必須。漏れると起動直後に FileNotFoundError で即死する
mkdir -p input/processed
gcloud storage cp gs://{BUCKET}/metadata/{ver}/train.csv input/
gcloud storage rsync -r gs://{BUCKET}/processed/{ver} input/processed/{ver}
```

**終了**:

```bash
gcloud storage rsync -r src/{exp_name}/output/{run_name} \
  gs://{BUCKET}/experiments/{exp_name}/{run_name}

gcloud compute instances delete {INSTANCE} --zone="$ZONE" --quiet
```

⚠ **セッション終了時にインスタンスが残っていないか必ず確認する**
（`gcloud compute instances list --project={PROJECT}`）。
放置コストの発生源は「消し忘れたインスタンス / ディスク」だけである。

### RunPod

ヘルパー一式をホーム直下（例: `~/.{project}-runpod/`）にまとめ、
**pod を作り直したら `POD_ID` の 1 行を書き換えるだけ**にする。

| ファイル | 役割 |
|---|---|
| `pod.env` | `POD_ID` / `NETWORK_VOLUME_ID` / `DATA_CENTER` / `IMAGE` / `GPU_ID`。値にスペースが入るのでクォートする（IP / PORT は `runpodctl ssh info` から都度解決） |
| `ssh.sh` | SSH 共通ラッパ（`-o IdentitiesOnly=yes` を必ず付ける） |
| `watch_train.sh` / `watch_gpu.sh` | herdr ペイン用の常時監視（自動再接続つき） |
| `snap.sh` | `tmux capture-pane` のワンショット（attach 不要） |
| `monitor_chain.sh` | チェックポイント名から epoch 完了を、ログから失敗を検出してイベント出力 |

pod は使い捨て設計にし、**環境はすべて network volume 側に永続化する**
（クラウド SDK・認証情報・前処理済みデータ・wandb の `.netrc`・repo と仮想環境）。

**踏んだ罠**:

- 仮想環境が network volume（分散 FS）上にあると、重いライブラリの import 走査に **5〜8 分**かかる。
  ハングではないので待つ（`/proc/PID/io` の `rchar` が伸びていれば正常）
- network volume はデータセンター固定なので **DC を変えられない**。
  人気 GPU は在庫切れになりやすいので、**在庫確認 API を見てから pod を作る**
- 自作イメージで pod が `RUNNING` なのに `ssh info` が "pod not ready" のまま死ぬ事例があった。
  **公式イメージだと即 SSH 可能**
