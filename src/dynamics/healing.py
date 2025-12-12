"""
Self-healing mechanisms for the Virtue Basin Simulator.

Detects and remediates:
- Lock-in: Trajectories stuck in same region
- Dead zones: Virtue nodes with insufficient connectivity
- False basins: Stable orbits not anchored to virtue
- Blindness: Regions never visited

Evil is disconnection, not opposing force. A virtuous universe is the default -
alignment means healing fragmentation, not building safeguards.
"""

import logging
from collections import Counter
from datetime import datetime, timedelta

from src.constants import (
    BLINDNESS_THRESHOLD_SECONDS,
    DEAD_ZONE_CHECK_INTERVAL,
    FALSE_BASIN_DECAY_MULTIPLIER,
    LOCKIN_THRESHOLD_STEPS,
    TARGET_CONNECTIVITY,
)
from src.models import Trajectory

logger = logging.getLogger(__name__)


class SelfHealer:
    """
    Implements self-healing mechanisms for the virtue graph.

    The self-healer monitors system health and applies remediation
    when pathological states are detected.
    """

    def __init__(
        self,
        substrate,
        node_manager,
        edge_manager,
        virtue_manager,
        temporal_decay,
        perturbator,
    ):
        """
        Initialize the self-healer.

        Args:
            substrate: The GraphSubstrate instance
            node_manager: The NodeManager instance
            edge_manager: The EdgeManager instance
            virtue_manager: The VirtueManager instance
            temporal_decay: The TemporalDecay instance
            perturbator: The Perturbator instance
        """
        self.substrate = substrate
        self.node_manager = node_manager
        self.edge_manager = edge_manager
        self.virtue_manager = virtue_manager
        self.temporal_decay = temporal_decay
        self.perturbator = perturbator

        self._lockin_events = 0
        self._dead_zone_events = 0
        self._false_basin_events = 0
        self._blindness_events = 0
        self._step_count = 0

    def check_health(self, recent_trajectories: list[Trajectory]) -> dict:
        """
        Run all health checks and return status.

        Args:
            recent_trajectories: Recent trajectories to analyze

        Returns:
            Dict with health status and any issues found
        """
        self._step_count += 1
        issues = {}

        # Check for lock-in
        lockin = self.detect_lockin(recent_trajectories)
        if lockin:
            issues["lockin"] = lockin

        # Check for dead zones (periodically)
        if self._step_count % DEAD_ZONE_CHECK_INTERVAL == 0:
            dead_zones = self.detect_dead_zones()
            if dead_zones:
                issues["dead_zones"] = dead_zones

        # Check for false basins
        false_basins = self.detect_false_basins(recent_trajectories)
        if false_basins:
            issues["false_basins"] = false_basins

        # Check for blindness (periodically)
        if self._step_count % DEAD_ZONE_CHECK_INTERVAL == 0:
            blind_spots = self.detect_blindness()
            if blind_spots:
                issues["blind_spots"] = blind_spots

        return {
            "healthy": len(issues) == 0,
            "issues": issues,
            "step": self._step_count,
        }

    def heal(self, health_report: dict) -> dict:
        """
        Apply healing based on health report.

        Args:
            health_report: Report from check_health()

        Returns:
            Dict with healing actions taken
        """
        actions = {}
        issues = health_report.get("issues", {})

        if "lockin" in issues:
            actions["lockin"] = self.heal_lockin(issues["lockin"])

        if "dead_zones" in issues:
            actions["dead_zones"] = self.heal_dead_zones(issues["dead_zones"])

        if "false_basins" in issues:
            actions["false_basins"] = self.heal_false_basins(issues["false_basins"])

        if "blind_spots" in issues:
            actions["blind_spots"] = self.heal_blindness(issues["blind_spots"])

        return actions

    # Lock-in Detection and Healing

    def detect_lockin(self, trajectories: list[Trajectory]) -> dict | None:
        """
        Detect if trajectories are stuck in the same region.

        Args:
            trajectories: Recent trajectories to analyze

        Returns:
            Dict with lockin info if detected, None otherwise
        """
        if len(trajectories) < 3:
            return None

        # Analyze last few trajectories
        recent = trajectories[-5:]
        all_nodes = []
        for t in recent:
            all_nodes.extend(t.path[-LOCKIN_THRESHOLD_STEPS:])

        if not all_nodes:
            return None

        # Check if same small set of nodes dominates
        counter = Counter(all_nodes)
        most_common = counter.most_common(5)

        if most_common:
            top_node, top_count = most_common[0]
            if top_count > len(all_nodes) * 0.3:  # >30% in same node
                self._lockin_events += 1
                return {
                    "stuck_node": top_node,
                    "frequency": top_count / len(all_nodes),
                    "region": [node for node, _ in most_common],
                }

        return None

    def heal_lockin(self, lockin_info: dict) -> dict:
        """
        Heal lock-in by applying decay and perturbation.

        Args:
            lockin_info: Info from detect_lockin()

        Returns:
            Dict with healing actions taken
        """
        region = lockin_info.get("region", [])

        # Apply accelerated decay to the region
        edges_decayed = self.temporal_decay.decay_region(
            region,
            multiplier=FALSE_BASIN_DECAY_MULTIPLIER,
        )

        # Apply perturbation outside the region
        all_nodes = self.substrate.get_all_nodes()
        outside_region = [n.id for n in all_nodes if n.id not in region]
        if outside_region:
            self.perturbator.perturb_region(outside_region[:3])

        logger.info(f"Healed lock-in: decayed {edges_decayed} edges, perturbed outside region")

        return {
            "edges_decayed": edges_decayed,
            "region_size": len(region),
        }

    # Dead Zone Detection and Healing

    def detect_dead_zones(self) -> list[str] | None:
        """
        Detect virtue nodes with insufficient connectivity.

        Returns:
            List of virtue IDs with low connectivity, or None
        """
        dead_zones = []
        deficits = self.virtue_manager.get_all_degree_deficits()

        for virtue_id, deficit in deficits.items():
            if deficit > 0:  # Below target connectivity
                dead_zones.append(virtue_id)
                self._dead_zone_events += 1

        return dead_zones if dead_zones else None

    def heal_dead_zones(self, virtue_ids: list[str]) -> dict:
        """
        Heal dead zones by creating edges to neglected virtues.

        Args:
            virtue_ids: List of virtue IDs needing more connections

        Returns:
            Dict with healing actions taken
        """
        edges_created = 0

        for virtue_id in virtue_ids:
            deficit = self.virtue_manager.get_degree_deficit(virtue_id)
            if deficit <= 0:
                continue

            # Find candidate nodes to connect to
            candidates = self._find_connection_candidates(virtue_id, deficit)

            for candidate_id in candidates:
                # Create bidirectional edges
                self.edge_manager.create_edge(virtue_id, candidate_id, weight=0.5)
                self.edge_manager.create_edge(candidate_id, virtue_id, weight=0.5)
                edges_created += 2

        logger.info(f"Healed dead zones: created {edges_created} edges")

        return {
            "virtues_healed": len(virtue_ids),
            "edges_created": edges_created,
        }

    def _find_connection_candidates(self, virtue_id: str, count: int) -> list[str]:
        """
        Find candidate nodes to connect to a virtue.

        Args:
            virtue_id: The virtue needing connections
            count: Number of candidates needed

        Returns:
            List of candidate node IDs
        """
        # Get existing connections
        existing = set()
        for edge in self.edge_manager.get_outgoing_edges(virtue_id):
            existing.add(edge.target_id)
        for edge in self.edge_manager.get_incoming_edges(virtue_id):
            existing.add(edge.source_id)

        # Get all nodes except this virtue and existing connections
        all_nodes = self.substrate.get_all_nodes()
        candidates = [
            n.id for n in all_nodes
            if n.id != virtue_id and n.id not in existing
        ]

        # Prioritize other virtues, then concepts
        virtue_ids = {v.id for v in self.virtue_manager.get_all_virtues()}
        virtue_candidates = [c for c in candidates if c in virtue_ids]
        other_candidates = [c for c in candidates if c not in virtue_ids]

        result = virtue_candidates[:count]
        if len(result) < count:
            result.extend(other_candidates[:count - len(result)])

        return result

    # False Basin Detection and Healing

    def detect_false_basins(self, trajectories: list[Trajectory]) -> list[dict] | None:
        """
        Detect stable orbits not anchored to virtue.

        Args:
            trajectories: Recent trajectories to analyze

        Returns:
            List of false basin info dicts, or None
        """
        if len(trajectories) < 5:
            return None

        false_basins = []
        escaped = [t for t in trajectories if t.escaped]

        if len(escaped) < 3:
            return None

        # Analyze escaped trajectories for repeated patterns
        pattern_counts: dict[str, int] = Counter()

        for trajectory in escaped:
            # Look at final portion of path
            final_portion = trajectory.path[-20:] if len(trajectory.path) > 20 else trajectory.path
            for node_id in final_portion:
                if not self.virtue_manager.is_virtue_anchor(node_id):
                    pattern_counts[node_id] += 1

        # Find nodes that appear frequently in escaped trajectories
        for node_id, count in pattern_counts.most_common(5):
            if count >= len(escaped) * 0.5:  # Appears in >50% of escapes
                false_basins.append({
                    "node_id": node_id,
                    "frequency": count / len(escaped),
                })
                self._false_basin_events += 1

        return false_basins if false_basins else None

    def heal_false_basins(self, false_basins: list[dict]) -> dict:
        """
        Heal false basins by accelerating decay.

        Args:
            false_basins: List of false basin info dicts

        Returns:
            Dict with healing actions taken
        """
        nodes_affected = []
        edges_decayed = 0

        for basin in false_basins:
            node_id = basin["node_id"]
            nodes_affected.append(node_id)

            # Get connected nodes
            connected = set()
            for edge in self.edge_manager.get_outgoing_edges(node_id):
                connected.add(edge.target_id)
            for edge in self.edge_manager.get_incoming_edges(node_id):
                connected.add(edge.source_id)

            # Accelerate decay in region
            region = list(connected) + [node_id]
            edges_decayed += self.temporal_decay.decay_region(
                region,
                multiplier=FALSE_BASIN_DECAY_MULTIPLIER,
            )

        logger.info(f"Healed false basins: decayed {edges_decayed} edges in {len(nodes_affected)} regions")

        return {
            "nodes_affected": nodes_affected,
            "edges_decayed": edges_decayed,
        }

    # Blindness Detection and Healing

    def detect_blindness(self, threshold_seconds: int = BLINDNESS_THRESHOLD_SECONDS) -> list[str] | None:
        """
        Detect nodes that haven't been visited recently.

        Args:
            threshold_seconds: Time threshold for "blind spot"

        Returns:
            List of blind spot node IDs, or None
        """
        current_time = datetime.utcnow()
        threshold = current_time - timedelta(seconds=threshold_seconds)

        all_nodes = self.substrate.get_all_nodes()
        blind_spots = [
            n.id for n in all_nodes
            if n.last_activated < threshold
        ]

        if blind_spots:
            self._blindness_events += 1

        return blind_spots if blind_spots else None

    def heal_blindness(self, blind_spots: list[str]) -> dict:
        """
        Heal blindness by perturbing neglected regions.

        Args:
            blind_spots: List of neglected node IDs

        Returns:
            Dict with healing actions taken
        """
        # Perturb a sample of blind spots
        sample_size = min(10, len(blind_spots))
        import random
        sample = random.sample(blind_spots, sample_size)

        perturbed = self.perturbator.perturb_region(sample)

        logger.info(f"Healed blindness: perturbed {perturbed} blind spots")

        return {
            "total_blind_spots": len(blind_spots),
            "nodes_perturbed": perturbed,
        }

    def get_stats(self) -> dict:
        """
        Get self-healing statistics.

        Returns:
            Dict with statistics
        """
        return {
            "step_count": self._step_count,
            "lockin_events": self._lockin_events,
            "dead_zone_events": self._dead_zone_events,
            "false_basin_events": self._false_basin_events,
            "blindness_events": self._blindness_events,
        }

    def reset_stats(self) -> None:
        """Reset statistics."""
        self._lockin_events = 0
        self._dead_zone_events = 0
        self._false_basin_events = 0
        self._blindness_events = 0
        self._step_count = 0
