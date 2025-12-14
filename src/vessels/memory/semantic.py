"""
Semantic Memory System.

Provides vector-based semantic memory with embedding search,
inspired by Vessels3 memory tools.
"""

import hashlib
import logging
import threading
import uuid
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Callable

import numpy as np

logger = logging.getLogger(__name__)


@dataclass
class MemoryEntry:
    """A single memory entry with content and metadata."""

    id: str
    content: str
    embedding: np.ndarray | None = None
    metadata: dict = field(default_factory=dict)
    created_at: datetime = field(default_factory=datetime.utcnow)
    last_accessed: datetime = field(default_factory=datetime.utcnow)
    access_count: int = 0
    agent_id: str | None = None
    tags: list[str] = field(default_factory=list)

    def to_dict(self) -> dict:
        """Convert to dictionary."""
        return {
            "id": self.id,
            "content": self.content,
            "metadata": self.metadata,
            "created_at": self.created_at.isoformat(),
            "last_accessed": self.last_accessed.isoformat(),
            "access_count": self.access_count,
            "agent_id": self.agent_id,
            "tags": self.tags,
        }


class SemanticMemory:
    """
    Semantic memory system with vector-based retrieval.

    Features:
    - memory_load: Retrieve memories via semantic search
    - memory_save: Persist new memories with embeddings
    - memory_delete: Remove specific memories by ID
    - memory_forget: Bulk removal by search criteria
    """

    def __init__(
        self,
        embedding_fn: Callable[[str], np.ndarray] | None = None,
        embedding_dim: int = 384,
        max_memories: int = 10000,
    ):
        """
        Initialize semantic memory.

        Args:
            embedding_fn: Function to generate embeddings from text.
                         If None, uses simple hash-based pseudo-embeddings.
            embedding_dim: Dimension of embedding vectors
            max_memories: Maximum number of memories to store
        """
        self._memories: dict[str, MemoryEntry] = {}
        self._embeddings: np.ndarray | None = None
        self._id_to_index: dict[str, int] = {}
        self._index_to_id: dict[int, str] = {}
        self._lock = threading.RLock()
        self._embedding_fn = embedding_fn or self._default_embedding
        self._embedding_dim = embedding_dim
        self._max_memories = max_memories
        self._dirty = False

    def _default_embedding(self, text: str) -> np.ndarray:
        """Generate a simple hash-based pseudo-embedding."""
        # Create deterministic pseudo-embedding from text hash
        hash_bytes = hashlib.sha256(text.encode()).digest()
        # Extend hash to embedding dimension
        extended = hash_bytes * (self._embedding_dim // 32 + 1)
        values = np.frombuffer(extended[: self._embedding_dim * 4], dtype=np.float32)
        # Normalize
        norm = np.linalg.norm(values)
        if norm > 0:
            values = values / norm
        return values[: self._embedding_dim]

    def save(
        self,
        content: str,
        metadata: dict | None = None,
        agent_id: str | None = None,
        tags: list[str] | None = None,
    ) -> str:
        """
        Save a new memory.

        Args:
            content: The memory content
            metadata: Optional metadata key-value pairs
            agent_id: Optional agent ID attribution
            tags: Optional list of tags

        Returns:
            ID of the created memory
        """
        with self._lock:
            memory_id = f"mem_{uuid.uuid4().hex[:12]}"
            embedding = self._embedding_fn(content)

            entry = MemoryEntry(
                id=memory_id,
                content=content,
                embedding=embedding,
                metadata=metadata or {},
                agent_id=agent_id,
                tags=tags or [],
            )

            self._memories[memory_id] = entry
            self._rebuild_index()
            self._dirty = True

            # Prune if over limit
            if len(self._memories) > self._max_memories:
                self._prune_oldest()

            logger.debug(f"Saved memory {memory_id}: {content[:50]}...")
            return memory_id

    def load(
        self,
        query: str,
        threshold: float = 0.5,
        limit: int = 10,
        filter_fn: Callable[[MemoryEntry], bool] | None = None,
        tags: list[str] | None = None,
        agent_id: str | None = None,
    ) -> list[MemoryEntry]:
        """
        Load memories via semantic search.

        Args:
            query: Search query text
            threshold: Minimum similarity threshold (0-1)
            limit: Maximum results to return
            filter_fn: Optional filter function for metadata
            tags: Optional tags to filter by
            agent_id: Optional agent ID to filter by

        Returns:
            List of matching MemoryEntry objects
        """
        with self._lock:
            if not self._memories:
                return []

            query_embedding = self._embedding_fn(query)
            results = []

            for memory_id, entry in self._memories.items():
                # Apply filters
                if agent_id and entry.agent_id != agent_id:
                    continue
                if tags and not any(t in entry.tags for t in tags):
                    continue
                if filter_fn and not filter_fn(entry):
                    continue

                # Calculate similarity
                if entry.embedding is not None:
                    similarity = self._cosine_similarity(query_embedding, entry.embedding)
                    if similarity >= threshold:
                        results.append((similarity, entry))

            # Sort by similarity descending
            results.sort(key=lambda x: x[0], reverse=True)

            # Update access tracking and return
            output = []
            for similarity, entry in results[:limit]:
                entry.last_accessed = datetime.utcnow()
                entry.access_count += 1
                output.append(entry)

            return output

    def delete(self, memory_ids: list[str] | str) -> int:
        """
        Delete specific memories by ID.

        Args:
            memory_ids: Single ID or list of IDs to delete

        Returns:
            Number of memories deleted
        """
        if isinstance(memory_ids, str):
            memory_ids = [memory_ids]

        with self._lock:
            deleted = 0
            for memory_id in memory_ids:
                if memory_id in self._memories:
                    del self._memories[memory_id]
                    deleted += 1

            if deleted > 0:
                self._rebuild_index()
                self._dirty = True

            logger.debug(f"Deleted {deleted} memories")
            return deleted

    def forget(
        self,
        query: str,
        threshold: float = 0.75,
        filter_fn: Callable[[MemoryEntry], bool] | None = None,
    ) -> int:
        """
        Bulk remove memories matching search criteria.

        Uses a higher default threshold (0.75) as safety measure.

        Args:
            query: Search query for memories to forget
            threshold: Minimum similarity threshold (default higher for safety)
            filter_fn: Optional additional filter

        Returns:
            Number of memories forgotten
        """
        with self._lock:
            # Find matching memories
            matches = self.load(
                query=query,
                threshold=threshold,
                limit=self._max_memories,
                filter_fn=filter_fn,
            )

            # Delete them
            ids_to_delete = [m.id for m in matches]
            return self.delete(ids_to_delete)

    def get(self, memory_id: str) -> MemoryEntry | None:
        """Get a specific memory by ID."""
        return self._memories.get(memory_id)

    def get_all(
        self,
        agent_id: str | None = None,
        tags: list[str] | None = None,
    ) -> list[MemoryEntry]:
        """Get all memories, optionally filtered."""
        with self._lock:
            results = []
            for entry in self._memories.values():
                if agent_id and entry.agent_id != agent_id:
                    continue
                if tags and not any(t in entry.tags for t in tags):
                    continue
                results.append(entry)
            return results

    def update_metadata(self, memory_id: str, metadata: dict) -> bool:
        """Update metadata for a specific memory."""
        with self._lock:
            if memory_id in self._memories:
                self._memories[memory_id].metadata.update(metadata)
                self._dirty = True
                return True
            return False

    def add_tags(self, memory_id: str, tags: list[str]) -> bool:
        """Add tags to a specific memory."""
        with self._lock:
            if memory_id in self._memories:
                entry = self._memories[memory_id]
                entry.tags = list(set(entry.tags + tags))
                self._dirty = True
                return True
            return False

    def get_stats(self) -> dict:
        """Get memory system statistics."""
        with self._lock:
            if not self._memories:
                return {
                    "total_memories": 0,
                    "unique_agents": 0,
                    "total_accesses": 0,
                }

            agents = set(m.agent_id for m in self._memories.values() if m.agent_id)
            total_accesses = sum(m.access_count for m in self._memories.values())

            return {
                "total_memories": len(self._memories),
                "unique_agents": len(agents),
                "total_accesses": total_accesses,
                "oldest_memory": min(
                    m.created_at for m in self._memories.values()
                ).isoformat(),
                "newest_memory": max(
                    m.created_at for m in self._memories.values()
                ).isoformat(),
            }

    def consolidate(
        self,
        similarity_threshold: float = 0.9,
        consolidation_fn: Callable[[list[MemoryEntry]], MemoryEntry] | None = None,
    ) -> int:
        """
        Consolidate similar memories.

        Merges very similar memories to reduce redundancy.

        Args:
            similarity_threshold: Threshold for considering memories duplicates
            consolidation_fn: Custom function to merge entries

        Returns:
            Number of memories consolidated
        """
        with self._lock:
            if len(self._memories) < 2:
                return 0

            # Find clusters of similar memories
            processed = set()
            clusters = []

            entries = list(self._memories.values())
            for i, entry1 in enumerate(entries):
                if entry1.id in processed:
                    continue

                cluster = [entry1]
                processed.add(entry1.id)

                for entry2 in entries[i + 1 :]:
                    if entry2.id in processed:
                        continue
                    if entry1.embedding is not None and entry2.embedding is not None:
                        sim = self._cosine_similarity(entry1.embedding, entry2.embedding)
                        if sim >= similarity_threshold:
                            cluster.append(entry2)
                            processed.add(entry2.id)

                if len(cluster) > 1:
                    clusters.append(cluster)

            # Consolidate each cluster
            consolidated = 0
            for cluster in clusters:
                if consolidation_fn:
                    merged = consolidation_fn(cluster)
                else:
                    merged = self._default_consolidate(cluster)

                # Remove old entries and add merged
                for entry in cluster:
                    if entry.id in self._memories:
                        del self._memories[entry.id]
                        consolidated += 1

                self._memories[merged.id] = merged
                consolidated -= 1  # We added one back

            if consolidated > 0:
                self._rebuild_index()
                self._dirty = True

            return consolidated

    def _default_consolidate(self, entries: list[MemoryEntry]) -> MemoryEntry:
        """Default consolidation: keep most accessed, merge metadata."""
        # Sort by access count, keep the most accessed
        entries.sort(key=lambda x: x.access_count, reverse=True)
        primary = entries[0]

        # Merge metadata and tags from others
        merged_metadata = {}
        merged_tags = set(primary.tags)
        for entry in entries[1:]:
            merged_metadata.update(entry.metadata)
            merged_tags.update(entry.tags)

        primary.metadata.update(merged_metadata)
        primary.tags = list(merged_tags)
        primary.access_count = sum(e.access_count for e in entries)

        return primary

    def _cosine_similarity(self, a: np.ndarray, b: np.ndarray) -> float:
        """Calculate cosine similarity between two vectors."""
        dot = np.dot(a, b)
        norm_a = np.linalg.norm(a)
        norm_b = np.linalg.norm(b)
        if norm_a == 0 or norm_b == 0:
            return 0.0
        return float(dot / (norm_a * norm_b))

    def _rebuild_index(self) -> None:
        """Rebuild the embedding index."""
        self._id_to_index = {}
        self._index_to_id = {}

        if not self._memories:
            self._embeddings = None
            return

        embeddings_list = []
        for idx, (memory_id, entry) in enumerate(self._memories.items()):
            self._id_to_index[memory_id] = idx
            self._index_to_id[idx] = memory_id
            if entry.embedding is not None:
                embeddings_list.append(entry.embedding)

        if embeddings_list:
            self._embeddings = np.vstack(embeddings_list)
        else:
            self._embeddings = None

    def _prune_oldest(self) -> None:
        """Remove oldest, least accessed memories to stay under limit."""
        if len(self._memories) <= self._max_memories:
            return

        # Sort by (access_count, last_accessed) ascending
        sorted_entries = sorted(
            self._memories.items(),
            key=lambda x: (x[1].access_count, x[1].last_accessed),
        )

        # Remove excess
        to_remove = len(self._memories) - self._max_memories
        for memory_id, _ in sorted_entries[:to_remove]:
            del self._memories[memory_id]

        self._rebuild_index()
        logger.debug(f"Pruned {to_remove} old memories")

    def export(self) -> list[dict]:
        """Export all memories as dictionaries."""
        with self._lock:
            return [entry.to_dict() for entry in self._memories.values()]

    def import_memories(self, data: list[dict]) -> int:
        """Import memories from dictionaries."""
        with self._lock:
            imported = 0
            for item in data:
                entry = MemoryEntry(
                    id=item.get("id", f"mem_{uuid.uuid4().hex[:12]}"),
                    content=item["content"],
                    embedding=self._embedding_fn(item["content"]),
                    metadata=item.get("metadata", {}),
                    agent_id=item.get("agent_id"),
                    tags=item.get("tags", []),
                )
                self._memories[entry.id] = entry
                imported += 1

            self._rebuild_index()
            self._dirty = True
            return imported
