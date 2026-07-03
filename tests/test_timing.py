"""src/utils/timing.py のテスト。"""

from src.utils.timing import timer, trace


def test_timer_prints_elapsed(capsys):
    with timer("unit"):
        pass
    out = capsys.readouterr().out
    assert "[unit] done in" in out
    assert " s" in out


def test_trace_prints_memory_and_time(capsys):
    with trace("unit"):
        pass
    err = capsys.readouterr().err
    assert "unit" in err
    assert "GB" in err
    assert "sec" in err
