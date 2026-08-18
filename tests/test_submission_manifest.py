"""Tests for src/utils/submission_manifest.py."""

import json
from pathlib import Path

from src.utils.submission_manifest import (
    build_manifest,
    describe_manifest,
    parse_ckpt_name,
    write_manifest,
)


def test_parse_full_ckpt_name() -> None:
    ref = parse_ckpt_name("exp006-run004-effv2s-f0-ep05-val_auc0.9104.ckpt")

    assert ref is not None
    assert ref.exp == "exp006"
    assert ref.run == "run004-effv2s"
    assert ref.fold == 0
    assert ref.epoch == 5
    assert ref.score == 0.9104


def test_parse_ckpt_without_epoch_and_score() -> None:
    ref = parse_ckpt_name("exp001-run000-base-f3.ckpt")

    assert ref is not None
    assert ref.run == "run000-base"
    assert ref.fold == 3
    assert ref.epoch is None
    assert ref.score is None


def test_parse_run_name_containing_f_letter() -> None:
    """run 名に 'f' を含んでも fold 抽出が壊れないこと。"""
    ref = parse_ckpt_name("exp009-run003-cnxb384full-f2-ep08-val_auc0.9436.ckpt")

    assert ref is not None
    assert ref.run == "run003-cnxb384full"
    assert ref.fold == 2


def test_parse_returns_none_for_unrecognized_name() -> None:
    assert parse_ckpt_name("last.ckpt") is None
    assert parse_ckpt_name("model_best.pth") is None


def test_build_manifest_groups_by_exp_and_run() -> None:
    files = [
        "exp006-run004-effv2s-f0-ep05-val_auc0.9104.ckpt",
        "exp006-run004-effv2s-f1-ep06-val_auc0.9002.ckpt",
        "exp010-run000-base-f0-ep11-val_auc0.9411.ckpt",
    ]

    manifest = build_manifest(files, notebook="comp-submit", notebook_version=20)

    assert manifest["components"] == [
        {"exp": "exp006", "run": "run004-effv2s", "folds": [0, 1]},
        {"exp": "exp010", "run": "run000-base", "folds": [0]},
    ]
    assert manifest["notebook_version"] == 20
    assert manifest["tta"] is False
    assert manifest["ckpt_files"] == sorted(files)


def test_build_manifest_expands_exp_names() -> None:
    manifest = build_manifest(
        ["exp006-run004-effv2s-f0.ckpt"],
        notebook="comp-submit",
        notebook_version=1,
        exp_names={"exp006": "exp006_canonside"},
    )

    assert manifest["components"][0]["exp"] == "exp006_canonside"


def test_build_manifest_skips_unparsable_files_and_records_them() -> None:
    manifest = build_manifest(
        ["exp006-run004-effv2s-f0.ckpt", "last.ckpt"],
        notebook="comp-submit",
        notebook_version=1,
    )

    assert len(manifest["components"]) == 1
    assert manifest["unparsed"] == ["last.ckpt"]


def test_describe_manifest_is_pasteable_one_liner() -> None:
    manifest = build_manifest(
        [
            "exp006-run004-effv2s-f0.ckpt",
            "exp006-run004-effv2s-f1.ckpt",
            "exp010-run000-base-f0.ckpt",
        ],
        notebook="comp-submit",
        notebook_version=20,
        blend={"method": "mean", "weights": [0.5, 0.5]},
        tta=False,
    )

    assert describe_manifest(manifest) == (
        "V20 exp006-run004-effv2s(2f) + exp010-run000-base(1f) "
        "| mean w=0.5/0.5 | tta=off"
    )


def test_describe_manifest_omits_weights_when_absent() -> None:
    manifest = build_manifest(
        ["exp006-run004-effv2s-f0.ckpt"],
        notebook="comp-submit",
        notebook_version=3,
        blend={"method": "mean"},
        tta=True,
    )

    assert describe_manifest(manifest) == "V3 exp006-run004-effv2s(1f) | mean | tta=on"


def test_write_manifest_roundtrip(tmp_path: Path) -> None:
    manifest = build_manifest(
        ["exp006-run004-effv2s-f0.ckpt"], notebook="comp-submit", notebook_version=1
    )
    path = write_manifest(manifest, tmp_path / "submission_manifest.json")

    assert json.loads(path.read_text(encoding="utf-8")) == manifest
