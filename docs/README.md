# docs ディレクトリ

このディレクトリはコンペティションに関する情報を整理して管理します。

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
