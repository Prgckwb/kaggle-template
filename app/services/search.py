"""Global search across experiments, knowledge docs, and data files."""

from __future__ import annotations

import time
from pathlib import Path

from app.services.data import list_input_files
from app.services.documents import list_docs
from app.services.experiments import list_experiments, list_runs
from app.services.helpers import PROJECT_ROOT

# ---------------------------------------------------------------------------
# In-module caches (キーストロークごとの全ファイル再読込を防ぐ)
# ---------------------------------------------------------------------------

# runs インデックス: config yaml の mtime シグネチャで無効化
_runs_cache: dict[str, object] = {"sig": None, "data": []}

# knowledge ドキュメント本文: (path, mtime) で無効化
_doc_text_cache: dict[str, tuple[float, str]] = {}

# input/ 配下のフラットなファイルリスト: 短い TTL で無効化
_data_files_cache: dict[str, object] = {"fetched_at": 0.0, "data": []}
_DATA_CACHE_TTL = 30.0  # seconds
_DATA_MAX_DEPTH = 4


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
            hits.append(
                {
                    "title": name,
                    "description": desc,
                    "url": f"/experiments/{name}",
                    "icon": "fa-flask",
                    "color": "emerald",
                }
            )
    return hits


def _config_signature() -> tuple:
    """src/exp*/config/*.yaml の (path, mtime) シグネチャ（stat のみで軽量）。"""
    sig = []
    src = PROJECT_ROOT / "src"
    if not src.exists():
        return ()
    for d in sorted(src.iterdir()):
        if not (d.is_dir() and d.name.startswith("exp")):
            continue
        config_dir = d / "config"
        if not config_dir.exists():
            continue
        for f in sorted(config_dir.glob("*.yaml")):
            sig.append((str(f), f.stat().st_mtime))
    return tuple(sig)


def _get_runs_index() -> list[dict]:
    """(exp_name, run_name) のインデックスを config mtime シグネチャでキャッシュ。"""
    sig = _config_signature()
    if sig != _runs_cache["sig"]:
        index = []
        for exp in list_experiments():
            for run in list_runs(exp["name"]):
                index.append({"exp_name": exp["name"], "run_name": run["name"]})
        _runs_cache["data"] = index
        _runs_cache["sig"] = sig
    return _runs_cache["data"]  # type: ignore[return-value]


def _search_runs(q: str) -> list[dict]:
    """実験配下の Run（小実験）を run 名で検索。"""
    hits = []
    for entry in _get_runs_index():
        if q in entry["run_name"].lower():
            hits.append(
                {
                    "title": entry["run_name"],
                    "description": entry["exp_name"],
                    "url": f"/experiments/{entry['exp_name']}",
                    "icon": "fa-vial",
                    "color": "emerald",
                }
            )
    return hits


def _read_doc_text(path: Path) -> str:
    """ドキュメント本文（小文字化済み）を (path, mtime) キーでキャッシュして返す。"""
    key = str(path)
    try:
        mtime = path.stat().st_mtime
    except OSError:
        return ""
    cached = _doc_text_cache.get(key)
    if cached is not None and cached[0] == mtime:
        return cached[1]
    try:
        text = path.read_text().lower()
    except (OSError, UnicodeDecodeError):
        text = ""
    _doc_text_cache[key] = (mtime, text)
    return text


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
                    body_match = q in _read_doc_text(file_path)

            if name_match or body_match:
                hits.append(
                    {
                        "title": name,
                        "description": _category_label(category),
                        "url": f"/knowledge/{category}/{filename}",
                        "icon": _category_icon(category),
                        "color": _category_color(category),
                        "match_type": "name" if name_match else "body",
                    }
                )
    return hits


def _search_data(q: str) -> list[dict]:
    """input/ 配下のファイル名で検索。"""
    hits = []
    for item in _get_data_file_index():
        if q in item["name"].lower():
            hits.append(
                {
                    "title": item["name"],
                    "description": item["path"],
                    "url": f"/data?file={item['path']}",
                    "icon": "fa-database",
                    "color": "amber",
                }
            )
    return hits


def _get_data_file_index() -> list[dict]:
    """input/ のフラットなファイルリストを短い TTL でキャッシュして返す。"""
    now = time.time()
    if now - _data_files_cache["fetched_at"] < _DATA_CACHE_TTL:  # type: ignore[operator]
        return _data_files_cache["data"]  # type: ignore[return-value]
    files: list[dict] = []
    _collect_data_files("", files, depth=0)
    _data_files_cache["data"] = files
    _data_files_cache["fetched_at"] = now
    return files


def _collect_data_files(directory: str, files: list[dict], depth: int) -> None:
    """input/ を最大 _DATA_MAX_DEPTH 階層まで走査してファイルを収集。"""
    for item in list_input_files(directory):
        if item["is_dir"]:
            if depth + 1 < _DATA_MAX_DEPTH:
                _collect_data_files(item["path"], files, depth + 1)
        else:
            files.append({"name": item["name"], "path": item["path"]})


def _category_label(category: str) -> str:
    return {
        "official": "Official",
        "insights": "Insights",
        "discussion": "Discussion",
    }.get(category, category)


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
