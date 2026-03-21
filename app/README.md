# Kaggle Dashboard App

FastAPI + htmx + Jinja2 によるダッシュボード。

## 起動方法

```bash
just app
# または
uv run uvicorn app.main:app --reload
```

アクセス: http://localhost:8000

## 技術スタック

| 技術 | 用途 | 読み込み方法 |
|------|------|-------------|
| FastAPI | Web フレームワーク | pip (dev 依存) |
| Jinja2 | テンプレートエンジン | pip (dev 依存) |
| nh3 | HTML サニタイズ (XSS 防止) | pip (dev 依存) |
| htmx 1.9.10 | 動的 UI 更新 | ローカル (`static/js/`) |
| Tailwind CSS + typography plugin | スタイリング | CDN |
| FontAwesome 6 Free | アイコン | CDN |
| Nunito (Google Fonts) | フォント | CDN |
| highlight.js 11.9.0 | シンタックスハイライト | ローカル (`static/`) |
| Chart.js 4.4.7 | スコアグラフ・OOF 可視化 | ローカル (`static/js/`) |

## スタイリング規則

### フォント

Nunito (wght 400/600/700/800)。Duolingo 風の丸みのあるフレンドリーなフォント。

### カラーパレット

| 用途 | Tailwind クラス | Hex |
|------|----------------|-----|
| アクセント | `emerald-500` | `#10b981` |
| アクセントホバー | `emerald-600` | `#059669` |
| アクセント薄背景 | `emerald-50` | `#ecfdf5` |
| ページ背景 | `gray-50` | `#f9fafb` |
| カード/サイドバー | `white` | `#ffffff` |
| テキスト（主） | `text-gray-800` | `#1f2937` |
| テキスト（副） | `text-gray-500` | `#6b7280` |
| テキスト（ミュート） | `text-gray-400` | `#9ca3af` |
| ボーダー | `border-gray-200` | `#e5e7eb` |

カードごとのアクセントカラー: emerald / amber / sky / rose

### コンポーネント規則

| コンポーネント | クラス |
|---------------|--------|
| カード | `bg-white rounded-2xl shadow-sm border border-gray-200` (hover: `shadow-md`) |
| ボタン (primary) | `bg-emerald-500 text-white rounded-full font-bold` (hover: `bg-emerald-600`) |
| バッジ | `rounded-full bg-{color}-50 text-{color}-600 text-xs font-semibold px-3 py-1` |
| ナビアイテム | `rounded-xl text-sm font-semibold` (active: `bg-emerald-50 text-emerald-600`) |
| アイコン背景 | `rounded-xl w-{size} h-{size} bg-{color}-50 flex items-center justify-center` |
| 影 | 通常 `shadow-sm`、ホバー `shadow-md` |

### アイコン

FontAwesome 6 Free (`fa-solid` 系) を使用。絵文字は使わない。

## レイアウトパターン

### サイドバー

- 固定幅 `w-64`、左端固定
- トグルボタンで非表示切替（`-translate-x-full` + `ml-0`）
- `localStorage('sidebar-collapsed')` で状態永続化
- Experiments, Data はシンプルリンク（サブアイテムなし）
- Knowledge のみ折りたたみ可能なサブアイテム（Official / Insights / Discussion）
  - ラベル（`<a>` でページ遷移）+ シェブロンボタン（展開/折りたたみ）
  - 展開状態は `localStorage('subnav-{id}')` で永続化
  - Knowledge ページにいるときは自動展開
  - サブアイテムに `active_subpage` による active 状態表示
- ナビ部分のみ `overflow-y-auto` でスクロール
- フッターなし（不要な情報を排除）

### メインコンテンツ

- `ml-64`（サイドバー表示時）/ `ml-0`（非表示時）
- CSS transition で滑らかに切替

### ページ幅の使い分け

`{% block content_width %}` で調整。デフォルトは `max-w-7xl mx-auto`。

| ページ種別 | `content_width` | 理由 |
|-----------|-----------------|------|
| Home | `max-w-4xl mx-auto` | コンパクトなダッシュボード |
| カード一覧（Knowledge トップ等） | `max-w-5xl mx-auto` | 3カラムカードに適した幅 |
| ドキュメント閲覧 | `max-w-4xl mx-auto` | 読みやすい散文幅 |
| テーブル・データ | `max-w-7xl mx-auto` | 全幅活用 |
| ファイルブラウザ（Data） | （デフォルト） | ページ内2カラム |

### 禁止パターン

- **2重サイドバー**: サイドバー内にさらにサイドバーを配置しない。Data ページのファイルツリーのようなページ固有の UI は例外。

## ナビゲーションパターン

### サイドバーのアクティブ状態

テンプレートに `active_page` 変数を渡し、サイドバーで条件分岐:
```jinja2
{% if active_page == 'experiments' %}bg-emerald-50 text-emerald-600{% else %}text-gray-500 ...{% endif %}
```

### パンくずナビ

