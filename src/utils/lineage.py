"""Run lineage utilities: declare and verify what changed from the parent run.

各 run は `lineage.parent`（親 run）と `lineage.varied`（親から変えたキー）を
config に宣言する。ここではその宣言を実際の config 差分と照合し、
「1 変数差分のつもりが実は 2 変数だった」事故を検出する。

背景: 複数変数を同時に変えた比較の Δ を 1 つの変数名で呼ぶと、次の実験の選択を誤る
（弱い側の延長に計算資源を投じ、強い側が未着手のまま残る）。
詳細は docs/experiment-methodology.md の「効果の帰属」。
"""

from __future__ import annotations

from collections.abc import Iterable, Mapping
from dataclasses import dataclass, field
from typing import Any

# run の同一性そのものを表すキーは差分から除く（必ず変わるため）
DEFAULT_IGNORE: frozenset[str] = frozenset(
    {"run_name", "lineage.parent", "lineage.varied"}
)


class _Missing:
    """欠落を表すセンチネル（None を値として持つキーと区別する）。"""

    def __repr__(self) -> str:  # pragma: no cover - デバッグ表示のみ
        return "<missing>"


_MISSING = _Missing()


def flatten_config(cfg: Mapping[str, Any], prefix: str = "") -> dict[str, Any]:
    """ネストした config をドット表記のフラットな dict にする。

    list はそれ自体を値として扱う（要素単位の差分は取らない）。
    """
    flat: dict[str, Any] = {}
    for key, value in cfg.items():
        full_key = f"{prefix}{key}"
        if isinstance(value, Mapping):
            flat.update(flatten_config(value, prefix=f"{full_key}."))
        else:
            flat[full_key] = value
    return flat


def diff_config_keys(
    child: Mapping[str, Any],
    parent: Mapping[str, Any],
    *,
    ignore: Iterable[str] = DEFAULT_IGNORE,
) -> list[str]:
    """親と子で値が異なるキー（追加・削除も含む）をソートして返す。"""
    ignored = set(ignore)
    flat_child = flatten_config(child)
    flat_parent = flatten_config(parent)

    keys = (set(flat_child) | set(flat_parent)) - ignored
    changed = [
        key
        for key in keys
        if flat_child.get(key, _MISSING) != flat_parent.get(key, _MISSING)
    ]
    return sorted(changed)


@dataclass
class LineageCheck:
    """`lineage.varied` の宣言と実際の差分の照合結果。"""

    actual: list[str] = field(default_factory=list)
    declared: list[str] = field(default_factory=list)
    missing: list[str] = field(default_factory=list)  # 実際に変わったが未宣言
    extra: list[str] = field(default_factory=list)  # 宣言されたが変わっていない

    @property
    def ok(self) -> bool:
        return not self.missing and not self.extra

    @property
    def n_varied(self) -> int:
        """実際に変わった変数の数。2 以上なら Δ を 1 変数の名前で呼べない。"""
        return len(self.actual)


def check_varied(
    child: Mapping[str, Any],
    parent: Mapping[str, Any],
    declared: Iterable[str],
    *,
    ignore: Iterable[str] = DEFAULT_IGNORE,
) -> LineageCheck:
    """宣言された varied と実際の config 差分を照合する。"""
    actual = diff_config_keys(child, parent, ignore=ignore)
    declared_list = sorted(set(declared))
    return LineageCheck(
        actual=actual,
        declared=declared_list,
        missing=sorted(set(actual) - set(declared_list)),
        extra=sorted(set(declared_list) - set(actual)),
    )
