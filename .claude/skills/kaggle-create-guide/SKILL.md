---
name: kaggle:create-guide
description: ダッシュボードの Guides に表示されるガイド・分析レポート（HTML）を対話的に作成する。
argument-hint: [ガイドの概要（例: 評価指標の解説、exp001 の OOF エラー分析）]
disable-model-invocation: true
allowed-tools: Bash, Read, Write, Edit, Glob, Grep
---

# ガイド・分析レポートを作成する

`docs/guides/{slug}/` に guide.json + index.html を作成する。作成したガイドはダッシュボードの
**Knowledge → Guides**（`/knowledge/guides`）に自動で表示される。アプリのコード変更は不要。

規約の詳細は `docs/guides/README.md`、実装例は `docs/guides/sample-guide/` を参照。

## ガイドの用途（すべてここに集約する）

- **guide**: 評価指標の解説、ドメイン知識の入門、手法の説明 等
- **eda**: データの探索的分析レポート（分布・欠損・相関の図と所見）
- **analysis**: OOF エラー分析、CV-LB 相関、実験比較レポート
- **viewer**: シミュレーションのリプレイビューア、インタラクティブな可視化ツール

分析画像は `docs/guides/{slug}/assets/` に置く（旧 `app/static/analysis/` への配置は廃止）。

## フェーズ 1: 要件のヒアリング

1. $ARGUMENTS があればそこから意図を読み取る。なければ質問する:
   - 「何を説明・可視化するガイドですか？」
   - 「読者は誰ですか？（未来の自分 / チームメイト / 実験の記録）」
2. 内容の素材を確認する:
   - 説明系 → `docs/official/` `docs/insights/` `docs/competition-profile.yaml` を Read して正確な情報源を押さえる
   - 分析系 → 対象データ・OOF・ログの場所を確認し、必要なら sandbox/ で図を生成する
3. slug（ケバブケース英語）とタグをユーザーと合意する

## フェーズ 2: render 方式の決定

| 方式 | 選ぶ基準 |
|------|---------|
| `iframe`（デフォルト） | 独自の JS・インタラクティブ要素・大量の図がある。D3/Chart 等のライブラリを使う |
| `fragment` | 静的な説明が主で、アプリの見た目に溶け込ませたい。JS 不要 |

- `iframe` は自己完結 HTML（CSS/JS インライン or `assets/` 相対パス）。**外部 CDN は使わない**
- テーマ連携と高さ通知のスクリプトを必ず入れる（`sample-guide/index.html` からコピーする）
- `fragment` は `app/README.md` の「構造化ガイドデザインパターン」に従った Tailwind 断片（`<html>`/`<head>` なし、`dark:` クラスでダークモード対応）。**新しい Tailwind クラスを使ったら `make css` を実行する**
- TypeScript を使いたい場合: sandbox/ で esbuild 等でビルドし、成果物 JS のみを `assets/` に置く（アプリのビルドパイプラインには組み込まない）

## フェーズ 3: 作成

1. `docs/guides/{slug}/guide.json` を作成:

   ```json
   {
     "title": "{タイトル}",
     "description": "{1行説明}",
     "icon": "{FontAwesome 6 Free クラス}",
     "color": "{emerald|amber|sky|rose|violet|blue|red}",
     "tags": ["{guide|eda|analysis|viewer}"],
     "created": "{今日の日付 YYYY-MM-DD}",
     "render": "{iframe|fragment}"
   }
   ```

2. `index.html` を作成する。内容面の遵守事項:
   - 情報は必ず一次ソース（docs/official/、実データ、実ログ）に基づく。**推測で埋めない**
   - 数値・図は再現手順（生成スクリプトのパス）をガイド末尾に記載する
   - 見出し・セクション構成で「見返したときに 30 秒で要点が掴める」ことを優先する
3. 図を生成した場合は sandbox/ のスクリプトを残し、画像は `assets/` にコピーする

## フェーズ 4: 確認

1. `make app` が起動していれば `http://localhost:{port}/knowledge/guides/{slug}` を案内する
2. 表示確認の観点:
   - ライト/ダーク両テーマで読めるか（iframe はテーマ連携が効いているか）
   - iframe 内スクロールが発生していないか（高さ通知が効いているか）
3. 内容の正確性をユーザーに確認してもらう

## フェーズ 5: 完了報告

- 作成したファイル一覧と閲覧 URL（`/knowledge/guides/{slug}`）
- 素材にした情報源のリスト
- ガイドはコミット対象（`/kaggle:commit` を案内）
