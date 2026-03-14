"""Discussions page router."""

from __future__ import annotations

from pathlib import Path

from fastapi import APIRouter, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates

from app.utils import (
    PROJECT_ROOT,
    is_htmx,
    list_discussion_docs,
    read_markdown_file,
    safe_relative_path,
)

router = APIRouter()
templates = Jinja2Templates(directory=Path(__file__).parent.parent / "templates")


@router.get("/discussions", response_class=HTMLResponse)
async def discussions_index(request: Request):
    docs = list_discussion_docs()
    return templates.TemplateResponse(
        "discussions/viewer.html",
        {
            "request": request,
            "docs": docs,
            "active_page": "discussions",
            "selected": None,
        },
    )


@router.get("/discussions/{filename}", response_class=HTMLResponse)
async def discussions_detail(request: Request, filename: str):
    docs_dir = PROJECT_ROOT / "docs" / "discussion"
    path = safe_relative_path(filename, docs_dir)
    if path is None or not path.exists():
        return HTMLResponse("<p>Not found</p>", status_code=404)

    doc = read_markdown_file(path)
    all_docs = list_discussion_docs()

    ctx = {
        "request": request,
        "docs": all_docs,
        "selected": {"filename": filename, **doc},
        "active_page": "discussions",
    }

    if is_htmx(request):
        return templates.TemplateResponse("partials/_doc_content.html", ctx)
    return templates.TemplateResponse("discussions/viewer.html", ctx)
