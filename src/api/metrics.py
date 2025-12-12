"""
Metrics collection and export for the Virtue Basin Simulator.

Provides metrics for monitoring simulation health and progress.
"""

import logging
from datetime import datetime
from typing import Any

logger = logging.getLogger(__name__)


class MetricsCollector:
    """
    Collects and exports metrics from the simulation.

    Tracks:
    - Evolution progress (fitness over time)
    - Basin coverage
    - Edge statistics
    - Healing events
    """

    def __init__(self):
        """Initialize the metrics collector."""
        self._metrics: dict[str, list[dict]] = {
            "fitness": [],
            "coverage": [],
            "edges": [],
            "healing": [],
            "trajectories": [],
        }
        self._start_time = datetime.utcnow()

    def record_fitness(
        self,
        generation: int,
        best: float,
        mean: float,
        min_fitness: float,
        max_fitness: float,
    ) -> None:
        """
        Record fitness metrics for a generation.

        Args:
            generation: Generation number
            best: Best fitness
            mean: Mean fitness
            min_fitness: Minimum fitness
            max_fitness: Maximum fitness
        """
        self._metrics["fitness"].append({
            "timestamp": datetime.utcnow().isoformat(),
            "generation": generation,
            "best": best,
            "mean": mean,
            "min": min_fitness,
            "max": max_fitness,
        })

    def record_coverage(
        self,
        virtue_captures: dict[str, int],
        total_trajectories: int,
    ) -> None:
        """
        Record basin coverage metrics.

        Args:
            virtue_captures: Captures per virtue
            total_trajectories: Total trajectories tested
        """
        self._metrics["coverage"].append({
            "timestamp": datetime.utcnow().isoformat(),
            "virtue_captures": virtue_captures,
            "total_trajectories": total_trajectories,
            "coverage_rate": len([v for v, c in virtue_captures.items() if c > 0]) / 19,
        })

    def record_edges(
        self,
        total_edges: int,
        mean_weight: float,
        virtue_degrees: dict[str, int],
    ) -> None:
        """
        Record edge statistics.

        Args:
            total_edges: Total edge count
            mean_weight: Mean edge weight
            virtue_degrees: Degrees per virtue
        """
        self._metrics["edges"].append({
            "timestamp": datetime.utcnow().isoformat(),
            "total_edges": total_edges,
            "mean_weight": mean_weight,
            "virtue_degrees": virtue_degrees,
            "min_virtue_degree": min(virtue_degrees.values()) if virtue_degrees else 0,
            "max_virtue_degree": max(virtue_degrees.values()) if virtue_degrees else 0,
        })

    def record_healing(
        self,
        event_type: str,
        details: dict,
    ) -> None:
        """
        Record a healing event.

        Args:
            event_type: Type of healing event
            details: Event details
        """
        self._metrics["healing"].append({
            "timestamp": datetime.utcnow().isoformat(),
            "event_type": event_type,
            "details": details,
        })

    def record_trajectory(
        self,
        captured: bool,
        captured_by: str | None,
        path_length: int,
    ) -> None:
        """
        Record trajectory metrics.

        Args:
            captured: Whether trajectory was captured
            captured_by: Virtue that captured (if any)
            path_length: Length of trajectory path
        """
        self._metrics["trajectories"].append({
            "timestamp": datetime.utcnow().isoformat(),
            "captured": captured,
            "captured_by": captured_by,
            "path_length": path_length,
        })

    def get_metrics(self, metric_type: str | None = None) -> dict:
        """
        Get recorded metrics.

        Args:
            metric_type: Optional type filter

        Returns:
            Dict with metrics
        """
        if metric_type:
            return {metric_type: self._metrics.get(metric_type, [])}
        return dict(self._metrics)

    def get_summary(self) -> dict:
        """
        Get a summary of all metrics.

        Returns:
            Dict with metric summary
        """
        fitness = self._metrics["fitness"]
        trajectories = self._metrics["trajectories"]

        summary = {
            "start_time": self._start_time.isoformat(),
            "elapsed_seconds": (datetime.utcnow() - self._start_time).total_seconds(),
            "generations_recorded": len(fitness),
            "trajectories_recorded": len(trajectories),
            "healing_events": len(self._metrics["healing"]),
        }

        if fitness:
            summary["best_fitness_ever"] = max(f["best"] for f in fitness)
            summary["latest_mean_fitness"] = fitness[-1]["mean"]

        if trajectories:
            captured = sum(1 for t in trajectories if t["captured"])
            summary["overall_capture_rate"] = captured / len(trajectories)

        return summary

    def export_prometheus(self) -> str:
        """
        Export metrics in Prometheus format.

        Returns:
            Prometheus-formatted metrics string
        """
        lines = []

        # Fitness metrics
        if self._metrics["fitness"]:
            latest = self._metrics["fitness"][-1]
            lines.append(f'vbs_fitness_best{{}} {latest["best"]}')
            lines.append(f'vbs_fitness_mean{{}} {latest["mean"]}')
            lines.append(f'vbs_generation{{}} {latest["generation"]}')

        # Coverage metrics
        if self._metrics["coverage"]:
            latest = self._metrics["coverage"][-1]
            lines.append(f'vbs_coverage_rate{{}} {latest["coverage_rate"]}')
            lines.append(f'vbs_total_trajectories{{}} {latest["total_trajectories"]}')

        # Edge metrics
        if self._metrics["edges"]:
            latest = self._metrics["edges"][-1]
            lines.append(f'vbs_total_edges{{}} {latest["total_edges"]}')
            lines.append(f'vbs_mean_edge_weight{{}} {latest["mean_weight"]}')

        # Healing events
        healing_count = len(self._metrics["healing"])
        lines.append(f'vbs_healing_events_total{{}} {healing_count}')

        return "\n".join(lines)

    def clear(self) -> None:
        """Clear all metrics."""
        for key in self._metrics:
            self._metrics[key].clear()
        self._start_time = datetime.utcnow()
