"""Data / input file utilities."""

from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path

from app.services.helpers import PROJECT_ROOT

IMAGE_EXTENSIONS = {".png", ".jpg", ".jpeg", ".gif", ".bmp", ".webp", ".tiff"}
VIDEO_EXTENSIONS = {".mp4", ".avi", ".mov", ".mkv", ".webm"}
TABULAR_EXTENSIONS = {".csv", ".tsv", ".parquet"}


def list_input_files(directory: str = "") -> list[dict]:
    """input/ 配下のファイルとディレクトリを列挙。"""
    base = PROJECT_ROOT / "input"
    target = base / directory if directory else base
    if not target.exists():
        return []

    items = []
    for f in sorted(target.iterdir()):
        if f.name.startswith("."):
            continue
        rel = str(f.relative_to(base))
        item: dict = {
            "name": f.name,
            "path": rel,
            "is_dir": f.is_dir(),
        }
        if f.is_file():
            item.update(
                {
                    "type": _data_file_type(f.suffix),
                    "size": f.stat().st_size,
                    "modified": datetime.fromtimestamp(
                        f.stat().st_mtime, tz=timezone.utc
                    ),
                }
            )
        elif f.is_dir():
            item["child_count"] = sum(
                1 for c in f.iterdir() if not c.name.startswith(".")
            )
        items.append(item)
    return items


def get_file_info(path: Path, base: Path) -> dict:
    """単一ファイルの詳細情報を返す。"""
    return {
        "name": path.name,
        "path": str(path.relative_to(base)),
        "type": _data_file_type(path.suffix),
        "size": path.stat().st_size,
        "modified": datetime.fromtimestamp(path.stat().st_mtime, tz=timezone.utc),
        "suffix": path.suffix.lower(),
    }


def read_csv_preview(path: Path, n_rows: int = 50) -> dict | None:
    """polars で CSV を先頭 N 行読み込み。"""
    if not path.exists():
        return None
    import polars as pl

    df = pl.scan_csv(path).head(n_rows).collect()
    total = pl.scan_csv(path).select(pl.len()).collect().item()
    return {
        "columns": df.columns,
        "rows": df.to_dicts(),
        "total_rows": total,
    }


def get_csv_preview_and_stats(
    path: Path, preview_rows: int = 50, stats_rows: int = 10000
) -> dict | None:
    """CSV のプレビューと統計を1回の読み込みで返す。"""
    if not path.exists():
        return None
    import polars as pl

    try:
        df_stats = pl.read_csv(path, n_rows=stats_rows)
        total = pl.scan_csv(path).select(pl.len()).collect().item()
        df_preview = df_stats.head(preview_rows)
        describe = df_stats.describe()
        null_counts = {col: df_stats[col].null_count() for col in df_stats.columns}

        return {
            "preview": {
                "columns": df_preview.columns,
                "rows": df_preview.to_dicts(),
                "total_rows": total,
            },
            "stats": {
                "total_rows": total,
                "total_cols": len(df_stats.columns),
                "dtypes": {col: str(df_stats[col].dtype) for col in df_stats.columns},
                "null_counts": null_counts,
                "describe_columns": describe.columns,
                "describe_rows": describe.to_dicts(),
            },
        }
    except Exception:
        return None


def get_csv_statistics(path: Path) -> dict | None:
    """polars でデータの統計情報を返す。"""
    if not path.exists():
        return None
    import polars as pl

    try:
        df = pl.read_csv(path, n_rows=10000)
        total = pl.scan_csv(path).select(pl.len()).collect().item()
        describe = df.describe()
        null_counts = {col: df[col].null_count() for col in df.columns}

        return {
            "total_rows": total,
            "total_cols": len(df.columns),
            "dtypes": {col: str(df[col].dtype) for col in df.columns},
            "null_counts": null_counts,
            "describe_columns": describe.columns,
            "describe_rows": describe.to_dicts(),
        }
    except Exception:
        return None


def list_directory_images(directory: str, base: Path) -> list[dict]:
    """指定ディレクトリ内の画像ファイルを列挙。"""
    target = base / directory if directory else base
    if not target.exists():
        return []
    images = []
    for f in sorted(target.iterdir()):
        if f.is_file() and f.suffix.lower() in IMAGE_EXTENSIONS:
            images.append(
                {
                    "name": f.name,
                    "path": str(f.relative_to(base)),
                }
            )
    return images


def _data_file_type(suffix: str) -> str:
    """拡張子をデータ型カテゴリに変換。"""
    s = suffix.lower()
    if s in TABULAR_EXTENSIONS:
        return "tabular"
    if s in IMAGE_EXTENSIONS:
        return "image"
    if s in VIDEO_EXTENSIONS:
        return "video"
    if s in {".json", ".jsonl"}:
        return "json"
    return "other"


def data_file_icon(file_type: str) -> str:
    """Data file type to FontAwesome icon class."""
    mapping = {
        "tabular": "fa-file-csv",
        "image": "fa-image",
        "video": "fa-film",
        "json": "fa-file-code",
        "other": "fa-file",
    }
    return mapping.get(file_type, "fa-file")
