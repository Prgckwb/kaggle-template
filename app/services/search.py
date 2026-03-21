"""Global search across experiments, knowledge docs, and data files."""

from __future__ import annotations

from pathlib import Path

from app.services.data import list_input_files
from app.services.documents import list_docs
from app.services.experiments import list_experiments, list_runs
from app.services.helpers import PROJECT_ROOT


def global_search(query: str, limit: int = 20) -> dict[str, list[dict]]:
    """全セクションを横断検索し、カテゴリ別に結果を返す。"""
    q = query.strip().lower()
    if not q:
        return {"experiments": [], "runs": [], "knowledge": [], "data": []}

    results: dict[str, list[dict]] = {
        "experiments": _search_experiments(q),
        "runs": _search_runs(q),
        "knowledge": _search_knowledge(q),
        "data": _search_data(q),
    }

    # 各カテゴリを limit 件に制限
    for key in results:
        results[key] = results[key][:limit]

    return results


def _search_experiments(q: str) -> list[dict]:
    """実験名・description で検索。"""
    hits = []
    for exp in list_experiments():
        name = exp.get("name", "")
        desc = exp.get("description", "") or ""
        if q in name.lower() or q in desc.lower():
            hits.append({
                "title": name,
                "description": desc,
                "url": f"/experiments/{name}",
                "icon": "fa-flask",
                "color": "emerald",
            })
    return hits


def _search_runs(q: str) -> list[dict]:
    """実験配下の Run（小実験）を run 名で検索。"""
    hits = []
    for exp in list_experiments():
        for run in list_runs(exp["name"]):
            if q in run["name"].lower():
                hits.append({
                    "title": run["name"],
                    "description": exp["name"],
                    "url": f"/experiments/{exp['name']}",
                    "icon": "fa-vial",
                    "color": "emerald",
                })
    return hits


def _search_knowledge(q: str) -> list[dict]:
    """ドキュメント名 + Markdown 本文で検索。"""
    hits = []
    all_docs = list_docs()
    for category, docs in all_docs.items():
        for doc in docs:
            name = doc.get("name", "")
            filename = doc.get("filename", "")

            # 名前マッチ
            name_match = q in name.lower()

            # 本文マッチ
            body_match = False
            if not name_match:
                file_path = PROJECT_ROOT / "docs" / category / filename
                if file_path.exists():
                    try:
                        content = file_path.read_text()
                        body_match = q in content.lower()
                    except (OSError, UnicodeDecodeError):
                        pass

            if name_match or body_match:
                hits.append({
                    "title": name,
                    "description": _category_label(category),
                    "url": f"/knowledge/{category}/{filename}",
                    "icon": _category_icon(category),
                    "color": _category_color(category),
                    "match_type": "name" if name_match else "body",
                })
    return hits


def _search_data(q: str) -> list[dict]:
    """input/ 配下のファイル名で検索。"""
    hits = []
    _search_data_recursive(q, "", hits)
    return hits


def _search_data_recursive(q: str, directory: str, hits: list[dict]) -> None:
    """input/ を再帰的に走査してファイル名検索。"""
    for item in list_input_files(directory):
        if item["is_dir"]:
            _search_data_recursive(q, item["path"], hits)
        elif q in item["name"].lower():
            hits.append({
                "title": item["name"],
                "description": item["path"],
                "url": f"/data?file={item['path']}",
                "icon": "fa-database",
                "color": "amber",
            })


def _category_label(category: str) -> str:
    return {"official": "Official", "insights": "Insights", "discussion": "Discussion"}.get(
        category, category
    )


def _category_icon(category: str) -> str:
    return {
        "official": "fa-building-columns",
        "insights": "fa-lightbulb",
        "discussion": "fa-comments",
    }.get(category, "fa-book")


def _category_color(category: str) -> str:
    return {"official": "sky", "insights": "amber", "discussion": "rose"}.get(
        category, "gray"
    )
