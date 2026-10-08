"""チェックポイントの選択と配布用の軽量化。

ckpt 名の規約は docs/training-conventions.md の「チェックポイント」
（`{exp番号}-{run_name}-f{k}-ep{NN}-val_{metric}-{score}.ckpt`）。
"""

from __future__ import annotations

from pathlib import Path

from src.utils.submission_manifest import parse_ckpt_name

# 推論に必要なキーだけを残す（optimizer / scheduler / loops 等の学習状態は捨てる）
SLIM_KEYS = ("state_dict", "hyper_parameters", "pytorch-lightning_version")


def select_best_ckpt(fold_dir: str | Path, mode: str) -> Path:
    """fold ディレクトリから、ファイル名のスコアが best の ckpt を選ぶ。

    `next(glob("*.ckpt"))` で任意の 1 個を掴むと、save_top_k >= 2 のとき非 best で提出してしまう。
    規約どおりの名前が 1 つも無ければ黙って選ばずエラーにする。
    """
    fold_dir = Path(fold_dir)
    ckpts = sorted(fold_dir.glob("*.ckpt"))
    if not ckpts:
        raise FileNotFoundError(f"ckpt が見つかりません: {fold_dir}")
    scored = [
        (ref.score, path)
        for path in ckpts
        if (ref := parse_ckpt_name(path.name)) and ref.score is not None
    ]
    if not scored:
        names = ", ".join(p.name for p in ckpts)
        raise RuntimeError(
            f"スコア入りの ckpt 名が {fold_dir} にありません（{names}）。"
            "docs/training-conventions.md の命名規約に合わせてください"
        )
    pick = max if mode == "max" else min
    return pick(scored, key=lambda item: item[0])[1]


def export_slim_checkpoint(src: str | Path, dst: str | Path) -> Path:
    """推論用に学習状態を落とした ckpt を書き出す（Kaggle Dataset の容量節約）。"""
    import torch

    ckpt = torch.load(Path(src), map_location="cpu", weights_only=False)
    if "state_dict" not in ckpt:
        raise ValueError(
            f"Lightning 形式の ckpt ではありません（state_dict が無い）: {src}"
        )
    dst = Path(dst)
    dst.parent.mkdir(parents=True, exist_ok=True)
    torch.save({k: ckpt[k] for k in SLIM_KEYS if k in ckpt}, dst)
    return dst
