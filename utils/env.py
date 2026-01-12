from dataclasses import dataclass
from pathlib import Path


def get_project_root() -> Path:
    """プロジェクトルートを取得"""
    return Path(__file__).parent.parent


@dataclass
class EnvConfig:
    """環境設定"""

    input_dir: str = str(get_project_root() / "input")
    output_dir: str = str(get_project_root() / "output")
    exp_output_dir: str = str(get_project_root() / "output" / "experiments")
