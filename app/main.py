"""Kaggle Competition Dashboard - FastAPI application."""

from pathlib import Path

import yaml
from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates

from app.pages import data, discussions, experiments, knowledge
from app.utils import (
    data_file_icon,
    file_icon,
    human_filesize,
    list_docs,
    list_experiments,
    list_input_files,
    timeago,
)

app = FastAPI(title="Kaggle Competition Dashboard", docs_url="/api-docs")
templates = Jinja2Templates(directory=Path(__file__).parent / "templates")

# Register routers
app.include_router(experiments.router)
app.include_router(discussions.router)
app.include_router(knowledge.router)
app.include_router(data.router)

# Register Jinja2 custom filters and globals
templates.env.filters["filesize"] = human_filesize
templates.env.filters["timeago"] = timeago
templates.env.filters["yaml_dump"] = lambda d: yaml.dump(
    d, default_flow_style=False, allow_unicode=True, sort_keys=False
)
templates.env.globals["file_icon"] = file_icon
templates.env.globals["data_file_icon"] = data_file_icon

# Share filters/globals with page routers
for mod in (experiments, discussions, knowledge, data):
    mod.templates.env.filters.update(templates.env.filters)
    mod.templates.env.globals.update(templates.env.globals)


@app.get("/", response_class=HTMLResponse)
async def index(request: Request):
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
