"""Experiments page router."""

from __future__ import annotations

from fastapi import APIRouter, Request
from fastapi.responses import FileResponse, HTMLResponse

from app.services.experiments import (
    get_all_experiment_scores,
    get_experiment_detail,
    get_experiment_file_content,
    get_oof_analysis,
    get_run_config,
    get_run_metrics,
    get_run_summary,
    list_experiments,
    list_run_logs,
    list_runs,
    parse_mermaid_tree,
)
from app.services.helpers import PROJECT_ROOT, is_htmx, safe_relative_path
from app.template_env import templates

router = APIRouter()


@router.get("/experiments", response_class=HTMLResponse)
def experiment_list(request: Request, q: str = "", source: str = ""):
    # Index page search: return empty HTML when query is cleared
    if is_htmx(request) and not q and source == "index":
        return HTMLResponse("")

    exps = list_experiments(query=q)
    mermaid_source = parse_mermaid_tree()
    ctx = {
        "experiments": exps,
        "query": q,
        "active_page": "experiments",
        "mermaid_source": mermaid_source,
    }
    if is_htmx(request):
        return templates.TemplateResponse(request, "partials/_experiment_list.html", ctx)
    return templates.TemplateResponse(request, "experiments/list.html", ctx)



@router.get("/experiments/_scores", response_class=HTMLResponse)
def experiment_scores(request: Request):
    scores = get_all_experiment_scores()
    return templates.TemplateResponse(
        request,
        "partials/_experiment_scores.html",
        {"scores": scores},
    )


@router.get("/experiments/{name}", response_class=HTMLResponse)
def experiment_detail(request: Request, name: str):
    src_dir = PROJECT_ROOT / "src"
    validated = safe_relative_path(name, src_dir)
    if validated is None or not validated.is_dir():
        return HTMLResponse("<p>Experiment not found</p>", status_code=404)

    detail = get_experiment_detail(name)
    if detail is None:
        return HTMLResponse("<p>Experiment not found</p>", status_code=404)
    return templates.TemplateResponse(
        request,
        "experiments/detail.html",
        {"exp": detail, "active_page": "experiments"},
    )


@router.get("/experiments/{name}/_readme", response_class=HTMLResponse)
def experiment_readme(request: Request, name: str):
    detail = get_experiment_detail(name)
    if detail is None:
        return HTMLResponse("<p>Not found</p>", status_code=404)
    return templates.TemplateResponse(
        request,
        "partials/_experiment_readme.html",
        {"exp": detail},
    )


@router.get("/experiments/{name}/_config", response_class=HTMLResponse)
def experiment_config(request: Request, name: str):
    detail = get_experiment_detail(name)
    if detail is None:
        return HTMLResponse("<p>Not found</p>", status_code=404)
    return templates.TemplateResponse(
        request,
        "partials/_experiment_config.html",
        {"exp": detail},
    )


@router.get("/experiments/{name}/_files", response_class=HTMLResponse)
def experiment_files(request: Request, name: str):
    detail = get_experiment_detail(name)
    if detail is None:
        return HTMLResponse("<p>Not found</p>", status_code=404)
    return templates.TemplateResponse(
        request,
        "partials/_experiment_files.html",
        {"exp": detail},
    )


@router.get("/experiments/{name}/_runs", response_class=HTMLResponse)
def experiment_runs(request: Request, name: str):
    runs = list_runs(name)
    return templates.TemplateResponse(
        request,
        "partials/_experiment_runs.html",
        {"runs": runs, "exp_name": name},
    )


@router.get("/experiments/{name}/_oof", response_class=HTMLResponse)
def experiment_oof(request: Request, name: str, run: str = ""):
    analysis = get_oof_analysis(name, run_name=run or None)
    runs = list_runs(name)
    oof_runs = [r for r in runs if r["has_oof"]]
    return templates.TemplateResponse(
        request,
        "partials/_experiment_oof.html",
        {"oof": analysis, "exp_name": name, "oof_runs": oof_runs, "selected_run": run},
    )


@router.get("/experiments/{name}/_logs", response_class=HTMLResponse)
def experiment_logs(request: Request, name: str):
    logs = list_run_logs(name)
    return templates.TemplateResponse(
        request,
        "partials/_experiment_logs.html",
        {"logs": logs, "exp_name": name},
    )


@router.get("/experiments/{name}/_logs/{run_name}", response_class=HTMLResponse)
def experiment_log_detail(request: Request, name: str, run_name: str, fold: int = 0):
    metrics = get_run_metrics(name, run_name, fold_idx=fold)
    summary = get_run_summary(name, run_name)
    logs_dir = PROJECT_ROOT / "src" / name / "logs" / run_name
    available_folds = sorted(
        int(f.stem.replace("fold", "").replace("_metrics", ""))
        for f in logs_dir.glob("fold*_metrics.csv")
    ) if logs_dir.exists() else []
    return templates.TemplateResponse(
        request,
        "partials/_experiment_log_detail.html",
        {
            "metrics": metrics,
            "summary": summary,
            "exp_name": name,
            "run_name": run_name,
            "fold": fold,
            "available_folds": available_folds,
        },
    )


@router.get("/experiments/{name}/_file_content/{file_path:path}", response_class=HTMLResponse)
def experiment_file_content(request: Request, name: str, file_path: str):
    content = get_experiment_file_content(name, file_path)
    if content is None:
        return HTMLResponse("<p>File not found</p>", status_code=404)
    return templates.TemplateResponse(
        request,
        "partials/_experiment_file_preview.html",
        {"file": content, "exp_name": name},
    )


@router.get("/experiments/{name}/_file_raw/{file_path:path}")
def experiment_file_raw(request: Request, name: str, file_path: str):
    exp_dir = PROJECT_ROOT / "src" / name
    full_path = safe_relative_path(file_path, exp_dir)
    if full_path is None or not full_path.exists() or not full_path.is_file():
        return HTMLResponse("<p>File not found</p>", status_code=404)
    return FileResponse(full_path)


@router.get("/experiments/{name}/_run_config/{run_name}", response_class=HTMLResponse)
def experiment_run_config(request: Request, name: str, run_name: str):
    config = get_run_config(name, run_name)
    if config is None:
        return HTMLResponse("<p>Config not found</p>", status_code=404)
    return templates.TemplateResponse(
        request,
        "partials/_run_config_detail.html",
        {"config": config, "run_name": run_name, "exp_name": name},
    )
