"""
Artifact System - KB Query Driven.

Surfaces contextual artifacts from the knowledge graph to serve understanding.
Artifacts are retrieved based on what's being discussed - the active concepts
in the graph determine what's relevant.

The key insight: artifacts are nodes in the KB, linked to concepts via
typed edges. When concepts activate, we query for linked artifacts.

Edge types for artifacts:
- DEPICTED_BY: concept -> image (visual representation)
- HAS_DOCUMENT: concept -> document (related documentation)
- HAS_SECTION: document -> section (specific part of doc)
- LOCATED_AT: resource -> location (spatial context)
- ILLUSTRATED_BY: concept -> diagram (explanatory visual)
- EXEMPLIFIED_BY: concept -> example (concrete instance)

Artifacts serve communication - they make the conversation more effective.
"""

import logging
import uuid
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any, Callable

from .topic_detector import TopicState

logger = logging.getLogger(__name__)


# Edge types that link concepts to artifacts
class ArtifactEdge(str, Enum):
    """Edge types that connect concepts to artifacts in the KB."""

    DEPICTED_BY = "DEPICTED_BY"  # Visual representation
    HAS_DOCUMENT = "HAS_DOCUMENT"  # Related document
    HAS_SECTION = "HAS_SECTION"  # Document section
    LOCATED_AT = "LOCATED_AT"  # Spatial location
    ILLUSTRATED_BY = "ILLUSTRATED_BY"  # Diagram/illustration
    EXEMPLIFIED_BY = "EXEMPLIFIED_BY"  # Concrete example
    HAS_REFERENCE = "HAS_REFERENCE"  # Citation/source
    HAS_TIMELINE = "HAS_TIMELINE"  # Process timeline
    HAS_CHECKLIST = "HAS_CHECKLIST"  # Task checklist
    COMPARED_WITH = "COMPARED_WITH"  # Comparison target


class ArtifactType(str, Enum):
    """Types of artifacts that can be surfaced."""

    # Media (retrieved from KB or external)
    IMAGE = "image"
    DOCUMENT = "document"
    DOCUMENT_SECTION = "document_section"
    MAP = "map"
    DIAGRAM = "diagram"

    # Structured (composed from KB data)
    TIMELINE = "timeline"
    CHECKLIST = "checklist"
    COMPARISON = "comparison"
    EXAMPLE = "example"

    # Reference
    REFERENCE = "reference"
    LINK = "link"


class ArtifactSource(str, Enum):
    """How the artifact was obtained."""

    KB_RETRIEVED = "kb_retrieved"  # Found in knowledge graph
    EXTERNAL = "external"  # Retrieved from external source
    GENERATED = "generated"  # Created via generation
    COMPOSED = "composed"  # Built from structured data


@dataclass
class ArtifactNode:
    """An artifact as stored in the knowledge graph."""

    id: str
    type: ArtifactType
    content_ref: str  # URL, path, or inline content
    title: str
    metadata: dict = field(default_factory=dict)

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "type": self.type.value,
            "content_ref": self.content_ref,
            "title": self.title,
            "metadata": self.metadata,
        }


@dataclass
class Artifact:
    """A surfaced artifact ready for display."""

    id: str
    type: ArtifactType
    source: ArtifactSource
    title: str
    content: Any  # Resolved content (URL, text, structured data)
    relevance: float = 1.0  # Based on activation + edge weight
    linked_concepts: list[str] = field(default_factory=list)
    metadata: dict = field(default_factory=dict)
    created_at: datetime = field(default_factory=datetime.utcnow)
    expires_at: datetime | None = None

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "type": self.type.value,
            "source": self.source.value,
            "title": self.title,
            "content": self.content,
            "relevance": self.relevance,
            "linked_concepts": self.linked_concepts,
            "metadata": self.metadata,
            "created_at": self.created_at.isoformat(),
            "expires_at": self.expires_at.isoformat() if self.expires_at else None,
        }


