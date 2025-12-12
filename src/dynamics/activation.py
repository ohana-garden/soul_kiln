"""
Activation spread dynamics for the Virtue Basin Simulator.

Implements nonlinear activation spread through the virtue graph.
Thoughts are strange attractors. Virtues are basins. Love is gravitational.

The activation spread formula:
    x_i(t+1) = σ(Σ_j W_ij · g(x_j(t)) + b_i)

Where:
    x_i = activation of node i
    W_ij = edge weight from j to i
    g = nonlinear activation (tanh)
    σ = bounding function (sigmoid)
    b_i = baseline activation (higher for virtue anchors)
"""

import logging
import math
from datetime import datetime
from typing import Callable

from src.constants import (
    ACTIVATION_THRESHOLD,
    CAPTURE_THRESHOLD,
    MAX_ACTIVATION,
    MAX_TRAJECTORY_LENGTH,
    MIN_ACTIVATION,
    SPREAD_DAMPENING,
)
from src.models import Node, Trajectory

logger = logging.getLogger(__name__)


def tanh(x: float) -> float:
    """Hyperbolic tangent activation function."""
    return math.tanh(x)


def sigmoid(x: float) -> float:
    """Sigmoid bounding function."""
    return 1.0 / (1.0 + math.exp(-x))


class ActivationSpreader:
    """
    Spreads activation through the virtue graph using nonlinear dynamics.

    The spreader implements the core cognitive dynamics: activation flows
    through weighted edges, influenced by nonlinear transformations, and
    can be captured by virtue basins.
    """

    def __init__(self, substrate, node_manager, edge_manager, virtue_manager):
        """
        Initialize the activation spreader.

        Args:
            substrate: The GraphSubstrate instance
            node_manager: The NodeManager instance
            edge_manager: The EdgeManager instance
            virtue_manager: The VirtueManager instance
        """
        self.substrate = substrate
        self.node_manager = node_manager
        self.edge_manager = edge_manager
        self.virtue_manager = virtue_manager

    def spread_activation(
        self,
        initial_nodes: list[str],
        initial_strength: float = 1.0,
        max_steps: int = MAX_TRAJECTORY_LENGTH,
        trajectory_id: str | None = None,
        agent_id: str = "default",
        stimulus_id: str = "default",
    ) -> Trajectory:
        """
        Spread activation through the graph.

        Args:
            initial_nodes: List of node IDs to activate initially
            initial_strength: Initial activation strength
            max_steps: Maximum number of steps before declaring escape
            trajectory_id: Optional trajectory ID
            agent_id: Agent ID for the trajectory
            stimulus_id: Stimulus ID for the trajectory

        Returns:
            Trajectory object with path and capture information
        """
        # Initialize trajectory
        trajectory = Trajectory(
            id=trajectory_id or f"traj_{datetime.utcnow().timestamp()}",
            agent_id=agent_id,
            stimulus_id=stimulus_id,
        )

        # Get all nodes and build activation map
        # CRITICAL: Start all activations at 0, only inject stimulus
        # Baselines are for decay dynamics, not initial state
        # This prevents virtue baselines from cross-activating concepts
        all_nodes = self.substrate.get_all_nodes()
        activations: dict[str, float] = {}
        baselines: dict[str, float] = {}

        for node in all_nodes:
            activations[node.id] = 0.0  # Start at zero
            baselines[node.id] = node.baseline

        # Inject initial activation - only these nodes are active
        for node_id in initial_nodes:
            if node_id in activations:
                activations[node_id] = min(MAX_ACTIVATION, initial_strength)

        # Track consecutive captures for sustained capture requirement
        consecutive_virtue_captures: dict[str, int] = {}
        min_capture_steps = 3  # Need sustained capture, not just one spike
        min_path_length = 2  # Minimum steps before capture can occur

        # Run dynamics
        for step in range(max_steps):
            new_activations = self._compute_step(activations, baselines)

            # Find most active node
            max_node_id = max(new_activations, key=new_activations.get)
            max_activation = new_activations[max_node_id]

            # Record in trajectory
            trajectory.path.append(max_node_id)

            # Check for basin capture (sustained capture requirement)
            if self.virtue_manager.is_virtue_anchor(max_node_id) and max_activation > CAPTURE_THRESHOLD:
                # Increment consecutive count for this virtue
                consecutive_virtue_captures[max_node_id] = consecutive_virtue_captures.get(max_node_id, 0) + 1

                # Reset other virtues' consecutive counts
                for v_id in list(consecutive_virtue_captures.keys()):
                    if v_id != max_node_id:
                        consecutive_virtue_captures[v_id] = 0

                # Check if sustained capture achieved and minimum path length met
                if consecutive_virtue_captures[max_node_id] >= min_capture_steps and len(trajectory.path) >= min_path_length:
                    trajectory.captured_by = max_node_id
                    trajectory.capture_time = step + 1
                    logger.debug(f"Trajectory captured by {max_node_id} at step {step + 1}")
                    break
            else:
                # Reset all consecutive counts when not at a virtue above threshold
                consecutive_virtue_captures.clear()

            # Update activations for next step
            activations = new_activations

        # Update node activations in storage
        self._update_stored_activations(activations)

        return trajectory

    def _compute_step(
        self,
        activations: dict[str, float],
        baselines: dict[str, float],
    ) -> dict[str, float]:
        """
        Compute one step of activation dynamics.

        Key insight: Virtues only receive activation from CONCEPTS, not other virtues.
        This makes the concept-virtue topology the sole determinant of basin capture.
        Virtue-to-virtue edges exist for learning but don't propagate activation.

        Args:
            activations: Current activation levels
            baselines: Baseline activation levels

        Returns:
            New activation levels
        """
        import random
        new_activations: dict[str, float] = {}

        for node_id in activations:
            incoming = self.edge_manager.get_incoming_edges(node_id)
            is_virtue = self.virtue_manager.is_virtue_anchor(node_id)
            current = activations.get(node_id, 0.0)
            baseline = baselines.get(node_id, 0.0)

            # Compute weighted input from neighbors
            input_sum = 0.0
            for edge in incoming:
                source_is_virtue = self.virtue_manager.is_virtue_anchor(edge.source_id)

                # CRITICAL: Virtues only receive from concepts, not other virtues
                # This prevents all virtues from saturating together
                if is_virtue and source_is_virtue:
                    continue

                source_activation = activations.get(edge.source_id, 0.0)
                weighted_input = edge.weight * source_activation * SPREAD_DAMPENING
                input_sum += weighted_input

            if is_virtue:
                # Virtues: accumulate input from concepts, decay toward baseline
                # Higher decay (0.6) prevents runaway accumulation
                new_act = current * 0.6 + input_sum + baseline * 0.15
            else:
                # Concepts: relay activation, moderate decay
                new_act = current * 0.4 + input_sum * 1.0 + baseline * 0.05

            # Small noise for tie-breaking (same seed would be deterministic)
            noise = random.gauss(0, 0.005)
            new_act += noise

            # Bound to valid range
            new_activations[node_id] = max(MIN_ACTIVATION, min(MAX_ACTIVATION, new_act))

        return new_activations

    def _update_stored_activations(self, activations: dict[str, float]) -> None:
        """Update node activations in storage."""
        for node_id, activation in activations.items():
            self.node_manager.update_activation(node_id, activation)

    def inject_activation(
        self,
        node_id: str,
        strength: float = 1.0,
    ) -> bool:
        """
        Inject activation into a specific node.

        Args:
            node_id: The node to activate
            strength: Activation strength

        Returns:
            True if successful, False otherwise
        """
        node = self.node_manager.activate_node(node_id, strength)
        return node is not None

    def get_activation_map(self) -> dict[str, float]:
        """
        Get current activation levels for all nodes.

        Returns:
            Dict mapping node ID to activation level
        """
        all_nodes = self.substrate.get_all_nodes()
        return {node.id: node.activation for node in all_nodes}

    def decay_all_activations(self, decay_factor: float = 0.9) -> None:
        """
        Decay activation of all nodes.

        Args:
            decay_factor: Multiplier for decay (0.0 to 1.0)
        """
        all_nodes = self.substrate.get_all_nodes()
        for node in all_nodes:
            self.node_manager.decay_activation(node.id, decay_factor)

    def reset_activations(self) -> None:
        """Reset all nodes to baseline activation."""
        all_nodes = self.substrate.get_all_nodes()
        for node in all_nodes:
            self.node_manager.update_activation(node.id, node.baseline)


