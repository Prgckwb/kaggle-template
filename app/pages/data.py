"""Data viewer page router."""

from __future__ import annotations

from fastapi import APIRouter, Request
from fastapi.responses import FileResponse, HTMLResponse

from app.template_env import templates
from app.utils import (
    PROJECT_ROOT,
    get_csv_preview_and_stats,
    get_file_info,
    is_htmx,
    list_directory_images,
    list_input_files,
    safe_relative_path,
)

router = APIRouter()

INPUT_DIR = PROJECT_ROOT / "input"


@router.get("/data", response_class=HTMLResponse)
def data_index(request: Request, dir: str = ""):
    files = list_input_files(dir)
    ctx = {
        "request": request,
        "files": files,
        "current_dir": dir,
        "active_page": "data",
        "selected": None,
    }
    return templates.TemplateResponse("data/viewer.html", ctx)


@router.get("/data/preview/{file_path:path}", response_class=HTMLResponse)
def data_preview(request: Request, file_path: str):
    full_path = safe_relative_path(file_path, INPUT_DIR)
    if full_path is None or not full_path.exists():
        return HTMLResponse("<p>File not found</p>", status_code=404)

    info = get_file_info(full_path, INPUT_DIR)
    preview_data = None
    stats = None
    sibling_images: list[dict] = []

    if info["type"] == "tabular":
        result = get_csv_preview_and_stats(full_path)
        if result:
            preview_data = result["preview"]
            stats = result["stats"]
    elif info["type"] == "image":
        parent_dir = str(full_path.parent.relative_to(INPUT_DIR))
        if parent_dir == ".":
            parent_dir = ""
        sibling_images = list_directory_images(parent_dir, INPUT_DIR)

    ctx = {
        "request": request,
        "file": info,
        "preview": preview_data,
        "stats": stats,
        "sibling_images": sibling_images,
    }

    if is_htmx(request):
        return templates.TemplateResponse("partials/_data_preview.html", ctx)

    # Full page: include file list sidebar
    parent_dir = str(full_path.parent.relative_to(INPUT_DIR))
    if parent_dir == ".":
        parent_dir = ""
    files = list_input_files(parent_dir)
    ctx["files"] = files
    ctx["current_dir"] = parent_dir
    ctx["active_page"] = "data"
    ctx["selected"] = info
    return templates.TemplateResponse("data/viewer.html", ctx)


@router.get("/data/gallery/{dir_path:path}", response_class=HTMLResponse)
def data_gallery(request: Request, dir_path: str):
    images = list_directory_images(dir_path, INPUT_DIR)
    ctx = {
        "request": request,
        "images": images,
        "dir_path": dir_path,
    }
    return templates.TemplateResponse("partials/_image_gallery.html", ctx)


@router.get("/data/raw/{file_path:path}")
def data_raw(file_path: str):
    full_path = safe_relative_path(file_path, INPUT_DIR)
    if full_path is None or not full_path.exists():
        return HTMLResponse("Not found", status_code=404)
    return FileResponse(full_path)