@dataclass
class ArtifactQuery:
    """Query for artifacts based on active concepts."""

    concepts: list[str]  # Active concept IDs
    activations: dict[str, float] = field(default_factory=dict)  # concept -> activation
    type_filter: list[ArtifactType] | None = None  # Only these types
    edge_filter: list[ArtifactEdge] | None = None  # Only via these edges
    limit: int = 5  # Max artifacts to return
    min_relevance: float = 0.3  # Minimum relevance threshold


class KBArtifactRetriever:
    """
    Retrieves artifacts from the knowledge graph based on active concepts.

    The KB contains artifact nodes linked to concept nodes via typed edges.
    When concepts activate, we find linked artifacts and rank by relevance.
    """

    # Map edge types to artifact types
    EDGE_TO_TYPE = {
        ArtifactEdge.DEPICTED_BY: ArtifactType.IMAGE,
        ArtifactEdge.HAS_DOCUMENT: ArtifactType.DOCUMENT,
        ArtifactEdge.HAS_SECTION: ArtifactType.DOCUMENT_SECTION,
        ArtifactEdge.LOCATED_AT: ArtifactType.MAP,
        ArtifactEdge.ILLUSTRATED_BY: ArtifactType.DIAGRAM,
        ArtifactEdge.EXEMPLIFIED_BY: ArtifactType.EXAMPLE,
        ArtifactEdge.HAS_REFERENCE: ArtifactType.REFERENCE,
        ArtifactEdge.HAS_TIMELINE: ArtifactType.TIMELINE,
        ArtifactEdge.HAS_CHECKLIST: ArtifactType.CHECKLIST,
    }

    def __init__(self, substrate=None, graph_client=None):
        """
        Initialize the retriever.

        Args:
            substrate: The GraphSubstrate for node access
            graph_client: Direct graph client for queries
        """
        self._substrate = substrate
        self._client = graph_client

    def set_substrate(self, substrate) -> None:
        """Set the graph substrate."""
        self._substrate = substrate

    def set_client(self, client) -> None:
        """Set the graph client."""
        self._client = client

    def query(self, query: ArtifactQuery) -> list[Artifact]:
        """
        Query for artifacts linked to active concepts.

        Args:
            query: The artifact query with concepts and filters

        Returns:
            List of artifacts sorted by relevance
        """
        if not query.concepts:
            return []

        candidates: list[tuple[Artifact, float]] = []

        # Query via graph client if available
        if self._client:
            candidates = self._query_via_client(query)
        # Fall back to substrate traversal
        elif self._substrate:
            candidates = self._query_via_substrate(query)

        # Sort by relevance and limit
        candidates.sort(key=lambda x: x[1], reverse=True)
        results = [
            artifact
            for artifact, relevance in candidates[:query.limit]
            if relevance >= query.min_relevance
        ]

        return results

    def _query_via_client(self, query: ArtifactQuery) -> list[tuple[Artifact, float]]:
        """Query using graph client (Cypher queries)."""
        candidates = []

        # Build edge type filter
        edge_types = query.edge_filter or list(ArtifactEdge)
        edge_type_str = "|".join(e.value for e in edge_types)

        # Query for artifacts linked to any active concept
        for concept_id in query.concepts:
            activation = query.activations.get(concept_id, 0.5)

            try:
                # Query pattern: (concept)-[edge]->(artifact)
                result = self._client.query(
                    f"""
                    MATCH (c {{id: $concept_id}})-[r:{edge_type_str}]->(a:Artifact)
                    RETURN a.id, a.type, a.content_ref, a.title, a.metadata,
                           type(r) as edge_type, r.weight as weight
                    """,
                    {"concept_id": concept_id}
                )

                for row in result:
                    artifact_id, artifact_type, content_ref, title, metadata, edge_type, weight = row
                    weight = weight or 0.5

                    # Apply type filter
                    try:
                        atype = ArtifactType(artifact_type)
                    except ValueError:
                        continue

                    if query.type_filter and atype not in query.type_filter:
                        continue

                    # Compute relevance: activation * edge_weight
                    relevance = activation * weight

                    artifact = Artifact(
                        id=artifact_id,
                        type=atype,
                        source=ArtifactSource.KB_RETRIEVED,
                        title=title or artifact_id,
                        content=content_ref,
                        relevance=relevance,
                        linked_concepts=[concept_id],
                        metadata=metadata or {},
                    )
                    candidates.append((artifact, relevance))

            except Exception as e:
                logger.debug(f"Artifact query failed for {concept_id}: {e}")

        # Deduplicate by artifact ID, keeping highest relevance
        seen: dict[str, tuple[Artifact, float]] = {}
        for artifact, relevance in candidates:
            if artifact.id not in seen or seen[artifact.id][1] < relevance:
                seen[artifact.id] = (artifact, relevance)

        return list(seen.values())

    def _query_via_substrate(self, query: ArtifactQuery) -> list[tuple[Artifact, float]]:
        """Query using substrate traversal."""
        candidates = []

        for concept_id in query.concepts:
            activation = query.activations.get(concept_id, 0.5)

            try:
                # Get outgoing edges from concept
                edges = self._substrate.get_outgoing_edges(concept_id)

                for edge in edges:
                    # Check if edge type is an artifact edge
                    try:
                        edge_type = ArtifactEdge(edge.edge_type)
                    except ValueError:
                        continue

                    if query.edge_filter and edge_type not in query.edge_filter:
                        continue

                    # Get target node (artifact)
                    target = self._substrate.get_node(edge.target_id)
                    if not target:
                        continue

                    # Infer artifact type from edge
                    atype = self.EDGE_TO_TYPE.get(edge_type, ArtifactType.REFERENCE)

                    if query.type_filter and atype not in query.type_filter:
                        continue

                    # Compute relevance
                    relevance = activation * edge.weight

                    artifact = Artifact(
                        id=target.id,
                        type=atype,
                        source=ArtifactSource.KB_RETRIEVED,
                        title=target.metadata.get("title", target.id),
                        content=target.metadata.get("content_ref", ""),
                        relevance=relevance,
                        linked_concepts=[concept_id],
                        metadata=target.metadata,
                    )
                    candidates.append((artifact, relevance))

            except Exception as e:
                logger.debug(f"Substrate query failed for {concept_id}: {e}")

        return candidates


