"""Experiment management utilities."""

from __future__ import annotations

import re
from datetime import datetime, timezone
from pathlib import Path

import yaml

from app.services.documents import read_markdown_file
from app.services.helpers import PROJECT_ROOT, _file_type

# ---------------------------------------------------------------------------
# README.md cache (mtime-based invalidation)
# ---------------------------------------------------------------------------

_readme_cache: dict[str, object] = {"mtime": 0.0, "data": []}


def _get_cached_experiments_table() -> list[dict]:
    """parse_experiments_table() の結果を mtime ベースでキャッシュする。"""
    readme = PROJECT_ROOT / "README.md"
    if not readme.exists():
        return []
    current_mtime = readme.stat().st_mtime
    if current_mtime != _readme_cache["mtime"]:
        _readme_cache["data"] = _parse_experiments_table_impl()
        _readme_cache["mtime"] = current_mtime
    return _readme_cache["data"]  # type: ignore[return-value]


def list_experiments(query: str = "") -> list[dict]:
    """src/exp* を走査し、README スコア情報とマージして返す。"""
    src = PROJECT_ROOT / "src"
    if not src.exists():
        return []

    score_map = {e["exp"]: e for e in _get_cached_experiments_table()}

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

    score_map = {e["exp"]: e for e in _get_cached_experiments_table()}
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
    """キャッシュ付き public API。"""
    return _get_cached_experiments_table()


def _parse_experiments_table_impl() -> list[dict]:
    """Root README.md の Experiments テーブルを解析する。ヘッダーからカラム位置を動的検出。"""
    readme = PROJECT_ROOT / "README.md"
    if not readme.exists():
        return []

    text = readme.read_text()
    rows = []
    headers: list[str] = []
    in_table = False

    header_aliases = {
        "exp": "exp",
        "name": "name",
        "split": "split",
        "key change": "description",
        "cv": "cv",
        "lb": "lb",
        "description": "description",
    }

    for line in text.splitlines():
        stripped = line.strip()
        if stripped.startswith("| Exp") and "Name" in stripped:
            raw_headers = [c.strip().lower() for c in stripped.strip("|").split("|")]
            headers = [header_aliases.get(h, h) for h in raw_headers]
            in_table = True
            continue
        if in_table and stripped.startswith("|---"):
            continue
        if in_table and stripped.startswith("|"):
            cells = [c.strip() for c in stripped.strip("|").split("|")]
            if len(cells) >= len(headers):
                row = {headers[i]: cells[i] for i in range(len(headers))}
                rows.append(row)
        elif in_table:
            break
    return rows


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


def get_oof_analysis(exp_name: str) -> dict | None:
    """OOF predictions の分析結果を返す。"""
    oof_path = PROJECT_ROOT / "output" / exp_name / "oof_predictions.csv"
    if not oof_path.exists():
        return None

    import polars as pl

    try:
        df = pl.read_csv(oof_path)
        columns = df.columns

        result: dict = {
            "total_rows": len(df),
            "columns": columns,
            "preview_rows": df.head(20).to_dicts(),
        }

        # confusion matrix (true_label vs pred_label がある場合)
        if "true_label" in columns and "pred_label" in columns:
            labels = sorted(df["true_label"].unique().to_list())
            matrix = []
            for true in labels:
                row = []
                for pred in labels:
                    count = df.filter(
                        (pl.col("true_label") == true) & (pl.col("pred_label") == pred)
                    ).height
                    row.append(count)
                matrix.append(row)
            accuracy = df.filter(pl.col("true_label") == pl.col("pred_label")).height / len(df)
            result["confusion_matrix"] = {
                "labels": [str(l) for l in labels],
                "matrix": matrix,
            }
            result["accuracy"] = round(accuracy, 4)

        # 確率カラムの分布 (prob_0, prob_1, ... がある場合)
        prob_cols = [c for c in columns if c.startswith("prob_")]
        if prob_cols:
            distributions = {}
            for col in prob_cols:
                vals = df[col].to_list()
                # 10 bins のヒストグラム
                hist_counts = [0] * 10
                for v in vals:
                    if v is not None:
                        bin_idx = min(int(v * 10), 9)
                        hist_counts[bin_idx] += 1
                distributions[col] = hist_counts
            result["prob_distributions"] = distributions

        return result
    except Exception:
        return None


def get_all_experiment_scores() -> list[dict]:
    """全実験の CV/LB スコアを返す（グラフ用）。"""
    table = _get_cached_experiments_table()
    scores = []
    for row in table:
        cv = row.get("cv", "-")
        lb = row.get("lb", "-")
        try:
            cv_val = float(cv) if cv != "-" else None
        except (ValueError, TypeError):
            cv_val = None
        try:
            lb_val = float(lb) if lb != "-" else None
        except (ValueError, TypeError):
            lb_val = None
        if cv_val is not None or lb_val is not None:
            scores.append({
                "exp": row.get("exp", ""),
                "name": row.get("name", ""),
                "cv": cv_val,
                "lb": lb_val,
            })
    return scores


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
