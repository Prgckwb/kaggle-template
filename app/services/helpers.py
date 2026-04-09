"""Generic helper utilities."""

from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path

from fastapi import Request
from fastapi.responses import HTMLResponse

PROJECT_ROOT = Path(__file__).parent.parent.parent


def is_htmx(request: Request) -> bool:
    """HX-Request header check."""
    return request.headers.get("HX-Request") == "true"


def page_context(request: Request, page: str, subpage: str = "", **kwargs) -> dict:
    """テンプレート用コンテキストを構築する。active_page/active_subpage の設定忘れを防止。"""
    return {"request": request, "active_page": page, "active_subpage": subpage, **kwargs}


def error_response(
    request: Request,
    templates,
    status_code: int,
    message: str,
) -> HTMLResponse:
    """htmx-aware なエラーレスポンスを返す。"""
    if is_htmx(request):
        return templates.TemplateResponse(
            "partials/_error.html",
            {
                "request": request,
                "error_title": f"Error {status_code}",
                "error_message": message,
            },
            status_code=status_code,
        )
    return templates.TemplateResponse(
        "error.html",
        {
            "request": request,
            "active_page": "",
            "status_code": status_code,
            "message": message,
        },
        status_code=status_code,
    )


def safe_relative_path(requested: str, allowed_root: Path) -> Path | None:
    """Path traversal prevention."""
    try:
        target = (allowed_root / requested).resolve()
        if target.is_relative_to(allowed_root.resolve()):
            return target
    except (ValueError, OSError):
        pass
    return None


def human_filesize(size: int | float) -> str:
    """bytes -> human readable string."""
    for unit in ("B", "KB", "MB", "GB"):
        if abs(size) < 1024:
            return f"{size:.1f} {unit}" if unit != "B" else f"{int(size)} B"
        size /= 1024
    return f"{size:.1f} TB"


def timeago(dt: datetime) -> str:
    """datetime -> relative time string (Japanese)."""
    now = datetime.now(tz=timezone.utc)
    diff = now - dt
    seconds = diff.total_seconds()
    if seconds < 60:
        return "たった今"
    if seconds < 3600:
        return f"{int(seconds // 60)}分前"
    if seconds < 86400:
        return f"{int(seconds // 3600)}時間前"
    days = int(seconds // 86400)
    if days < 30:
        return f"{days}日前"
    if days < 365:
        return f"{days // 30}ヶ月前"
    return f"{days // 365}年前"


IMAGE_EXTENSIONS = {".png", ".jpg", ".jpeg", ".gif", ".bmp", ".webp", ".tiff", ".svg"}
VIDEO_EXTENSIONS = {".mp4", ".avi", ".mov", ".mkv", ".webm"}
AUDIO_EXTENSIONS = {".ogg", ".wav", ".mp3", ".flac", ".m4a", ".aac", ".wma"}
BINARY_EXTENSIONS = {".ckpt", ".bin", ".pt", ".pth", ".pkl", ".pyc", ".so", ".o", ".a"}


def _file_type(suffix: str) -> str:
    """File extension to type category."""
    s = suffix.lower()
    mapping = {
        ".py": "python",
        ".yaml": "yaml",
        ".yml": "yaml",
        ".md": "markdown",
        ".csv": "csv",
        ".ipynb": "notebook",
        ".json": "json",
        ".jsonl": "json",
        ".txt": "text",
        ".log": "text",
        ".cfg": "text",
        ".ini": "text",
        ".toml": "text",
        ".sh": "bash",
        ".bash": "bash",
    }
    if s in mapping:
        return mapping[s]
    if s in IMAGE_EXTENSIONS:
        return "image"
    if s in VIDEO_EXTENSIONS:
        return "video"
    if s in AUDIO_EXTENSIONS:
        return "audio"
    if s in BINARY_EXTENSIONS:
        return "binary"
    return "other"


def file_icon(file_type: str) -> str:
    """File type to FontAwesome icon class."""
    mapping = {
        "python": "fa-python",
        "yaml": "fa-file-code",
        "markdown": "fa-file-lines",
        "csv": "fa-file-csv",
        "binary": "fa-weight-hanging",
        "notebook": "fa-book",
        "json": "fa-file-code",
        "text": "fa-file-lines",
        "bash": "fa-terminal",
        "image": "fa-image",
        "video": "fa-film",
        "audio": "fa-music",
        "other": "fa-file",
    }
    icon = mapping.get(file_type, "fa-file")
    prefix = "fa-brands" if file_type == "python" else "fa-solid"
    return f"{prefix} {icon}"