class ArtifactComposer:
    """
    Composes structured artifacts from KB data.

    Some artifacts are composed from multiple KB nodes rather than
    retrieved as single nodes (e.g., timelines, comparisons).
    """

    def __init__(self, substrate=None):
        self._substrate = substrate

    def set_substrate(self, substrate) -> None:
        self._substrate = substrate

    def compose_timeline(
        self,
        concept_id: str,
        title: str | None = None,
    ) -> Artifact | None:
        """
        Compose a timeline from HAS_TIMELINE edges.

        Expects timeline nodes to have: stage, order, status, description
        """
        if not self._substrate:
            return None

        try:
            edges = self._substrate.get_edges_from(concept_id)
            timeline_edges = [
                e for e in edges
                if e.edge_type == ArtifactEdge.HAS_TIMELINE.value
            ]

            if not timeline_edges:
                return None

            stages = []
            for edge in timeline_edges:
                node = self._substrate.get_node(edge.target_id)
                if node:
                    stages.append({
                        "name": node.metadata.get("stage", node.id),
                        "order": node.metadata.get("order", 0),
                        "status": node.metadata.get("status", "pending"),
                        "description": node.metadata.get("description", ""),
                    })

            stages.sort(key=lambda x: x["order"])
            current = next(
                (i for i, s in enumerate(stages) if s["status"] == "current"),
                None
            )

            return Artifact(
                id=f"timeline_{uuid.uuid4().hex[:8]}",
                type=ArtifactType.TIMELINE,
                source=ArtifactSource.COMPOSED,
                title=title or f"Timeline: {concept_id}",
                content={"stages": stages, "current_stage": current},
                linked_concepts=[concept_id],
            )

        except Exception as e:
            logger.error(f"Timeline composition failed: {e}")
            return None

    def compose_checklist(
        self,
        concept_id: str,
        title: str | None = None,
    ) -> Artifact | None:
        """
        Compose a checklist from HAS_CHECKLIST edges.

        Expects checklist item nodes to have: text, checked, priority
        """
        if not self._substrate:
            return None

        try:
            edges = self._substrate.get_edges_from(concept_id)
            checklist_edges = [
                e for e in edges
                if e.edge_type == ArtifactEdge.HAS_CHECKLIST.value
            ]

            if not checklist_edges:
                return None

            items = []
            for edge in checklist_edges:
                node = self._substrate.get_node(edge.target_id)
                if node:
                    items.append({
                        "text": node.metadata.get("text", node.id),
                        "checked": node.metadata.get("checked", False),
                        "priority": node.metadata.get("priority", 0),
                    })

            items.sort(key=lambda x: -x["priority"])

            return Artifact(
                id=f"checklist_{uuid.uuid4().hex[:8]}",
                type=ArtifactType.CHECKLIST,
                source=ArtifactSource.COMPOSED,
                title=title or f"Checklist: {concept_id}",
                content={"items": items},
                linked_concepts=[concept_id],
            )

        except Exception as e:
            logger.error(f"Checklist composition failed: {e}")
            return None

    def compose_comparison(
        self,
        concept_ids: list[str],
        criteria: list[str] | None = None,
        title: str | None = None,
    ) -> Artifact | None:
        """
        Compose a comparison from multiple concepts.

        Compares concepts across specified criteria from their metadata.
        """
        if not self._substrate or len(concept_ids) < 2:
            return None

        try:
            options = []
            all_criteria = set(criteria) if criteria else set()

            for concept_id in concept_ids:
                node = self._substrate.get_node(concept_id)
                if node:
                    option = {
                        "id": concept_id,
                        "name": node.metadata.get("name", concept_id),
                        "values": {},
                    }

                    # Extract comparable values from metadata
                    for key, value in node.metadata.items():
                        if isinstance(value, (str, int, float, bool)):
                            option["values"][key] = value
                            if not criteria:
                                all_criteria.add(key)

                    options.append(option)

            if len(options) < 2:
                return None

            return Artifact(
                id=f"comparison_{uuid.uuid4().hex[:8]}",
                type=ArtifactType.COMPARISON,
                source=ArtifactSource.COMPOSED,
                title=title or "Comparison",
                content={
                    "options": options,
                    "criteria": list(all_criteria),
                },
                linked_concepts=concept_ids,
            )

        except Exception as e:
            logger.error(f"Comparison composition failed: {e}")
            return None


