"""src/utils/env.py のテスト。"""

from pathlib import Path

from src.utils import env


def test_project_root_points_to_repo_root():
    root = env.project_root()
    assert (root / "pyproject.toml").exists()
    assert (root / "src" / "utils").is_dir()


def test_input_dir_prefers_env_var(monkeypatch):
    monkeypatch.setenv("INPUT_DIR", "/custom/input")
    assert env.input_dir() == Path("/custom/input")


def test_input_dir_defaults_to_local(monkeypatch):
    monkeypatch.delenv("INPUT_DIR", raising=False)
    monkeypatch.delenv("KAGGLE_KERNEL_RUN_TYPE", raising=False)
    monkeypatch.setattr(env, "KAGGLE_INPUT_ROOT", Path("/nonexistent/kaggle/input"))
    assert env.input_dir() == env.project_root() / "input"


def test_input_dir_on_kaggle(monkeypatch):
    monkeypatch.delenv("INPUT_DIR", raising=False)
    monkeypatch.setenv("KAGGLE_KERNEL_RUN_TYPE", "Interactive")
    assert env.input_dir() == env.KAGGLE_INPUT_ROOT


def test_output_dir_local(monkeypatch):
    monkeypatch.delenv("KAGGLE_KERNEL_RUN_TYPE", raising=False)
    monkeypatch.setattr(env, "KAGGLE_INPUT_ROOT", Path("/nonexistent/kaggle/input"))
    assert env.output_dir() == env.project_root() / "output"
