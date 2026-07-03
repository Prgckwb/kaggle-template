# docs/guides — ガイド・分析レポート置き場

ダッシュボードの **Knowledge → Guides** に自動で一覧表示される成果物ディレクトリ。
評価指標の解説、EDA レポート、OOF エラー分析、シミュレーションのリプレイビューアなど、
「HTML で見やすく表示して見返したいもの」はすべてここに置く。

**1ガイド = 1ディレクトリ。追加にアプリのコード変更は不要**（`/kaggle:create-guide` で対話的に作成できる）。

## 構成

```
docs/guides/
├── {slug}/                 # ケバブケースのディレクトリ名が URL になる
│   ├── guide.json          # メタデータ（必須）
│   ├── index.html          # 本体（必須）
│   └── assets/             # 画像・ビルド済み JS 等（任意。名前は自由）
└── README.md               # このファイル（一覧には表示されない）
```

## guide.json

```json
{
  "title": "評価指標の完全ガイド",
  "description": "計算方法・エッジケース・最適化の考慮点",
  "icon": "fa-calculator",
  "color": "amber",
  "tags": ["guide"],
  "created": "2026-07-04",
  "render": "iframe"
}
```

| キー | 必須 | 説明 |
|------|------|------|
| `title` | 推奨 | カード・詳細ページの見出し（省略時は slug） |
| `description` | - | カードの説明文 |
| `icon` | - | FontAwesome 6 Free のクラス（デフォルト `fa-book-open`） |
| `color` | - | Tailwind 色ファミリー: emerald / amber / sky / rose / violet / blue / red（デフォルト `violet`） |
| `tags` | - | フィルタ用タグ。推奨語彙: `guide`（手引き・解説）, `eda`, `analysis`（OOF・CV-LB 等の分析レポート）, `viewer`（リプレイ・インタラクティブツール） |
| `created` | 推奨 | `YYYY-MM-DD`。一覧の並び順（降順）に使う |
| `render` | - | `iframe`（デフォルト）or `fragment`。下記参照 |

## render の選び方

### `iframe` — 自己完結 HTML（デフォルト）

`index.html` を sandbox 付き iframe で表示する。**CSS/JS を自由に持てて、アプリ本体と一切衝突しない。**
D3 等のインタラクティブ可視化、TS で書いた説明アプリ、リプレイビューアはこちら。

- CSS・JS はインライン or `assets/` 相対パスで自己完結させる（アプリの Tailwind は使えない）
- 外部 CDN は使わない（セルフホスト方針）。ライブラリが必要なら `assets/` に vendor する
- TypeScript を使う場合は sandbox/ でビルドし、**成果物 JS のみ** `assets/` に置く（アプリのビルドには組み込まない）

**テーマ連携プロトコル**（推奨。`sample-guide/index.html` に実装例）:

1. 初期テーマは URL クエリ `?theme=dark|light` で渡される
2. 切替はホストから `postMessage({type: "theme", theme: "dark"|"light"})` で通知される
3. 高さを伝えたい場合は `parent.postMessage({type: "guide-height", height: N}, "*")` を送る（iframe の内部スクロールが消える）

### `fragment` — Tailwind 断片

`index.html` の中身（`<div>` 断片。`<html>`/`<head>` は書かない）をページ内に直接埋め込む。
アプリの look & feel・ダークモードに完全統合される。JS を持たない、または最小限のガイド向け。

- `app/README.md` の「構造化ガイドデザインパターン」の HTML をそのまま使える
- ダークモードは `dark:` クラスで自前対応する
- **新しい Tailwind クラスを使ったら `make css` で再ビルドが必要**（ビルド対象に `docs/guides/**/*.html` が含まれる）

## 運用ルール

- コンペ固有の成果物なのでコミットしてよい（docs/ の他ファイルと同じ扱い）
- 分析画像は `assets/` に置き、ガイドから相対パスで参照する（旧 `app/static/analysis/` への配置は廃止）
- ファイルは `/knowledge/guides/{slug}/raw/{path}` で配信される（`index.html` からは相対パスで書けばよい）
