# Kaggle Dashboard App

FastAPI + htmx + Jinja2 によるダッシュボード。

## 起動方法

```bash
make app
# または
uv run uvicorn app.main:app --reload
```

アクセス: http://localhost:{port}（空きポートが自動選択される）

## 技術スタック

| 技術 | 用途 | 読み込み方法 |
|------|------|-------------|
| FastAPI | Web フレームワーク | pip (dev 依存) |
| Jinja2 | テンプレートエンジン | pip (dev 依存) |
| nh3 | HTML サニタイズ (XSS 防止) | pip (dev 依存) |
| htmx 1.9.10 | 動的 UI 更新 | ローカル (`static/js/`) |
| Tailwind CSS 3.4 + typography plugin | スタイリング | ビルド済み CSS (`static/css/app.css`、`make css` で再ビルド) |
| FontAwesome 6.5.1 Free | アイコン | ローカル (`static/css/` + `static/webfonts/`) |
| Nunito | フォント | ローカル (`static/css/fonts.css` + `static/fonts/`) |
| highlight.js 11.9.0 | シンタックスハイライト | ローカル (`static/`) |
| Chart.js 4.4.7 | スコアグラフ・OOF 可視化 | ローカル (`static/js/`) |
| wavesurfer.js 7 | 音声プレビューの波形表示 | ローカル (`static/js/`) |
| Mermaid 11 | Experiment Tree 等の図のレンダリング | CDN (jsdelivr) |

フロントエンドはセルフホスト方針。**CDN 読み込みは Mermaid 11 のみ**、それ以外はすべてローカル同梱 (vendored)。
Tailwind のビルド環境は `static/build/`（コミット対象。詳細は `static/build/README.md`）。

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

### ダークモード対応マッピング

ダークモード実装済み（`darkMode: 'class'`、`localStorage('theme')` で永続化、サイドバーフッターの `toggleDarkMode()` で切替）。新規 UI は以下の Tailwind クラスマッピングに従う:

| 用途 | Light | Dark |
|------|-------|------|
| ページ背景 | `bg-gray-50` | `dark:bg-gray-900` |
| カード/サイドバー | `bg-white` | `dark:bg-gray-800` |
| テキスト（主） | `text-gray-800` | `dark:text-gray-100` |
| テキスト（副） | `text-gray-500` | `dark:text-gray-400` |
| テキスト（ミュート） | `text-gray-400` | `dark:text-gray-500` |
| ボーダー | `border-gray-200` | `dark:border-gray-700` |
| ホバー背景 | `hover:bg-gray-50` | `dark:hover:bg-gray-700` |
| アクセント薄背景 | `bg-emerald-50` | `dark:bg-emerald-900/30` |
| 入力フィールド背景 | `bg-gray-50` | `dark:bg-gray-700` |
| コードブロック背景 | `bg-gray-50` | `dark:bg-gray-900` |
| 影 | `shadow-sm` | `dark:shadow-gray-900/20` |

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
- フッターにはダークモード切替ボタンのみを配置（それ以外の情報は置かない）

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

カテゴリは `KNOWLEDGE_PAGES` レジストリ辞書で一元管理。

### Guides（ガイド・分析レポートのファイルベースレジストリ）

**可視化・説明コンテンツはまず Guides で足りないか検討する**（アプリのコード変更なしで追加できる）。
評価指標の解説、EDA レポート、OOF エラー分析、リプレイビューア等はすべてここに置く。

- 置き場所: `docs/guides/{slug}/`（`guide.json` + `index.html` + `assets/`）。規約は `docs/guides/README.md`
- ルート: `/knowledge/guides`（一覧・タグフィルタ）、`/knowledge/guides/{slug}`（詳細）、`/knowledge/guides/{slug}/raw/{path}`（アセット配信。StaticFiles マウントは増やさず `FileResponse` で返す）
- サービス: `app/services/guides.py`（`docs/guides/*/guide.json` の自動スキャン）
- render 2形態:
  - `iframe`: 自己完結 HTML を sandbox 付き iframe で表示。独自 CSS/JS/TS 成果物を持てて base.html と衝突しない。テーマは `?theme=` クエリ + `postMessage({type:"theme"})` で連携、高さは `postMessage({type:"guide-height"})` で通知（実装例: `docs/guides/sample-guide/`）
  - `fragment`: Tailwind 断片をページ内に直接埋め込み。下記「構造化ガイドデザインパターン」を使う。**新しい Tailwind クラスを使ったら `make css`**（`docs/guides/**/*.html` はビルドのスキャン対象）
- 作成は `/kaggle:create-guide` スキルで対話的に行える

### Knowledge サブページ追加パターン

