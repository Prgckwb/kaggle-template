"""Document and markdown utilities."""

from __future__ import annotations

import re
from datetime import datetime, timezone
from pathlib import Path

import markdown
import nh3

from app.services.helpers import PROJECT_ROOT


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
    html = markdown.markdown(section, extensions=["tables", "fenced_code"])
    return _sanitize_html(html)


def read_markdown_file(path: Path) -> dict:
    """Markdown -> HTML 変換（サニタイズ済み）。"""
    raw = path.read_text()
    html = markdown.markdown(
        raw,
        extensions=["tables", "fenced_code", "toc"],
        extension_configs={"fenced_code": {"lang_prefix": "language-"}},
    )
    title_match = re.search(r"^#\s+(.+)", raw, re.MULTILINE)
    return {
        "raw": raw,
        "html": _sanitize_html(html),
        "title": title_match.group(1) if title_match else path.stem,
    }


def _sanitize_html(html: str) -> str:
    """nh3 で HTML をサニタイズ（XSS 防止）。"""
    return nh3.clean(
        html,
        tags={
            "h1", "h2", "h3", "h4", "h5", "h6",
            "p", "br", "hr",
            "ul", "ol", "li",
            "a", "strong", "em", "code", "pre", "blockquote",
            "table", "thead", "tbody", "tr", "th", "td",
            "img", "div", "span",
            "dl", "dt", "dd",
            "sup", "sub",
        },
        attributes={
            "*": {"class", "id"},
            "a": {"href", "title"},
            "img": {"src", "alt", "title", "width", "height"},
            "td": {"align"},
            "th": {"align"},
        },
    )
