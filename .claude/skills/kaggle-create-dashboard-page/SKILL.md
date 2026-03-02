---
name: kaggle:create-dashboard-page
description: ダッシュボードに新しいページを追加する。FastAPI ルーターと htmx テンプレートを作成。
argument-hint: [page-name]
disable-model-invocation: true
allowed-tools: Read, Write, Edit, Glob
---

# ダッシュボードにページを追加

$ARGUMENTS をページ名として新しいダッシュボードページを作成する。

## レイアウト仕様

全ページは以下のデザインシステムに従う:

- **構成**: 左サイドバー（260px 固定）+ メインコンテンツエリアの2カラムレイアウト
- **アクセントカラー**: 緑（`#22c55e`）
- **テンプレート継承**: `{% extends "base.html" %}` を使用し、CSS・レイアウト・サイドバーを共有する
- **コンポーネント**: `.card`（カード）、`.grid-2` / `.grid-3`（グリッド）、`.btn-primary`（緑ボタン）、`.page-header`（ページヘッダー）

## 手順

### 1. base.html の存在確認

`app/templates/base.html` を Read で読む。

- **ファイルが存在する場合** → 手順3に進む
- **ファイルが存在しない場合** → 手順2に進む

### 2. base.html を作成（初回のみ）

`app/templates/base.html` を以下の内容で **Write** する:

```html
<!DOCTYPE html>
<html lang="ja">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{% block title %}Dashboard{% endblock %} - Kaggle Dashboard</title>
    <script src="https://unpkg.com/htmx.org@1.9.10"></script>
    <style>
        *, *::before, *::after { margin: 0; padding: 0; box-sizing: border-box; }
        :root {
            --color-accent: #22c55e;
            --color-accent-hover: #16a34a;
            --color-accent-light: #dcfce7;
            --color-bg: #f8f9fa;
            --color-bg-sidebar: #ffffff;
            --color-bg-card: #ffffff;
            --color-text: #1a1a2e;
            --color-text-secondary: #6b7280;
            --color-text-muted: #9ca3af;
            --color-border: #e5e7eb;
            --sidebar-width: 260px;
            --radius: 12px;
            --radius-sm: 8px;
            --shadow: 0 1px 3px rgba(0,0,0,0.05), 0 1px 2px rgba(0,0,0,0.1);
            --font-sans: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
            --font-mono: 'SF Mono', 'Fira Code', monospace;
        }
        body { font-family: var(--font-sans); line-height: 1.6; color: var(--color-text); background: var(--color-bg); }
        .layout { display: flex; min-height: 100vh; }
        .sidebar {
            width: var(--sidebar-width); background: var(--color-bg-sidebar);
            border-right: 1px solid var(--color-border); padding: 1.5rem 1rem;
            position: fixed; top: 0; left: 0; bottom: 0;
            display: flex; flex-direction: column; overflow-y: auto;
        }
        .sidebar-brand { display: flex; align-items: center; gap: 0.75rem; padding: 0.5rem 0.75rem; margin-bottom: 1.5rem; font-weight: 700; font-size: 1rem; }
        .brand-icon { font-size: 1.4rem; }
        .sidebar-nav { display: flex; flex-direction: column; gap: 0.25rem; flex: 1; }
        .nav-item {
            display: flex; align-items: center; gap: 0.75rem;
            padding: 0.625rem 0.75rem; border-radius: var(--radius-sm);
            color: var(--color-text-secondary); text-decoration: none;
            font-size: 0.9rem; transition: background 0.15s ease, color 0.15s ease;
        }
        .nav-item:hover { background: var(--color-bg); color: var(--color-text); }
        .nav-item.active { background: var(--color-accent-light); color: var(--color-accent); font-weight: 600; }
        .sidebar-footer { margin-top: auto; padding-top: 1rem; border-top: 1px solid var(--color-border); }
        .main { margin-left: var(--sidebar-width); flex: 1; padding: 2rem 3rem; max-width: calc(100% - var(--sidebar-width)); }
        .page-header { margin-bottom: 2rem; }
        .page-header h1 { font-size: 1.75rem; font-weight: 700; margin-bottom: 0.25rem; }
        .page-subtitle { color: var(--color-text-secondary); font-size: 0.95rem; }
        .card { background: var(--color-bg-card); border-radius: var(--radius); padding: 1.5rem; margin-bottom: 1rem; box-shadow: var(--shadow); border: 1px solid var(--color-border); }
        .card h2 { font-size: 1.1rem; font-weight: 600; margin-bottom: 0.75rem; }
        .card p { color: var(--color-text-secondary); font-size: 0.95rem; }
        .grid { display: grid; gap: 1rem; }
        .grid-2 { grid-template-columns: repeat(2, 1fr); }
        .grid-3 { grid-template-columns: repeat(3, 1fr); }
        .btn { display: inline-flex; align-items: center; gap: 0.5rem; padding: 0.625rem 1.25rem; border-radius: var(--radius-sm); font-size: 0.9rem; font-weight: 500; cursor: pointer; border: none; transition: background 0.15s ease; text-decoration: none; font-family: var(--font-sans); }
        .btn-primary { background: var(--color-accent); color: white; }
        .btn-primary:hover { background: var(--color-accent-hover); }
        .btn-outline { background: transparent; border: 1px solid var(--color-border); color: var(--color-text); }
        .btn-outline:hover { background: var(--color-bg); }
        code { background: var(--color-bg); padding: 0.2em 0.4em; border-radius: 4px; font-family: var(--font-mono); font-size: 0.875em; color: var(--color-accent-hover); }
        table { width: 100%; border-collapse: collapse; }
        th, td { padding: 0.75rem 1rem; text-align: left; border-bottom: 1px solid var(--color-border); }
        th { font-weight: 600; color: var(--color-text-secondary); font-size: 0.85rem; text-transform: uppercase; letter-spacing: 0.05em; }
        td { font-size: 0.95rem; }
        .text-muted { color: var(--color-text-muted); font-size: 0.85rem; }
        .accent { color: var(--color-accent); }
        .mt-1 { margin-top: 0.5rem; }
        .mt-2 { margin-top: 1rem; }
        .mt-4 { margin-top: 2rem; }
    </style>
    {% block head %}{% endblock %}
</head>
<body>
    <div class="layout">
        <aside class="sidebar">
            <div class="sidebar-brand">
                <span class="brand-icon">📊</span>
                <span>Kaggle Dashboard</span>
            </div>
            <nav class="sidebar-nav">
                <a href="/" class="nav-item {% if active_page == 'home' %}active{% endif %}">🏠 Home</a>
            </nav>
            <div class="sidebar-footer">
                <p class="text-muted">Kaggle Competition Dashboard</p>
            </div>
        </aside>
        <main class="main">
            {% block content %}{% endblock %}
        </main>
    </div>
</body>
</html>
```

