"""Dashboard common utilities."""

from __future__ import annotations

import re
from datetime import datetime, timezone
from pathlib import Path

import markdown
import yaml
from fastapi import Request

PROJECT_ROOT = Path(__file__).parent.parent


# ---------------------------------------------------------------------------
# Experiments
# ---------------------------------------------------------------------------


def list_experiments(query: str = "") -> list[dict]:
    """src/exp* を走査し、README スコア情報とマージして返す。"""
    src = PROJECT_ROOT / "src"
    if not src.exists():
        return []

    score_map = {e["exp"]: e for e in parse_experiments_table()}

    exps = []
    for d in sorted(src.iterdir()):
        if not (d.is_dir() and d.name.startswith("exp")):
            continue
        info = {
            "name": d.name,
            "has_readme": (d / "README.md").exists(),
            "has_config": (d / "config" / "config.yaml").exists(),
            "has_inference": (d / "inference.py").exists(),
            "cv": score_map.get(d.name, {}).get("cv", "-"),
            "lb": score_map.get(d.name, {}).get("lb", "-"),
            "description": score_map.get(d.name, {}).get("description", ""),
        }
        if query and query.lower() not in d.name.lower():
            continue
        exps.append(info)
    return exps


def get_experiment_detail(exp_name: str) -> dict | None:
    """単一実験の詳細情報を返す。"""
    exp_dir = PROJECT_ROOT / "src" / exp_name
    if not exp_dir.is_dir():
        return None

    config = None
    config_path = exp_dir / "config" / "config.yaml"
    if config_path.exists():
        config = read_config_yaml(config_path)

    readme_html = None
    if (exp_dir / "README.md").exists():
        readme_html = read_markdown_file(exp_dir / "README.md")["html"]

    files = list_experiment_files(exp_dir)
    checkpoints = list_checkpoints(exp_name)

    score_map = {e["exp"]: e for e in parse_experiments_table()}
    scores = score_map.get(exp_name, {})

    return {
        "name": exp_name,
        "config": config,
        "readme_html": readme_html,
        "files": files,
        "checkpoints": checkpoints,
        "oof_exists": (PROJECT_ROOT / "output" / exp_name / "oof_predictions.csv").exists(),
        "cv": scores.get("cv", "-"),
        "lb": scores.get("lb", "-"),
    }


def read_config_yaml(path: Path) -> dict:
    """config.yaml を dict として返す。"""
    with open(path) as f:
        return yaml.safe_load(f) or {}


def list_experiment_files(exp_dir: Path) -> list[dict]:
    """実験ディレクトリ内のファイルツリーを返す。"""
    files = []
    for f in sorted(exp_dir.rglob("*")):
        if f.is_file() and not f.name.startswith("."):
            files.append(
                {
                    "name": str(f.relative_to(exp_dir)),
                    "type": _file_type(f.suffix),
                    "size": f.stat().st_size,
                    "modified": datetime.fromtimestamp(
                        f.stat().st_mtime, tz=timezone.utc
                    ),
                }
            )
    return files


def parse_experiments_table() -> list[dict]:
    """Root README.md の Experiments テーブルを解析する。"""
    readme = PROJECT_ROOT / "README.md"
    if not readme.exists():
        return []

    text = readme.read_text()
    rows = []
    in_table = False
    for line in text.splitlines():
        stripped = line.strip()
        if stripped.startswith("| Exp") and "Name" in stripped:
            in_table = True
            continue
        if in_table and stripped.startswith("|---"):
            continue
        if in_table and stripped.startswith("|"):
            cells = [c.strip() for c in stripped.strip("|").split("|")]
            if len(cells) >= 5:
                rows.append(
                    {
                        "exp": cells[0],
                        "name": cells[1],
                        "cv": cells[2],
                        "lb": cells[3],
                        "description": cells[4],
                    }
                )
        elif in_table:
            break
    return rows


# ---------------------------------------------------------------------------
# Mermaid Experiment Tree
# ---------------------------------------------------------------------------


def parse_mermaid_tree() -> str | None:
    """Root README.md から Mermaid コードブロックを抽出する。"""
    readme = PROJECT_ROOT / "README.md"
    if not readme.exists():
        return None

    text = readme.read_text()
    match = re.search(r"```mermaid\s*\n(.*?)```", text, re.DOTALL)
    if match:
        return match.group(1).strip()
    return None


# ---------------------------------------------------------------------------
# Output / Checkpoints
# ---------------------------------------------------------------------------


