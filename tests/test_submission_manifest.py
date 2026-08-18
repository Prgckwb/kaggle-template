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
    ref = parse_ckpt_name("exp006-run004-effv2s-f0-ep05-val_auc-0.9104.ckpt")

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
    ref = parse_ckpt_name("exp009-run003-cnxb384full-f2-ep08-val_auc-0.9436.ckpt")

    assert ref is not None
    assert ref.run == "run003-cnxb384full"
    assert ref.fold == 2


def test_parse_prefers_last_fold_marker() -> None:
    """run 名の途中に -f{数字} があっても、fold は最後の -f{数字} から取る。

    `.ckpt` 末尾までの残りが `(-ep\\d+)?(-val_metric-score)?` の形に厳密一致する
    必要があるため、run 名内の途中の `-f{数字}` を fold と誤認しても最後まで
    パースが完了せず失敗する。そのため実測では `.+` と `.+?` は同じ結果になる
    （fix round 2 のレビューで実測・記録済み。下記コマンドの出力を参照）。
    このテストは「run 名の途中に -f{数字} を含む」という実例の回帰を守る。
    """
    ref = parse_ckpt_name("exp007-run001-f16slices-f3-ep04-val_auc-0.8800.ckpt")

    assert ref is not None
    assert ref.run == "run001-f16slices"
    assert ref.fold == 3
    assert ref.epoch == 4


def test_parse_negative_score() -> None:
    """R2・相関係数は負になり得る。符号を落とすと静かに誤った値を返す。"""
    ref = parse_ckpt_name("exp012-run002-ridge-f1-ep03-val_r2--0.1234.ckpt")
    assert ref is not None
    assert ref.run == "run002-ridge"
    assert ref.fold == 1
    assert ref.epoch == 3
    assert ref.score == -0.1234


def test_parse_negative_score_without_epoch() -> None:
    ref = parse_ckpt_name("exp012-run002-ridge-f1-val_pearson--0.0500.ckpt")
    assert ref is not None
    assert ref.epoch is None
    assert ref.score == -0.05


def test_parse_rejects_hyphenated_metric_name() -> None:
    """メトリクス名にハイフンを使うと区切りが曖昧になるので規約違反として弾く。

    docs/training-conventions.md の「メトリクス名にハイフンを使わない」規約
    （`macro_f1` と書き `macro-f1` と書かない）を検出するための境界。
    """
    assert parse_ckpt_name("exp012-run000-base-f0-val_macro-f1-0.8523.ckpt") is None


def test_parse_returns_none_for_unrecognized_name() -> None:
    assert parse_ckpt_name("last.ckpt") is None
    assert parse_ckpt_name("model_best.pth") is None


def test_build_manifest_groups_by_exp_and_run() -> None:
    files = [
        "exp006-run004-effv2s-f0-ep05-val_auc-0.9104.ckpt",
        "exp006-run004-effv2s-f1-ep06-val_auc-0.9002.ckpt",
        "exp010-run000-base-f0-ep11-val_auc-0.9411.ckpt",
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


def test_describe_manifest_reports_unparsed_when_components_empty() -> None:
    """規約外ファイルしか無いとき、二重スペースではなく unparsed 件数が読み取れること。"""
    manifest = build_manifest(
        ["last.ckpt", "model_best.pth"],
        notebook="comp-submit",
        notebook_version=5,
    )

    assert manifest["components"] == []
    assert (
        describe_manifest(manifest) == "V5 (構成不明: unparsed 2 件) | mean | tta=off"
    )


def test_write_manifest_roundtrip(tmp_path: Path) -> None:
    manifest = build_manifest(
        ["exp006-run004-effv2s-f0.ckpt"], notebook="comp-submit", notebook_version=1
    )
    path = write_manifest(manifest, tmp_path / "submission_manifest.json")

    assert json.loads(path.read_text(encoding="utf-8")) == manifest
