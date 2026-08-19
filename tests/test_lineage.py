"""Tests for src/utils/lineage.py."""

from pathlib import Path

from src.utils.lineage import (
    check_varied,
    diff_config_keys,
    flatten_config,
)


def test_flatten_config_uses_dot_notation() -> None:
    result = flatten_config({"training": {"lr": 1e-3, "epochs": 10}, "seed": 42})

    assert result == {"training.lr": 1e-3, "training.epochs": 10, "seed": 42}


def test_flatten_config_keeps_lists_as_values() -> None:
    result = flatten_config({"aug": {"scales": [0.9, 1.1]}})

    assert result == {"aug.scales": [0.9, 1.1]}


def test_diff_reports_changed_key() -> None:
    parent = {"training": {"lr": 1e-3, "epochs": 10}}
    child = {"training": {"lr": 2e-4, "epochs": 10}}

    assert diff_config_keys(child, parent) == ["training.lr"]


def test_diff_reports_added_keys_but_not_parent_only_keys() -> None:
    """子にあって親に無いキーは「追加」。親にしか無いキーは継承なので数えない。"""
    parent = {"model": {"name": "a"}, "inherited_only": 1}
    child = {"model": {"name": "a", "layers": 2}}

    assert diff_config_keys(child, parent) == ["model.layers"]


def test_diff_ignores_run_identity_keys_by_default() -> None:
    parent = {"run_name": "run000-base", "lineage": {"parent": "config", "varied": []}}
    child = {
        "run_name": "run001-lr",
        "lineage": {"parent": "run000-base", "varied": ["x"]},
    }

    assert diff_config_keys(child, parent) == []


def test_check_varied_ok_when_declaration_matches() -> None:
    parent = {"training": {"lr": 1e-3}}
    child = {"training": {"lr": 2e-4}}

    result = check_varied(child, parent, declared=["training.lr"])

    assert result.ok is True
    assert result.n_varied == 1
    assert result.missing == []
    assert result.extra == []


def test_check_varied_detects_undeclared_change() -> None:
    """宣言漏れ = 「1 変数差分のつもりが 2 変数だった」事故の検出。"""
    parent = {"training": {"lr": 1e-3, "epochs": 10}}
    child = {"training": {"lr": 2e-4, "epochs": 20}}

    result = check_varied(child, parent, declared=["training.lr"])

    assert result.ok is False
    assert result.missing == ["training.epochs"]
    assert result.n_varied == 2


def test_check_varied_detects_stale_declaration() -> None:
    parent = {"training": {"lr": 1e-3}}
    child = {"training": {"lr": 1e-3}}

    result = check_varied(child, parent, declared=["training.lr"])

    assert result.ok is False
    assert result.extra == ["training.lr"]
    assert result.n_varied == 0


def test_check_varied_multi_variable_run_is_flagged() -> None:
    """2 変数以上を同時に変えた run は Δ を 1 変数の名前で呼べない。"""
    parent = {"model": {"name": "a"}, "input": {"size": 224}}
    child = {"model": {"name": "b"}, "input": {"size": 384}}

    result = check_varied(child, parent, declared=["model.name", "input.size"])

    assert result.ok is True
    assert result.n_varied == 2


def test_diff_treats_parent_only_keys_as_inherited() -> None:
    """親にしか無いキーは「継承」であり差分ではない。

    Hydra の `defaults:` は `yaml.safe_load` では compose されないので、
    差分 config を素で読むと継承キーは必ず「親にしか無いキー」になる。
    子 config に「キーの削除」を表現する手段は無いため、和集合を取ると
    触っていない継承キーが全部差分に数えられてしまう。
    """
    parent = {"data": {"input_dir": "input"}, "debug": {"epochs": 1}}
    child = {"training": {"lr": 2e-4}}

    assert diff_config_keys(child, parent) == ["training.lr"]


def test_diff_ignores_hydra_defaults_declaration() -> None:
    """`defaults:` は Hydra の継承宣言であり実験変数ではない。"""
    parent = {"defaults": ["base_schema", "_self_"], "training": {"lr": 1e-3}}
    child = {"defaults": ["config"], "training": {"lr": 2e-4}}

    assert diff_config_keys(child, parent) == ["training.lr"]


def test_diff_on_bundled_sample_run_config() -> None:
    """テンプレート同梱の差分 config が「子が触ったキーだけ」を返すこと。"""
    import yaml

    config_dir = Path("src/exp000_sample/config")
    parent = yaml.safe_load((config_dir / "config.yaml").read_text())
    child = yaml.safe_load((config_dir / "run001-sample-v2.yaml").read_text())

    actual = diff_config_keys(child, parent)

    child_keys = set(flatten_config(child))
    assert set(actual) <= child_keys, "子が触っていないキーが差分に入っている"
    assert "defaults" not in actual
    assert "data.input_dir" not in actual
    assert "debug.epochs" not in actual
    assert actual == ["model.name", "training.epochs", "training.lr"]


def test_bundled_sample_run_config_declares_matching_lineage() -> None:
    """同梱サンプルの `lineage.varied` 宣言が実際の差分と一致すること。"""
    import yaml

    config_dir = Path("src/exp000_sample/config")
    parent = yaml.safe_load((config_dir / "config.yaml").read_text())
    child = yaml.safe_load((config_dir / "run001-sample-v2.yaml").read_text())

    result = check_varied(child, parent, declared=child["lineage"]["varied"])

    assert result.ok is True, f"missing={result.missing} extra={result.extra}"
