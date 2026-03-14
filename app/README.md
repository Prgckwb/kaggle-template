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
| htmx 1.9.10 | 動的 UI 更新 | CDN |
| Tailwind CSS + typography plugin | スタイリング | CDN |
| FontAwesome 6 Free | アイコン | CDN |
| Nunito (Google Fonts) | フォント | CDN |

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

## ディレクトリ構成

```
app/
├── README.md        # このファイル
├── main.py          # FastAPI アプリ本体、Router 登録、Jinja2 フィルタ
├── utils.py         # 共通データ取得ユーティリティ
├── pages/           # 各ページの APIRouter
│   ├── __init__.py
│   ├── experiments.py  # 実験一覧 + 詳細
│   └── docs.py         # ドキュメント閲覧
└── templates/
    ├── base.html           # 共通レイアウト（サイドバー + メイン）
    ├── index.html          # ホームページ
    ├── components/         # 再利用可能な Jinja2 マクロ
    │   ├── _data_table.html
    │   ├── _metric_card.html
    │   ├── _badge.html
    │   ├── _empty_state.html
    │   ├── _yaml_viewer.html
    │   └── _markdown.html
    ├── partials/           # htmx 差し替え用パーシャル
    │   ├── _experiment_list.html
    │   └── _doc_content.html
    ├── experiments/
    │   ├── list.html       # 実験一覧ページ
    │   └── detail.html     # 実験詳細ページ
    └── docs/
        └── viewer.html     # ドキュメント閲覧ページ
```

## htmx パターン

### Full page vs Partial 出し分け

`HX-Request` ヘッダーの有無で、同一エンドポイントから full page か partial を返す:

```python
from app.utils import is_htmx

@router.get("/experiments")
async def experiment_list(request: Request):
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

1. `app/pages/xxx.py` に `APIRouter` を作成
2. `app/templates/xxx/` にテンプレートを配置
3. `app/main.py` で `app.include_router(xxx.router)` を追加
4. `base.html` のサイドバーにナビリンクを追加（コンペ固有なら `{% block sidebar_nav %}` を使用）

## Jinja2 コンポーネントの使い方

```jinja2
{% from "components/_metric_card.html" import metric_card %}
{% from "components/_badge.html" import badge %}
{% from "components/_data_table.html" import data_table %}

{{ metric_card("CV Score", "0.95", icon="fa-chart-line", color="emerald") }}
{{ badge("completed", color="emerald", icon="fa-check") }}
{{ data_table(columns, rows) }}
```
