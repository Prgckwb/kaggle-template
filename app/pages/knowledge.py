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
from app.services.helpers import PROJECT_ROOT, error_response, is_htmx, safe_relative_path
from app.template_env import templates

router = APIRouter()

VALID_CATEGORIES = {"official", "insights", "discussion"}

CATEGORY_META = {
    "official": {
        "label": "Official",
        "icon": "fa-building-columns",
        "color": "emerald",
        "description": "コンペティションの公式情報",
    },
    "insights": {
        "label": "Insights",
        "icon": "fa-lightbulb",
        "color": "amber",
        "description": "実験から得られた知見",
    },
    "discussion": {
        "label": "Discussion",
        "icon": "fa-comments",
        "color": "sky",
        "description": "Kaggle Discussion の要約・メモ",
    },
}


@router.get("/knowledge", response_class=HTMLResponse)
def knowledge_index(request: Request):
    all_docs = list_all_knowledge_docs()
    overview = get_competition_overview()
    return templates.TemplateResponse(
        "knowledge/index.html",
        {
            "request": request,
            "active_page": "knowledge",
            "active_subpage": "",
            "docs": all_docs,
            "overview": overview,
            "categories": CATEGORY_META,
        },
    )


@router.get("/knowledge/{category}", response_class=HTMLResponse)
def knowledge_category(request: Request, category: str):
    if category not in VALID_CATEGORIES:
        return error_response(request, templates, 404, "無効なカテゴリです")

    docs = _list_docs_for_category(category)
    meta = CATEGORY_META[category]

    # Official: few docs → show tabbed content directly
    if category == "official" and docs:
        docs_dir = PROJECT_ROOT / "docs" / category
        doc_contents = []
        for doc_info in docs:
            path = docs_dir / doc_info["filename"]
            if path.exists():
                content = read_markdown_file(path)
                doc_contents.append({**doc_info, **content})

        # Determine active tab from ?tab= query parameter
        tab_param = request.query_params.get("tab", "")
        active_tab = 1  # default to first tab
        for i, doc_info in enumerate(doc_contents, 1):
            if doc_info.get("filename") == tab_param:
                active_tab = i
                break

        return templates.TemplateResponse(
            "knowledge/official_tabbed.html",
            {
                "request": request,
                "active_page": "knowledge",
                "active_subpage": category,
                "category": category,
                "meta": meta,
                "doc_contents": doc_contents,
                "active_tab": active_tab,
            },
        )

    return templates.TemplateResponse(
        "knowledge/category.html",
        {
            "request": request,
            "active_page": "knowledge",
            "active_subpage": category,
            "category": category,
            "meta": meta,
            "docs": docs,
        },
    )


@router.get("/knowledge/{category}/{filename}", response_class=HTMLResponse)
def knowledge_detail(request: Request, category: str, filename: str):
    if category not in VALID_CATEGORIES:
        return error_response(request, templates, 404, "無効なカテゴリです")

    # Official docs use tabbed view — redirect to category page with tab param
    if category == "official":
        return RedirectResponse(url=f"/knowledge/official?tab={filename}", status_code=302)

    docs_dir = PROJECT_ROOT / "docs" / category
    path = safe_relative_path(filename, docs_dir)
    if path is None or not path.exists():
        return error_response(request, templates, 404, "ドキュメントが見つかりませんでした")

    doc = read_markdown_file(path)
    meta = CATEGORY_META[category]

    ctx = {
        "request": request,
        "active_page": "knowledge",
        "active_subpage": category,
        "category": category,
        "meta": meta,
        "doc": {"filename": filename, **doc},
    }

    if is_htmx(request):
        return templates.TemplateResponse("partials/_doc_content.html", ctx)
    return templates.TemplateResponse("knowledge/document.html", ctx)