Knowledge 配下にカスタムサブページを追加する手順（**コンテンツの追加なら上記 Guides を優先**。
アプリのロジックが必要なページのみこのパターンを使う）:

1. `app/pages/knowledge.py` の `KNOWLEDGE_PAGES` 辞書に `type: "special"` で追加
2. テンプレートを作成: `app/templates/knowledge/{page}.html` + `app/templates/partials/_{page}_content.html`
3. サイドバーは `KNOWLEDGE_PAGES` から自動生成されるため、base.html の編集は不要

```python
# knowledge.py に追加（例: 独自ロジックを持つページ）
KNOWLEDGE_PAGES["mypage"] = {
    "type": "special",
    "label": "MyPage",
    "icon": "fa-chart-bar",
    "color": "emerald",
    "description": "説明",
}
```

**⚠️ FastAPI ルート定義順序の注意（全ページ共通）**: 固定パスのルートは**必ずパスパラメータ付きルートより前に定義**すること。違反すると固定パスが path parameter にマッチし 404 になる。

```python
# ✅ 正しい順序
@router.get("/experiments/_scores")    # 固定パス（先）
@router.get("/experiments/{name}")     # パスパラメータ（後）

# ❌ 間違い — /experiments/_scores が {name} にマッチしてしまう
@router.get("/experiments/{name}")     # パスパラメータ（先）
@router.get("/experiments/_scores")    # 到達不能
```

Knowledge ページはレジストリパターンを使っているため、この問題は発生しない。

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
│   ├── data.py         # データファイル操作（CSV/TSV/Parquet、画像、音声等）
│   ├── guides.py       # Guides レジストリ（docs/guides/ スキャン）
│   ├── leaderboard.py  # リーダーボードサマリー（キャッシュ付き）
│   └── search.py       # グローバル検索（実験・ドキュメント横断）
├── static/             # ローカル静的ファイル
│   ├── build/          # Tailwind ビルド環境（make css。コミット対象）
│   ├── css/            # ビルド済み app.css, FontAwesome, fonts, highlight.js CSS
│   └── js/             # htmx, highlight.js, Chart.js, wavesurfer.js
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

## ダッシュボードが期待する実験ディレクトリ規約

Experiments ページは `src/exp*/` ディレクトリを以下の規約でスキャンする:

```
src/exp{NNN}_{subtitle}/
├── config/
│   ├── config.yaml               # ベース run。run_name キーを参照（既定: run000-base）
│   └── run{NNN}-{subtitle}.yaml  # 小実験 config。run_name で run を識別
├── output/{run_name}/
│   ├── fold{idx}/*.ckpt          # チェックポイント一覧に表示
│   └── oof_predictions.csv       # OOF タブの分析対象
└── logs/{run_name}/
    ├── run_summary.json          # cv_score / run_mode / finished_at キーを参照
    └── fold{idx}_metrics.csv     # Logs タブの epoch メトリクス表示
```

この規約に従わない実験はエラーにはならず、該当タブが空状態（empty state）で表示される。

## アーキテクチャ

### テンプレート環境の共有

`template_env.py` に単一の `Jinja2Templates` インスタンスを定義。全ページモジュールがこれをインポートすることで、フィルタ・グローバル関数の登録が一箇所で完結する。

### サービス層

`app/services/` にビジネスロジックを分離。各ページモジュールは `app.services.*` から直接インポートする。

### エンドポイント定義

全エンドポイントは `def`（非 `async`）で定義。FastAPI が自動でスレッドプールで実行するため、同期 I/O（ファイル操作、Polars、YAML パース等）がイベントループをブロックしない。

### 静的ファイルのマウント

`app/static/` の単一 StaticFiles マウントのみ使用。別途 StaticFiles マウントを追加しない。静的ファイルは必ず `app/static/` 配下に配置し、`/static/...` パスで参照する。

### 画像モーダル

分析画像のクリック拡大用に `openImageModal()` が `base.html` に組み込み済み。画像に `onclick` を付与するだけで利用可能:

```html
<img src="/static/analysis/eda/distribution.png" alt="分布"
     class="rounded-xl cursor-pointer hover:shadow-md transition-shadow"
     onclick="openImageModal(this.src, this.alt)">
```

## htmx パターン

### Full page vs Partial 出し分け

`HX-Request` ヘッダーの有無で、同一エンドポイントから full page か partial を返す:

