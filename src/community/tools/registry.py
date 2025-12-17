"""
Tool Registry.

Manages shared tools available to communities.
Tools are shared across all communities - "enhancing the perfection of collective".
"""

import logging
import threading
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any, Callable

logger = logging.getLogger(__name__)


class ToolCategory(str, Enum):
    """Categories of community tools."""

    DISCOVERY = "discovery"  # Finding resources
    CREATION = "creation"  # Creating content
    VALIDATION = "validation"  # Checking compliance
    SCHEDULING = "scheduling"  # Time management
    COMMUNICATION = "communication"  # Inter-agent chat
    ANALYSIS = "analysis"  # Data analysis
    GENERAL = "general"  # Multi-purpose


@dataclass
class ToolResult:
    """Result from a tool execution."""

    success: bool
    data: Any = None
    error: str | None = None
    metadata: dict = field(default_factory=dict)
    execution_time_ms: float = 0.0

    def to_dict(self) -> dict:
        """Convert to dictionary."""
        return {
            "success": self.success,
            "data": self.data,
            "error": self.error,
            "metadata": self.metadata,
            "execution_time_ms": self.execution_time_ms,
        }


class Tool(ABC):
    """
    Base class for community tools.

    All tools must implement the execute method.
    Tools are stateless - they don't maintain agent-specific state.
    """

    def __init__(self):
        """Initialize the tool."""
        self.id: str = ""
        self.name: str = ""
        self.description: str = ""
        self.category: ToolCategory = ToolCategory.GENERAL
        self.version: str = "1.0.0"

    @abstractmethod
    def execute(self, **kwargs) -> ToolResult:
        """
        Execute the tool.

        Args:
            **kwargs: Tool-specific arguments

        Returns:
            ToolResult with success status and data
        """
        pass

    def get_schema(self) -> dict:
        """Get the tool's input schema."""
        return {}

    def to_dict(self) -> dict:
        """Convert to dictionary."""
        return {
            "id": self.id,
            "name": self.name,
            "description": self.description,
            "category": self.category.value,
            "version": self.version,
            "schema": self.get_schema(),
        }


class ToolRegistry:
    """
    Registry for community tools.

    Tools are registered globally and shared across all communities.
    This embodies "I am, because we are" - tools that help one help all.
    """

    def __init__(self):
        """Initialize the registry."""
        self._tools: dict[str, Tool] = {}
        self._invocation_counts: dict[str, int] = {}
        self._lock = threading.RLock()
        self._callbacks: list[Callable[[str, ToolResult], None]] = []

    def register(self, tool: Tool) -> None:
        """
        Register a tool.

        Args:
            tool: Tool instance to register
        """
        with self._lock:
            self._tools[tool.id] = tool
            self._invocation_counts[tool.id] = 0

        logger.info(f"Registered tool: {tool.name} ({tool.id})")

    def unregister(self, tool_id: str) -> bool:
        """Unregister a tool."""
        with self._lock:
            if tool_id in self._tools:
                del self._tools[tool_id]
                return True
        return False

    def get(self, tool_id: str) -> Tool | None:
        """Get a tool by ID."""
        return self._tools.get(tool_id)

    def get_by_name(self, name: str) -> Tool | None:
        """Get a tool by name."""
        for tool in self._tools.values():
            if tool.name == name:
                return tool
        return None

    def list_all(self) -> list[Tool]:
        """List all registered tools."""
        return list(self._tools.values())

    def list_by_category(self, category: ToolCategory) -> list[Tool]:
        """List tools by category."""
        return [t for t in self._tools.values() if t.category == category]

    def invoke(
        self,
        tool_id: str,
        agent_id: str | None = None,
        community_id: str | None = None,
        **kwargs,
    ) -> ToolResult:
        """
        Invoke a tool.

        Args:
            tool_id: Tool ID to invoke
            agent_id: Invoking agent (for tracking)
            community_id: Invoking community (for tracking)
            **kwargs: Tool-specific arguments

        Returns:
            ToolResult from the tool
        """
        tool = self._tools.get(tool_id)
        if not tool:
            return ToolResult(
                success=False,
                error=f"Tool not found: {tool_id}",
            )

        start_time = datetime.utcnow()

        try:
            result = tool.execute(**kwargs)
        except Exception as e:
            logger.error(f"Tool {tool_id} execution error: {e}")
            result = ToolResult(
                success=False,
                error=str(e),
            )

        end_time = datetime.utcnow()
        result.execution_time_ms = (end_time - start_time).total_seconds() * 1000

        # Track invocation
        with self._lock:
            self._invocation_counts[tool_id] = self._invocation_counts.get(tool_id, 0) + 1

        # Add tracking metadata
        result.metadata["tool_id"] = tool_id
        result.metadata["agent_id"] = agent_id
        result.metadata["community_id"] = community_id
        result.metadata["invoked_at"] = start_time.isoformat()

        # Notify callbacks
        for callback in self._callbacks:
            try:
                callback(tool_id, result)
            except Exception as e:
                logger.error(f"Tool callback error: {e}")

        return result

    def on_invocation(self, callback: Callable[[str, ToolResult], None]) -> None:
        """Register a callback for tool invocations."""
        self._callbacks.append(callback)

    def get_stats(self) -> dict:
        """Get registry statistics."""
        return {
            "total_tools": len(self._tools),
            "by_category": {
                cat.value: len([t for t in self._tools.values() if t.category == cat])
                for cat in ToolCategory
            },
            "invocation_counts": dict(self._invocation_counts),
            "total_invocations": sum(self._invocation_counts.values()),
        }

    def export(self) -> list[dict]:
        """Export all tools as dictionaries."""
        return [t.to_dict() for t in self._tools.values()]


# Singleton instance
_tool_registry: ToolRegistry | None = None


def get_tool_registry() -> ToolRegistry:
    """Get the singleton tool registry instance."""
    global _tool_registry
    if _tool_registry is None:
        _tool_registry = ToolRegistry()
    return _tool_registry
