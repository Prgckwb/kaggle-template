"""Kaggle Competition Dashboard - FastAPI application."""

import logging
import traceback
from pathlib import Path

from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles

from app.pages import data, discussions, experiments, knowledge, notebooks
from app.template_env import templates
from app.utils import list_docs, list_experiments, list_input_files

logger = logging.getLogger(__name__)

app = FastAPI(title="Kaggle Competition Dashboard", docs_url="/api-docs")

# Static files
app.mount("/static", StaticFiles(directory=Path(__file__).parent / "static"), name="static")

# Register routers
app.include_router(experiments.router)
app.include_router(discussions.router)
app.include_router(knowledge.router)
app.include_router(data.router)
app.include_router(notebooks.router)


@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    """500 エラー時にユーザーフレンドリーなエラーページを返す。"""
    logger.error("Unhandled exception: %s\n%s", exc, traceback.format_exc())
    return templates.TemplateResponse(
        "error.html",
        {
            "request": request,
            "active_page": "",
            "status_code": 500,
            "message": str(exc),
        },
        status_code=500,
    )


@app.get("/", response_class=HTMLResponse)
def index(request: Request):
    all_docs = list_docs()
    input_files = list_input_files()
    return templates.TemplateResponse(
        "index.html",
        {
            "request": request,
            "title": "Dashboard",
            "active_page": "home",
            "experiments": list_experiments(),
            "discussions": all_docs,
            "input_files": input_files,
        },
    )
