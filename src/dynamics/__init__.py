"""
Dynamics engine for the Virtue Basin Simulator.

Implements:
- Activation spread through the graph
- Hebbian learning for edge strengthening
- Temporal decay for edge weakening
- Perturbation for exploration
- Self-healing mechanisms
"""

from src.dynamics.activation import ActivationSpreader
from src.dynamics.hebbian import HebbianLearner
from src.dynamics.decay import TemporalDecay
from src.dynamics.perturbation import Perturbator
from src.dynamics.healing import SelfHealer

__all__ = [
    "ActivationSpreader",
    "HebbianLearner",
    "TemporalDecay",
    "Perturbator",
    "SelfHealer",
]
