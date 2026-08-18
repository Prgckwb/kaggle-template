<!-- lifecycle: invariant -->
# docs ディレクトリ

このディレクトリはコンペティションに関する情報を整理して管理します。

## lifecycle 二層

各ドキュメントの 1 行目に lifecycle マーカーがある。

| マーカー | 意味 |
|---|---|
| `<!-- lifecycle: invariant -->` | コンペを跨いで持ち越す。`/kaggle:init` は触らない |
| `<!-- lifecycle: per-competition -->` | コンペ固有。`/kaggle:init` がテンプレート状態にリセットする |

| ファイル | lifecycle | 役割 |
|---|---|---|
| `ai-agent-guidelines.md` | invariant | 人間と AI の分担 + 運用の合意（Working Agreements） |
| `experiment-methodology.md` | invariant | 効果の帰属・判定の資格・対照群の設計（コンペ非依存の実験作法） |
| `remote-training-ops.md` | invariant | リモート GPU 学習の運用と監視（herdr 前提） |
| `wandb-spec.md` | invariant | wandb の k-fold ログ方針 |
| `experiment-formats.md` | invariant | EXP_SUMMARY の記述フォーマット |
| `competition-types.md` | invariant | supervised / optimization / simulation の解釈 |
| `competition-profile.yaml` | per-competition | コンペ固有値の SSOT（`/kaggle:init` が書く） |
| `training-conventions.md` | per-competition | 学習実験の規約（コンペ固有の穴埋めつき） |
| `guardrails.md` | per-competition | 評価関数の正誤・既知のバグパターン・やってはいけないこと |
| `submissions.md` | per-competition | 全提出のログ（SSOT） |
| `experiment-log.md` | per-competition | 実験台帳（時系列 + 探索バックログ） |
| `official/` `discussion/` `insights/` `guides/` | per-competition | 収集物・知見・レポート（マーカー不要） |

**新しいドキュメントを `docs/` 直下に置いたら、マーカーとこの表の行を必ず追加する。**

## ディレクトリ構成

### `official/`

Kaggle 公式から提供される情報を記載します。

- コンペティションの概要・ルール
- 評価指標の詳細
- データの説明
- 制約事項

**例**: `overview.md`, `data.md`

### `discussion/`

外部から収集した情報を記載します（Kaggle Discussion のほか、`kaggle-researcher` エージェントによる論文・過去解法サーベイの成果物もここに置く）。

- 他の参加者からの知見・Tips
- 有用なコード片やアプローチ
- バグ報告や注意点
- データに関する追加情報
- 論文・外部資料のサーベイ結果

**命名規則**: `YYYY-MM-DD_topic.md`

### `guides/`

ダッシュボードの **Knowledge → Guides** に自動表示されるガイド・分析レポート置き場（1ガイド = 1ディレクトリ、`guide.json` + `index.html`）。評価指標の解説、EDA レポート、OOF エラー分析、リプレイビューア等の「HTML で見やすく表示して見返したいもの」はすべてここに置く。`/kaggle:create-guide` で作成できる。規約は `guides/README.md`。

### `guardrails.md`

コンペ進行中に発見した評価関数の正誤・既知のバグパターン・「やってはいけないこと」を蓄積するファイル。AI エージェントは実験の実装・修正・提案の前に必ず参照する。`/kaggle:init` がテンプレート状態にリセットする。運用方針は `ai-agent-guidelines.md` を参照。

### `submissions.md`

提出履歴の Single Source of Truth。すべての提出（日付・Exp/Run・ファイル・CV・Public LB・提出理由）を1行ずつ記録する。CV-LB 相関分析と終盤の final submission 選定の元データ。`/kaggle:record-result` が LB 記録時に追記する。

### `ai-agent-guidelines.md`

AI エージェント運用の詳細ガイド（人間と AI の役割分担、失敗履歴の読ませ方、ガードレール運用）。CLAUDE.md の「AI エージェントへの注意」を補完する。

### `insights/`

自分の実験から得られた知見を記載します。

- 実験結果の考察
- 失敗した試みとその理由
- 有効だったテクニック
- 今後試すべきアイデア

**命名規則**: `YYYY-MM-DD_topic.md`

**自動生成されるもの**: `past_solutions_{competition_slug}.md` は `/kaggle:past-solutions` スキルが Kaggle MCP（or `kaggle` パッケージによるフォールバック）経由で類似過去コンペの上位解法を収集して生成する。新コンペ開始時の初期仮説づくりに使う。