def list_checkpoints(exp_name: str) -> list[dict]:
    """output/{exp_name}/ の best-*.ckpt を列挙。"""
    out_dir = PROJECT_ROOT / "output" / exp_name
    if not out_dir.exists():
        return []
    return [
        {
            "filename": f.name,
            "size": f.stat().st_size,
            "modified": datetime.fromtimestamp(f.stat().st_mtime, tz=timezone.utc),
        }
        for f in sorted(out_dir.glob("best-*.ckpt"))
    ]


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


# ---------------------------------------------------------------------------
# Documents
# ---------------------------------------------------------------------------


def list_docs() -> dict:
    """docs/ 配下を分類して返す。"""
    result: dict[str, list[dict]] = {"official": [], "discussion": [], "insights": []}
    for category in result:
        d = PROJECT_ROOT / "docs" / category
        if not d.exists():
            continue
        for f in sorted(d.glob("*.md")):
            result[category].append(
                {
                    "name": f.stem,
                    "filename": f.name,
                    "category": category,
                    "modified": datetime.fromtimestamp(
                        f.stat().st_mtime, tz=timezone.utc
                    ),
                }
            )
    return result


def _list_docs_for_category(category: str) -> list[dict]:
    """指定カテゴリの docs を列挙。"""
    d = PROJECT_ROOT / "docs" / category
    if not d.exists():
        return []
    return [
        {
            "name": f.stem,
            "filename": f.name,
            "category": category,
            "modified": datetime.fromtimestamp(f.stat().st_mtime, tz=timezone.utc),
        }
        for f in sorted(d.glob("*.md"))
    ]


def list_discussion_docs() -> list[dict]:
    """docs/discussion/ のドキュメントを列挙。"""
    return _list_docs_for_category("discussion")


def list_knowledge_docs() -> dict:
    """Knowledge ページ用: official + insights を返す。"""
    return {
        "official": _list_docs_for_category("official"),
        "insights": _list_docs_for_category("insights"),
    }


# ---------------------------------------------------------------------------
# Competition Overview (from README.md)
# ---------------------------------------------------------------------------


def get_competition_overview() -> dict | None:
    """README.md からコンペ概要を抽出する。"""
    readme = PROJECT_ROOT / "README.md"
    if not readme.exists():
        return None

    text = readme.read_text()
    lines = text.splitlines()

    title = None
    description_lines = []
    for line in lines:
        if line.startswith("# ") and title is None:
            title = line[2:].strip()
            continue
        if title and line.startswith("## "):
            break
        if title and line.strip().startswith(">"):
            description_lines.append(line.strip().lstrip("> ").strip())

    if not title:
        return None
    return {
        "title": title,
        "description": " ".join(description_lines) if description_lines else None,
    }


def get_validation_strategy() -> str | None:
    """README.md から Validation Strategy セクションを HTML で返す。"""
    readme = PROJECT_ROOT / "README.md"
    if not readme.exists():
        return None

    text = readme.read_text()
    match = re.search(
        r"## Validation Strategy\s*\n(.*?)(?=\n## |\Z)", text, re.DOTALL
    )
    if not match:
        return None

    section = match.group(1).strip()
    if not section:
        return None
    return markdown.markdown(section, extensions=["tables", "fenced_code"])


def read_markdown_file(path: Path) -> dict:
    """Markdown -> HTML 変換。"""
    raw = path.read_text()
    html = markdown.markdown(
        raw,
        extensions=["tables", "fenced_code", "toc"],
        extension_configs={"fenced_code": {"lang_prefix": "language-"}},
    )
    title_match = re.search(r"^#\s+(.+)", raw, re.MULTILINE)
    return {
        "raw": raw,
        "html": html,
        "title": title_match.group(1) if title_match else path.stem,
    }


# ---------------------------------------------------------------------------
# Notebooks
# ---------------------------------------------------------------------------


def list_notebooks() -> list[dict]:
    """notebook/*.ipynb を列挙。"""
    nb_dir = PROJECT_ROOT / "notebook"
    if not nb_dir.exists():
        return []
    return [
        {
            "name": f.stem,
            "filename": f.name,
            "size": f.stat().st_size,
            "modified": datetime.fromtimestamp(f.stat().st_mtime, tz=timezone.utc),
        }
        for f in sorted(nb_dir.glob("*.ipynb"))
    ]


# ---------------------------------------------------------------------------
# Data / Input Files
# ---------------------------------------------------------------------------

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
            item["child_count"] = sum(1 for c in f.rglob("*") if c.is_file())
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


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


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
