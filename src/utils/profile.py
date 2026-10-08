"""docs/competition-profile.yaml（コンペ固有値の SSOT）の読み出し。

実験 config は値を転記せず `${profile:metric.name}` のように resolver で参照する。
"""

from __future__ import annotations

from functools import cache
from pathlib import Path
from typing import Any

from omegaconf import OmegaConf

PROJECT_ROOT = Path(__file__).resolve().parents[2]
PROFILE_PATH = PROJECT_ROOT / "docs" / "competition-profile.yaml"


@cache
def load_profile() -> dict[str, Any]:
    if not PROFILE_PATH.exists():
        raise FileNotFoundError(f"competition profile が見つかりません: {PROFILE_PATH}")
    return OmegaConf.to_container(OmegaConf.load(PROFILE_PATH), resolve=True)  # type: ignore[return-value]


def profile_value(key: str) -> Any:
    """ドット区切りのキーで profile の値を返す（例: "metric.mode"）。"""
    node: Any = load_profile()
    for part in key.split("."):
        if not isinstance(node, dict) or part not in node:
            raise KeyError(f"competition profile に {key} がありません")
        node = node[part]
    return node


def register_profile_resolver() -> None:
    """`${profile:<key>}` を OmegaConf に登録する（Hydra の main より前に呼ぶ）。"""
    if not OmegaConf.has_resolver("profile"):
        OmegaConf.register_new_resolver("profile", profile_value)