次に `app/templates/index.html` を **Write** で以下の内容に書き換える:

```html
{% extends "base.html" %}

{% block title %}Home{% endblock %}

{% block content %}
<div class="page-header">
    <h1>Kaggle Competition Dashboard</h1>
    <p class="page-subtitle">EDA や実験結果の可視化用ダッシュボードです。</p>
</div>

<div class="grid grid-2">
    <div class="card">
        <h2>Welcome</h2>
        <p>新しいページは <code>app/pages/</code> に追加してください。</p>
        <p class="mt-1">スキル <code>/create-dashboard-page [page-name]</code> で自動生成できます。</p>
    </div>
    <div class="card">
        <h2>Getting Started</h2>
        <p>実験を開始するには <code>src/</code> ディレクトリに実験フォルダを追加してください。</p>
    </div>
</div>
{% endblock %}
```

次に `app/main.py` の `index` 関数のテンプレートレスポンスのコンテキストに `"active_page": "home"` を **Edit** で追加する。

### 3. ルーターを作成

`app/pages/{page-name}.py` を **Write** で作成する。`{page-name}` はハイフン区切り、`{page_name_snake}` はスネークケース（例: `page-name` → `page_name`）に変換する:

```python
from fastapi import APIRouter, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from pathlib import Path

router = APIRouter()
templates = Jinja2Templates(directory=Path(__file__).parent.parent / "templates")


@router.get("/{page-name}", response_class=HTMLResponse)
async def {page_name_snake}(request: Request):
    return templates.TemplateResponse(
        "{page-name}.html",
        {"request": request, "title": "{Page Name}", "active_page": "{page-name}"},
    )
```

### 4. テンプレートを作成

`app/templates/{page-name}.html` を **Write** で作成する:

```html
{% extends "base.html" %}

{% block title %}{{ title }}{% endblock %}

{% block content %}
<div class="page-header">
    <h1>{Page Name}</h1>
    <p class="page-subtitle">ページの説明をここに記載</p>
</div>

<div class="card">
    <!-- コンテンツをここに追加 -->
    <h2>セクション名</h2>
    <p>説明テキスト</p>
</div>
{% endblock %}
```

### 5. app/main.py にルーターを登録

`app/main.py` を **Read** して現在の内容を確認した後、**Edit** で以下を追加する:

- import を追加: `from app.pages.{page_name} import router as {page_name}_router`
- `app.include_router({page_name}_router)` を追加

### 6. base.html のサイドバーナビゲーションを更新

`app/templates/base.html` を **Edit** で変更する。

`<a href="/" class="nav-item ...">🏠 Home</a>` の直後に以下を追加する:

```html
                <a href="/{page-name}" class="nav-item {% if active_page == '{page-name}' %}active{% endif %}">{Page Name}</a>
```

### 7. 完了報告

- 作成・変更したファイルの一覧を表示
- アクセス URL を案内: `http://localhost:8000/{page-name}`
- 起動コマンドを案内: `uv run uvicorn app.main:app --reload`
