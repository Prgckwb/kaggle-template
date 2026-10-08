"""run の best ckpt（fold ごと）を軽量化して Kaggle Dataset にアップロードする。

`/kaggle:upload-checkpoints` スキルの実体。Claude Code なしでも直接使える。
各 fold の best ckpt（ファイル名のスコアで選ぶ）を optimizer 等を落とした slim ckpt にして
`src/{exp}/output/{run}/kaggle_dataset/fold{k}/` に置き、そのディレクトリをアップロードする。
`kaggle_dataset/dataset-metadata.json` があればバージョン更新、無ければ新規作成（非公開）。

Usage:
    uv run python -m tools.upload_checkpoints exp001_baseline run000-base --user your-name  # 初回
    uv run python -m tools.upload_checkpoints exp001_baseline run000-base -m "全 fold 追加"
"""

from __future__ import annotations

import argparse
import json
import re
import shutil
import sys
from pathlib import Path

from src.utils.checkpoint import export_slim_checkpoint, select_best_ckpt
from src.utils.profile import PROJECT_ROOT, profile_value


def to_kebab(name: str) -> str:
    """Kaggle の dataset slug に使えるのは英数字とハイフンのみ。"""
    return re.sub(r"[^a-z0-9-]+", "-", name.lower()).strip("-")


def stage(run_dir: Path, staging: Path, mode: str) -> list[Path]:
    """各 fold の best ckpt を slim 化して staging に置く（古いステージは作り直す）。"""
    for old in staging.glob("fold*"):
        shutil.rmtree(old)
    staged = []
    for fold_dir in sorted(run_dir.glob("fold*")):
        best = select_best_ckpt(fold_dir, mode)
        staged.append(export_slim_checkpoint(best, staging / fold_dir.name / best.name))
    return staged


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("exp_name", help="実験名（例: exp001_baseline）")
    parser.add_argument("run_name", help="run 名（例: run000-base）")
    parser.add_argument("--user", help="Kaggle ユーザー名（新規作成時に必須）")
    parser.add_argument(
        "-m", "--message", default="update checkpoints", help="バージョン更新メッセージ"
    )
    args = parser.parse_args()

    run_dir = PROJECT_ROOT / "src" / args.exp_name / "output" / args.run_name
    if not run_dir.is_dir():
        print(f"output ディレクトリが見つかりません: {run_dir}", file=sys.stderr)
        return 1
    staging = run_dir / "kaggle_dataset"
    metadata_path = staging / "dataset-metadata.json"
    is_new = not metadata_path.exists()

    if is_new:
        if not args.user:
            print("新規作成には --user（Kaggle ユーザー名）が必要です", file=sys.stderr)
            return 1
        slug = profile_value("competition.slug")
        staging.mkdir(parents=True, exist_ok=True)
        metadata = {
            "title": f"{slug} {args.exp_name} {args.run_name}".strip(),
            "id": f"{args.user}/{to_kebab(f'{slug}-{args.exp_name}-{args.run_name}')}",
            "licenses": [{"name": "CC0-1.0"}],
        }
        metadata_path.write_text(json.dumps(metadata, indent=2) + "\n")
    metadata = json.loads(metadata_path.read_text())

    staged = stage(run_dir, staging, profile_value("metric.mode"))
    if not staged:
        print(f"fold*/ に ckpt がありません: {run_dir}", file=sys.stderr)
        return 1
    for path in staged:
        print(
            f"  - {path.relative_to(staging)} ({path.stat().st_size / 2**20:.1f} MiB)"
        )

    from kaggle.api.kaggle_api_extended import KaggleApi

    api = KaggleApi()
    api.authenticate()
    if is_new:
        api.dataset_create_new(folder=str(staging), dir_mode="zip", public=False)
        print(f"Dataset を新規作成しました: {metadata['id']}")
    else:
        api.dataset_create_version(
            folder=str(staging), version_notes=args.message, dir_mode="zip"
        )
        print(f"Dataset を更新しました: {metadata['id']} ({args.message})")
    print(
        "Notebook でのマウントパスは docs/training-conventions.md の「実行環境」を参照"
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
