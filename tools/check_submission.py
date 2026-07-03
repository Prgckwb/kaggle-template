"""最新の Kaggle 提出のステータスを監視し、完了したら LB スコアを表示する。

読み取り専用（提出は行わない）。提出直後に実行してスコア確定を待つ用途。

Usage:
    uv run python tools/check_submission.py                # profile の slug を使用
    uv run python tools/check_submission.py -c titanic     # コンペを明示指定
    uv run python tools/check_submission.py -i 30          # ポーリング間隔 30 秒
"""

from __future__ import annotations

import argparse
import sys
import time
from pathlib import Path

import yaml

PROFILE_PATH = (
    Path(__file__).resolve().parent.parent / "docs" / "competition-profile.yaml"
)


def default_competition() -> str | None:
    """docs/competition-profile.yaml から competition.slug を読む。"""
    if not PROFILE_PATH.exists():
        return None
    with open(PROFILE_PATH) as f:
        profile = yaml.safe_load(f) or {}
    slug = (profile.get("competition") or {}).get("slug") or ""
    return slug or None


def latest_submission(api, competition: str):
    submissions = api.competition_submissions(competition)
    if not submissions:
        return None
    return submissions[0]


def is_finished(status: object) -> bool:
    # kaggle パッケージのバージョンにより status は str / enum のことがある
    text = str(status).lower()
    return any(word in text for word in ("complete", "error"))


def main() -> int:
    parser = argparse.ArgumentParser(
        description="最新の Kaggle 提出のステータスを監視し、完了したら LB スコアを表示する"
    )
    parser.add_argument(
        "-c",
        "--competition",
        default=None,
        help="コンペの slug（省略時は docs/competition-profile.yaml の competition.slug）",
    )
    parser.add_argument(
        "-i", "--interval", type=int, default=60, help="ポーリング間隔（秒）"
    )
    args = parser.parse_args()

    competition = args.competition or default_competition()
    if not competition:
        print(
            "コンペの slug が未指定です。-c で指定するか、"
            "docs/competition-profile.yaml の competition.slug を設定してください。",
            file=sys.stderr,
        )
        return 1

    from kaggle.api.kaggle_api_extended import KaggleApi

    api = KaggleApi()
    api.authenticate()

    latest = latest_submission(api, competition)
    if latest is None:
        print(f"{competition} に提出が見つかりませんでした。", file=sys.stderr)
        return 1

    latest_ref = str(latest.ref)
    print(f"最新の提出を監視します: ref={latest_ref}")
    if getattr(latest, "url", None):
        print(f"URL: {latest.url}")

    started = time.time()
    while True:
        submissions = api.competition_submissions(competition)
        current = next(
            (s for s in submissions if str(s.ref) == latest_ref), submissions[0]
        )
        elapsed_min = int((time.time() - started) / 60)

        if is_finished(current.status):
            public_score = getattr(current, "public_score", None) or getattr(
                current, "publicScore", None
            )
            print(f"\rstatus: {current.status}, public LB: {public_score}" + " " * 20)
            return 0

        print(f"\rstatus: {current.status} (elapsed: {elapsed_min} min)", end="")
        time.sleep(args.interval)


if __name__ == "__main__":
    sys.exit(main())
