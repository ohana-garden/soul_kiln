"""
Moral Geometry Analysis.

Detects structural patterns in the virtue graph topology.
The "moral geometry" is the shape of ethical space - how virtues relate,
cluster, and form basins of attraction for thoughts.

Patterns detected:
1. Triads - tightly coupled virtue clusters
2. Bridge nodes - virtues connecting different clusters
3. Basin topology - the shape of each virtue's attraction region
4. Resonance patterns - virtues that co-activate
5. Geodesics - shortest moral paths between concepts
"""

import logging
from collections import defaultdict
from dataclasses import dataclass, field
from typing import Any

import numpy as np

logger = logging.getLogger(__name__)


@dataclass
class VirtueTriad:
    """Three virtues with high mutual affinity."""

    virtues: tuple[str, str, str]
    total_affinity: float  # Sum of pairwise affinities
    cluster: str | None = None  # Common cluster if any
    is_bridge_triad: bool = False  # Spans multiple clusters

    def to_dict(self) -> dict:
        return {
            "virtues": self.virtues,
            "total_affinity": self.total_affinity,
            "cluster": self.cluster,
            "is_bridge_triad": self.is_bridge_triad,
        }


@dataclass
class BridgeNode:
    """A virtue that connects different clusters."""

    virtue_id: str
    clusters_connected: list[str]
    bridge_score: float  # How much it bridges (betweenness-like)
    affinity_balance: dict[str, float]  # Affinity to each cluster

    def to_dict(self) -> dict:
        return {
            "virtue_id": self.virtue_id,
            "clusters_connected": self.clusters_connected,
            "bridge_score": self.bridge_score,
            "affinity_balance": self.affinity_balance,
        }


@dataclass
class BasinTopology:
    """The shape of a virtue's attraction basin."""

    virtue_id: str
    cluster: str
    direct_concepts: int  # Concepts directly connected
    reachable_concepts: int  # Concepts within 2 hops
    basin_volume: float  # Estimated volume based on activation simulations
    neighboring_virtues: list[str]
    affinity_sum: float  # Total edge weight to this virtue

    def to_dict(self) -> dict:
        return {
            "virtue_id": self.virtue_id,
            "cluster": self.cluster,
            "direct_concepts": self.direct_concepts,
            "reachable_concepts": self.reachable_concepts,
            "basin_volume": self.basin_volume,
            "neighboring_virtues": self.neighboring_virtues,
            "affinity_sum": self.affinity_sum,
        }


@dataclass
class ResonancePattern:
    """Virtues that tend to co-activate."""

    primary: str
    resonant: list[str]
    correlation_matrix: dict[str, float]  # Pairwise correlations
    pattern_type: str  # "harmonic", "cascade", "mutual"

    def to_dict(self) -> dict:
        return {
            "primary": self.primary,
            "resonant": self.resonant,
            "correlation_matrix": self.correlation_matrix,
            "pattern_type": self.pattern_type,
        }


@dataclass
class MoralGeodesic:
    """Shortest moral path between two points."""

    start: str
    end: str
    path: list[str]
    total_distance: float
    waypoint_virtues: list[str]

    def to_dict(self) -> dict:
        return {
            "start": self.start,
            "end": self.end,
            "path": self.path,
            "total_distance": self.total_distance,
            "waypoint_virtues": self.waypoint_virtues,
        }


@dataclass
class GeometrySnapshot:
    """Complete snapshot of moral geometry state."""

    triads: list[VirtueTriad]
    bridges: list[BridgeNode]
    basins: dict[str, BasinTopology]
    resonance_patterns: list[ResonancePattern]
    cluster_cohesion: dict[str, float]
    global_connectivity: float

    def to_dict(self) -> dict:
        return {
            "triads": [t.to_dict() for t in self.triads],
            "bridges": [b.to_dict() for b in self.bridges],
            "basins": {k: v.to_dict() for k, v in self.basins.items()},
            "resonance_patterns": [r.to_dict() for r in self.resonance_patterns],
            "cluster_cohesion": self.cluster_cohesion,
            "global_connectivity": self.global_connectivity,
        }


