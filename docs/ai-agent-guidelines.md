<!-- lifecycle: invariant -->
# AI エージェント運用ガイドライン

CLAUDE.md の「AI エージェントへの注意」を補完する詳細ガイド。
Kaggle 金メダリストの実戦知見（kinosuke 氏の Image2Biomass 5位解法等）に基づく。

## 運用の合意（Working Agreements）

エージェントの実行時の既定値は **`docs/competition-profile.yaml` の `workflow` ブロックが正本**
（値と選択肢はそちらを見る。`/kaggle:init` が対話で埋める）。ここには各項目を**なぜそうするか**だけを書く。

| 項目 | なぜ |
|---|---|
| `default_run_mode` | GPU 時間の節約。fold0 で有望と分かった run だけを、ユーザーの明示指示で full に昇格させる。アンサンブル・提出で全 fold が必要になったら昇格を提案して承認を得る |
| `submission_by` | 提出枠は 1 日数回しかなく、ユーザーが手元で提出することもある。二重提出は枠を無駄に消費する。`user` の間、エージェントは notebook の commit・出力確認までで止め、貼り付け用の description（`describe_manifest()` の出力）を添えて引き渡す |
| `branching` | 実験ブランチ運用で同内容が別 SHA で二重コミットされ、統合時にマージ衝突が起きた |
| `concurrent_sessions` | 複数セッションが**同じ作業ディレクトリの同一実体**を編集する。`git status` の未コミット変更が自分のものだとは限らない |
| `remote_training` | リモート GPU を使う場合の運用は `docs/remote-training-ops.md` |
| `max_runs_per_exp` | 超えると README で「何の 1 変数差分だったか」が追えなくなる（実コンペで 26 run / 14 run の exp が発生した） |

### 併走セッション前提の作業規律

`concurrent_sessions: true` のとき、相手の未コミット作業を巻き込む・消す git 操作
（`git add -A` / `git commit -a` / `git stash` / `git reset --hard` / `git restore` 等）と、
`submission_by: user` のときの提出は `.claude/hooks/guard.py` が止める
（**止める操作の一覧と理由は guard.py の docstring が正本**）。hook に頼らず、次も守る:

- **`git add` は常にパスを明示する**
- ⚠ **共有ファイル**（`docs/guardrails.md` / `EXP_SUMMARY.md` 等）は複数セッションの集約先。
  コミット前に `git diff <file> | grep "^+## "` で追加された節の持ち主を確認する。
  末尾への連続追記は hunk が 1 個にまとまるので `git add -p` の split は当てにできない。
  両者の作業が混在したら片方がまとめて 1 コミットにし、メッセージに両方の由来を書く
- ⚠ **run 番号は予約も含めて確認する**: `config/` の既存ファイルだけを見て次の空き番号を決めない。
  `grep -rnE "run[0-9]{3}" docs src` で plans / specs の予約も見る

### 情報源の優先順位

1. **`kaggle` CLI**（`uv run kaggle ...`）: LB・提出履歴・データ・notebook など CLI で取れるものはすべてこちら。
   クラウド（`gcloud` 等）も CLI を主経路にする
2. **Kaggle MCP**: Writeup・Discussion など **CLI で取れないもの**に使う。
   未認証だと公開ツールが `authenticate` だけになり、気づかないまま「使えない」状態になる（`/mcp` で認証）
3. **WebFetch / Web 検索**: 上の 2 つで取れないときだけ

提出系の API・コマンドはどの経路でも使わない（`workflow.submission_by: user` の間）。

## アイデアの役割分担

AI は実験の候補を出してよい。ただし**採否と優先順位は人間が決める**。
この 2 つを両立させるため、候補の作り方に条件を付ける:

- **候補は問題設定・データの特性・公開情報（Discussion・過去解法）から生成する。**
  EXP_SUMMARY.md の失敗履歴（dead・棄却理由）から「次の一手」を導かない
- **失敗履歴は「同じ失敗を繰り返さない」ためのフィルタとしてだけ使う。**
  生成した候補が過去の失敗と同一でないかを照合する用途に限る
- 失敗履歴を発想の起点にすると、AI は過度に消極的になり「もう打ち手がない」と撤退を提案し始める。
  また過去の「効かなかった」は判定の資格を欠いていることが多い（`docs/experiment-methodology.md`「判定の資格」）

### AI に積極的に任せてよいタスク

- OOF 予測の誤差分析（どのカテゴリ・サンプルで外しているか）
- CV-LB 相関の可視化と傾向把握
- Public Notebook / Discussion の要約・比較
- 実験結果の可視化・レポート作成（`docs/insights/` に Markdown で残す）
- 実装（train / inference パイプライン、モデル定義、前処理）
- 問題設定とデータ特性からの候補の列挙（上の条件つき）

### 人間が判断すべきタスク

- 候補の採否と優先順位
- CV 設計の方針（データのどの軸で分割すべきか）
- コンペ特有のドメイン知識に基づく仮説の確定

### AI の提案の注意点

「精度を上げろ」のようなアバウトな指示には教科書的な施策（アンサンブル、TTA、正規化追加等）しか出てこない。
コンペ固有の本質的な改善は、データを観察して立てた仮説から出てくる。

AI が出しがちで、効くかどうかを AI 自身が判断できない提案の典型:

| AI の提案パターン | 問題点 |
|-----------------|--------|
| 苦手カテゴリの loss weight 変更 | Train の分布を歪め、CV↑ LB↓ になりがち |
| 推論時のスコア補正（1.2倍等） | 根拠のない後処理で汎化しない |
| EMA（指数移動平均） | 過学習を助長する場合がある |
| 補助タスクの追加 | タスク設計が雑だと主タスクの学習を阻害 |

これらが悪いわけではない。提案には「なぜ今のデータ・タスクで効くと考えるか」の仮説を添え、
人間がその仮説を持てるかどうかで採否を決める。

## コンペ中のガードレール蓄積

コンペ進行中に発見したバグや AI の繰り返しミスは **`docs/guardrails.md`** に蓄積する
（CLAUDE.md はコンペごとに書き換えない）。コンペ非依存の作法は `docs/experiment-methodology.md` に書く。
どちらに書くかは `docs/README.md` の「知見の routing」表に従う。

`docs/guardrails.md` に記載すべき項目:

- **評価関数**: 正しい実装と間違った実装の両方（正しい実装の実体は `src/metric.py`）
- **既知のバグパターン**: AI が繰り返すミス
- **やってはいけないこと**: LB を下げることが判明した施策（理由付き）
- **変数名・形式の注意**: `inference.py` の出力形式、submission の列名等

記載例:

```markdown
### 評価関数
正しい実装:
  sklearn.metrics.root_mean_squared_error(y_true, y_pred)
間違った実装（過去に2回発生）:
  np.sqrt(np.mean((y_true - y_pred) ** 2))  # NaN がある場合に結果が異なる

### やってはいけないこと
- Species ごとの loss weight 変更 → CV↑ LB↓（exp023 で確認済み）
- 推論時のカテゴリ別スコア補正 → LB 悪化（exp031 で確認済み）
```

## 実験サイクル

1. **人間 / AI**: データを観察し、仮説の候補を出す（AI の候補は上の条件つき）
2. **人間**: 採る仮説を決め、具体的に指示する
3. **AI**: 実装する（`train.py` / config / `inference.py`）
4. **人間 / AI**: 実行し結果を取得する
5. **AI**: 結果を分析・可視化する（OOF 分析、誤差傾向等）。`/kaggle:record-result` で記録する
6. **人間**: 分析結果を見て次の仮説を選ぶ（→ 1 に戻る）
