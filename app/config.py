"""App-level configuration."""

from pathlib import Path

import yaml

PROJECT_ROOT = Path(__file__).resolve().parent.parent


def _load_competition_slug() -> str:
    """docs/competition-profile.yaml から competition.slug を読む。

    ファイルが存在しない・壊れている・キーが空の場合は "" を返す。
    """
    profile_path = PROJECT_ROOT / "docs" / "competition-profile.yaml"
    try:
        data = yaml.safe_load(profile_path.read_text()) or {}
        slug = (data.get("competition") or {}).get("slug") or ""
        return slug if isinstance(slug, str) else ""
    except Exception:
        return ""


# /kaggle:init で docs/competition-profile.yaml の competition.slug を設定すること
COMPETITION_ID = _load_competition_slug()
