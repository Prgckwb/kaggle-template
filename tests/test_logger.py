"""src/utils/logger.py のテスト。"""

import logging

from src.utils.logger import get_logger, resolve_logs_dir


def test_resolve_logs_dir_debug_suffix(tmp_path):
    logs_dir = tmp_path / "logs" / "run000-base"
    resolved = resolve_logs_dir(logs_dir, "debug")
    assert resolved.name == "run000-base-debug"
    assert resolved.parent == logs_dir.parent


def test_resolve_logs_dir_non_debug(tmp_path):
    logs_dir = tmp_path / "logs" / "run000-base"
    for mode in ("fold0", "full"):
        assert resolve_logs_dir(logs_dir, mode) == logs_dir


def test_get_logger_writes_to_file(tmp_path):
    logger = get_logger("test_logger_file", tmp_path)
    logger.info("hello")

    log_files = list(tmp_path.glob("*.log"))
    assert len(log_files) == 1
    content = log_files[0].read_text()
    assert "hello" in content
    assert "INFO" in content

    # 後始末（同名ロガーは再利用されるためハンドラを閉じる）
    for handler in logger.handlers[:]:
        handler.close()
        logger.removeHandler(handler)


def test_get_logger_no_duplicate_handlers(tmp_path):
    logger1 = get_logger("test_logger_dedup", tmp_path)
    n_handlers = len(logger1.handlers)
    logger2 = get_logger("test_logger_dedup", tmp_path)

    assert logger1 is logger2
    assert len(logger2.handlers) == n_handlers
    assert len(list(tmp_path.glob("*.log"))) == 1

    for handler in logger1.handlers[:]:
        handler.close()
        logger1.removeHandler(handler)


def test_get_logger_without_file():
    logger = get_logger("test_logger_stream_only")
    assert all(not isinstance(h, logging.FileHandler) for h in logger.handlers)
    for handler in logger.handlers[:]:
        logger.removeHandler(handler)
