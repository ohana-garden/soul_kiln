"""
Artifact System.

Manages contextual artifacts that surface in the workspace to serve understanding.
Artifacts are retrieved, generated, or composed based on graph state and conversation needs.

Artifacts are utilitarian - they enhance information value, not ambiance.
Examples:
- A document under review (retrieved)
- An image highlighting an aspect of a concept (retrieved or generated)
- A timeline showing process stages (composed)
- A checklist with status indicators (composed)
- A comparison of options (composed)
"""

import logging
import uuid
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any, Callable

from .topic_detector import TopicState

logger = logging.getLogger(__name__)


class ArtifactType(str, Enum):
    """Types of artifacts that can be surfaced."""

    # Retrieved
    DOCUMENT = "document"  # Actual document being discussed
    IMAGE = "image"  # Reference image, photo, illustration
    REFERENCE = "reference"  # Link, citation, source material

    # Generated
    ILLUSTRATION = "illustration"  # Generated image to explain concept
    DIAGRAM = "diagram"  # Generated diagram showing relationships

    # Composed from data
    TIMELINE = "timeline"  # Process stages, deadlines
    CHECKLIST = "checklist"  # Items with status
    COMPARISON = "comparison"  # Side-by-side options
    PROGRESS = "progress"  # Progress indicator
    CONCEPT_MAP = "concept_map"  # Subset of graph relevant to current topic


class ArtifactSource(str, Enum):
    """How the artifact was obtained."""

    RETRIEVED = "retrieved"  # Found in memory/storage
    GENERATED = "generated"  # Created via generation (image gen, etc.)
    COMPOSED = "composed"  # Built from structured data


@dataclass
class Artifact:
    """A contextual artifact surfaced in the workspace."""

    id: str
    type: ArtifactType
    source: ArtifactSource
    title: str
    content: Any  # Type depends on artifact type
    relevance: float = 1.0  # 0-1, how relevant to current context
    metadata: dict = field(default_factory=dict)
    created_at: datetime = field(default_factory=datetime.utcnow)
    expires_at: datetime | None = None  # When to auto-dismiss

    def to_dict(self) -> dict:
        """Convert to dictionary for rendering."""
        return {
            "id": self.id,
            "type": self.type.value,
            "source": self.source.value,
            "title": self.title,
            "content": self._serialize_content(),
            "relevance": self.relevance,
            "metadata": self.metadata,
            "created_at": self.created_at.isoformat(),
            "expires_at": self.expires_at.isoformat() if self.expires_at else None,
        }

    def _serialize_content(self) -> Any:
        """Serialize content based on type."""
        if self.type == ArtifactType.IMAGE:
            # Content is URL or base64
            return self.content
        elif self.type == ArtifactType.DOCUMENT:
            # Content is text or structured doc
            return self.content
        elif self.type in (ArtifactType.TIMELINE, ArtifactType.CHECKLIST):
            # Content is list of items
            return self.content
        elif self.type == ArtifactType.COMPARISON:
            # Content is dict of options
            return self.content
        elif self.type == ArtifactType.CONCEPT_MAP:
            # Content is graph subset
            return self.content
        else:
            return str(self.content)


@dataclass
class ArtifactRequest:
    """Request for an artifact based on context."""

    context: str  # What we're trying to show/explain
    type_hint: ArtifactType | None = None  # Preferred type if any
    topic_state: TopicState | None = None
    concepts: list[str] = field(default_factory=list)
    urgency: float = 0.5  # 0-1, how important to surface now


class ArtifactProvider(ABC):
    """Base class for artifact providers."""

    @abstractmethod
    def can_provide(self, request: ArtifactRequest) -> bool:
        """Check if this provider can fulfill the request."""
        pass

    @abstractmethod
    def provide(self, request: ArtifactRequest) -> Artifact | None:
        """Provide an artifact for the request."""
        pass


