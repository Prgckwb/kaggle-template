"""run の系譜（親と、親から変えたキー）を config ファイルから自動計算する。

小実験 yaml は `defaults: [<親>]` + 変えたキーだけを書く「差分」なので、
親も変えたキーもそこから一意に決まる。手で宣言させると宣言と実体がずれるため宣言はさせない。

背景: 複数変数を同時に変えた比較の Δ を 1 つの変数名で呼ぶと、次の実験の選択を誤る。
`changed` が 2 つ以上の run の Δ は単一変数に帰属できない（docs/experiment-methodology.md「効果の帰属」）。
"""

from __future__ import annotations

from collections.abc import Mapping
from pathlib import Path
from typing import Any

from omegaconf import OmegaConf

# run の同一性・実行方法を表すキーは「変えた変数」に数えない
IGNORED_KEYS = frozenset({"run_name", "run_mode", "defaults", "hydra"})
IGNORED_PREFIXES = ("hydra.", "wandb.")


def _flatten(cfg: Mapping[str, Any], prefix: str = "") -> dict[str, Any]:
    flat: dict[str, Any] = {}
    for key, value in cfg.items():
        full_key = f"{prefix}{key}"
        if isinstance(value, Mapping):
            flat.update(_flatten(value, prefix=f"{full_key}."))
        else:
            flat[full_key] = value
    return flat


def _is_ignored(key: str) -> bool:
    return key in IGNORED_KEYS or key.startswith(IGNORED_PREFIXES)


def _load_raw(config_dir: Path, name: str) -> dict[str, Any]:
    return OmegaConf.to_container(OmegaConf.load(config_dir / f"{name}.yaml"))  # type: ignore[return-value]


def _parent_name(config_dir: Path, raw: Mapping[str, Any]) -> str | None:
    for entry in raw.get("defaults") or []:
        if isinstance(entry, str) and (config_dir / f"{entry}.yaml").exists():
            return entry
    return None


def _compose(config_dir: Path, name: str) -> dict[str, Any]:
    """defaults の親チェーンを辿って yaml をマージする（Hydra の compose の簡易版）。"""
    raw = _load_raw(config_dir, name)
    parent = _parent_name(config_dir, raw)
    body = {k: v for k, v in raw.items() if k != "defaults"}
    if parent is None:
        return body
    merged = OmegaConf.merge(_compose(config_dir, parent), body)
    return OmegaConf.to_container(merged)  # type: ignore[return-value]


def run_lineage(
    config_dir: str | Path, config_name: str, overrides: list[str]
) -> dict[str, Any]:
    """`{"parent": 親 config 名 | None, "changed": [変えたキー]}` を返す。

    - yaml に書かれたキーのうち、親（を compose した値）と異なるもの
    - CLI override で指定されたキー（`run_mode` 等の実行方法は除く）
    親に存在しないキーを小実験で足すのはタイポとみなしてエラーにする。
    """
    config_dir = Path(config_dir)
    raw = _load_raw(config_dir, config_name)
    parent = _parent_name(config_dir, raw)

    changed: set[str] = set()
    if parent is not None:
        parent_flat = _flatten(_compose(config_dir, parent))
        child_flat = _flatten({k: v for k, v in raw.items() if k != "defaults"})
        for key, value in child_flat.items():
            if _is_ignored(key):
                continue
            if key not in parent_flat:
                raise KeyError(
                    f"{config_name}.yaml の `{key}` は親 {parent}.yaml に存在しません（タイポ？）。"
                    "新しいキーは先にベース config に追加してください"
                )
            if parent_flat[key] != value:
                changed.add(key)

    for override in overrides:
        key = override.split("=", 1)[0].lstrip("+~")
        if not _is_ignored(key):
            changed.add(key)

    return {"parent": parent, "changed": sorted(changed)}
