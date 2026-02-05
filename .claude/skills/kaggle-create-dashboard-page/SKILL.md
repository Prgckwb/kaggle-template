---
name: kaggle:create-dashboard-page
description: ダッシュボードに新しいページを追加する。FastAPI ルーターと htmx テンプレートを作成。
argument-hint: [page-name]
disable-model-invocation: true
allowed-tools: Read, Write, Edit
---

# ダッシュボードにページを追加

$ARGUMENTS をページ名として新しいダッシュボードページを作成する。

## 手順

1. **ルーターを作成**
   - `app/pages/{page-name}.py` を作成:
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
             {"request": request, "title": "{Page Name}"},
         )
     ```

2. **テンプレートを作成**
   - `app/templates/{page-name}.html` を作成:
     ```html
     <!DOCTYPE html>
     <html lang="ja">
     <head>
         <meta charset="UTF-8">
         <meta name="viewport" content="width=device-width, initial-scale=1.0">
         <title>{{ title }}</title>
         <script src="https://unpkg.com/htmx.org@1.9.10"></script>
         <!-- index.html と同じスタイルを使用 -->
     </head>
     <body>
         <nav>
             <a href="/">Home</a>
             <a href="/{page-name}">{Page Name}</a>
         </nav>
         <h1>{Page Name}</h1>
         <div class="card">
             <!-- コンテンツをここに追加 -->
         </div>
     </body>
     </html>
     ```

3. **app/main.py にルーターを登録**
   - import を追加: `from app.pages.{page_name} import router as {page_name}_router`
   - `app.include_router({page_name}_router)` を追加

4. **index.html のナビゲーションを更新**
   - `<nav>` にリンクを追加: `<a href="/{page-name}">{Page Name}</a>`

5. **完了報告**
   - 作成したファイルの一覧を表示
   - アクセス URL を案内: `http://localhost:8000/{page-name}`