class DocumentProvider(ArtifactProvider):
    """Provides document artifacts from storage."""

    def __init__(self, document_store: dict[str, Any] | None = None):
        self._store = document_store or {}

    def can_provide(self, request: ArtifactRequest) -> bool:
        if request.type_hint and request.type_hint != ArtifactType.DOCUMENT:
            return False
        # Check if we have relevant documents
        return any(
            concept.lower() in doc_id.lower()
            for concept in request.concepts
            for doc_id in self._store.keys()
        )

    def provide(self, request: ArtifactRequest) -> Artifact | None:
        # Find most relevant document
        for concept in request.concepts:
            for doc_id, doc_content in self._store.items():
                if concept.lower() in doc_id.lower():
                    return Artifact(
                        id=f"doc_{uuid.uuid4().hex[:8]}",
                        type=ArtifactType.DOCUMENT,
                        source=ArtifactSource.RETRIEVED,
                        title=doc_id,
                        content=doc_content,
                        metadata={"matched_concept": concept},
                    )
        return None

    def add_document(self, doc_id: str, content: Any) -> None:
        """Add a document to the store."""
        self._store[doc_id] = content


class ImageProvider(ArtifactProvider):
    """Provides image artifacts - retrieved or generated."""

    def __init__(
        self,
        image_store: dict[str, str] | None = None,
        generator_fn: Callable[[str], str] | None = None,
    ):
        self._store = image_store or {}
        self._generator = generator_fn  # Returns URL or base64

    def can_provide(self, request: ArtifactRequest) -> bool:
        if request.type_hint and request.type_hint not in (
            ArtifactType.IMAGE,
            ArtifactType.ILLUSTRATION,
        ):
            return False
        # Can always try to generate if we have a generator
        return bool(self._store) or bool(self._generator)

    def provide(self, request: ArtifactRequest) -> Artifact | None:
        # Try retrieval first
        for concept in request.concepts:
            for img_id, img_url in self._store.items():
                if concept.lower() in img_id.lower():
                    return Artifact(
                        id=f"img_{uuid.uuid4().hex[:8]}",
                        type=ArtifactType.IMAGE,
                        source=ArtifactSource.RETRIEVED,
                        title=img_id,
                        content=img_url,
                        metadata={"matched_concept": concept},
                    )

        # Fall back to generation
        if self._generator and request.context:
            try:
                generated_url = self._generator(request.context)
                return Artifact(
                    id=f"img_{uuid.uuid4().hex[:8]}",
                    type=ArtifactType.ILLUSTRATION,
                    source=ArtifactSource.GENERATED,
                    title=f"Illustration: {request.context[:50]}",
                    content=generated_url,
                    metadata={"prompt": request.context},
                )
            except Exception as e:
                logger.error(f"Image generation failed: {e}")

        return None

    def add_image(self, img_id: str, url: str) -> None:
        """Add an image to the store."""
        self._store[img_id] = url


class TimelineProvider(ArtifactProvider):
    """Composes timeline artifacts from structured data."""

    def can_provide(self, request: ArtifactRequest) -> bool:
        return request.type_hint == ArtifactType.TIMELINE

    def provide(self, request: ArtifactRequest) -> Artifact | None:
        # Would typically query for timeline data based on context
        # For now, return None - needs data source
        return None

    def compose(
        self,
        title: str,
        stages: list[dict[str, Any]],
        current_stage: int | None = None,
    ) -> Artifact:
        """Compose a timeline artifact from stage data."""
        return Artifact(
            id=f"timeline_{uuid.uuid4().hex[:8]}",
            type=ArtifactType.TIMELINE,
            source=ArtifactSource.COMPOSED,
            title=title,
            content={
                "stages": stages,
                "current_stage": current_stage,
            },
        )


class ChecklistProvider(ArtifactProvider):
    """Composes checklist artifacts from structured data."""

    def can_provide(self, request: ArtifactRequest) -> bool:
        return request.type_hint == ArtifactType.CHECKLIST

    def provide(self, request: ArtifactRequest) -> Artifact | None:
        return None

    def compose(
        self,
        title: str,
        items: list[dict[str, Any]],
    ) -> Artifact:
        """
        Compose a checklist artifact.

        Items should have: {text: str, checked: bool, status?: str}
        """
        return Artifact(
            id=f"checklist_{uuid.uuid4().hex[:8]}",
            type=ArtifactType.CHECKLIST,
            source=ArtifactSource.COMPOSED,
            title=title,
            content={"items": items},
        )


