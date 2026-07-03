"""Data / input file utilities."""

from __future__ import annotations

from datetime import UTC, datetime
from pathlib import Path

from app.services.helpers import PROJECT_ROOT

IMAGE_EXTENSIONS = {".png", ".jpg", ".jpeg", ".gif", ".bmp", ".webp", ".tiff"}
VIDEO_EXTENSIONS = {".mp4", ".avi", ".mov", ".mkv", ".webm"}
AUDIO_EXTENSIONS = {".ogg", ".wav", ".mp3", ".flac", ".m4a", ".aac", ".wma"}
TABULAR_EXTENSIONS = {".csv", ".tsv", ".parquet"}
TEXT_EXTENSIONS = {
    ".txt",
    ".log",
    ".cfg",
    ".ini",
    ".md",
    ".py",
    ".sh",
    ".bash",
    ".r",
    ".sql",
    ".yaml",
    ".yml",
    ".toml",
    ".xml",
    ".html",
    ".css",
    ".js",
    ".ts",
    ".c",
    ".cpp",
    ".h",
    ".java",
    ".go",
    ".rs",
}


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
                    "modified": datetime.fromtimestamp(f.stat().st_mtime, tz=UTC),
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
        "modified": datetime.fromtimestamp(path.stat().st_mtime, tz=UTC),
        "suffix": path.suffix.lower(),
    }


def _read_tabular_head(path: Path, n_rows: int):
    """テーブルファイル（CSV / TSV / Parquet）の先頭 n_rows を DataFrame で返す。"""
    import polars as pl

    suffix = path.suffix.lower()
    if suffix == ".parquet":
        return pl.read_parquet(path, n_rows=n_rows)
    separator = "\t" if suffix == ".tsv" else ","
    return pl.read_csv(
        path, n_rows=n_rows, separator=separator, infer_schema_length=10000
    )


def _count_tabular_rows(path: Path) -> int:
    """テーブルファイルの総行数を lazy scan で数える。"""
    import polars as pl

    suffix = path.suffix.lower()
    if suffix == ".parquet":
        lf = pl.scan_parquet(path)
    else:
        separator = "\t" if suffix == ".tsv" else ","
        lf = pl.scan_csv(path, separator=separator, infer_schema_length=10000)
    return lf.select(pl.len()).collect().item()


def get_csv_preview(path: Path, preview_rows: int = 5) -> dict | None:
    """テーブルファイル（CSV / TSV / Parquet）の先頭行プレビューを返す（軽量）。"""
    if not path.exists():
        return None
    try:
        df = _read_tabular_head(path, preview_rows)
        return {
            "columns": df.columns,
            "rows": df.to_dicts(),
            "total_rows": _count_tabular_rows(path),
            "total_cols": len(df.columns),
        }
    except Exception:
        return None


def get_csv_stats(path: Path, stats_rows: int = 10000) -> dict | None:
    """テーブルファイル（CSV / TSV / Parquet）の統計情報を返す（重い処理）。"""
    if not path.exists():
        return None
    try:
        df = _read_tabular_head(path, stats_rows)
        describe = df.describe()
        null_counts = {col: df[col].null_count() for col in df.columns}

        return {
            "total_rows": _count_tabular_rows(path),
            "total_cols": len(df.columns),
            "dtypes": {col: str(df[col].dtype) for col in df.columns},
            "null_counts": null_counts,
            "describe_columns": describe.columns,
            "describe_rows": describe.to_dicts(),
        }
    except Exception:
        return None


def get_tabular_records(path: Path, offset: int = 0, limit: int = 5) -> dict | None:
    """長文テキスト向けのレコード単位ビュー（1行 = 1カード）。"""
    if not path.exists():
        return None
    try:
        df = _read_tabular_head(path, offset + limit)
        rows = df.to_dicts()[offset : offset + limit]
        return {
            "columns": df.columns,
            "rows": rows,
            "offset": offset,
            "limit": limit,
            "total_rows": _count_tabular_rows(path),
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


def read_text_preview(path: Path, max_bytes: int = 100_000) -> str | None:
    """テキストファイルの先頭を読み取る。"""
    if not path.exists() or not path.is_file():
        return None
    try:
        size = path.stat().st_size
        if size > max_bytes:
            with open(path, encoding="utf-8", errors="replace") as f:
                return f.read(max_bytes) + "\n... (truncated)"
        return path.read_text(encoding="utf-8", errors="replace")
    except Exception:
        return None


def read_json_preview(path: Path, max_bytes: int = 100_000) -> str | None:
    """JSON ファイルを整形して返す。"""
    import json

    if not path.exists():
        return None
    raw = ""
    try:
        raw = path.read_text(encoding="utf-8", errors="replace")
        if path.suffix.lower() == ".jsonl":
            lines = raw.splitlines()[:50]
            return "\n".join(lines)
        obj = json.loads(raw)
        formatted = json.dumps(obj, indent=2, ensure_ascii=False)
        if len(formatted) > max_bytes:
            return formatted[:max_bytes] + "\n... (truncated)"
        return formatted
    except Exception:
        return raw[:max_bytes] if len(raw) <= max_bytes else raw[:max_bytes] + "\n..."


def _data_file_type(suffix: str) -> str:
    """拡張子をデータ型カテゴリに変換。"""
    s = suffix.lower()
    if s in TABULAR_EXTENSIONS:
        return "tabular"
    if s in IMAGE_EXTENSIONS:
        return "image"
    if s in VIDEO_EXTENSIONS:
        return "video"
    if s in AUDIO_EXTENSIONS:
        return "audio"
    if s in {".json", ".jsonl"}:
        return "json"
    if s in TEXT_EXTENSIONS:
        return "text"
    return "other"


def data_file_icon(file_type: str) -> str:
    """Data file type to FontAwesome icon class."""
    mapping = {
        "tabular": "fa-file-csv",
        "image": "fa-image",
        "video": "fa-film",
        "audio": "fa-music",
        "json": "fa-file-code",
        "text": "fa-file-lines",
        "other": "fa-file",
    }
    return mapping.get(file_type, "fa-file")
