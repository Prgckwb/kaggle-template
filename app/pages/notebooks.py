"""Notebooks page router."""

from __future__ import annotations

from fastapi import APIRouter, Request
from fastapi.responses import HTMLResponse

from app.template_env import templates
from app.utils import list_notebooks

router = APIRouter()


@router.get("/notebooks", response_class=HTMLResponse)
def notebooks_index(request: Request):
    notebooks = list_notebooks()
    return templates.TemplateResponse(
        "notebooks/list.html",
        {
            "request": request,
            "notebooks": notebooks,
            "active_page": "notebooks",
        },
    )
