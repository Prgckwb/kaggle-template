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

    files = list_experiment_files_flat(exp_dir)
    file_tree = list_experiment_files(exp_dir)
    checkpoints = list_checkpoints(exp_name)

    score_map = {e["exp"]: e for e in _get_cached_experiments_table()}
    scores = score_map.get(exp_name, {})

    runs = list_runs(exp_name)

    return {
        "name": exp_name,
        "config": config,
        "readme_html": readme_html,
        "files": files,
        "file_tree": file_tree,
        "checkpoints": checkpoints,
        "runs": runs,
        "cv": scores.get("cv", "-"),
        "lb": scores.get("lb", "-"),
    }


def read_config_yaml(path: Path) -> dict:
    """config.yaml を dict として返す。"""
    with open(path) as f:
        return yaml.safe_load(f) or {}


# Directories and patterns to exclude from experiment file listings
_EXCLUDED_DIRS = {"__pycache__", "output", "logs", ".git", ".venv", "node_modules"}
_EXCLUDED_SUFFIXES = {".pyc", ".pyo"}


def list_experiment_files(exp_dir: Path) -> list[dict]:
    """実験ディレクトリ内のファイルツリーをツリー構造で返す。"""
    return _build_file_tree(exp_dir, exp_dir)


def _build_file_tree(directory: Path, root: Path) -> list[dict]:
    """ディレクトリを再帰的に走査し、ツリー構造を返す。"""
    items: list[dict] = []
    if not directory.exists():
        return items
    for entry in sorted(directory.iterdir(), key=lambda p: (not p.is_dir(), p.name)):
        if entry.name.startswith("."):
            continue
        if entry.is_dir():
            if entry.name in _EXCLUDED_DIRS:
                continue
            children = _build_file_tree(entry, root)
            if children:  # 空ディレクトリはスキップ
                items.append({
                    "name": entry.name,
                    "path": str(entry.relative_to(root)),
                    "is_dir": True,
                    "children": children,
                })
        else:
            if entry.suffix.lower() in _EXCLUDED_SUFFIXES:
                continue
            items.append({
                "name": entry.name,
                "path": str(entry.relative_to(root)),
                "is_dir": False,
                "type": _file_type(entry.suffix),
                "size": entry.stat().st_size,
            })
    return items


def list_experiment_files_flat(exp_dir: Path) -> list[dict]:
    """フラットなファイルリスト（ファイル数カウント用）。"""
    files = []
    for f in sorted(exp_dir.rglob("*")):
        if f.is_file() and not f.name.startswith("."):
            rel = f.relative_to(exp_dir)
            parts = rel.parts
            if any(p in _EXCLUDED_DIRS for p in parts):
                continue
            if f.suffix.lower() in _EXCLUDED_SUFFIXES:
                continue
            files.append({
                "name": str(rel),
                "type": _file_type(f.suffix),
                "size": f.stat().st_size,
            })
    return files


def get_experiment_file_content(exp_name: str, file_path: str) -> dict | None:
    """実験ファイルのプレビュー用情報を返す。"""
    exp_dir = PROJECT_ROOT / "src" / exp_name
    full_path = (exp_dir / file_path).resolve()

    # Path traversal prevention
    if not full_path.is_relative_to(exp_dir.resolve()):
        return None
    if not full_path.exists() or not full_path.is_file():
        return None

    file_type = _file_type(full_path.suffix)
    result: dict = {
        "name": full_path.name,
        "path": file_path,
        "type": file_type,
        "size": full_path.stat().st_size,
        "suffix": full_path.suffix.lower(),
    }

    # Determine highlight.js language
    lang_map = {
        "python": "python",
        "yaml": "yaml",
        "json": "json",
        "bash": "bash",
        "text": "",
        "markdown": "markdown",
    }

    if file_type == "markdown":
        result["content_html"] = read_markdown_file(full_path)["html"]
    elif file_type in ("python", "yaml", "json", "bash", "text"):
        try:
            text = full_path.read_text(encoding="utf-8", errors="replace")
            if len(text) > 200_000:
                text = text[:200_000] + "\n... (truncated)"
            result["content_text"] = text
            result["language"] = lang_map.get(file_type, "")
        except Exception:
            result["content_text"] = None
    elif file_type in ("image", "video", "audio"):
        result["media_url"] = f"/experiments/{exp_name}/_file_raw/{file_path}"
    elif file_type == "csv":
        try:
            import polars as pl
            df = pl.read_csv(full_path, n_rows=50)
            result["csv_columns"] = df.columns
            result["csv_rows"] = df.to_dicts()
            result["csv_total"] = pl.scan_csv(full_path).select(pl.len()).collect().item()
        except Exception:
            result["content_text"] = full_path.read_text(encoding="utf-8", errors="replace")[:50_000]
            result["language"] = ""
    elif file_type == "binary":
        pass  # No content, template will show binary message
    else:
        # Try to read as text for unknown types
        try:
            text = full_path.read_text(encoding="utf-8", errors="strict")
            if len(text) > 200_000:
                text = text[:200_000] + "\n... (truncated)"
            result["content_text"] = text
            result["language"] = ""
        except (UnicodeDecodeError, Exception):
            result["type"] = "binary"  # fallback to binary

    return result


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


