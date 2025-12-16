"""
Canonical activation functions for Soul Kiln.

These are used throughout the codebase for activation spread dynamics.
Import from here rather than defining locally.
"""

import math


def tanh(x: float) -> float:
    """
    Hyperbolic tangent activation function.

    Maps inputs to range (-1, 1) with smooth nonlinearity.
    Used for input transformation in activation spread.
    """
    return math.tanh(x)


def sigmoid(x: float, clip: float = 500.0) -> float:
    """
    Sigmoid bounding function with overflow protection.

    Maps inputs to range (0, 1). The clip parameter prevents
    overflow errors with extreme inputs.

    Args:
        x: Input value
        clip: Threshold for numerical stability (default 500)

    Returns:
        Sigmoid of x, bounded to (0, 1)
    """
    if x < -clip:
        return 0.0
    if x > clip:
        return 1.0
    return 1.0 / (1.0 + math.exp(-x))


def relu(x: float) -> float:
    """
    Rectified linear unit.

    Returns max(0, x). Not currently used but available
    for future activation dynamics experiments.
    """
    return max(0.0, x)


def softplus(x: float, beta: float = 1.0) -> float:
    """
    Softplus activation: smooth approximation to ReLU.

    Returns (1/beta) * log(1 + exp(beta * x))
    """
    if beta * x > 20:  # Avoid overflow
        return x
    return (1.0 / beta) * math.log(1.0 + math.exp(beta * x))
