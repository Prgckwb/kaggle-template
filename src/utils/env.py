"""実行環境の検出とパス解決。

Hydra を使わないスクリプト（tools/、notebook、sandbox/）から
プロジェクトのパスを一元的に参照するためのヘルパー。
Hydra config 側は `${oc.env:INPUT_DIR,...}` で同じ環境変数を参照する。

優先順位:
1. 環境変数 INPUT_DIR（明示指定）
2. Kaggle Notebook 環境なら /kaggle/input
3. ローカルのプロジェクトルート直下の input/
"""

from __future__ import annotations

import os
from pathlib import Path

KAGGLE_INPUT_ROOT = Path("/kaggle/input")


def project_root() -> Path:
    """リポジトリのルートディレクトリ（src/ の親）を返す。"""
    return Path(__file__).resolve().parent.parent.parent


def is_kaggle_notebook() -> bool:
    """Kaggle Notebook 上で実行されているかどうか。"""
    return "KAGGLE_KERNEL_RUN_TYPE" in os.environ or KAGGLE_INPUT_ROOT.is_dir()


def input_dir() -> Path:
    """データの入力ディレクトリを返す。

    Kaggle Notebook では /kaggle/input を返す。コンペデータは
    さらに /kaggle/input/{competition_slug}/ 配下にマウントされる点に注意
    （実際のマウントパスは Notebook のサイドバーで確認すること）。
    """
    env_value = os.environ.get("INPUT_DIR")
    if env_value:
        return Path(env_value)
    if is_kaggle_notebook():
        return KAGGLE_INPUT_ROOT
    return project_root() / "input"


def output_dir() -> Path:
    """学習出力のルートディレクトリを返す。

    Kaggle Notebook では書き込み可能な /kaggle/working を使う。
    """
    if is_kaggle_notebook():
        return Path("/kaggle/working")
    return project_root() / "output"
