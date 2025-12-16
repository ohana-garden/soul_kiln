"""
Graph View Renderer.

Renders the actual semantic graph as a visual - the truth layer.
Shows activation patterns, node relationships, and allows exploration.

This view is always available as an alternative to the workspace view.
Good for understanding "what's happening under the hood" and exploring
the semantic structure directly.

Now includes moral geometry overlays - patterns in the virtue structure:
- Triads (tightly coupled virtue clusters)
- Bridges (virtues connecting different clusters)
- Basin topology (attraction regions)
- Resonance patterns (co-activating virtues)
"""

import logging
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any, Callable

from .topic_detector import TopicState, TopicRegion

logger = logging.getLogger(__name__)


class GraphLayout(str, Enum):
    """Layout algorithms for graph visualization."""

    FORCE_DIRECTED = "force_directed"  # Physics-based, organic
    HIERARCHICAL = "hierarchical"  # Virtues at top, concepts below
    RADIAL = "radial"  # Virtues at center, concepts radiating out
    CLUSTERED = "clustered"  # Grouped by virtue affinity


class NodeVisual(str, Enum):
    """Visual representation styles for nodes."""

    CIRCLE = "circle"
    SQUARE = "square"  # For virtue anchors
    DIAMOND = "diamond"  # For agents
    PILL = "pill"  # For concepts with names


@dataclass
class GraphNode:
    """A node for graph visualization."""

    id: str
    label: str
    type: str  # virtue_anchor, concept, memory, agent
    activation: float  # 0-1
    baseline: float  # 0-1
    position: tuple[float, float] | None = None  # x, y (computed by layout)
    size: float = 1.0  # Computed from activation
    color: str = "#666666"  # Computed from type/activation
    visual: NodeVisual = NodeVisual.CIRCLE
    metadata: dict = field(default_factory=dict)

    def to_dict(self) -> dict:
        """Convert to render-ready dictionary."""
        return {
            "id": self.id,
            "label": self.label,
            "type": self.type,
            "activation": self.activation,
            "position": self.position,
            "size": self.size,
            "color": self.color,
            "visual": self.visual.value,
            "metadata": self.metadata,
        }


@dataclass
class GraphEdge:
    """An edge for graph visualization."""

    source: str
    target: str
    weight: float  # 0-1
    width: float = 1.0  # Computed from weight
    color: str = "#999999"
    opacity: float = 0.6
    animated: bool = False  # Show activation flow

    def to_dict(self) -> dict:
        """Convert to render-ready dictionary."""
        return {
            "source": self.source,
            "target": self.target,
            "weight": self.weight,
            "width": self.width,
            "color": self.color,
            "opacity": self.opacity,
            "animated": self.animated,
        }


@dataclass
class CameraState:
    """Camera/viewport state for graph view."""

    center_x: float = 0.0
    center_y: float = 0.0
    zoom: float = 1.0
    focus_node: str | None = None  # Node to track

    def to_dict(self) -> dict:
        return {
            "center": [self.center_x, self.center_y],
            "zoom": self.zoom,
            "focus_node": self.focus_node,
        }


@dataclass
class GeometryOverlay:
    """Moral geometry patterns to overlay on graph."""

    triads: list[dict] = field(default_factory=list)  # Highlighted virtue triangles
    bridges: list[dict] = field(default_factory=list)  # Bridge node indicators
    basin_hints: list[dict] = field(default_factory=list)  # Basin size indicators
    resonance_links: list[dict] = field(default_factory=list)  # Co-activation patterns
    pattern_summary: dict = field(default_factory=dict)

    def to_dict(self) -> dict:
        return {
            "triads": self.triads,
            "bridges": self.bridges,
            "basin_hints": self.basin_hints,
            "resonance_links": self.resonance_links,
            "pattern_summary": self.pattern_summary,
        }


