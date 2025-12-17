"""
View System.

Manages the two views available in the theatre:
1. Workspace View - primary, utilitarian, shows contextual artifacts
2. Graph View - shows the actual semantic graph (truth layer)

User can switch between views at any time.
"""

import logging
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any, Callable

from .artifacts import Artifact, ArtifactCurator, get_artifact_curator
from .graph_view import GraphViewRenderer, GraphViewState, get_graph_view_renderer
from .topic_detector import TopicState
from .captions import Caption

logger = logging.getLogger(__name__)


class ViewType(str, Enum):
    """Available view types."""

    WORKSPACE = "workspace"  # Primary utilitarian view
    GRAPH = "graph"  # Semantic graph visualization


@dataclass
class WorkspaceLayout:
    """Layout configuration for workspace view."""

    artifact_position: str = "center"  # center, left, right, split
    caption_position: str = "bottom"  # bottom, top
    max_artifacts: int = 3
    artifact_size: str = "medium"  # small, medium, large, full


@dataclass
class WorkspaceState:
    """State of the workspace view."""

    artifacts: list[dict]  # Render-ready artifact dicts
    captions: list[dict]  # Render-ready caption dicts
    layout: WorkspaceLayout
    topic_hint: str | None = None  # Brief topic indicator
    community: str | None = None  # Active community context
    timestamp: datetime = field(default_factory=datetime.utcnow)

    def to_dict(self) -> dict:
        """Convert to render-ready dictionary."""
        return {
            "view_type": ViewType.WORKSPACE.value,
            "artifacts": self.artifacts,
            "captions": self.captions,
            "layout": {
                "artifact_position": self.layout.artifact_position,
                "caption_position": self.layout.caption_position,
                "max_artifacts": self.layout.max_artifacts,
                "artifact_size": self.layout.artifact_size,
            },
            "topic_hint": self.topic_hint,
            "community": self.community,
            "timestamp": self.timestamp.isoformat(),
        }


@dataclass
class ViewState:
    """Combined view state (either workspace or graph)."""

    view_type: ViewType
    workspace: WorkspaceState | None = None
    graph: GraphViewState | None = None

    def to_dict(self) -> dict:
        """Convert to render-ready dictionary."""
        if self.view_type == ViewType.WORKSPACE and self.workspace:
            return self.workspace.to_dict()
        elif self.view_type == ViewType.GRAPH and self.graph:
            data = self.graph.to_dict()
            data["view_type"] = ViewType.GRAPH.value
            return data
        else:
            return {"view_type": self.view_type.value, "error": "No state"}


class ViewManager:
    """
    Manages view state and switching between workspace and graph views.

    The view manager coordinates:
    - Current view type
    - Artifact curator (for workspace)
    - Graph renderer (for graph view)
    - Captions (shown in both)
    """

    def __init__(
        self,
        artifact_curator: ArtifactCurator | None = None,
        graph_renderer: GraphViewRenderer | None = None,
    ):
        """
        Initialize the view manager.

        Args:
            artifact_curator: Curator for workspace artifacts
            graph_renderer: Renderer for graph view
        """
        self._curator = artifact_curator or get_artifact_curator()
        self._graph_renderer = graph_renderer or get_graph_view_renderer()

        self._current_view = ViewType.WORKSPACE
        self._workspace_layout = WorkspaceLayout()
        self._captions: list[dict] = []
        self._topic_state: TopicState | None = None
        self._community: str | None = None

        # Callbacks
        self._view_change_callbacks: list[Callable[[ViewType], None]] = []
        self._state_change_callbacks: list[Callable[[ViewState], None]] = []

    @property
    def current_view(self) -> ViewType:
        """Get current view type."""
        return self._current_view

    @property
    def curator(self) -> ArtifactCurator:
        """Get the artifact curator."""
        return self._curator

    @property
    def graph_renderer(self) -> GraphViewRenderer:
        """Get the graph renderer."""
        return self._graph_renderer

    def switch_to(self, view_type: ViewType) -> ViewState:
        """
        Switch to a different view.

        Args:
            view_type: The view to switch to

        Returns:
            New view state
        """
        old_view = self._current_view
        self._current_view = view_type

        if old_view != view_type:
            self._notify_view_change(view_type)

        return self.get_state()

    def toggle_view(self) -> ViewState:
        """Toggle between workspace and graph view."""
        if self._current_view == ViewType.WORKSPACE:
            return self.switch_to(ViewType.GRAPH)
        else:
            return self.switch_to(ViewType.WORKSPACE)

    def update_captions(self, captions: list[dict]) -> None:
        """Update the captions to display."""
        self._captions = captions

    def update_topic(self, topic_state: TopicState) -> None:
        """Update the current topic state."""
        self._topic_state = topic_state

    def set_community(self, community: str | None) -> None:
        """Set the active community context."""
        self._community = community

    def set_layout(self, layout: WorkspaceLayout) -> None:
        """Set workspace layout."""
        self._workspace_layout = layout

    def get_state(self) -> ViewState:
        """Get current view state."""
        if self._current_view == ViewType.WORKSPACE:
            workspace_state = WorkspaceState(
                artifacts=self._curator.get_artifacts_for_render(),
                captions=self._captions,
                layout=self._workspace_layout,
                topic_hint=self._get_topic_hint(),
                community=self._community,
            )
            return ViewState(
                view_type=ViewType.WORKSPACE,
                workspace=workspace_state,
            )
        else:
            graph_state = self._graph_renderer.render(self._topic_state)
            return ViewState(
                view_type=ViewType.GRAPH,
                graph=graph_state,
            )

    def get_render_data(self) -> dict:
        """Get render-ready data for current view."""
        state = self.get_state()
        data = state.to_dict()

        # Always include captions in both views
        if self._current_view == ViewType.GRAPH:
            data["captions"] = self._captions

        return data

    def _get_topic_hint(self) -> str | None:
        """Get a brief topic hint for display."""
        if not self._topic_state:
            return None

        region = self._topic_state.primary_region.value
        confidence = self._topic_state.confidence

        if confidence > 0.7:
            return f"Topic: {region}"
        elif confidence > 0.4:
            return f"Topic: {region}?"
        else:
            return "Exploring..."

    def surface_artifact(self, artifact: Artifact) -> None:
        """Surface an artifact in workspace view."""
        # Artifact is already handled by curator
        # Just notify of state change
        self._notify_state_change()

    def dismiss_artifact(self, artifact_id: str) -> bool:
        """Dismiss an artifact from workspace."""
        result = self._curator.dismiss(artifact_id)
        if result:
            self._notify_state_change()
        return result

    def on_view_change(self, callback: Callable[[ViewType], None]) -> None:
        """Register callback for view changes."""
        self._view_change_callbacks.append(callback)

    def on_state_change(self, callback: Callable[[ViewState], None]) -> None:
        """Register callback for state changes."""
        self._state_change_callbacks.append(callback)

    def _notify_view_change(self, view_type: ViewType) -> None:
        """Notify callbacks of view change."""
        for callback in self._view_change_callbacks:
            try:
                callback(view_type)
            except Exception as e:
                logger.error(f"View change callback error: {e}")

    def _notify_state_change(self) -> None:
        """Notify callbacks of state change."""
        state = self.get_state()
        for callback in self._state_change_callbacks:
            try:
                callback(state)
            except Exception as e:
                logger.error(f"State change callback error: {e}")


# Singleton
_manager: ViewManager | None = None


def get_view_manager() -> ViewManager:
    """Get the singleton view manager."""
    global _manager
    if _manager is None:
        _manager = ViewManager()
    return _manager