class ComparisonProvider(ArtifactProvider):
    """Composes comparison artifacts for side-by-side views."""

    def can_provide(self, request: ArtifactRequest) -> bool:
        return request.type_hint == ArtifactType.COMPARISON

    def provide(self, request: ArtifactRequest) -> Artifact | None:
        return None

    def compose(
        self,
        title: str,
        options: list[dict[str, Any]],
        criteria: list[str] | None = None,
    ) -> Artifact:
        """
        Compose a comparison artifact.

        Options should have: {name: str, values: dict[criterion, value]}
        """
        return Artifact(
            id=f"comparison_{uuid.uuid4().hex[:8]}",
            type=ArtifactType.COMPARISON,
            source=ArtifactSource.COMPOSED,
            title=title,
            content={
                "options": options,
                "criteria": criteria or [],
            },
        )


class ConceptMapProvider(ArtifactProvider):
    """Extracts relevant subgraph as concept map artifact."""

    def __init__(self, substrate=None):
        self._substrate = substrate

    def can_provide(self, request: ArtifactRequest) -> bool:
        return (
            request.type_hint == ArtifactType.CONCEPT_MAP
            and self._substrate is not None
        )

    def provide(self, request: ArtifactRequest) -> Artifact | None:
        if not self._substrate or not request.concepts:
            return None

        # Extract subgraph around the specified concepts
        subgraph = self._extract_subgraph(request.concepts)
        if subgraph:
            return Artifact(
                id=f"conceptmap_{uuid.uuid4().hex[:8]}",
                type=ArtifactType.CONCEPT_MAP,
                source=ArtifactSource.COMPOSED,
                title="Concept Map",
                content=subgraph,
            )
        return None

    def _extract_subgraph(self, concept_ids: list[str], depth: int = 2) -> dict | None:
        """Extract a subgraph around the given concepts."""
        if not self._substrate:
            return None

        nodes = []
        edges = []
        visited = set()

        def traverse(node_id: str, current_depth: int):
            if node_id in visited or current_depth > depth:
                return
            visited.add(node_id)

            node = self._substrate.get_node(node_id)
            if node:
                nodes.append({
                    "id": node.id,
                    "type": node.type.value,
                    "activation": node.activation,
                    "label": node.metadata.get("name", node.id),
                })

                # Get edges
                if current_depth < depth:
                    for edge in self._substrate.get_edges_from(node_id):
                        edges.append({
                            "source": edge.source_id,
                            "target": edge.target_id,
                            "weight": edge.weight,
                        })
                        traverse(edge.target_id, current_depth + 1)

        for concept_id in concept_ids:
            traverse(concept_id, 0)

        if not nodes:
            return None

        return {"nodes": nodes, "edges": edges}