```python
from app.services.helpers import is_htmx

@router.get("/experiments")
def experiment_list(request: Request):
    template = "partials/_experiment_list.html" if is_htmx(request) else "experiments/list.html"
    return templates.TemplateResponse(request, template, {...})
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

## 構造化ガイドデザインパターン

`render: "fragment"` のガイド（`docs/guides/`。上記 Guides 節参照）で使う、Markdown ではなく Tailwind HTML で作る構造化コンテンツのパターン。ダークモードは `dark:` クラスで自前対応する。

### パターン 1: セクションナビゲーション

ページ冒頭にピルボタンでセクションジャンプ。各セクションに固有の色テーマを割り当てる。

**色テーマプリセット**: emerald(導入/背景), blue(タスク概要), amber(評価指標), red(チャレンジ), violet(戦略), sky(用語集)

```html
<div class="bg-white dark:bg-gray-900 rounded-2xl shadow-sm border border-gray-200 dark:border-gray-700 p-4 mb-8">
    <div class="flex flex-wrap gap-2">
        <a href="#section-1"
           class="inline-flex items-center gap-1.5 px-3 py-1.5 rounded-full text-xs font-semibold
                  bg-emerald-50 dark:bg-emerald-900/30 text-emerald-600 dark:text-emerald-400
                  hover:bg-emerald-100 transition-colors">
            <i class="fa-solid fa-satellite-dish"></i>1. セクション名
        </a>
        <!-- 各セクション分繰り返し、色を変える -->
    </div>
</div>
```

### パターン 2: セクションカード

各セクションは独立したカードで、ヘッダー（アイコン + タイトル）+ コンテンツ領域で構成。`scroll-mt-4` でピルナビからのジャンプ時にヘッダーの背後に隠れない。

```html
<div id="section-1" class="bg-white dark:bg-gray-900 rounded-2xl shadow-sm border border-gray-200 dark:border-gray-700 mb-6 scroll-mt-4">
    <div class="flex items-center gap-3 p-5 border-b border-gray-100 dark:border-gray-800">
        <div class="w-9 h-9 bg-emerald-50 dark:bg-emerald-900/30 rounded-xl flex items-center justify-center">
            <i class="fa-solid fa-satellite-dish text-emerald-500"></i>
        </div>
        <h2 class="text-lg font-bold text-gray-800 dark:text-gray-100">1. セクション名</h2>
    </div>
    <div class="p-5 space-y-6">
        <div class="flex gap-3">
            <div class="w-8 h-8 bg-emerald-50 dark:bg-emerald-900/30 rounded-lg flex items-center justify-center flex-shrink-0 mt-0.5">
                <i class="fa-solid fa-microphone text-emerald-500 text-sm"></i>
            </div>
            <div>
                <h3 class="font-bold text-gray-800 dark:text-gray-100 mb-1">サブトピック名</h3>
                <p class="text-sm text-gray-600 dark:text-gray-300 leading-relaxed">説明文。</p>
            </div>
        </div>
    </div>
</div>
```

### パターン 3: パイプライン可視化

処理フローを「カラーバッジ + 矢印」で表現。

```html
<div class="bg-gray-50 dark:bg-gray-800 rounded-xl p-4">
    <div class="flex flex-wrap items-center gap-2 text-xs font-semibold">
        <span class="bg-blue-100 text-blue-700 px-2.5 py-1 rounded-lg">ステップ1</span>
        <i class="fa-solid fa-arrow-right text-gray-400"></i>
        <span class="bg-violet-100 text-violet-700 px-2.5 py-1 rounded-lg">ステップ2</span>
        <i class="fa-solid fa-arrow-right text-gray-400"></i>
        <span class="bg-emerald-100 text-emerald-700 px-2.5 py-1 rounded-lg">ステップ3</span>
    </div>
</div>
```

### パターン 4: 用語集テーブル

最終セクションに配置。カード形式ではなくテーブルで効率的に参照可能。

```html
<div class="overflow-x-auto">
    <table class="w-full text-sm">
        <thead>
            <tr class="border-b border-gray-200 dark:border-gray-700">
                <th class="text-left py-2 px-3 font-bold text-gray-800 dark:text-gray-100 w-1/4">用語</th>
                <th class="text-left py-2 px-3 font-bold text-gray-800 dark:text-gray-100">説明</th>
            </tr>
        </thead>
        <tbody class="text-gray-600 dark:text-gray-300">
            <tr class="border-b border-gray-100 dark:border-gray-800">
                <td class="py-2.5 px-3 font-semibold text-gray-700 dark:text-gray-200">用語名</td>
                <td class="py-2.5 px-3">説明文</td>
            </tr>
        </tbody>
    </table>
</div>
```

## Jinja2 コンポーネントの使い方

```jinja2
{% from "components/_metric_card.html" import metric_card %}
{% from "components/_badge.html" import badge %}
{% from "components/_data_table.html" import data_table %}

{{ metric_card("CV Score", "0.95", icon="fa-chart-line", color="emerald") }}
{{ badge("completed", color="emerald", icon="fa-check") }}
{{ data_table(columns, rows) }}
```
