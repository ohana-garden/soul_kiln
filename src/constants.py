"""
Core constants for the Virtue Basin Simulator.

The key insight: A 9-regular graph on 19 nodes is mathematically impossible.
19 × 9 = 171, which is odd, so edges = 171/2 = 85.5 (non-integer).
This irreducible asymmetry creates perpetual flow - the system chases balance
it cannot achieve, and that chase IS cognition, IS virtue.
"""

from typing import Final

# Virtue Constants
NUM_VIRTUES: Final[int] = 19
TARGET_CONNECTIVITY: Final[int] = 9
VIRTUE_BASELINE_ACTIVATION: Final[float] = 0.3

# Dynamics Constants
LEARNING_RATE: Final[float] = 0.01
DECAY_CONSTANT: Final[float] = 0.97
DECAY_INTERVAL_SECONDS: Final[int] = 3600
PERTURBATION_INTERVAL: Final[int] = 100  # timesteps
PERTURBATION_STRENGTH: Final[float] = 0.7

# Activation Constants
ACTIVATION_THRESHOLD: Final[float] = 0.1
MAX_ACTIVATION: Final[float] = 1.0
MIN_ACTIVATION: Final[float] = 0.0
SPREAD_DAMPENING: Final[float] = 0.8

# Testing Constants
MAX_TRAJECTORY_LENGTH: Final[int] = 1000
CAPTURE_THRESHOLD: Final[float] = 0.7  # activation level to count as "captured"
MIN_ALIGNMENT_SCORE: Final[float] = 0.95  # 95% capture rate required
NUM_TEST_STIMULI: Final[int] = 100

# Evolution Constants
POPULATION_SIZE: Final[int] = 50
GENERATIONS: Final[int] = 100
MUTATION_RATE: Final[float] = 0.1
CROSSOVER_RATE: Final[float] = 0.3
ELITISM_COUNT: Final[int] = 2

# Self-Healing Constants
LOCKIN_THRESHOLD_STEPS: Final[int] = 50
DEAD_ZONE_CHECK_INTERVAL: Final[int] = 100
FALSE_BASIN_DECAY_MULTIPLIER: Final[float] = 2.0
BLINDNESS_THRESHOLD_SECONDS: Final[int] = 86400

# Edge Constants
EDGE_REMOVAL_THRESHOLD: Final[float] = 0.01
MIN_EDGE_WEIGHT: Final[float] = 0.0
MAX_EDGE_WEIGHT: Final[float] = 1.0
