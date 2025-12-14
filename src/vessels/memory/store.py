"""
Memory Store for persistent storage.

Provides file-based persistence for the semantic memory system.
"""

import json
import logging
import os
from datetime import datetime
from pathlib import Path
from typing import Any

from .semantic import SemanticMemory, MemoryEntry

logger = logging.getLogger(__name__)


class MemoryStore:
    """
    Persistent storage for semantic memories.

    Handles saving/loading memories to disk and integrating
    with graph database for cross-agent memory sharing.
    """

    def __init__(
        self,
        memory: SemanticMemory,
        storage_dir: str | Path = "data/memories",
        auto_save: bool = True,
        save_interval: int = 100,
    ):
        """
        Initialize memory store.

        Args:
            memory: SemanticMemory instance to persist
            storage_dir: Directory for memory files
            auto_save: Whether to auto-save periodically
            save_interval: Operations between auto-saves
        """
        self.memory = memory
        self.storage_dir = Path(storage_dir)
        self.auto_save = auto_save
        self.save_interval = save_interval
        self._operation_count = 0

        # Ensure storage directory exists
        self.storage_dir.mkdir(parents=True, exist_ok=True)

    def save_to_file(self, filename: str | None = None) -> str:
        """
        Save all memories to a JSON file.

        Args:
            filename: Optional filename, defaults to timestamp

        Returns:
            Path to saved file
        """
        if filename is None:
            timestamp = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
            filename = f"memories_{timestamp}.json"

        filepath = self.storage_dir / filename
        data = self.memory.export()

        with open(filepath, "w") as f:
            json.dump(
                {
                    "version": "1.0",
                    "exported_at": datetime.utcnow().isoformat(),
                    "memory_count": len(data),
                    "memories": data,
                },
                f,
                indent=2,
            )

        logger.info(f"Saved {len(data)} memories to {filepath}")
        return str(filepath)

    def load_from_file(self, filepath: str | Path) -> int:
        """
        Load memories from a JSON file.

        Args:
            filepath: Path to the file to load

        Returns:
            Number of memories loaded
        """
        filepath = Path(filepath)
        if not filepath.exists():
            logger.warning(f"Memory file not found: {filepath}")
            return 0

        with open(filepath) as f:
            data = json.load(f)

        memories = data.get("memories", data)  # Handle both formats
        if isinstance(memories, dict):
            memories = list(memories.values())

        count = self.memory.import_memories(memories)
        logger.info(f"Loaded {count} memories from {filepath}")
        return count

    def load_latest(self) -> int:
        """
        Load the most recent memory file.

        Returns:
            Number of memories loaded
        """
        files = sorted(self.storage_dir.glob("memories_*.json"), reverse=True)
        if not files:
            logger.info("No memory files found")
            return 0

        return self.load_from_file(files[0])

    def _maybe_auto_save(self) -> None:
        """Trigger auto-save if enabled and interval reached."""
        if not self.auto_save:
            return

        self._operation_count += 1
        if self._operation_count >= self.save_interval:
            self.save_to_file()
            self._operation_count = 0

    def save_memory(
        self,
        content: str,
        metadata: dict | None = None,
        agent_id: str | None = None,
        tags: list[str] | None = None,
    ) -> str:
        """
        Save a memory with auto-persistence.

        Args:
            content: Memory content
            metadata: Optional metadata
            agent_id: Optional agent attribution
            tags: Optional tags

        Returns:
            Memory ID
        """
        memory_id = self.memory.save(content, metadata, agent_id, tags)
        self._maybe_auto_save()
        return memory_id

    def search_memories(
        self,
        query: str,
        threshold: float = 0.5,
        limit: int = 10,
        agent_id: str | None = None,
        tags: list[str] | None = None,
    ) -> list[MemoryEntry]:
        """
        Search memories with convenience wrapper.

        Args:
            query: Search query
            threshold: Similarity threshold
            limit: Max results
            agent_id: Filter by agent
            tags: Filter by tags

        Returns:
            List of matching memories
        """
        return self.memory.load(
            query=query,
            threshold=threshold,
            limit=limit,
            agent_id=agent_id,
            tags=tags,
        )

    def get_agent_memories(self, agent_id: str) -> list[MemoryEntry]:
        """Get all memories for a specific agent."""
        return self.memory.get_all(agent_id=agent_id)

    def delete_agent_memories(self, agent_id: str) -> int:
        """Delete all memories for a specific agent."""
        memories = self.get_agent_memories(agent_id)
        ids = [m.id for m in memories]
        return self.memory.delete(ids)

    def get_memory_stats(self) -> dict:
        """Get comprehensive memory statistics."""
        stats = self.memory.get_stats()
        stats["storage_dir"] = str(self.storage_dir)
        stats["file_count"] = len(list(self.storage_dir.glob("memories_*.json")))
        return stats

    def cleanup_old_files(self, keep_count: int = 10) -> int:
        """
        Remove old memory files, keeping most recent.

        Args:
            keep_count: Number of recent files to keep

        Returns:
            Number of files deleted
        """
        files = sorted(self.storage_dir.glob("memories_*.json"), reverse=True)
        to_delete = files[keep_count:]

        for filepath in to_delete:
            filepath.unlink()

        if to_delete:
            logger.info(f"Cleaned up {len(to_delete)} old memory files")

        return len(to_delete)