class ArtifactCurator:
    """
    Decides what artifacts to surface based on graph state and conversation.

    The curator is like a research assistant who finds/creates the right
    visual aid for the current moment.
    """

    def __init__(self):
        self._providers: list[ArtifactProvider] = []
        self._active_artifacts: dict[str, Artifact] = {}
        self._history: list[Artifact] = []

        # Callbacks
        self._surface_callbacks: list[Callable[[Artifact], None]] = []
        self._dismiss_callbacks: list[Callable[[str], None]] = []

        # Initialize default providers
        self._document_provider = DocumentProvider()
        self._image_provider = ImageProvider()
        self._timeline_provider = TimelineProvider()
        self._checklist_provider = ChecklistProvider()
        self._comparison_provider = ComparisonProvider()
        self._concept_map_provider = ConceptMapProvider()

        self._providers = [
            self._document_provider,
            self._image_provider,
            self._timeline_provider,
            self._checklist_provider,
            self._comparison_provider,
            self._concept_map_provider,
        ]

    def set_substrate(self, substrate) -> None:
        """Set the graph substrate for concept map extraction."""
        self._concept_map_provider._substrate = substrate

    def set_image_generator(self, generator_fn: Callable[[str], str]) -> None:
        """Set the image generation function."""
        self._image_provider._generator = generator_fn

    def request_artifact(self, request: ArtifactRequest) -> Artifact | None:
        """
        Request an artifact based on context.

        Tries providers in order until one can fulfill the request.
        """
        for provider in self._providers:
            if provider.can_provide(request):
                artifact = provider.provide(request)
                if artifact:
                    self._surface_artifact(artifact)
                    return artifact
        return None

    def surface_from_topic(self, topic_state: TopicState) -> list[Artifact]:
        """
        Automatically surface relevant artifacts based on topic state.

        Called when topic changes significantly.
        """
        artifacts = []

        # Request concept map for active concepts
        if topic_state.active_concepts:
            request = ArtifactRequest(
                context="Current topic concepts",
                type_hint=ArtifactType.CONCEPT_MAP,
                topic_state=topic_state,
                concepts=topic_state.active_concepts[:5],
            )
            artifact = self.request_artifact(request)
            if artifact:
                artifacts.append(artifact)

        return artifacts

    def compose_timeline(
        self,
        title: str,
        stages: list[dict[str, Any]],
        current_stage: int | None = None,
    ) -> Artifact:
        """Directly compose and surface a timeline."""
        artifact = self._timeline_provider.compose(title, stages, current_stage)
        self._surface_artifact(artifact)
        return artifact

    def compose_checklist(
        self,
        title: str,
        items: list[dict[str, Any]],
    ) -> Artifact:
        """Directly compose and surface a checklist."""
        artifact = self._checklist_provider.compose(title, items)
        self._surface_artifact(artifact)
        return artifact

    def compose_comparison(
        self,
        title: str,
        options: list[dict[str, Any]],
        criteria: list[str] | None = None,
    ) -> Artifact:
        """Directly compose and surface a comparison."""
        artifact = self._comparison_provider.compose(title, options, criteria)
        self._surface_artifact(artifact)
        return artifact

    def add_document(self, doc_id: str, content: Any) -> None:
        """Add a document to the retrieval store."""
        self._document_provider.add_document(doc_id, content)

    def add_image(self, img_id: str, url: str) -> None:
        """Add an image to the retrieval store."""
        self._image_provider.add_image(img_id, url)

    def _surface_artifact(self, artifact: Artifact) -> None:
        """Surface an artifact in the workspace."""
        self._active_artifacts[artifact.id] = artifact
        self._history.append(artifact)

        for callback in self._surface_callbacks:
            try:
                callback(artifact)
            except Exception as e:
                logger.error(f"Surface callback error: {e}")

    def dismiss(self, artifact_id: str) -> bool:
        """Dismiss an artifact from the workspace."""
        if artifact_id in self._active_artifacts:
            del self._active_artifacts[artifact_id]

            for callback in self._dismiss_callbacks:
                try:
                    callback(artifact_id)
                except Exception as e:
                    logger.error(f"Dismiss callback error: {e}")

            return True
        return False

    def dismiss_all(self) -> None:
        """Dismiss all active artifacts."""
        for artifact_id in list(self._active_artifacts.keys()):
            self.dismiss(artifact_id)

    def get_active_artifacts(self) -> list[Artifact]:
        """Get all currently active artifacts."""
        return list(self._active_artifacts.values())

    def get_artifacts_for_render(self) -> list[dict]:
        """Get active artifacts in render-ready format."""
        return [a.to_dict() for a in self._active_artifacts.values()]

    def on_surface(self, callback: Callable[[Artifact], None]) -> None:
        """Register callback for when artifacts are surfaced."""
        self._surface_callbacks.append(callback)

    def on_dismiss(self, callback: Callable[[str], None]) -> None:
        """Register callback for when artifacts are dismissed."""
        self._dismiss_callbacks.append(callback)


# Singleton
_curator: ArtifactCurator | None = None


def get_artifact_curator() -> ArtifactCurator:
    """Get the singleton artifact curator."""
    global _curator
    if _curator is None:
        _curator = ArtifactCurator()
    return _curator
