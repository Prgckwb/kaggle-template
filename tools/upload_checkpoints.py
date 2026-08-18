"""実験の output ディレクトリを Kaggle Dataset としてアップロードする。

`/kaggle:upload-checkpoints` スキルの実体。Claude Code なしでも直接使える。
output ディレクトリの構造（fold0/, fold1/, ...）がそのまま Kaggle 上に反映される。

Usage:
    # 初回（Dataset 新規作成。--user が必須）
    uv run python tools/upload_checkpoints.py exp001_baseline run000-base --user your-name --new

    # 2回目以降（バージョン更新。dataset-metadata.json を再利用）
    uv run python tools/upload_checkpoints.py exp001_baseline run000-base -m "全 fold 追加"
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path

import yaml

PROJECT_ROOT = Path(__file__).resolve().parent.parent
PROFILE_PATH = PROJECT_ROOT / "docs" / "competition-profile.yaml"


def competition_slug() -> str:
    if not PROFILE_PATH.exists():
        return ""
    with open(PROFILE_PATH) as f:
        profile = yaml.safe_load(f) or {}
    return (profile.get("competition") or {}).get("slug") or ""


def to_kebab(name: str) -> str:
    """Kaggle の dataset slug に使えるのは英数字とハイフンのみ。"""
    return re.sub(r"[^a-z0-9-]+", "-", name.lower()).strip("-")


def ensure_metadata(target_dir: Path, exp_name: str, user: str | None) -> dict:
    """dataset-metadata.json を返す（無ければ作成する）。"""
    metadata_path = target_dir / "dataset-metadata.json"
    if metadata_path.exists():
        with open(metadata_path) as f:
            return json.load(f)

    if not user:
        print(
            "dataset-metadata.json がありません。初回は --user で "
            "Kaggle ユーザー名を指定してください。",
            file=sys.stderr,
        )
        sys.exit(1)

    slug = competition_slug()
    dataset_slug = to_kebab(f"{slug}-{exp_name}" if slug else exp_name)
    metadata = {
        "title": f"{slug} {exp_name}".strip(),
        "id": f"{user}/{dataset_slug}",
        "licenses": [{"name": "CC0-1.0"}],
    }
    with open(metadata_path, "w") as f:
        json.dump(metadata, f, indent=2)
    print(f"dataset-metadata.json を作成しました: {metadata['id']}")
    print(
        "注意: このファイルは gitignore された output/ 配下にあるため、"
        "slug を実験 README.md にも記録してください。"
    )
    return metadata


def main() -> int:
    parser = argparse.ArgumentParser(
        description="実験の output ディレクトリを Kaggle Dataset としてアップロードする"
    )
    parser.add_argument("exp_name", help="実験名（例: exp001_baseline）")
    parser.add_argument("run_name", help="run 名（例: run000-base）")
    parser.add_argument(
        "--user", default=None, help="Kaggle ユーザー名（初回作成時に必須）"
    )
    parser.add_argument(
        "-m", "--message", default="update checkpoints", help="バージョン更新メッセージ"
    )
    parser.add_argument(
        "--new", action="store_true", help="新規 Dataset として作成する（初回のみ）"
    )
    args = parser.parse_args()

    target_dir = PROJECT_ROOT / "src" / args.exp_name / "output" / args.run_name
    if not target_dir.is_dir():
        print(f"output ディレクトリが見つかりません: {target_dir}", file=sys.stderr)
        return 1

    checkpoints = sorted(target_dir.rglob("*.ckpt")) + sorted(target_dir.rglob("*.pt"))
    if not checkpoints:
        print(f"警告: {target_dir} にチェックポイントが見つかりません", file=sys.stderr)

    metadata = ensure_metadata(target_dir, args.exp_name, args.user)
    print(f"アップロード対象: {target_dir}")
    for ckpt in checkpoints:
        size_mb = ckpt.stat().st_size / 2**20
        print(f"  - {ckpt.relative_to(target_dir)} ({size_mb:.1f} MB)")

    from kaggle.api.kaggle_api_extended import KaggleApi

    api = KaggleApi()
    api.authenticate()

    if args.new:
        # デフォルトで非公開 Dataset として作成される
        api.dataset_create_new(folder=str(target_dir), dir_mode="zip", public=False)
        print(f"Dataset を新規作成しました: {metadata['id']}")
    else:
        api.dataset_create_version(
            folder=str(target_dir), version_notes=args.message, dir_mode="zip"
        )
        print(f"Dataset を更新しました: {metadata['id']} ({args.message})")

    owner, dataset_slug = metadata["id"].split("/", 1)
    print(
        "Notebook のマウントパス（通常）: "
        f"/kaggle/input/datasets/{owner}/{dataset_slug}/"
    )
    print("※ Add Data 後に Notebook のサイドバーで実際のパスを必ず確認すること")
    return 0


if __name__ == "__main__":
    sys.exit(main())
