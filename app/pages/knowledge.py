"""Knowledge page router."""

from __future__ import annotations

from fastapi import APIRouter, Request
from fastapi.responses import HTMLResponse, RedirectResponse

from app.services.documents import (
    _list_docs_for_category,
    get_competition_overview,
    list_all_knowledge_docs,
    read_markdown_file,
)
from app.services.helpers import PROJECT_ROOT, error_response, is_htmx, page_context, safe_relative_path
from app.template_env import templates

router = APIRouter()

# Knowledge ページレジストリ
# type: "category" = Markdown ドキュメント一覧、"special" = 構造化 HTML ページ
# 新しいページを追加するには、この辞書に1行追加するだけでよい
KNOWLEDGE_PAGES: dict[str, dict] = {
    "official": {
        "type": "category",
        "label": "Official",
        "icon": "fa-building-columns",
        "color": "emerald",
        "description": "コンペティションの公式情報",
    },
    "insights": {
        "type": "category",
        "label": "Insights",
        "icon": "fa-lightbulb",
        "color": "amber",
        "description": "実験から得られた知見",
    },
    "discussion": {
        "type": "category",
        "label": "Discussion",
        "icon": "fa-comments",
        "color": "sky",
        "description": "Kaggle Discussion の要約・メモ",
    },
}


# サイドバー用: テンプレートグローバルに登録（base.html でループ表示）
templates.env.globals["knowledge_subnav"] = [
    {"key": k, **v} for k, v in KNOWLEDGE_PAGES.items()
]


@router.get("/knowledge", response_class=HTMLResponse)
def knowledge_index(request: Request):
    all_docs = list_all_knowledge_docs()
    overview = get_competition_overview()
    return templates.TemplateResponse(
        "knowledge/index.html",
        page_context(
            request, "knowledge",
            docs=all_docs, overview=overview, categories=KNOWLEDGE_PAGES,
        ),
    )


@router.get("/knowledge/{page}", response_class=HTMLResponse)
def knowledge_page(request: Request, page: str):
    if page not in KNOWLEDGE_PAGES:
        return error_response(request, templates, 404, "ページが見つかりません")

    meta = KNOWLEDGE_PAGES[page]

    if meta["type"] == "special":
        return _render_special_page(request, page, meta)
    return _render_category(request, page, meta)


@router.get("/knowledge/{category}/{filename}", response_class=HTMLResponse)
def knowledge_detail(request: Request, category: str, filename: str):
    if category not in KNOWLEDGE_PAGES or KNOWLEDGE_PAGES[category]["type"] != "category":
        return error_response(request, templates, 404, "無効なカテゴリです")

    # Official docs use tabbed view — redirect to category page with tab param
    if category == "official":
        return RedirectResponse(url=f"/knowledge/official?tab={filename}", status_code=302)

    docs_dir = PROJECT_ROOT / "docs" / category
    path = safe_relative_path(filename, docs_dir)
    if path is None or not path.exists():
        return error_response(request, templates, 404, "ドキュメントが見つかりませんでした")

    doc = read_markdown_file(path)
    meta = KNOWLEDGE_PAGES[category]

    ctx = page_context(
        request, "knowledge", category,
        category=category, meta=meta, doc={"filename": filename, **doc},
    )

    if is_htmx(request):
        return templates.TemplateResponse("partials/_doc_content.html", ctx)
    return templates.TemplateResponse("knowledge/document.html", ctx)


def _render_category(request: Request, category: str, meta: dict) -> HTMLResponse:
    """Markdown ドキュメント一覧を表示する。"""
    docs = _list_docs_for_category(category)

    # Official: few docs → show tabbed content directly
    if category == "official" and docs:
        docs_dir = PROJECT_ROOT / "docs" / category
        doc_contents = []
        for doc_info in docs:
            path = docs_dir / doc_info["filename"]
            if path.exists():
                content = read_markdown_file(path)
                if content:
                    doc_contents.append({**doc_info, **content})

        tab_param = request.query_params.get("tab", "")
        active_tab = 1
        for i, doc_info in enumerate(doc_contents, 1):
            if doc_info.get("filename") == tab_param:
                active_tab = i
                break

        return templates.TemplateResponse(
            "knowledge/official_tabbed.html",
            page_context(
                request, "knowledge", category,
                category=category, meta=meta, doc_contents=doc_contents, active_tab=active_tab,
            ),
        )

    return templates.TemplateResponse(
        "knowledge/category.html",
        page_context(request, "knowledge", category, category=category, meta=meta, docs=docs),
    )


def _render_special_page(request: Request, page: str, meta: dict) -> HTMLResponse:
    """構造化 HTML の専用ページを表示する。"""
    template_name = meta.get("template", f"knowledge/{page}.html")
    partial_name = meta.get("partial", f"partials/_{page}_content.html")

    ctx = page_context(request, "knowledge", page, meta=meta)

    if is_htmx(request):
        return templates.TemplateResponse(partial_name, ctx)
    return templates.TemplateResponse(template_name, ctx)