階層の深いページ（Knowledge のドキュメント詳細等）ではパンくずナビを表示:
```html
<nav class="flex items-center gap-2 text-sm text-gray-500 mb-6">
    <a href="/knowledge" class="hover:text-emerald-500 font-semibold">Knowledge</a>
    <i class="fa-solid fa-chevron-right text-xs text-gray-300"></i>
    <span class="font-semibold text-gray-800">Current Page</span>
</nav>
```

## ページ構造パターン

### 階層遷移パターン（Knowledge）

トップ → カテゴリ → 詳細 の3階層:
- `/knowledge` — カテゴリカード表示
- `/knowledge/{category}` — ドキュメント一覧
- `/knowledge/{category}/{filename}` — ドキュメント全幅表示

カテゴリは `VALID_CATEGORIES` + `CATEGORY_META` で管理。

### ページ内2カラムパターン（Data）

左にファイルツリー + 右にプレビュー:
- ファイルツリーのディレクトリは htmx で遅延展開
- ファイルクリックで右パネルにプレビューを表示

### htmx 遅延読み込みパターン

ディレクトリやリストの遅延展開:
```html
<button hx-get="/data/tree/{{ path }}"
        hx-target="next ul"
        hx-swap="innerHTML"
        hx-trigger="click once">
    <i class="fa-solid fa-chevron-right"></i>
</button>
<ul></ul>
```

## ディレクトリ構成

```
app/
├── README.md           # このファイル
├── main.py             # FastAPI アプリ本体、Router 登録、エラーハンドリング
├── template_env.py     # 共有 Jinja2 テンプレート環境（単一インスタンス）
├── services/           # ビジネスロジック
│   ├── helpers.py      # 汎用ヘルパー（パス検証、サイズ変換等）
│   ├── experiments.py  # 実験管理（一覧、詳細、OOF、スコア）
│   ├── documents.py    # ドキュメント・Markdown 処理
│   └── data.py         # データファイル操作（CSV、画像等）
├── static/             # ローカル静的ファイル
│   ├── css/            # highlight.js CSS
│   └── js/             # htmx, highlight.js, Chart.js
├── pages/              # 各ページの APIRouter
│   ├── experiments.py  # 実験一覧 + 詳細 + OOF + スコア
│   ├── knowledge.py    # 知識ベース（official / insights / discussion）
│   └── data.py         # データ閲覧（input/ 配下）
└── templates/
    ├── base.html           # 共通レイアウト（サイドバー + メイン）
    ├── error.html          # エラーページ
    ├── index.html          # ホームページ
    ├── components/         # 再利用可能な Jinja2 マクロ
    ├── partials/           # htmx 差し替え用パーシャル
    ├── experiments/        # 実験ページ
    ├── knowledge/          # 知識ベースページ（index / category / document）
    └── data/               # データ閲覧ページ
```

## アーキテクチャ

### テンプレート環境の共有

`template_env.py` に単一の `Jinja2Templates` インスタンスを定義。全ページモジュールがこれをインポートすることで、フィルタ・グローバル関数の登録が一箇所で完結する。

### サービス層

`app/services/` にビジネスロジックを分離。各ページモジュールは `app.services.*` から直接インポートする。

### エンドポイント定義

全エンドポイントは `def`（非 `async`）で定義。FastAPI が自動でスレッドプールで実行するため、同期 I/O（ファイル操作、Polars、YAML パース等）がイベントループをブロックしない。

## htmx パターン

### Full page vs Partial 出し分け

`HX-Request` ヘッダーの有無で、同一エンドポイントから full page か partial を返す:

```python
from app.services.helpers import is_htmx

@router.get("/experiments")
def experiment_list(request: Request):
    template = "partials/_experiment_list.html" if is_htmx(request) else "experiments/list.html"
    return templates.TemplateResponse(template, {...})
```

### 検索フィルタ

```html
<input type="search" name="q"
       hx-get="/experiments"
       hx-trigger="keyup changed delay:300ms"
       hx-target="#results">
```

### タブ切り替え

```html
<button hx-get="/experiments/{name}/_config"
        hx-target="#tab-content">
    Config
</button>
<div id="tab-content">...</div>
```

### ローディングインジケーター

グローバルインジケーター（ページ上部のエメラルドバー）が `base.html` に組み込み済み。

## 新しいページの追加方法

**まずサブページとして追加できないか検討する**（詳細は `.claude/skills/kaggle-add-app-page/SKILL.md` を参照）。

新規トップレベルページが必要な場合:

1. `app/pages/xxx.py` に `APIRouter` を作成
2. `app/templates/xxx/` にテンプレートを配置
3. `app/main.py` で `app.include_router(xxx.router)` を追加
4. `base.html` のサイドバーに折りたたみナビアイテムを追加
5. `index.html` の Home カードグリッドにカードを追加

## Jinja2 コンポーネントの使い方

```jinja2
{% from "components/_metric_card.html" import metric_card %}
{% from "components/_badge.html" import badge %}
{% from "components/_data_table.html" import data_table %}

{{ metric_card("CV Score", "0.95", icon="fa-chart-line", color="emerald") }}
{{ badge("completed", color="emerald", icon="fa-check") }}
{{ data_table(columns, rows) }}
```
