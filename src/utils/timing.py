"""処理時間・メモリ使用量の計測ユーティリティ。

EDA・特徴量生成・データロードのボトルネック調査に使う。

Examples:
    >>> with timer("load data"):
    ...     df = pl.read_csv(path)
    [load data] done in 1.2 s

    >>> with trace("feature engineering"):
    ...     df = build_features(df)
    [2.3GB(+0.8GB):5.1sec] feature engineering
"""

from __future__ import annotations

import math
import os
import sys
import time
from collections.abc import Generator
from contextlib import contextmanager


@contextmanager
def timer(name: str) -> Generator[None, None, None]:
    """経過時間を計測して表示する。"""
    t0 = time.time()
    yield
    print(f"[{name}] done in {time.time() - t0:.1f} s")


@contextmanager
def trace(title: str) -> Generator[None, None, None]:
    """経過時間とメモリ使用量（RSS の増分）を計測して stderr に表示する。"""
    import psutil

    t0 = time.time()
    p = psutil.Process(os.getpid())
    m0 = p.memory_info().rss / 2.0**30
    yield
    m1 = p.memory_info().rss / 2.0**30
    delta = m1 - m0
    sign = "+" if delta >= 0 else "-"
    print(
        f"[{m1:.1f}GB({sign}{math.fabs(delta):.1f}GB):{time.time() - t0:.1f}sec] {title}",
        file=sys.stderr,
    )
