"""Agent skeleton for simulation competitions."""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any


class BaseAgent(ABC):
    """Base class for competition agents."""

    @abstractmethod
    def act(self, observation: Any) -> Any:
        """Choose an action given the current observation."""
        ...

    def reset(self) -> None:  # noqa: B027 - デフォルトは状態なし（必要な場合のみ override）
        """Reset agent state for a new episode."""
        pass


class SampleAgent(BaseAgent):
    """Simple rule-based agent (replace with your implementation)."""

    def act(self, observation: Any) -> Any:
        return 0  # Default action