@dataclass
class GraphViewState:
    """Complete state for graph view rendering."""

    nodes: list[GraphNode]
    edges: list[GraphEdge]
    camera: CameraState
    layout: GraphLayout
    hot_region: TopicRegion | None = None
    geometry_overlay: GeometryOverlay | None = None
    timestamp: datetime = field(default_factory=datetime.utcnow)

    def to_dict(self) -> dict:
        """Convert to render-ready dictionary."""
        return {
            "nodes": [n.to_dict() for n in self.nodes],
            "edges": [e.to_dict() for e in self.edges],
            "camera": self.camera.to_dict(),
            "layout": self.layout.value,
            "hot_region": self.hot_region.value if self.hot_region else None,
            "geometry": self.geometry_overlay.to_dict() if self.geometry_overlay else None,
            "timestamp": self.timestamp.isoformat(),
        }


class GraphViewRenderer:
    """
    Renders the semantic graph as a visual representation.

    The graph view shows truth - the actual activation state and
    structure of the knowledge graph. It's not a metaphor; it IS
    the semantic space made visible.
    """

    # Color schemes for different node types
    TYPE_COLORS = {
        "virtue_anchor": "#673AB7",  # Deep purple for virtues
        "concept": "#2196F3",  # Blue for concepts
        "memory": "#4CAF50",  # Green for memories
        "agent": "#FF9800",  # Orange for agents
    }

    # Virtue cluster colors (for highlighting regions)
    CLUSTER_COLORS = {
        TopicRegion.FOUNDATION: "#1A237E",  # Deep blue
        TopicRegion.CORE: "#4A148C",  # Deep purple
        TopicRegion.RELATIONAL: "#E65100",  # Deep orange
        TopicRegion.PERSONAL: "#1B5E20",  # Deep green
        TopicRegion.TRANSCENDENT: "#311B92",  # Deep indigo
    }

    def __init__(
        self,
        substrate=None,
        layout: GraphLayout = GraphLayout.FORCE_DIRECTED,
        activation_threshold: float = 0.1,
        show_geometry: bool = True,
    ):
        """
        Initialize the graph view renderer.

        Args:
            substrate: The graph substrate for node/edge access
            layout: Layout algorithm to use
            activation_threshold: Minimum activation to show node prominently
            show_geometry: Whether to include moral geometry overlay
        """
        self._substrate = substrate
        self._layout = layout
        self._activation_threshold = activation_threshold
        self._show_geometry = show_geometry
        self._camera = CameraState()
        self._last_state: GraphViewState | None = None
        self._geometry_analyzer = None

        # Callbacks
        self._update_callbacks: list[Callable[[GraphViewState], None]] = []

    def _get_geometry_analyzer(self):
        """Lazy load geometry analyzer."""
        if self._geometry_analyzer is None:
            try:
                from ..graph.moral_geometry import MoralGeometryAnalyzer
                self._geometry_analyzer = MoralGeometryAnalyzer(self._substrate)
            except ImportError:
                logger.debug("Moral geometry analyzer not available")
        return self._geometry_analyzer

    def set_substrate(self, substrate) -> None:
        """Set the graph substrate."""
        self._substrate = substrate

    def set_layout(self, layout: GraphLayout) -> None:
        """Change the layout algorithm."""
        self._layout = layout

    def render(self, topic_state: TopicState | None = None) -> GraphViewState:
        """
        Render the current graph state.

        Args:
            topic_state: Optional topic state for highlighting

        Returns:
            GraphViewState ready for rendering
        """
        if not self._substrate:
            return GraphViewState(
                nodes=[],
                edges=[],
                camera=self._camera,
                layout=self._layout,
            )

        # Get all nodes and edges
        all_nodes = self._substrate.get_all_nodes()
        nodes = [self._node_to_visual(n, topic_state) for n in all_nodes]

        # Get edges (with activation-based animation)
        edges = self._get_visual_edges(topic_state)

        # Update camera to follow activation
        self._update_camera(nodes, topic_state)

        # Build geometry overlay if enabled
        geometry_overlay = None
        if self._show_geometry:
            geometry_overlay = self._build_geometry_overlay(topic_state)

        state = GraphViewState(
            nodes=nodes,
            edges=edges,
            camera=self._camera,
            layout=self._layout,
            hot_region=topic_state.primary_region if topic_state else None,
            geometry_overlay=geometry_overlay,
        )

        self._last_state = state
        self._notify_update(state)

        return state

    def _build_geometry_overlay(self, topic_state: TopicState | None) -> GeometryOverlay:
        """Build moral geometry overlay for visualization."""
        analyzer = self._get_geometry_analyzer()
        if not analyzer:
            return GeometryOverlay()

        # Record activation for resonance analysis
        if topic_state and self._substrate:
            activation_map = {
                n.id: n.activation for n in self._substrate.get_all_nodes()
            }
            analyzer.record_activation(activation_map)

        # Analyze geometry
        try:
            geometry = analyzer.analyze()
        except Exception as e:
            logger.error(f"Geometry analysis failed: {e}")
            return GeometryOverlay()

        # Build overlay data
        triads = []
        for triad in geometry.triads[:5]:  # Top 5 triads
            triads.append({
                "virtues": triad.virtues,
                "affinity": triad.total_affinity,
                "color": "#FFD700" if triad.is_bridge_triad else "#90CAF9",
                "highlight": triad.total_affinity > 1.3,
            })

        bridges = []
        for bridge in geometry.bridges[:5]:  # Top 5 bridges
            bridges.append({
                "virtue_id": bridge.virtue_id,
                "score": bridge.bridge_score,
                "connects": bridge.clusters_connected,
                "color": "#FF9800",
            })

        basin_hints = []
        for vid, basin in geometry.basins.items():
            basin_hints.append({
                "virtue_id": vid,
                "volume": basin.basin_volume,
                "cluster": basin.cluster,
                "radius_hint": min(50, basin.basin_volume * 20),
            })

        resonance_links = []
        for pattern in geometry.resonance_patterns[:10]:
            for resonant in pattern.resonant:
                resonance_links.append({
                    "source": pattern.primary,
                    "target": resonant,
                    "strength": pattern.correlation_matrix.get(resonant, 0.5),
                    "type": pattern.pattern_type,
                })

        return GeometryOverlay(
            triads=triads,
            bridges=bridges,
            basin_hints=basin_hints,
            resonance_links=resonance_links,
            pattern_summary=analyzer.get_pattern_summary(),
        )

    def _node_to_visual(
        self, node, topic_state: TopicState | None
    ) -> GraphNode:
        """Convert a graph node to visual representation."""
        node_type = node.type.value if hasattr(node.type, "value") else str(node.type)

        # Determine visual style
        if node_type == "virtue_anchor":
            visual = NodeVisual.SQUARE
        elif node_type == "agent":
            visual = NodeVisual.DIAMOND
        else:
            visual = NodeVisual.CIRCLE

        # Determine color
        base_color = self.TYPE_COLORS.get(node_type, "#666666")

        # Highlight if active
        is_active = node.activation > self._activation_threshold
        is_hot = (
            topic_state
            and node.id in topic_state.active_concepts + topic_state.active_virtues
        )

        if is_hot:
            color = self._brighten_color(base_color, 0.3)
        elif is_active:
            color = base_color
        else:
            color = self._dim_color(base_color, 0.5)

        # Size based on activation
        size = 0.5 + (node.activation * 1.5)

        # Get label
        label = node.metadata.get("name", node.id)
        if node_type == "virtue_anchor" and node.id.startswith("V"):
            # Use virtue name if available
            label = node.metadata.get("name", node.id)

        return GraphNode(
            id=node.id,
            label=label,
            type=node_type,
            activation=node.activation,
            baseline=node.baseline,
            size=size,
            color=color,
            visual=visual,
            metadata=node.metadata,
        )

    def _get_visual_edges(self, topic_state: TopicState | None) -> list[GraphEdge]:
        """Get edges with visual properties."""
        edges = []

        if not self._substrate:
            return edges

        # Get all edges from substrate
        all_edges = self._substrate.get_all_edges()

        for edge in all_edges:
            # Width based on weight
            width = 0.5 + (edge.weight * 2.0)

            # Opacity based on weight
            opacity = 0.3 + (edge.weight * 0.5)

            # Animate if source is active
            animated = False
            if topic_state:
                if edge.source_id in topic_state.active_concepts:
                    animated = True

            edges.append(GraphEdge(
                source=edge.source_id,
                target=edge.target_id,
                weight=edge.weight,
                width=width,
                opacity=opacity,
                animated=animated,
            ))

        return edges

    def _update_camera(
        self, nodes: list[GraphNode], topic_state: TopicState | None
    ) -> None:
        """Update camera to follow activation."""
        if not topic_state or not topic_state.active_concepts:
            return

        # Find the most active node to focus on
        active_nodes = [
            n for n in nodes
            if n.id in topic_state.active_concepts[:3]
        ]

        if active_nodes:
            # Focus on first active node
            self._camera.focus_node = active_nodes[0].id

    def focus_on_node(self, node_id: str) -> None:
        """Focus camera on a specific node."""
        self._camera.focus_node = node_id

    def focus_on_region(self, region: TopicRegion) -> None:
        """Focus camera on a virtue region."""
        # Would compute centroid of nodes in region
        # For now, just note the intent
        pass

    def zoom_in(self, factor: float = 1.5) -> None:
        """Zoom in."""
        self._camera.zoom *= factor

    def zoom_out(self, factor: float = 1.5) -> None:
        """Zoom out."""
        self._camera.zoom /= factor

    def reset_camera(self) -> None:
        """Reset camera to default."""
        self._camera = CameraState()

    def get_node_at_position(self, x: float, y: float) -> str | None:
        """Get node ID at screen position (for interaction)."""
        if not self._last_state:
            return None

        # Would do hit testing based on node positions
        # For now, return None
        return None

    def on_update(self, callback: Callable[[GraphViewState], None]) -> None:
        """Register callback for view updates."""
        self._update_callbacks.append(callback)

    def _notify_update(self, state: GraphViewState) -> None:
        """Notify callbacks of update."""
        for callback in self._update_callbacks:
            try:
                callback(state)
            except Exception as e:
                logger.error(f"Graph view update callback error: {e}")

    @staticmethod
    def _brighten_color(hex_color: str, factor: float) -> str:
        """Brighten a hex color."""
        try:
            r = int(hex_color[1:3], 16)
            g = int(hex_color[3:5], 16)
            b = int(hex_color[5:7], 16)

            r = min(255, int(r + (255 - r) * factor))
            g = min(255, int(g + (255 - g) * factor))
            b = min(255, int(b + (255 - b) * factor))

            return f"#{r:02x}{g:02x}{b:02x}"
        except (ValueError, IndexError):
            return hex_color

    @staticmethod
    def _dim_color(hex_color: str, factor: float) -> str:
        """Dim a hex color."""
        try:
            r = int(hex_color[1:3], 16)
            g = int(hex_color[3:5], 16)
            b = int(hex_color[5:7], 16)

            r = int(r * (1 - factor))
            g = int(g * (1 - factor))
            b = int(b * (1 - factor))

            return f"#{r:02x}{g:02x}{b:02x}"
        except (ValueError, IndexError):
            return hex_color


# Singleton
_renderer: GraphViewRenderer | None = None


def get_graph_view_renderer() -> GraphViewRenderer:
    """Get the singleton graph view renderer."""
    global _renderer
    if _renderer is None:
        _renderer = GraphViewRenderer()
    return _renderer
