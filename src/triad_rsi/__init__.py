"""Triad-RSI: public research core for coordinated self-improvement."""

from .bandit import Bandit
from .gate import gate_from_vectors, paired_gate
from .confirmation import confirm_gate
from .scheduler import select

__version__ = "0.1.0"
__all__ = ["Bandit", "gate_from_vectors", "paired_gate", "confirm_gate", "select"]
