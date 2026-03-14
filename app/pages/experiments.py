"""Experiments page router."""

from __future__ import annotations

from pathlib import Path

from fastapi import APIRouter, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates

from app.utils import (
    get_experiment_detail,
    is_htmx,
    list_experiments,
    parse_mermaid_tree,
)

router = APIRouter()
templates = Jinja2Templates(directory=Path(__file__).parent.parent / "templates")


@router.get("/experiments", response_class=HTMLResponse)
async def experiment_list(request: Request, q: str = "", source: str = ""):
    # Index page search: return empty HTML when query is cleared
    if is_htmx(request) and not q and source == "index":
        return HTMLResponse("")

    exps = list_experiments(query=q)
    mermaid_source = parse_mermaid_tree()
    ctx = {
        "request": request,
        "experiments": exps,
        "query": q,
        "active_page": "experiments",
        "mermaid_source": mermaid_source,
    }
    if is_htmx(request):
        return templates.TemplateResponse("partials/_experiment_list.html", ctx)
    return templates.TemplateResponse("experiments/list.html", ctx)


@router.get("/experiments/{name}", response_class=HTMLResponse)
async def experiment_detail(request: Request, name: str):
    detail = get_experiment_detail(name)
    if detail is None:
        return HTMLResponse("<p>Experiment not found</p>", status_code=404)
    return templates.TemplateResponse(
        "experiments/detail.html",
        {"request": request, "exp": detail, "active_page": "experiments"},
    )


@router.get("/experiments/{name}/_readme", response_class=HTMLResponse)
async def experiment_readme(request: Request, name: str):
    detail = get_experiment_detail(name)
    if detail is None:
        return HTMLResponse("<p>Not found</p>", status_code=404)
    return templates.TemplateResponse(
        "partials/_experiment_readme.html",
        {"request": request, "exp": detail},
    )


@router.get("/experiments/{name}/_config", response_class=HTMLResponse)
async def experiment_config(request: Request, name: str):
    detail = get_experiment_detail(name)
    if detail is None:
        return HTMLResponse("<p>Not found</p>", status_code=404)
    return templates.TemplateResponse(
        "partials/_experiment_config.html",
        {"request": request, "exp": detail},
    )


@router.get("/experiments/{name}/_files", response_class=HTMLResponse)
async def experiment_files(request: Request, name: str):
    detail = get_experiment_detail(name)
    if detail is None:
        return HTMLResponse("<p>Not found</p>", status_code=404)
    return templates.TemplateResponse(
        "partials/_experiment_files.html",
        {"request": request, "exp": detail},
    )
