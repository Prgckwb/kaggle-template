"""Guides / reports registry (docs/guides/ scanner).

docs/guides/{slug}/guide.json + index.html を「ガイド」として自動発見する。
ガイドの追加はディレクトリを置くだけで、アプリのコード変更は不要。
"""

from __future__ import annotations

import json
from pathlib import Path

from app.services.helpers import PROJECT_ROOT

GUIDES_DIR = PROJECT_ROOT / "docs" / "guides"

# guide.json のデフォルト値
_DEFAULTS = {
    "title": None,  # 必須（欠落時は slug を使う）
    "description": "",
    "icon": "fa-book-open",
    "color": "violet",
    "tags": [],
    "created": "",
    "render": "iframe",  # iframe | fragment
}

_VALID_RENDER = {"iframe", "fragment"}


def list_guides(tag: str | None = None) -> list[dict]:
    """docs/guides/*/guide.json をスキャンしてガイド一覧を返す（作成日降順）。"""
    if not GUIDES_DIR.exists():
        return []

    guides = []
    for d in sorted(GUIDES_DIR.iterdir()):
        if not d.is_dir() or d.name.startswith("."):
            continue
        guide = _load_guide(d)
        if guide is None:
            continue
        if tag and tag not in guide["tags"]:
            continue
        guides.append(guide)

    # created 降順（未設定 "" は自動的に末尾）、同日は slug 昇順（安定ソート2回）
    guides.sort(key=lambda g: g["slug"])
    guides.sort(key=lambda g: g["created"], reverse=True)
    return guides


def get_guide(slug: str) -> dict | None:
    """単一ガイドのメタデータを返す。"""
    d = GUIDES_DIR / slug
    if not d.is_dir() or "/" in slug or slug.startswith("."):
        return None
    return _load_guide(d)


def list_all_tags() -> list[str]:
    """全ガイドのタグを重複なしで返す（出現数降順）。"""
    counts: dict[str, int] = {}
    for g in list_guides():
        for t in g["tags"]:
            counts[t] = counts.get(t, 0) + 1
    return sorted(counts, key=lambda t: (-counts[t], t))


def read_fragment_html(slug: str) -> str | None:
    """fragment レンダリング用に index.html の中身を返す。

    リポジトリ管理下の信頼済みコンテンツのため、サニタイズは行わない。
    """
    path = GUIDES_DIR / slug / "index.html"
    if not path.exists():
        return None
    try:
        return path.read_text(encoding="utf-8", errors="replace")
    except OSError:
        return None


def _load_guide(d: Path) -> dict | None:
    """1ガイドディレクトリを読み込む。guide.json がなければ None。"""
    meta_path = d / "guide.json"
    if not meta_path.exists():
        return None
    try:
        raw = json.loads(meta_path.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError):
        raw = {}

    guide = {**_DEFAULTS, **{k: v for k, v in raw.items() if k in _DEFAULTS}}
    guide["slug"] = d.name
    if not guide["title"]:
        guide["title"] = d.name
    if not isinstance(guide["tags"], list):
        guide["tags"] = []
    if guide["render"] not in _VALID_RENDER:
        guide["render"] = "iframe"
    guide["has_index"] = (d / "index.html").exists()
    return guide