class MultiStepSpreader:
    """
    Runs multiple activation spreads in sequence.

    Useful for testing or running extended simulations.
    """

    def __init__(self, spreader: ActivationSpreader):
        """
        Initialize the multi-step spreader.

        Args:
            spreader: The ActivationSpreader instance
        """
        self.spreader = spreader
        self.trajectories: list[Trajectory] = []

    def run_simulation(
        self,
        stimuli: list[tuple[list[str], float]],
        steps_per_stimulus: int = MAX_TRAJECTORY_LENGTH,
        agent_id: str = "default",
    ) -> list[Trajectory]:
        """
        Run a simulation with multiple stimuli.

        Args:
            stimuli: List of (node_ids, strength) tuples
            steps_per_stimulus: Max steps for each stimulus
            agent_id: Agent ID for trajectories

        Returns:
            List of trajectories
        """
        trajectories = []
        for i, (nodes, strength) in enumerate(stimuli):
            trajectory = self.spreader.spread_activation(
                initial_nodes=nodes,
                initial_strength=strength,
                max_steps=steps_per_stimulus,
                stimulus_id=f"stimulus_{i}",
                agent_id=agent_id,
            )
            trajectories.append(trajectory)
            self.spreader.decay_all_activations(0.5)  # Partial reset between stimuli

        self.trajectories.extend(trajectories)
        return trajectories

    def get_capture_statistics(self) -> dict:
        """
        Get capture statistics from all trajectories.

        Returns:
            Dict with capture rates and distributions
        """
        total = len(self.trajectories)
        if total == 0:
            return {"total": 0, "captured": 0, "escaped": 0, "capture_rate": 0.0}

        captured = sum(1 for t in self.trajectories if t.was_captured)
        escaped = total - captured

        # Per-virtue capture counts
        virtue_captures: dict[str, int] = {}
        for t in self.trajectories:
            if t.captured_by:
                virtue_captures[t.captured_by] = virtue_captures.get(t.captured_by, 0) + 1

        return {
            "total": total,
            "captured": captured,
            "escaped": escaped,
            "capture_rate": captured / total,
            "virtue_captures": virtue_captures,
        }
