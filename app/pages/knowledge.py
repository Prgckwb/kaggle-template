"""Knowledge page router."""

from __future__ import annotations

from fastapi import APIRouter, Request
from fastapi.responses import FileResponse, HTMLResponse, RedirectResponse

from app.services.documents import (
    _list_docs_for_category,
    get_competition_overview,
    list_all_knowledge_docs,
    read_markdown_file,
)
from app.services.guides import (
    GUIDES_DIR,
    get_guide,
    list_all_tags,
    list_guides,
    read_fragment_html,
)
from app.services.helpers import (
    PROJECT_ROOT,
    error_response,
    is_htmx,
    page_context,
    safe_relative_path,
)
from app.template_env import templates

router = APIRouter()

# Knowledge ページレジストリ
# type: "category" = Markdown ドキュメント一覧、"special" = 構造化 HTML ページ、
#       "guides" = docs/guides/ の自動発見レジストリ（ガイド・分析レポート）
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
    "guides": {
        "type": "guides",
        "label": "Guides",
        "icon": "fa-compass",
        "color": "violet",
        "description": "ガイド・EDA・分析レポート（docs/guides/ から自動発見）",
    },
}


# サイドバー用: テンプレートグローバルに登録（base.html でループ表示）
templates.env.globals["knowledge_subnav"] = [
    {"key": k, **v} for k, v in KNOWLEDGE_PAGES.items()
]


@router.get("/knowledge", response_class=HTMLResponse)
def knowledge_index(request: Request):
    all_docs = list_all_knowledge_docs()
    all_docs["guides"] = list_guides()
    overview = get_competition_overview()
    return templates.TemplateResponse(
        request,
        "knowledge/index.html",
        page_context(
            request,
            "knowledge",
            docs=all_docs,
            overview=overview,
            categories=KNOWLEDGE_PAGES,
        ),
    )


# --- Guides ---------------------------------------------------------------
# 固定パス（/knowledge/guides/...）はパスパラメータ付きルート
# （/knowledge/{page} 等）より先に定義すること（app/README.md 参照）


@router.get("/knowledge/guides", response_class=HTMLResponse)
def guides_index(request: Request, tag: str = ""):
    guides = list_guides(tag=tag or None)
    ctx = page_context(
        request,
        "knowledge",
        "guides",
        meta=KNOWLEDGE_PAGES["guides"],
        guides=guides,
        tags=list_all_tags(),
        active_tag=tag,
    )
    if is_htmx(request):
        return templates.TemplateResponse(request, "partials/_guide_cards.html", ctx)
    return templates.TemplateResponse(request, "knowledge/guides.html", ctx)


@router.get("/knowledge/guides/{slug}", response_class=HTMLResponse)
def guide_detail(request: Request, slug: str):
    guide = get_guide(slug)
    if guide is None:
        return error_response(request, templates, 404, "ガイドが見つかりません")
    if not guide["has_index"]:
        return error_response(
            request, templates, 404, "index.html がありません（guide.json のみ存在）"
        )

    fragment_html = None
    if guide["render"] == "fragment":
        fragment_html = read_fragment_html(slug)

    return templates.TemplateResponse(
        request,
        "knowledge/guide_detail.html",
        page_context(
            request,
            "knowledge",
            "guides",
            meta=KNOWLEDGE_PAGES["guides"],
            guide=guide,
            fragment_html=fragment_html,
        ),
    )


@router.get("/knowledge/guides/{slug}/raw/{asset_path:path}")
def guide_raw(request: Request, slug: str, asset_path: str):
    guide_dir = GUIDES_DIR / slug
    if get_guide(slug) is None:
        return error_response(request, templates, 404, "ガイドが見つかりません")
    full_path = safe_relative_path(asset_path, guide_dir)
    if full_path is None or not full_path.is_file():
        return error_response(request, templates, 404, "ファイルが見つかりません")
    return FileResponse(full_path)


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
    if (
        category not in KNOWLEDGE_PAGES
        or KNOWLEDGE_PAGES[category]["type"] != "category"
    ):
        return error_response(request, templates, 404, "無効なカテゴリです")

    # Official docs use tabbed view — redirect to category page with tab param
    if category == "official":
        return RedirectResponse(
            url=f"/knowledge/official?tab={filename}", status_code=302
        )

    docs_dir = PROJECT_ROOT / "docs" / category
    path = safe_relative_path(filename, docs_dir)
    if path is None or not path.exists():
        return error_response(
            request, templates, 404, "ドキュメントが見つかりませんでした"
        )

    doc = read_markdown_file(path)
    meta = KNOWLEDGE_PAGES[category]

    ctx = page_context(
        request,
        "knowledge",
        category,
        category=category,
        meta=meta,
        doc={"filename": filename, **doc},
    )

    if is_htmx(request):
        return templates.TemplateResponse(request, "partials/_doc_content.html", ctx)
    return templates.TemplateResponse(request, "knowledge/document.html", ctx)


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
            request,
            "knowledge/official_tabbed.html",
            page_context(
                request,
                "knowledge",
                category,
                category=category,
                meta=meta,
                doc_contents=doc_contents,
                active_tab=active_tab,
            ),
        )

    return templates.TemplateResponse(
        request,
        "knowledge/category.html",
        page_context(
            request, "knowledge", category, category=category, meta=meta, docs=docs
        ),
    )


def _render_special_page(request: Request, page: str, meta: dict) -> HTMLResponse:
    """構造化 HTML の専用ページを表示する。"""
    template_name = meta.get("template", f"knowledge/{page}.html")
    partial_name = meta.get("partial", f"partials/_{page}_content.html")

    ctx = page_context(request, "knowledge", page, meta=meta)

    if is_htmx(request):
        return templates.TemplateResponse(request, partial_name, ctx)
    return templates.TemplateResponse(request, template_name, ctx)
