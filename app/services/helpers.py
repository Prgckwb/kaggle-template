"""Generic helper utilities."""

from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path

from fastapi import Request

PROJECT_ROOT = Path(__file__).parent.parent.parent


def is_htmx(request: Request) -> bool:
    """HX-Request header check."""
    return request.headers.get("HX-Request") == "true"


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


def _file_type(suffix: str) -> str:
    """File extension to type category."""
    mapping = {
        ".py": "python",
        ".yaml": "yaml",
        ".yml": "yaml",
        ".md": "markdown",
        ".csv": "csv",
        ".ckpt": "checkpoint",
        ".ipynb": "notebook",
        ".json": "json",
        ".txt": "text",
    }
    return mapping.get(suffix.lower(), "other")


def file_icon(file_type: str) -> str:
    """File type to FontAwesome icon class."""
    mapping = {
        "python": "fa-python",
        "yaml": "fa-file-code",
        "markdown": "fa-file-lines",
        "csv": "fa-file-csv",
        "checkpoint": "fa-weight-hanging",
        "notebook": "fa-book",
        "json": "fa-file-code",
        "text": "fa-file",
        "other": "fa-file",
    }
    icon = mapping.get(file_type, "fa-file")
    prefix = "fa-brands" if file_type == "python" else "fa-solid"
    return f"{prefix} {icon}"
