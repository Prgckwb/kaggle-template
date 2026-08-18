"""Tests for src/utils/lineage.py."""

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


def test_diff_reports_added_and_removed_keys() -> None:
    parent = {"model": {"name": "a"}, "dropped": 1}
    child = {"model": {"name": "a", "layers": 2}}

    assert diff_config_keys(child, parent) == ["dropped", "model.layers"]


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
