"""Leaderboard data fetching, caching, and aggregation."""

from __future__ import annotations

import csv
import logging
import math
import subprocess
import time
import zipfile
from datetime import datetime, timezone
from pathlib import Path

from app.config import COMPETITION_ID
from app.services.helpers import PROJECT_ROOT

logger = logging.getLogger(__name__)

CACHE_DIR = PROJECT_ROOT / ".cache" / "leaderboard"
TTL_SECONDS = 3600  # 1 hour

# In-memory cache
_cache: dict[str, object] = {"data": None, "fetched_at": 0.0}


def _find_csv() -> Path | None:
    """Find the leaderboard CSV in the cache directory."""
    if not CACHE_DIR.exists():
        return None
    csvs = sorted(CACHE_DIR.glob("*.csv"))
    return csvs[-1] if csvs else None


def _download_leaderboard() -> Path | None:
    """Download leaderboard via kaggle CLI and return the CSV path."""
    if not COMPETITION_ID:
        return None

    CACHE_DIR.mkdir(parents=True, exist_ok=True)

    # Remove old files
    for f in CACHE_DIR.iterdir():
        f.unlink()

    try:
        subprocess.run(
            [
                "kaggle", "competitions", "leaderboard",
                COMPETITION_ID, "-d", "-p", str(CACHE_DIR),
            ],
            capture_output=True,
            text=True,
            timeout=60,
            check=True,
        )
    except (subprocess.CalledProcessError, FileNotFoundError, subprocess.TimeoutExpired) as e:
        logger.warning("Failed to download leaderboard: %s", e)
        return None

    # Unzip
    zips = list(CACHE_DIR.glob("*.zip"))
    if not zips:
        return _find_csv()

    with zipfile.ZipFile(zips[0]) as zf:
        zf.extractall(CACHE_DIR)
    zips[0].unlink()

    return _find_csv()


def _parse_csv(csv_path: Path) -> list[dict]:
    """Parse leaderboard CSV into list of dicts."""
    with csv_path.open(encoding="utf-8-sig") as f:
        reader = csv.DictReader(f)
        rows = []
        for row in reader:
            try:
                rows.append({
                    "rank": int(row["Rank"]),
                    "team_name": row["TeamName"],
                    "score": float(row["Score"]),
                    "submissions": int(row["SubmissionCount"]),
                })
            except (ValueError, KeyError):
                continue
    return rows


def _compute_medal_boundaries(total: int) -> dict[str, int]:
    """Compute medal boundary ranks based on Kaggle rules (approximate)."""
    if total < 100:
        return {"gold": 0, "silver": 0, "bronze": 0}

    gold = max(10, math.ceil(total * 0.002))
    silver = math.ceil(total * 0.05)
    bronze = math.ceil(total * 0.10)
    return {"gold": gold, "silver": silver, "bronze": bronze}


def _build_summary(rows: list[dict], updated_at: datetime) -> dict:
    """Build leaderboard summary from parsed rows."""
    total = len(rows)
    boundaries = _compute_medal_boundaries(total)

    medals = {}
    for medal, rank in boundaries.items():
        if rank > 0 and rank <= total:
            entry = rows[rank - 1]
            medals[medal] = {"rank": rank, "score": entry["score"]}
        else:
            medals[medal] = None

    return {
        "top_score": rows[0]["score"] if rows else None,
        "total_teams": total,
        "medals": medals,
        "top_entries": rows[:5],
        "updated_at": updated_at,
    }


def is_default_competition() -> bool:
    """Check if COMPETITION_ID is still the template default."""
    return COMPETITION_ID == "titanic"


def get_leaderboard_summary(force_refresh: bool = False) -> dict | None:
    """Return cached leaderboard summary, refreshing if TTL expired.

    Returns None if no data is available.
    """
    now = time.time()

    # Check in-memory cache
    if not force_refresh and _cache["data"] is not None:
        if now - _cache["fetched_at"] < TTL_SECONDS:
            return _cache["data"]

    # Try existing CSV first (may be from previous session)
    csv_path = _find_csv()
    need_download = force_refresh or csv_path is None

    if not need_download and csv_path is not None:
        file_age = now - csv_path.stat().st_mtime
        if file_age > TTL_SECONDS:
            need_download = True

    if need_download:
        csv_path = _download_leaderboard()

    if csv_path is None:
        return None

    rows = _parse_csv(csv_path)
    if not rows:
        return None

    mtime = csv_path.stat().st_mtime
    updated_at = datetime.fromtimestamp(mtime, tz=timezone.utc)
    summary = _build_summary(rows, updated_at)

    _cache["data"] = summary
    _cache["fetched_at"] = now

    return summary
