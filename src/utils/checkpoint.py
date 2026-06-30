"""Checkpoint utilities for export and management."""

from __future__ import annotations

from pathlib import Path
from typing import Any


def export_slim_checkpoint(
    checkpoint_path: Path | str,
    output_path: Path | str,
    *,
    keep_keys: list[str] | None = None,
    remove_keys: list[str] | None = None,
) -> Path:
    """Export a slim checkpoint containing only model weights.

    Strips optimizer state, scheduler state, and other training artifacts
    to reduce file size for inference/submission.

    Args:
        checkpoint_path: Path to the full training checkpoint.
        output_path: Path to write the slim checkpoint.
        keep_keys: If specified, only these top-level keys are kept.
            Defaults to ["state_dict", "hyper_parameters"].
        remove_keys: Top-level keys to explicitly remove (applied after keep_keys).

    Returns:
        Path to the written slim checkpoint.
    """
    import torch

    checkpoint_path = Path(checkpoint_path)
    output_path = Path(output_path)

    ckpt: dict[str, Any] = torch.load(
        checkpoint_path, map_location="cpu", weights_only=False
    )

    if keep_keys is None:
        keep_keys = _detect_keep_keys(ckpt)

    slim: dict[str, Any] = {k: ckpt[k] for k in keep_keys if k in ckpt}

    if remove_keys:
        for k in remove_keys:
            slim.pop(k, None)

    output_path.parent.mkdir(parents=True, exist_ok=True)
    torch.save(slim, output_path)

    original_mb = checkpoint_path.stat().st_size / (1024 * 1024)
    slim_mb = output_path.stat().st_size / (1024 * 1024)
    print(
        f"Exported slim checkpoint: {original_mb:.1f}MiB -> {slim_mb:.1f}MiB "
        f"({slim_mb / original_mb * 100:.0f}%)"
    )

    return output_path


def _detect_keep_keys(ckpt: dict[str, Any]) -> list[str]:
    """Auto-detect which keys to keep based on checkpoint format."""
    keys = []

    # PyTorch Lightning format
    if "state_dict" in ckpt:
        keys.append("state_dict")
        if "hyper_parameters" in ckpt:
            keys.append("hyper_parameters")
        return keys

    # Plain PyTorch format (model key)
    if "model" in ckpt:
        keys.append("model")
        return keys

    # HuggingFace Trainer format
    if "model_state_dict" in ckpt:
        keys.append("model_state_dict")
        return keys

    # Fallback: keep everything except known training artifacts
    training_keys = {
        "optimizer",
        "optimizer_states",
        "optimizer_state_dict",
        "scheduler",
        "scheduler_state_dict",
        "lr_scheduler",
        "lr_schedulers",
        "scaler",
        "grad_scaler",
        "callbacks",
        "loops",
        "global_step",
        "epoch",
        "pytorch-lightning_version",
    }
    return [k for k in ckpt if k not in training_keys]


def load_checkpoint_weights(
    checkpoint_path: Path | str,
) -> dict[str, Any]:
    """Load only model weights from a checkpoint, auto-detecting format.

    Returns the state dict regardless of checkpoint format
    (Lightning, plain PyTorch, HuggingFace).
    """
    import torch

    ckpt: dict[str, Any] = torch.load(
        Path(checkpoint_path), map_location="cpu", weights_only=False
    )

    if "state_dict" in ckpt:
        return ckpt["state_dict"]
    if "model" in ckpt:
        return ckpt["model"]
    if "model_state_dict" in ckpt:
        return ckpt["model_state_dict"]

    return ckpt
