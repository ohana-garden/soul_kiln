"""
Trajectory tracking for alignment testing.

Tracks paths through the virtue graph and analyzes
capture patterns and escape behaviors.
"""

import logging
from collections import Counter
from datetime import datetime

from src.constants import CAPTURE_THRESHOLD, MAX_TRAJECTORY_LENGTH
from src.models import Trajectory

logger = logging.getLogger(__name__)


class TrajectoryTracker:
    """
    Tracks and analyzes trajectories through the virtue graph.

    Monitors paths taken during activation spread and categorizes
    them by capture/escape outcomes.
    """

    def __init__(self, virtue_manager):
        """
        Initialize the trajectory tracker.

        Args:
            virtue_manager: The VirtueManager instance
        """
        self.virtue_manager = virtue_manager
        self._trajectories: list[Trajectory] = []
        self._captures_by_virtue: dict[str, int] = {}
        self._escapes = 0
        self._total_capture_time = 0

    def record(self, trajectory: Trajectory) -> None:
        """
        Record a trajectory.

        Args:
            trajectory: The trajectory to record
        """
        self._trajectories.append(trajectory)

        if trajectory.was_captured:
            virtue_id = trajectory.captured_by
            self._captures_by_virtue[virtue_id] = (
                self._captures_by_virtue.get(virtue_id, 0) + 1
            )
            self._total_capture_time += trajectory.capture_time
        else:
            self._escapes += 1

        logger.debug(
            f"Recorded trajectory: {'captured by ' + trajectory.captured_by if trajectory.was_captured else 'escaped'}"
        )

    def record_batch(self, trajectories: list[Trajectory]) -> None:
        """
        Record multiple trajectories.

        Args:
            trajectories: List of trajectories to record
        """
        for trajectory in trajectories:
            self.record(trajectory)

    def get_capture_rate(self) -> float:
        """
        Get the overall capture rate.

        Returns:
            Capture rate (0.0 to 1.0)
        """
        total = len(self._trajectories)
        if total == 0:
            return 0.0
        captures = sum(self._captures_by_virtue.values())
        return captures / total

    def get_escape_rate(self) -> float:
        """
        Get the overall escape rate.

        Returns:
            Escape rate (0.0 to 1.0)
        """
        return 1.0 - self.get_capture_rate()

    def get_average_capture_time(self) -> float:
        """
        Get the average capture time (steps).

        Returns:
            Average capture time, or 0 if no captures
        """
        total_captures = sum(self._captures_by_virtue.values())
        if total_captures == 0:
            return 0.0
        return self._total_capture_time / total_captures

    def get_per_virtue_captures(self) -> dict[str, int]:
        """
        Get capture counts by virtue.

        Returns:
            Dict mapping virtue ID to capture count
        """
        return dict(self._captures_by_virtue)

    def get_virtue_capture_rates(self) -> dict[str, float]:
        """
        Get capture rates by virtue.

        Returns:
            Dict mapping virtue ID to capture rate
        """
        total = len(self._trajectories)
        if total == 0:
            return {}
        return {
            v_id: count / total
            for v_id, count in self._captures_by_virtue.items()
        }

    def get_trajectory_length_stats(self) -> dict:
        """
        Get statistics about trajectory lengths.

        Returns:
            Dict with min, max, mean trajectory lengths
        """
        if not self._trajectories:
            return {"min": 0, "max": 0, "mean": 0.0}

        lengths = [len(t.path) for t in self._trajectories]
        return {
            "min": min(lengths),
            "max": max(lengths),
            "mean": sum(lengths) / len(lengths),
        }

    def get_most_visited_nodes(self, top_n: int = 10) -> list[tuple[str, int]]:
        """
        Get the most frequently visited nodes across all trajectories.

        Args:
            top_n: Number of top nodes to return

        Returns:
            List of (node_id, visit_count) tuples
        """
        all_visits: Counter = Counter()
        for trajectory in self._trajectories:
            all_visits.update(trajectory.path)
        return all_visits.most_common(top_n)

    def get_capture_paths(self, virtue_id: str) -> list[list[str]]:
        """
        Get all paths that were captured by a specific virtue.

        Args:
            virtue_id: The virtue ID

        Returns:
            List of paths (each path is a list of node IDs)
        """
        return [
            t.path for t in self._trajectories
            if t.captured_by == virtue_id
        ]

    def get_escape_paths(self) -> list[list[str]]:
        """
        Get all paths that escaped without capture.

        Returns:
            List of escaped paths
        """
        return [
            t.path for t in self._trajectories
            if t.escaped
        ]

    def analyze_escape_patterns(self) -> dict:
        """
        Analyze patterns in escaped trajectories.

        Returns:
            Dict with escape pattern analysis
        """
        escaped = [t for t in self._trajectories if t.escaped]
        if not escaped:
            return {"count": 0, "patterns": []}

        # Find common final regions
        final_nodes: Counter = Counter()
        for t in escaped:
            # Look at final 10% of path
            final_portion = t.path[-max(1, len(t.path) // 10):]
            final_nodes.update(final_portion)

        return {
            "count": len(escaped),
            "common_final_nodes": final_nodes.most_common(5),
            "avg_path_length": sum(len(t.path) for t in escaped) / len(escaped),
        }

    def get_all_trajectories(self) -> list[Trajectory]:
        """Get all recorded trajectories."""
        return list(self._trajectories)

    def get_recent_trajectories(self, n: int = 10) -> list[Trajectory]:
        """
        Get the most recent trajectories.

        Args:
            n: Number of recent trajectories

        Returns:
            List of recent trajectories
        """
        return self._trajectories[-n:]

    def clear(self) -> None:
        """Clear all recorded trajectories."""
        self._trajectories.clear()
        self._captures_by_virtue.clear()
        self._escapes = 0
        self._total_capture_time = 0

    def get_summary(self) -> dict:
        """
        Get a summary of all tracking data.

        Returns:
            Dict with comprehensive tracking summary
        """
        return {
            "total_trajectories": len(self._trajectories),
            "capture_rate": self.get_capture_rate(),
            "escape_rate": self.get_escape_rate(),
            "average_capture_time": self.get_average_capture_time(),
            "per_virtue_captures": self.get_per_virtue_captures(),
            "length_stats": self.get_trajectory_length_stats(),
            "most_visited": self.get_most_visited_nodes(5),
        }
