"""Data viewer page router."""

from __future__ import annotations

from fastapi import APIRouter, Request
from fastapi.responses import FileResponse, HTMLResponse

from app.services.data import (
    get_csv_preview,
    get_csv_stats,
    get_file_info,
    list_directory_images,
    list_input_files,
    read_json_preview,
    read_text_preview,
)
from app.services.helpers import PROJECT_ROOT, error_response, is_htmx, safe_relative_path
from app.template_env import templates

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


@router.get("/data/tree/{dir_path:path}", response_class=HTMLResponse)
def data_tree_children(request: Request, dir_path: str):
    safe_path = safe_relative_path(dir_path, INPUT_DIR)
    if safe_path is None or not safe_path.is_dir():
        return error_response(request, templates, 404, "ディレクトリが見つかりません")
    files = list_input_files(dir_path)
    return templates.TemplateResponse(
        "partials/_data_tree_children.html",
        {"request": request, "files": files},
    )


@router.get("/data/preview/{file_path:path}", response_class=HTMLResponse)
def data_preview(request: Request, file_path: str):
    full_path = safe_relative_path(file_path, INPUT_DIR)
    if full_path is None or not full_path.exists():
        return error_response(request, templates, 404, "ファイルが見つかりませんでした")

    info = get_file_info(full_path, INPUT_DIR)
    preview_data = None
    sibling_images: list[dict] = []

    text_content: str | None = None

    if info["type"] == "tabular":
        preview_data = get_csv_preview(full_path)
    elif info["type"] == "image":
        parent_dir = str(full_path.parent.relative_to(INPUT_DIR))
        if parent_dir == ".":
            parent_dir = ""
        sibling_images = list_directory_images(parent_dir, INPUT_DIR)
    elif info["type"] == "json":
        text_content = read_json_preview(full_path)
    elif info["type"] == "text":
        text_content = read_text_preview(full_path)

    ctx = {
        "request": request,
        "file": info,
        "preview": preview_data,
        "sibling_images": sibling_images,
        "text_content": text_content,
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


@router.get("/data/stats/{file_path:path}", response_class=HTMLResponse)
def data_stats(request: Request, file_path: str):
    full_path = safe_relative_path(file_path, INPUT_DIR)
    if full_path is None or not full_path.exists():
        return error_response(request, templates, 404, "ファイルが見つかりません")
    stats = get_csv_stats(full_path)
    ctx = {"request": request, "stats": stats}
    return templates.TemplateResponse("partials/_data_stats.html", ctx)


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
def data_raw(request: Request, file_path: str):
    full_path = safe_relative_path(file_path, INPUT_DIR)
    if full_path is None or not full_path.exists():
        return error_response(request, templates, 404, "ファイルが見つかりませんでした")
    return FileResponse(full_path)
