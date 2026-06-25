"""Kaggle Competition Dashboard - FastAPI application."""

import logging
import traceback
from pathlib import Path

from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from starlette.exceptions import HTTPException as StarletteHTTPException

from app.pages import data, experiments, knowledge
from app.services.data import list_input_files
from app.services.documents import get_competition_overview, list_docs
from app.services.experiments import get_all_experiment_scores, list_experiments
from app.services.helpers import PROJECT_ROOT, error_response
from app.services.leaderboard import get_leaderboard_summary, is_default_competition
from app.services.search import global_search
from app.template_env import templates

logger = logging.getLogger(__name__)

app = FastAPI(title="Kaggle Competition Dashboard", docs_url="/api-docs")

# Static files
app.mount(
    "/static", StaticFiles(directory=Path(__file__).parent / "static"), name="static"
)

# Register routers
app.include_router(experiments.router)
app.include_router(knowledge.router)
app.include_router(data.router)


@app.exception_handler(StarletteHTTPException)
async def http_exception_handler(request: Request, exc: StarletteHTTPException):
    """HTTP エラー（404 等）をスタイル付きページで返す。"""
    return error_response(request, templates, exc.status_code, str(exc.detail))


@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    """500 エラー時にユーザーフレンドリーなエラーページを返す。"""
    logger.error("Unhandled exception: %s\n%s", exc, traceback.format_exc())
    return error_response(request, templates, 500, "内部エラーが発生しました")


@app.get("/search", response_class=HTMLResponse)
def search(request: Request, q: str = ""):
    if not q.strip():
        return HTMLResponse("")
    results = global_search(q)
    total = sum(len(v) for v in results.values())
    return templates.TemplateResponse(
        request,
        "partials/_search_results.html",
        {"results": results, "query": q, "total": total},
    )


@app.post("/leaderboard/refresh", response_class=HTMLResponse)
def leaderboard_refresh(request: Request):
    leaderboard = get_leaderboard_summary(force_refresh=True)
    return templates.TemplateResponse(
        request,
        "partials/_leaderboard_card.html",
        {"leaderboard": leaderboard, "lb_is_default": is_default_competition()},
    )


# ---------------------------------------------------------------------------
# Metric direction heuristic
# ---------------------------------------------------------------------------

_LOWER_IS_BETTER_KEYWORDS = ("loss", "rmse", "mae", "mse", "error")


def _get_best_score_fn():
    """Return min or max depending on metric direction.

    1. Check experiment configs for a ``greater_is_better`` field.
    2. Otherwise infer from the metric name: if it contains loss/rmse/mae/mse/error
       use ``min``; else ``max``.
    """
    src = PROJECT_ROOT / "src"
    if src.exists():
        for d in sorted(src.iterdir()):
            if not (d.is_dir() and d.name.startswith("exp")):
                continue
            cfg_path = d / "config" / "config.yaml"
            if not cfg_path.exists():
                continue
            try:
                import yaml

                cfg = yaml.safe_load(cfg_path.read_text()) or {}
            except Exception:
                continue
            # Explicit flag takes priority
            gib = cfg.get("greater_is_better")
            if gib is not None:
                return max if gib else min
            # Infer from metric name in ModelCheckpoint monitor or similar
            monitor = cfg.get("training", {}).get("monitor", "")
            if not monitor:
                monitor = cfg.get("monitor", "")
            if monitor:
                if any(kw in monitor.lower() for kw in _LOWER_IS_BETTER_KEYWORDS):
                    return min
                return max
    # Default: higher is better
    return max


@app.get("/", response_class=HTMLResponse)
def index(request: Request):
    all_docs = list_docs()
    input_files = list_input_files()
    scores = get_all_experiment_scores()
    competition = get_competition_overview()

    best_fn = _get_best_score_fn()
    best_lb = best_fn((s["lb"] for s in scores if s["lb"] is not None), default=None)
    best_cv = best_fn((s["cv"] for s in scores if s["cv"] is not None), default=None)

    recent_docs = sorted(
        [doc for docs_list in all_docs.values() for doc in docs_list],
        key=lambda d: d["modified"],
        reverse=True,
    )[:5]

    leaderboard = get_leaderboard_summary()

    return templates.TemplateResponse(
        request,
        "index.html",
        {
            "title": "Dashboard",
            "active_page": "home",
            "experiments": list_experiments(),
            "all_docs": all_docs,
            "input_files": input_files,
            "best_lb": best_lb,
            "best_cv": best_cv,
            "competition": competition,
            "recent_docs": recent_docs,
            "leaderboard": leaderboard,
            "lb_is_default": is_default_competition(),
        },
    )