def list_runs(exp_name: str) -> list[dict]:
    """src/{exp_name}/config/run*.yaml をスキャンし、各 run の情報を返す。"""
    exp_dir = PROJECT_ROOT / "src" / exp_name
    config_dir = exp_dir / "config"
    output_dir = exp_dir / "output"

    runs = []

    logs_dir = exp_dir / "logs"

    # ベース config (run000-base)
    base_config = config_dir / "config.yaml"
    if base_config.exists():
        cfg = read_config_yaml(base_config)
        run_name = cfg.get("run_name", "run000-base")
        run_output = output_dir / run_name
        ckpts = list(run_output.glob("fold*/*.ckpt")) if run_output.exists() else []
        runs.append({
            "name": run_name,
            "config_file": "config.yaml",
            "has_output": run_output.exists(),
            "checkpoint_count": len(ckpts),
            "has_oof": (run_output / "oof_predictions.csv").exists(),
            "has_logs": (logs_dir / run_name).exists(),
        })

    # 小実験 config (run*.yaml)
    if config_dir.exists():
        for f in sorted(config_dir.glob("run*.yaml")):
            cfg = read_config_yaml(f)
            run_name = cfg.get("run_name", f.stem)
            run_output = output_dir / run_name
            ckpts = list(run_output.glob("fold*/*.ckpt")) if run_output.exists() else []
            runs.append({
                "name": run_name,
                "config_file": f.name,
                "has_output": run_output.exists(),
                "checkpoint_count": len(ckpts),
                "has_oof": (run_output / "oof_predictions.csv").exists(),
                "has_logs": (logs_dir / run_name).exists(),
            })

    return runs


def get_run_config(exp_name: str, run_name: str) -> dict | None:
    """特定 run の config を読む。"""
    exp_dir = PROJECT_ROOT / "src" / exp_name
    config_dir = exp_dir / "config"

    # ベース config
    base_path = config_dir / "config.yaml"
    if base_path.exists():
        base_cfg = read_config_yaml(base_path)
        if base_cfg.get("run_name", "run000-base") == run_name:
            return base_cfg

    # 小実験 config
    for f in config_dir.glob("run*.yaml"):
        cfg = read_config_yaml(f)
        if cfg.get("run_name", f.stem) == run_name:
            return cfg

    return None


def list_checkpoints(exp_name: str) -> list[dict]:
    """src/{exp_name}/output/*/fold*/*.ckpt を列挙。"""
    out_dir = PROJECT_ROOT / "src" / exp_name / "output"
    if not out_dir.exists():
        return []
    results = []
    for f in sorted(out_dir.glob("*/fold*/*.ckpt")):
        run_name = f.parent.parent.name
        results.append({
            "run": run_name,
            "filename": f"{f.parent.name}/{f.name}",
            "size": f.stat().st_size,
            "modified": datetime.fromtimestamp(f.stat().st_mtime, tz=timezone.utc),
        })
    return results


def get_oof_analysis(exp_name: str, run_name: str | None = None) -> dict | None:
    """OOF predictions の分析結果を返す。"""
    if run_name:
        oof_path = PROJECT_ROOT / "src" / exp_name / "output" / run_name / "oof_predictions.csv"
    else:
        # run_name 未指定時は最初に見つかった OOF を返す
        out_dir = PROJECT_ROOT / "src" / exp_name / "output"
        oof_path = None
        if out_dir.exists():
            for d in sorted(out_dir.iterdir()):
                candidate = d / "oof_predictions.csv"
                if candidate.exists():
                    oof_path = candidate
                    break
        if oof_path is None:
            return None
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


# ---------------------------------------------------------------------------
# Training logs
# ---------------------------------------------------------------------------


def list_run_logs(exp_name: str) -> list[dict]:
    """logs/{run_name}/ ディレクトリを走査し、ログの有無を返す。"""
    import json as _json

    logs_dir = PROJECT_ROOT / "src" / exp_name / "logs"
    if not logs_dir.exists():
        return []
    results = []
    for d in sorted(logs_dir.iterdir()):
        if not d.is_dir():
            continue
        summary_path = d / "run_summary.json"
        summary = None
        if summary_path.exists():
            with open(summary_path) as f:
                summary = _json.load(f)
        fold_csvs = sorted(d.glob("fold*_metrics.csv"))
        results.append({
            "run_name": d.name,
            "has_summary": summary is not None,
            "cv_score": summary.get("cv_score") if summary else None,
            "run_mode": summary.get("run_mode") if summary else None,
            "fold_count": len(fold_csvs),
            "finished_at": summary.get("finished_at") if summary else None,
        })
    return results


def get_run_metrics(exp_name: str, run_name: str, fold_idx: int = 0) -> dict | None:
    """特定 run/fold の epoch メトリクスを返す。"""
    csv_path = (
        PROJECT_ROOT / "src" / exp_name / "logs" / run_name / f"fold{fold_idx}_metrics.csv"
    )
    if not csv_path.exists():
        return None

    import polars as pl

    df = pl.read_csv(csv_path)
    return {
        "columns": df.columns,
        "rows": df.to_dicts(),
        "fold_idx": fold_idx,
        "run_name": run_name,
    }


def get_run_summary(exp_name: str, run_name: str) -> dict | None:
    """run_summary.json を返す。"""
    import json as _json

    path = PROJECT_ROOT / "src" / exp_name / "logs" / run_name / "run_summary.json"
    if not path.exists():
        return None
    with open(path) as f:
        return _json.load(f)
