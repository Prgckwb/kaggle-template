"""Knowledge page router."""

from __future__ import annotations

from pathlib import Path

from fastapi import APIRouter, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates

from app.utils import (
    PROJECT_ROOT,
    get_competition_overview,
    get_validation_strategy,
    is_htmx,
    list_knowledge_docs,
    read_markdown_file,
    safe_relative_path,
)

router = APIRouter()
templates = Jinja2Templates(directory=Path(__file__).parent.parent / "templates")

VALID_CATEGORIES = {"official", "insights"}


@router.get("/knowledge", response_class=HTMLResponse)
async def knowledge_index(request: Request):
    overview = get_competition_overview()
    validation = get_validation_strategy()
    docs = list_knowledge_docs()

    return templates.TemplateResponse(
        "knowledge/viewer.html",
        {
            "request": request,
            "overview": overview,
            "validation": validation,
            "docs": docs,
            "active_page": "knowledge",
            "selected": None,
        },
    )


@router.get("/knowledge/{category}/{filename}", response_class=HTMLResponse)
async def knowledge_detail(request: Request, category: str, filename: str):
    if category not in VALID_CATEGORIES:
        return HTMLResponse("<p>Invalid category</p>", status_code=404)

    docs_dir = PROJECT_ROOT / "docs" / category
    path = safe_relative_path(filename, docs_dir)
    if path is None or not path.exists():
        return HTMLResponse("<p>Not found</p>", status_code=404)

    doc = read_markdown_file(path)
    overview = get_competition_overview()
    validation = get_validation_strategy()
    all_docs = list_knowledge_docs()

    ctx = {
        "request": request,
        "overview": overview,
        "validation": validation,
        "docs": all_docs,
        "selected": {"category": category, "filename": filename, **doc},
        "active_page": "knowledge",
    }

    if is_htmx(request):
        return templates.TemplateResponse("partials/_doc_content.html", ctx)
    return templates.TemplateResponse("knowledge/viewer.html", ctx)
