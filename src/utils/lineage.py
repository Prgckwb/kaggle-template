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

# run の同一性そのものを表すキー（必ず変わる）と、Hydra の継承宣言は差分から除く。
# `defaults` は list 値のフラットキーになるため、除かないと差分に混入する。
DEFAULT_IGNORE: frozenset[str] = frozenset(
    {"run_name", "lineage.parent", "lineage.varied", "defaults"}
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
    """子が親から変えたキーをソートして返す。

    走査対象は**子に存在するキーだけ**である。親にしか無いキーは
    「継承（inherited）」とみなし、差分に数えない。

    理由: Hydra の `defaults:` は `yaml.safe_load` では compose されないため、
    差分 config（`defaults: [config]` + 変えたキーだけ）を素で読むと、
    子が触っていない継承キーは必ず「親にしか無いキー」として現れる。
    さらに Hydra の子 config には「キーの削除」を表現する手段が無いので、
    親にしか無いキーを「削除された差分」と読むこと自体が誤りになる。

    - 子と親の両方にあり値が異なるキー → 差分
    - 子にあって親に無いキー → 「追加」として差分
    - 親にしか無いキー → 継承。差分に数えない

    差分 config（Hydra の子 config）をそのまま渡してよい。
    """
    ignored = set(ignore)
    flat_child = flatten_config(child)
    flat_parent = flatten_config(parent)

    keys = set(flat_child) - ignored
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
