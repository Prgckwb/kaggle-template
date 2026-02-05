"""Model definitions."""


class BaselineModel:
    """Baseline model template."""

    def __init__(self, config):
        self.config = config

    def forward(self, x):
        """Forward pass."""
        raise NotImplementedError

    def save(self, path):
        """Save model weights."""
        raise NotImplementedError

    def load(self, path):
        """Load model weights."""
        raise NotImplementedError
