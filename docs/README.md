<!-- lifecycle: invariant -->
# docs ディレクトリ

## lifecycle 二層

各ドキュメントの 1 行目に lifecycle マーカーを置く（YAML / Python は `# lifecycle: ...` のコメント形式）。

| マーカー | 意味 |
|---|---|
| `invariant` | コンペを跨いで持ち越す。`/kaggle:init` は触らない |
| `per-competition` | コンペ固有。`/kaggle:init` がテンプレート状態にリセットする |

| ファイル | lifecycle | 役割 |
|---|---|---|
| `README.md`（このファイル） | invariant | docs の地図・lifecycle・知見の routing |
| `ai-agent-guidelines.md` | invariant | 人間と AI の分担・運用の合意の理由 |
| `experiment-methodology.md` | invariant | 効果の帰属・判定の資格・停滞の定義などコンペ非依存の作法 |
| `remote-training-ops.md` | invariant | リモート GPU 学習の運用と監視 |
| `wandb-spec.md` | invariant | wandb のログ方針 |
| `competition-types.md` | invariant | supervised / optimization / simulation の解釈 |
| `competition-profile.yaml` | per-competition | コンペ固有値の SSOT |
| `training-conventions.md` | per-competition | 学習・出力契約・ckpt・提出 notebook・実行環境の規約 |
| `guardrails.md` | per-competition | 評価関数の罠・既知のバグ・やってはいけないこと |
| `submissions.md` | per-competition | 全提出のログ |
| `SESSION_NOTES.md` | per-competition | セッション間の引き継ぎ |
| `../EXP_SUMMARY.md` | per-competition | 実験一覧・ツリー・探索マップ・バックログ・ノイズ較正 |
| `../src/metric.py` | per-competition | 競技指標の実装 |
| `official/` `discussion/` `insights/` | per-competition | 収集物と知見（マーカー不要） |

**新しいドキュメントを `docs/` 直下に置いたら、マーカーとこの表の行を必ず追加する。**

## 知見の routing（どこに書くか）

`/kaggle:record-result` と `/kaggle:harvest-template` はこの表だけを基準に振り分ける。

| 知見の種類 | 書く先 | テンプレートへ還流するか |
|---|---|---|
| コンペ固有の罠（評価関数の誤実装・データの癖・LB を下げた施策） | `docs/guardrails.md` | しない |
| コンペ非依存の判定作法・実験設計の教訓 | `docs/experiment-methodology.md` | する |
| 人間と AI の働き方の合意（理由） | `docs/ai-agent-guidelines.md`（値は profile の `workflow`） | する |
| 実装上の工夫・ハマりどころ・分析レポート | `docs/insights/YYYY-MM-DD_topic.md` | 汎用部分だけ methodology / training-conventions へ |
| 学習・推論の規約の追加 | `docs/training-conventions.md` | 穴埋め部分以外はする |
| テンプレート自体の誤り（docs・スキル・コードの矛盾） | 該当の正本を直す | する |

## ディレクトリ

- `official/`: Kaggle 公式の情報（概要・ルール・評価指標・データ説明・制約）。例: `overview.md`, `data.md`
- `discussion/`: 外部から集めた情報（Discussion・公開 notebook・論文サーベイ。`kaggle-researcher` の成果物もここ）。
  命名 `YYYY-MM-DD_topic.md`
- `insights/`: 自分の実験・分析から得た知見とレポート（`kaggle-analyst` の成果物もここ。画像は `insights/assets/`）。
  命名 `YYYY-MM-DD_topic.md`。例外: `/kaggle:past-solutions` が作る `past_solutions_{slug}.md`
