"""
Semantic Memory Module.

Provides vector-based semantic memory with:
- Embedding-based storage and retrieval
- Threshold-based similarity search
- Metadata filtering
- Memory consolidation
"""

from .semantic import SemanticMemory, MemoryEntry
from .store import MemoryStore

__all__ = ["SemanticMemory", "MemoryEntry", "MemoryStore"]