class MoralGeometryAnalyzer:
    """
    Analyzes structural patterns in the virtue graph.

    The moral geometry is not static - it evolves as edges strengthen
    and new concepts are added. This analyzer provides tools for
    understanding the current state and detecting significant patterns.
    """

    # Virtue cluster membership (from tiers.py)
    VIRTUE_CLUSTERS = {
        "V01": "foundation",
        "V02": "core",
        "V03": "relational",
        "V04": "relational",
        "V05": "personal",
        "V06": "relational",
        "V07": "personal",
        "V08": "personal",
        "V09": "relational",
        "V10": "personal",
        "V11": "transcendent",
        "V12": "core",
        "V13": "relational",
        "V14": "transcendent",
        "V15": "core",
        "V16": "transcendent",
        "V17": "transcendent",
        "V18": "transcendent",
        "V19": "transcendent",
    }

    # Known natural affinities (from anchors.py)
    NATURAL_AFFINITIES = {
        "V01": ["V02", "V08", "V12"],
        "V02": ["V01", "V12", "V03"],
        "V03": ["V04", "V15", "V16"],
        "V04": ["V03", "V13", "V18"],
        "V05": ["V10", "V14", "V17"],
        "V06": ["V09", "V13", "V07"],
        "V07": ["V06", "V16", "V17"],
        "V08": ["V01", "V19", "V18"],
        "V09": ["V06", "V13", "V19"],
        "V10": ["V05", "V14", "V11"],
        "V11": ["V14", "V12", "V16"],
        "V12": ["V02", "V01", "V11"],
        "V13": ["V09", "V04", "V18"],
        "V14": ["V11", "V10", "V15"],
        "V15": ["V03", "V14", "V16"],
        "V16": ["V03", "V07", "V17"],
        "V17": ["V16", "V05", "V11"],
        "V18": ["V04", "V13", "V19"],
        "V19": ["V08", "V09", "V18"],
    }

    def __init__(self, substrate=None):
        """
        Initialize the analyzer.

        Args:
            substrate: The graph substrate for accessing current state
        """
        self._substrate = substrate
        self._cached_geometry: GeometrySnapshot | None = None
        self._activation_history: list[dict[str, float]] = []

    def set_substrate(self, substrate) -> None:
        """Set the graph substrate."""
        self._substrate = substrate
        self._cached_geometry = None

    def record_activation(self, activation_map: dict[str, float]) -> None:
        """Record activation state for resonance analysis."""
        self._activation_history.append(activation_map.copy())
        # Keep last 100 states
        if len(self._activation_history) > 100:
            self._activation_history.pop(0)

    def analyze(self) -> GeometrySnapshot:
        """
        Perform full geometry analysis.

        Returns:
            Complete GeometrySnapshot
        """
        triads = self._find_triads()
        bridges = self._find_bridges()
        basins = self._compute_basins()
        resonance = self._analyze_resonance()
        cohesion = self._compute_cluster_cohesion()
        connectivity = self._compute_global_connectivity()

        self._cached_geometry = GeometrySnapshot(
            triads=triads,
            bridges=bridges,
            basins=basins,
            resonance_patterns=resonance,
            cluster_cohesion=cohesion,
            global_connectivity=connectivity,
        )

        return self._cached_geometry

    def _find_triads(self) -> list[VirtueTriad]:
        """Find all virtue triads with high mutual affinity."""
        triads = []
        virtue_ids = list(self.VIRTUE_CLUSTERS.keys())

        # Build affinity matrix
        affinity_matrix = self._get_affinity_matrix()

        # Find all triads above threshold
        for i, v1 in enumerate(virtue_ids):
            for j, v2 in enumerate(virtue_ids[i + 1 :], i + 1):
                for k, v3 in enumerate(virtue_ids[j + 1 :], j + 1):
                    # Sum pairwise affinities
                    total = (
                        affinity_matrix.get((v1, v2), 0)
                        + affinity_matrix.get((v2, v3), 0)
                        + affinity_matrix.get((v1, v3), 0)
                    )

                    if total > 1.0:  # Threshold for meaningful triad
                        # Determine cluster
                        clusters = {
                            self.VIRTUE_CLUSTERS[v1],
                            self.VIRTUE_CLUSTERS[v2],
                            self.VIRTUE_CLUSTERS[v3],
                        }

                        common_cluster = (
                            list(clusters)[0] if len(clusters) == 1 else None
                        )
                        is_bridge = len(clusters) > 1

                        triads.append(
                            VirtueTriad(
                                virtues=(v1, v2, v3),
                                total_affinity=total,
                                cluster=common_cluster,
                                is_bridge_triad=is_bridge,
                            )
                        )

        # Sort by affinity
        triads.sort(key=lambda t: t.total_affinity, reverse=True)
        return triads[:20]  # Top 20 triads

    def _find_bridges(self) -> list[BridgeNode]:
        """Find virtues that bridge different clusters."""
        bridges = []
        affinity_matrix = self._get_affinity_matrix()

        for virtue_id, cluster in self.VIRTUE_CLUSTERS.items():
            # Compute affinity to each cluster
            cluster_affinities: dict[str, float] = defaultdict(float)

            for other_id, other_cluster in self.VIRTUE_CLUSTERS.items():
                if virtue_id != other_id:
                    affinity = affinity_matrix.get(
                        (virtue_id, other_id), 0
                    ) + affinity_matrix.get((other_id, virtue_id), 0)
                    cluster_affinities[other_cluster] += affinity

            # Is this a bridge? Has significant affinity to other clusters
            own_cluster_affinity = cluster_affinities.get(cluster, 0)
            other_affinities = {
                k: v for k, v in cluster_affinities.items() if k != cluster
            }

            if other_affinities:
                max_other = max(other_affinities.values())
                # Bridge score: ratio of external to internal affinity
                if own_cluster_affinity > 0:
                    bridge_score = max_other / own_cluster_affinity
                else:
                    bridge_score = max_other

                # Significant bridges have score > 0.5
                if bridge_score > 0.3:
                    connected = [
                        k
                        for k, v in other_affinities.items()
                        if v > max_other * 0.5
                    ]
                    connected.append(cluster)

                    bridges.append(
                        BridgeNode(
                            virtue_id=virtue_id,
                            clusters_connected=sorted(connected),
                            bridge_score=bridge_score,
                            affinity_balance=dict(cluster_affinities),
                        )
                    )

        bridges.sort(key=lambda b: b.bridge_score, reverse=True)
        return bridges

    def _compute_basins(self) -> dict[str, BasinTopology]:
        """Compute basin topology for each virtue."""
        basins = {}

        for virtue_id, cluster in self.VIRTUE_CLUSTERS.items():
            # Get direct and reachable concepts from substrate
            direct_concepts = 0
            reachable_concepts = 0
            affinity_sum = 0.0
            neighboring_virtues = []

            if self._substrate:
                # Get edges to this virtue
                try:
                    edges = self._substrate.get_incoming_edges(virtue_id)
                    for edge in edges:
                        if edge.source_id.startswith("V"):
                            neighboring_virtues.append(edge.source_id)
                        else:
                            direct_concepts += 1
                        affinity_sum += edge.weight
                except AttributeError:
                    pass

                # Estimate reachable (2-hop)
                reachable_concepts = direct_concepts * 3  # Rough estimate

            else:
                # Use natural affinities
                neighboring_virtues = self.NATURAL_AFFINITIES.get(virtue_id, [])
                affinity_sum = len(neighboring_virtues) * 0.5

            # Basin volume is a function of connectivity and threshold
            # Higher threshold = smaller effective basin
            from ..virtues.tiers import get_base_threshold

            threshold = get_base_threshold(virtue_id)
            basin_volume = affinity_sum * (1.0 - threshold + 0.5)

            basins[virtue_id] = BasinTopology(
                virtue_id=virtue_id,
                cluster=cluster,
                direct_concepts=direct_concepts,
                reachable_concepts=reachable_concepts,
                basin_volume=basin_volume,
                neighboring_virtues=neighboring_virtues,
                affinity_sum=affinity_sum,
            )

        return basins

    def _analyze_resonance(self) -> list[ResonancePattern]:
        """Analyze which virtues tend to co-activate."""
        patterns = []

        if len(self._activation_history) < 10:
            # Not enough data - use structural resonance
            return self._structural_resonance()

        # Compute correlation from activation history
        virtue_ids = list(self.VIRTUE_CLUSTERS.keys())
        n = len(virtue_ids)

        # Build activation matrix
        activations = np.zeros((len(self._activation_history), n))
        for i, state in enumerate(self._activation_history):
            for j, vid in enumerate(virtue_ids):
                activations[i, j] = state.get(vid, 0.0)

        # Compute correlation matrix
        if activations.std() > 0:
            corr_matrix = np.corrcoef(activations.T)
        else:
            corr_matrix = np.eye(n)

        # Find resonant pairs
        for i, v1 in enumerate(virtue_ids):
            resonant = []
            correlations = {}

            for j, v2 in enumerate(virtue_ids):
                if i != j and corr_matrix[i, j] > 0.5:
                    resonant.append(v2)
                    correlations[v2] = float(corr_matrix[i, j])

            if resonant:
                # Determine pattern type
                same_cluster = all(
                    self.VIRTUE_CLUSTERS[r] == self.VIRTUE_CLUSTERS[v1]
                    for r in resonant
                )
                pattern_type = "harmonic" if same_cluster else "cascade"

                patterns.append(
                    ResonancePattern(
                        primary=v1,
                        resonant=resonant,
                        correlation_matrix=correlations,
                        pattern_type=pattern_type,
                    )
                )

        return patterns

    def _structural_resonance(self) -> list[ResonancePattern]:
        """Compute resonance from structure when no activation history."""
        patterns = []

        for virtue_id in self.VIRTUE_CLUSTERS:
            affinities = self.NATURAL_AFFINITIES.get(virtue_id, [])
            if affinities:
                correlations = {v: 0.5 for v in affinities}
                patterns.append(
                    ResonancePattern(
                        primary=virtue_id,
                        resonant=affinities,
                        correlation_matrix=correlations,
                        pattern_type="structural",
                    )
                )

        return patterns

    def _compute_cluster_cohesion(self) -> dict[str, float]:
        """Compute internal cohesion of each cluster."""
        cohesion = {}
        affinity_matrix = self._get_affinity_matrix()

        # Group virtues by cluster
        clusters: dict[str, list[str]] = defaultdict(list)
        for vid, cluster in self.VIRTUE_CLUSTERS.items():
            clusters[cluster].append(vid)

        for cluster, virtues in clusters.items():
            if len(virtues) < 2:
                cohesion[cluster] = 1.0
                continue

            # Sum internal affinities
            internal_sum = 0.0
            pair_count = 0

            for i, v1 in enumerate(virtues):
                for v2 in virtues[i + 1 :]:
                    internal_sum += affinity_matrix.get((v1, v2), 0)
                    internal_sum += affinity_matrix.get((v2, v1), 0)
                    pair_count += 1

            cohesion[cluster] = internal_sum / pair_count if pair_count > 0 else 0.0

        return cohesion

    def _compute_global_connectivity(self) -> float:
        """Compute overall graph connectivity."""
        affinity_matrix = self._get_affinity_matrix()
        total = sum(affinity_matrix.values())
        max_possible = len(self.VIRTUE_CLUSTERS) * (len(self.VIRTUE_CLUSTERS) - 1) / 2
        return total / max_possible if max_possible > 0 else 0.0

    def _get_affinity_matrix(self) -> dict[tuple[str, str], float]:
        """Get affinity matrix from substrate or natural affinities."""
        matrix: dict[tuple[str, str], float] = {}

        if self._substrate:
            # Get from substrate
            try:
                edges = self._substrate.get_all_edges()
                for edge in edges:
                    if edge.source_id.startswith("V") and edge.target_id.startswith(
                        "V"
                    ):
                        matrix[(edge.source_id, edge.target_id)] = edge.weight
            except AttributeError:
                pass

        # Fall back to / supplement with natural affinities
        for v1, affinities in self.NATURAL_AFFINITIES.items():
            for v2 in affinities:
                key = (v1, v2)
                if key not in matrix:
                    matrix[key] = 0.5  # Default affinity weight

        return matrix

    def find_geodesic(self, start: str, end: str) -> MoralGeodesic | None:
        """
        Find shortest moral path between two nodes.

        Uses Dijkstra's algorithm on the virtue graph.
        """
        if not self._substrate:
            return None

        # Simple BFS for now
        from collections import deque

        visited = {start}
        queue = deque([(start, [start], 0.0)])
        virtue_ids = set(self.VIRTUE_CLUSTERS.keys())

        while queue:
            current, path, distance = queue.popleft()

            if current == end:
                waypoints = [n for n in path if n in virtue_ids]
                return MoralGeodesic(
                    start=start,
                    end=end,
                    path=path,
                    total_distance=distance,
                    waypoint_virtues=waypoints,
                )

            try:
                edges = self._substrate.get_outgoing_edges(current)
                for edge in edges:
                    if edge.target_id not in visited:
                        visited.add(edge.target_id)
                        new_dist = distance + (1.0 - edge.weight)
                        queue.append(
                            (edge.target_id, path + [edge.target_id], new_dist)
                        )
            except AttributeError:
                break

        return None

    def get_virtue_neighborhood(self, virtue_id: str, depth: int = 2) -> dict:
        """
        Get the local neighborhood around a virtue.

        Returns subgraph data for visualization.
        """
        if virtue_id not in self.VIRTUE_CLUSTERS:
            return {"nodes": [], "edges": []}

        nodes = []
        edges = []
        visited = set()

        def traverse(node_id: str, current_depth: int):
            if node_id in visited or current_depth > depth:
                return
            visited.add(node_id)

            is_virtue = node_id in self.VIRTUE_CLUSTERS
            nodes.append(
                {
                    "id": node_id,
                    "type": "virtue" if is_virtue else "concept",
                    "cluster": self.VIRTUE_CLUSTERS.get(node_id),
                    "depth": current_depth,
                }
            )

            if self._substrate and current_depth < depth:
                try:
                    for edge in self._substrate.get_outgoing_edges(node_id):
                        edges.append(
                            {
                                "source": node_id,
                                "target": edge.target_id,
                                "weight": edge.weight,
                            }
                        )
                        traverse(edge.target_id, current_depth + 1)
                except AttributeError:
                    pass

        traverse(virtue_id, 0)
        return {"nodes": nodes, "edges": edges}

    def get_pattern_summary(self) -> dict:
        """Get a summary of detected patterns."""
        if not self._cached_geometry:
            self.analyze()

        geo = self._cached_geometry

        return {
            "strongest_triads": [
                {"virtues": t.virtues, "affinity": t.total_affinity}
                for t in geo.triads[:5]
            ],
            "key_bridges": [
                {"virtue": b.virtue_id, "connects": b.clusters_connected}
                for b in geo.bridges[:5]
            ],
            "largest_basins": sorted(
                [
                    {"virtue": k, "volume": v.basin_volume}
                    for k, v in geo.basins.items()
                ],
                key=lambda x: x["volume"],
                reverse=True,
            )[:5],
            "cluster_health": geo.cluster_cohesion,
            "global_connectivity": geo.global_connectivity,
        }


# Singleton
_analyzer: MoralGeometryAnalyzer | None = None


def get_geometry_analyzer() -> MoralGeometryAnalyzer:
    """Get the singleton geometry analyzer."""
    global _analyzer
    if _analyzer is None:
        _analyzer = MoralGeometryAnalyzer()
    return _analyzer
