"""ファイル + 標準出力へのロガー。

学習スクリプトのログを logs_dir にタイムスタンプ付きで保存する。
MetricsLogger（メトリクス専用）と併用し、こちらは自由形式の
実行ログ（進捗・警告・デバッグ情報）を担当する。
"""

from __future__ import annotations

import logging
import time
from pathlib import Path


def resolve_logs_dir(logs_dir: str | Path, run_mode: str) -> Path:
    """run_mode に応じたログディレクトリを返す。

    debug のログは `{logs_dir}-debug/` に隔離し、fold0/full のログを
    上書きしない（MetricsLogger と同じ規約）。
    """
    logs_dir = Path(logs_dir)
    if run_mode == "debug":
        logs_dir = logs_dir.with_name(f"{logs_dir.name}-debug")
    return logs_dir


def get_logger(name: str, log_dir: str | Path | None = None) -> logging.Logger:
    """ストリーム + ファイル出力のロガーを返す。

    - log_dir を指定すると `{log_dir}/{YYYYmmdd_HHMMSS}.log` にも書き出す
      （ディレクトリは自動作成）
    - 同名ロガーの再取得ではハンドラを重複追加しない
    """
    logger = logging.getLogger(name)
    if logger.handlers:
        return logger

    logger.setLevel(logging.INFO)
    formatter = logging.Formatter(
        "[%(asctime)s : %(levelname)s - %(filename)s] %(message)s"
    )

    stream_handler = logging.StreamHandler()
    stream_handler.setLevel(logging.INFO)
    stream_handler.setFormatter(formatter)
    logger.addHandler(stream_handler)

    if log_dir is not None:
        log_dir = Path(log_dir)
        log_dir.mkdir(parents=True, exist_ok=True)
        log_file = log_dir / f"{time.strftime('%Y%m%d_%H%M%S')}.log"
        file_handler = logging.FileHandler(log_file)
        file_handler.setLevel(logging.INFO)
        file_handler.setFormatter(formatter)
        logger.addHandler(file_handler)

    logger.propagate = False
    return logger
