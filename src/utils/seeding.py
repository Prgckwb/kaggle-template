"""乱数シードの固定。"""

from __future__ import annotations

import os
import random


def seed_everything(seed: int) -> None:
    """random / numpy / torch（入っていれば）のシードを固定する。

    cudnn の決定論モードは速度を大きく落とすので既定では有効にしない。
    判定は seed を変えた run の揺れ（metric.noise.seed_spread）を分母にする前提なので、
    ビット単位の再現性は要らない。
    """
    random.seed(seed)
    os.environ["PYTHONHASHSEED"] = str(seed)
    import numpy as np

    np.random.seed(seed)
    try:
        import torch
    except ImportError:
        return
    torch.manual_seed(seed)
    torch.cuda.manual_seed_all(seed)