class ArtifactCurator:
    """
    Decides what artifacts to surface based on conversation state.

    Queries the KB for artifacts linked to active concepts,
    and composes structured artifacts when appropriate.
    """

    def __init__(self, substrate=None, graph_client=None):
        self._retriever = KBArtifactRetriever(substrate, graph_client)
        self._composer = ArtifactComposer(substrate)
        self._active_artifacts: dict[str, Artifact] = {}
        self._history: list[Artifact] = []

        # Callbacks
        self._surface_callbacks: list[Callable[[Artifact], None]] = []
        self._dismiss_callbacks: list[Callable[[str], None]] = []

        # Generation function for when KB has no artifact
        self._image_generator: Callable[[str, list[str]], str] | None = None

    def set_substrate(self, substrate) -> None:
        """Set the graph substrate."""
        self._retriever.set_substrate(substrate)
        self._composer.set_substrate(substrate)

    def set_client(self, client) -> None:
        """Set the graph client."""
        self._retriever.set_client(client)

    def set_image_generator(
        self,
        generator_fn: Callable[[str, list[str]], str]
    ) -> None:
        """
        Set image generation function.

        Args:
            generator_fn: Takes (prompt, concept_ids) -> image_url
        """
        self._image_generator = generator_fn

    def surface_for_topic(self, topic_state: TopicState) -> list[Artifact]:
        """
        Surface relevant artifacts for the current topic state.

        This is the main entry point - called when topic detection
        identifies active concepts.
        """
        if not topic_state.active_concepts:
            return []

        # Build activation map
        activations = {}
        for concept_id in topic_state.active_concepts:
            # Estimate activation from position in list
            activations[concept_id] = 1.0 - (
                topic_state.active_concepts.index(concept_id) * 0.1
            )

        # Query for artifacts
        query = ArtifactQuery(
            concepts=topic_state.active_concepts,
            activations=activations,
            limit=3,  # Don't overwhelm
            min_relevance=0.3,
        )

        artifacts = self._retriever.query(query)

        # Surface each artifact
        for artifact in artifacts:
            self._surface_artifact(artifact)

        return artifacts

    def request_artifact(
        self,
        concepts: list[str],
        artifact_type: ArtifactType | None = None,
        context: str | None = None,
    ) -> Artifact | None:
        """
        Explicitly request an artifact for given concepts.

        Args:
            concepts: Concept IDs to find artifacts for
            artifact_type: Preferred type (optional)
            context: Context string for generation fallback

        Returns:
            Retrieved or generated artifact
        """
        query = ArtifactQuery(
            concepts=concepts,
            type_filter=[artifact_type] if artifact_type else None,
            limit=1,
        )

        results = self._retriever.query(query)

        if results:
            artifact = results[0]
            self._surface_artifact(artifact)
            return artifact

        # Fall back to generation for images
        if (
            artifact_type == ArtifactType.IMAGE
            and self._image_generator
            and context
        ):
            try:
                image_url = self._image_generator(context, concepts)
                artifact = Artifact(
                    id=f"gen_img_{uuid.uuid4().hex[:8]}",
                    type=ArtifactType.IMAGE,
                    source=ArtifactSource.GENERATED,
                    title=f"Generated: {context[:30]}",
                    content=image_url,
                    linked_concepts=concepts,
                    metadata={"prompt": context},
                )
                self._surface_artifact(artifact)
                return artifact
            except Exception as e:
                logger.error(f"Image generation failed: {e}")

        return None

    def request_timeline(
        self,
        concept_id: str,
        title: str | None = None,
    ) -> Artifact | None:
        """Request a timeline artifact for a concept."""
        artifact = self._composer.compose_timeline(concept_id, title)
        if artifact:
            self._surface_artifact(artifact)
        return artifact

    def request_checklist(
        self,
        concept_id: str,
        title: str | None = None,
    ) -> Artifact | None:
        """Request a checklist artifact for a concept."""
        artifact = self._composer.compose_checklist(concept_id, title)
        if artifact:
            self._surface_artifact(artifact)
        return artifact

    def request_comparison(
        self,
        concept_ids: list[str],
        criteria: list[str] | None = None,
        title: str | None = None,
    ) -> Artifact | None:
        """Request a comparison artifact between concepts."""
        artifact = self._composer.compose_comparison(concept_ids, criteria, title)
        if artifact:
            self._surface_artifact(artifact)
        return artifact

    def request_map(
        self,
        concept_id: str,
    ) -> Artifact | None:
        """Request a map artifact for a concept with location."""
        query = ArtifactQuery(
            concepts=[concept_id],
            edge_filter=[ArtifactEdge.LOCATED_AT],
            type_filter=[ArtifactType.MAP],
            limit=1,
        )
        results = self._retriever.query(query)
        if results:
            self._surface_artifact(results[0])
            return results[0]
        return None

    def request_document_section(
        self,
        document_id: str,
        section_hint: str | None = None,
    ) -> Artifact | None:
        """Request a specific section of a document."""
        query = ArtifactQuery(
            concepts=[document_id],
            edge_filter=[ArtifactEdge.HAS_SECTION],
            type_filter=[ArtifactType.DOCUMENT_SECTION],
            limit=5,
        )
        results = self._retriever.query(query)

        if not results:
            return None

        # If section hint provided, find best match
        if section_hint and len(results) > 1:
            section_hint_lower = section_hint.lower()
            best = max(
                results,
                key=lambda a: (
                    1.0 if section_hint_lower in a.title.lower()
                    else 0.5 if any(
                        section_hint_lower in str(v).lower()
                        for v in a.metadata.values()
                    )
                    else 0.0
                )
            )
            self._surface_artifact(best)
            return best

        # Return first result
        self._surface_artifact(results[0])
        return results[0]

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
