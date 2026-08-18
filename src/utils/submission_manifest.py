"""Submission manifest: recover the composition of a submission from ckpt names.

提出 notebook は submission.csv と同じ場所に submission_manifest.json を書く。
Kaggle の出力に残るので、後から Version を開けば「どの実験のどの fold を
どう混ぜたか」が確定できる（時系列やログからの事後推測が不要になる）。

前提はチェックポイント名が自己記述的であること:
    {exp番号}-{run_name}-f{fold}[-ep{NN}][-val_{metric}-{score}].ckpt
docs/training-conventions.md の「チェックポイント」節でこの命名を規約にしている。

⚠ メトリクス名とスコアの間の `-` は必須（区切りが無いと数字を含むメトリクス名
   例: f1 / top5 で境界が決まらない）。`=` は使わない — Kaggle がファイル名の `=`
   を除去することがあり、Dataset 経由の重み配布が壊れる。
"""

from __future__ import annotations

import json
import re
from collections.abc import Iterable, Mapping
from dataclasses import dataclass
from pathlib import Path
from typing import Any

# run 名は貪欲マッチにして、最後に現れる -f{数字} を fold として拾う
# （run 名に 'full' 等の f を含んでも壊れない）。
# メトリクス名とスコアは `-` で区切る（`val_f10.8523` のように区切りが無いと
# f1 のような数字入りメトリクス名でスコアの境界が決まらず、誤った値を静かに返す）。
_CKPT_RE = re.compile(
    r"^(?P<exp>exp\d+)-(?P<run>.+)-f(?P<fold>\d+)"
    r"(?:-ep(?P<epoch>\d+))?"
    r"(?:-val_(?P<metric>[A-Za-z0-9_]+)-(?P<score>[0-9]+\.[0-9]+))?"
    r"\.ckpt$"
)


@dataclass(frozen=True)
class CkptRef:
    """1 チェックポイントの出自。"""

    exp: str
    run: str
    fold: int
    epoch: int | None
    score: float | None
    filename: str


def parse_ckpt_name(name: str) -> CkptRef | None:
    """チェックポイント名を分解する。規約外の名前なら None。"""
    match = _CKPT_RE.match(Path(name).name)
    if match is None:
        return None
    epoch = match.group("epoch")
    score = match.group("score")
    return CkptRef(
        exp=match.group("exp"),
        run=match.group("run"),
        fold=int(match.group("fold")),
        epoch=int(epoch) if epoch is not None else None,
        score=float(score) if score is not None else None,
        filename=Path(name).name,
    )


def build_manifest(
    ckpt_files: Iterable[str | Path],
    *,
    notebook: str,
    notebook_version: int,
    blend: dict[str, Any] | None = None,
    tta: bool = False,
    dataset_slugs: Iterable[str] = (),
    code_sha: str | None = None,
    exp_names: Mapping[str, str] | None = None,
) -> dict[str, Any]:
    """ckpt 名の一覧から manifest を組み立てる。

    exp_names: exp 番号 → 実験ディレクトリ名の対応（例 {"exp006": "exp006_canonside"}）。
               与えなければ番号のまま記録する。
    """
    names = sorted(Path(f).name for f in ckpt_files)
    refs = [(name, parse_ckpt_name(name)) for name in names]

    grouped: dict[tuple[str, str], list[int]] = {}
    unparsed: list[str] = []
    for name, ref in refs:
        if ref is None:
            unparsed.append(name)
            continue
        grouped.setdefault((ref.exp, ref.run), []).append(ref.fold)

    components = [
        {
            "exp": (exp_names or {}).get(exp, exp),
            "run": run,
            "folds": sorted(set(folds)),
        }
        for (exp, run), folds in sorted(grouped.items())
    ]

    return {
        "notebook": notebook,
        "notebook_version": notebook_version,
        "components": components,
        "blend": blend or {"method": "mean"},
        "tta": tta,
        "ckpt_files": names,
        "unparsed": unparsed,
        "dataset_slugs": sorted(dataset_slugs),
        "code_sha": code_sha,
    }


def describe_manifest(manifest: Mapping[str, Any]) -> str:
    """提出時の description に貼れる 1 行を作る。

    `manifest` は `build_manifest` が返した形の mapping を渡すこと
    （`notebook_version` / `components` / `blend` / `tta` / `unparsed` キーを前提にする）。

    例: "V20 exp006-run004-effv2s(2f) + exp010-run000-base(1f) | mean w=0.5/0.5 | tta=off"
    """
    components = manifest["components"]
    if components:
        parts_text = " + ".join(
            f"{component['exp'].split('_')[0]}-{component['run']}({len(component['folds'])}f)"
            for component in components
        )
    else:
        unparsed_count = len(manifest.get("unparsed") or [])
        parts_text = f"(構成不明: unparsed {unparsed_count} 件)"
    blend = manifest.get("blend") or {}
    blend_text = str(blend.get("method", "mean"))
    weights = blend.get("weights")
    if weights and len(weights) > 1:
        blend_text += " w=" + "/".join(f"{w:g}" for w in weights)
    tta_text = "on" if manifest.get("tta") else "off"
    return (
        f"V{manifest['notebook_version']} {parts_text} | {blend_text} | tta={tta_text}"
    )


def write_manifest(manifest: Mapping[str, Any], path: str | Path) -> Path:
    """manifest を JSON として書き出す（submission.csv と同じディレクトリに置く）。"""
    out = Path(path)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(
        json.dumps(manifest, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )
    return out
