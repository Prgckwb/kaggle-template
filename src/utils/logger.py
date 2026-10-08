"""ファイル + 標準出力へのロガー（自由形式の実行ログ。メトリクスは Lightning の CSVLogger / wandb）。"""

from __future__ import annotations

import logging
import time
from pathlib import Path


def get_logger(name: str, log_dir: str | Path | None = None) -> logging.Logger:
    """ストリーム + `{log_dir}/{YYYYmmdd_HHMMSS}.log` に出すロガー。同名の再取得でハンドラを重複させない。"""
    logger = logging.getLogger(name)
    if logger.handlers:
        return logger
    logger.setLevel(logging.INFO)
    formatter = logging.Formatter(
        "[%(asctime)s : %(levelname)s - %(filename)s] %(message)s"
    )
    handlers: list[logging.Handler] = [logging.StreamHandler()]
    if log_dir is not None:
        log_dir = Path(log_dir)
        log_dir.mkdir(parents=True, exist_ok=True)
        handlers.append(
            logging.FileHandler(log_dir / f"{time.strftime('%Y%m%d_%H%M%S')}.log")
        )
    for handler in handlers:
        handler.setFormatter(formatter)
        logger.addHandler(handler)
    logger.propagate = False
    return logger
