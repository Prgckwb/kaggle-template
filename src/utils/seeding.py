"""Reproducible seeding for all common frameworks."""

from __future__ import annotations

import os
import random


def seed_everything(seed: int) -> None:
    """Fix random seeds for reproducibility across all frameworks."""
    random.seed(seed)
    os.environ["PYTHONHASHSEED"] = str(seed)

    try:
        import numpy as np

        # グローバルシード固定が目的なので legacy API を意図的に使用
        np.random.seed(seed)  # noqa: NPY002
    except ImportError:
        pass

    try:
        import torch

        torch.manual_seed(seed)
        torch.cuda.manual_seed_all(seed)
        torch.backends.cudnn.deterministic = True
        torch.backends.cudnn.benchmark = False
    except ImportError:
        pass
