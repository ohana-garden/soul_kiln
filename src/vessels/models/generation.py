"""
Chat Generation Result with Reasoning Separation.

Handles streaming responses with separation of reasoning
and response content.
"""

import logging
import re
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any

logger = logging.getLogger(__name__)


@dataclass
class ChatChunk:
    """A streaming response chunk."""

    response_delta: str = ""
    reasoning_delta: str = ""
    metadata: dict = field(default_factory=dict)


@dataclass
class ThinkingPair:
    """A pair of thinking/reasoning content."""

    thinking: str
    tag: str = "thinking"
    start_pos: int = 0
    end_pos: int = 0


class ChatGenerationResult:
    """
    Accumulates and processes streaming response chunks.

    Features:
    - Separates reasoning from response content
    - Handles thinking tags (<thinking>, <reasoning>, etc.)
    - Supports native reasoning from providers
    - Provides structured access to all components
    """

    # Common thinking/reasoning tags
    THINKING_TAGS = [
        "thinking",
        "reasoning",
        "thought",
        "analysis",
        "reflection",
        "deliberation",
    ]

    def __init__(
        self,
        custom_thinking_tags: list[str] | None = None,
        strip_thinking_from_response: bool = True,
    ):
        """
        Initialize generation result.

        Args:
            custom_thinking_tags: Additional tags to treat as thinking
            strip_thinking_from_response: Whether to remove thinking from response
        """
        self._raw_content = ""
        self._response = ""
        self._reasoning = ""
        self._thinking_pairs: list[ThinkingPair] = []
        self._native_reasoning: str | None = None
        self._unprocessed = ""
        self._thinking_tags = list(self.THINKING_TAGS)
        if custom_thinking_tags:
            self._thinking_tags.extend(custom_thinking_tags)
        self._strip_thinking = strip_thinking_from_response
        self._metadata: dict = {}
        self._chunks_received = 0
        self._started_at = datetime.utcnow()
        self._completed_at: datetime | None = None
        self._in_thinking = False
        self._current_thinking_tag = ""
        self._thinking_buffer = ""

    def add_chunk(self, chunk: ChatChunk | dict | str) -> None:
        """
        Add a response chunk.

        Args:
            chunk: The chunk to add (ChatChunk, dict, or string)
        """
        self._chunks_received += 1

        # Normalize chunk
        if isinstance(chunk, str):
            content = chunk
            reasoning = ""
        elif isinstance(chunk, dict):
            content = self._extract_content(chunk)
            reasoning = self._extract_reasoning(chunk)
        else:
            content = chunk.response_delta
            reasoning = chunk.reasoning_delta

        # Handle native reasoning
        if reasoning:
            if self._native_reasoning is None:
                self._native_reasoning = ""
            self._native_reasoning += reasoning

        # Add to raw content
        self._raw_content += content

        # Process for thinking tags
        self._process_content(content)

    def _extract_content(self, chunk: dict) -> str:
        """Extract content from a chunk dictionary."""
        # Handle OpenAI format
        if "choices" in chunk:
            for choice in chunk.get("choices", []):
                delta = choice.get("delta", {})
                if "content" in delta:
                    return delta["content"]

        # Handle direct content
        if "content" in chunk:
            return chunk["content"]

        # Handle message format
        if "message" in chunk:
            return chunk["message"].get("content", "")

        return ""

    def _extract_reasoning(self, chunk: dict) -> str:
        """Extract reasoning from a chunk dictionary."""
        # Handle Claude format
        if "reasoning" in chunk:
            return chunk["reasoning"]

        # Handle OpenAI-style
        if "choices" in chunk:
            for choice in chunk.get("choices", []):
                delta = choice.get("delta", {})
                if "reasoning" in delta:
                    return delta["reasoning"]

        return ""

    def _process_content(self, content: str) -> None:
        """Process content for thinking tags."""
        self._unprocessed += content

        # Process complete thinking blocks
        while True:
            if self._in_thinking:
                # Look for closing tag
                close_pattern = f"</{self._current_thinking_tag}>"
                close_pos = self._unprocessed.find(close_pattern)

                if close_pos >= 0:
                    # Extract thinking content
                    thinking_content = self._unprocessed[:close_pos]
                    self._thinking_buffer += thinking_content
                    self._reasoning += self._thinking_buffer

                    # Record thinking pair
                    self._thinking_pairs.append(
                        ThinkingPair(
                            thinking=self._thinking_buffer,
                            tag=self._current_thinking_tag,
                        )
                    )

                    # Move past closing tag
                    self._unprocessed = self._unprocessed[close_pos + len(close_pattern) :]
                    self._in_thinking = False
                    self._thinking_buffer = ""
                    self._current_thinking_tag = ""
                else:
                    # Still accumulating thinking
                    self._thinking_buffer += self._unprocessed
                    self._unprocessed = ""
                    break

            else:
                # Look for opening tag
                found_tag = None
                found_pos = len(self._unprocessed)

                for tag in self._thinking_tags:
                    open_pattern = f"<{tag}>"
                    pos = self._unprocessed.find(open_pattern)
                    if pos >= 0 and pos < found_pos:
                        found_tag = tag
                        found_pos = pos

                if found_tag:
                    # Add content before tag to response
                    if not self._strip_thinking:
                        self._response += self._unprocessed[: found_pos]
                    else:
                        self._response += self._unprocessed[:found_pos]

                    # Enter thinking mode
                    open_pattern = f"<{found_tag}>"
                    self._unprocessed = self._unprocessed[found_pos + len(open_pattern) :]
                    self._in_thinking = True
                    self._current_thinking_tag = found_tag
                else:
                    # No thinking tag found, all is response
                    self._response += self._unprocessed
                    self._unprocessed = ""
                    break

    def complete(self) -> None:
        """Mark generation as complete."""
        self._completed_at = datetime.utcnow()

        # Flush any remaining content
        if self._in_thinking:
            # Incomplete thinking block
            self._reasoning += self._thinking_buffer
            self._thinking_pairs.append(
                ThinkingPair(
                    thinking=self._thinking_buffer,
                    tag=self._current_thinking_tag,
                )
            )
        else:
            self._response += self._unprocessed

        self._unprocessed = ""

    @property
    def response(self) -> str:
        """Get the response content (without thinking)."""
        return self._response.strip()

    @property
    def reasoning(self) -> str:
        """Get accumulated reasoning content."""
        all_reasoning = self._reasoning
        if self._native_reasoning:
            all_reasoning = self._native_reasoning + "\n" + all_reasoning
        return all_reasoning.strip()

    @property
    def thinking(self) -> str:
        """Alias for reasoning."""
        return self.reasoning

    @property
    def raw_content(self) -> str:
        """Get raw unprocessed content."""
        return self._raw_content

    @property
    def thinking_pairs(self) -> list[ThinkingPair]:
        """Get all thinking/reasoning pairs."""
        return self._thinking_pairs

    @property
    def has_thinking(self) -> bool:
        """Check if any thinking/reasoning was extracted."""
        return bool(self._reasoning or self._native_reasoning)

    @property
    def native_reasoning(self) -> str | None:
        """Get native reasoning from provider (if any)."""
        return self._native_reasoning

    @property
    def is_complete(self) -> bool:
        """Check if generation is complete."""
        return self._completed_at is not None

    @property
    def duration_seconds(self) -> float | None:
        """Get generation duration."""
        if self._completed_at:
            return (self._completed_at - self._started_at).total_seconds()
        return None

    def output(self, include_thinking: bool = False) -> str:
        """
        Get final output.

        Args:
            include_thinking: Whether to include thinking content

        Returns:
            Final output string
        """
        if include_thinking and self.has_thinking:
            return f"<thinking>\n{self.reasoning}\n</thinking>\n\n{self.response}"
        return self.response

    def to_dict(self) -> dict:
        """Convert to dictionary."""
        return {
            "response": self.response,
            "reasoning": self.reasoning,
            "has_thinking": self.has_thinking,
            "native_reasoning": self._native_reasoning,
            "thinking_pairs": [
                {"thinking": p.thinking, "tag": p.tag} for p in self._thinking_pairs
            ],
            "chunks_received": self._chunks_received,
            "started_at": self._started_at.isoformat(),
            "completed_at": self._completed_at.isoformat() if self._completed_at else None,
            "duration_seconds": self.duration_seconds,
        }

    def __str__(self) -> str:
        """String representation."""
        return self.response

    def __repr__(self) -> str:
        """Detailed representation."""
        return (
            f"ChatGenerationResult("
            f"response_len={len(self.response)}, "
            f"reasoning_len={len(self.reasoning)}, "
            f"chunks={self._chunks_received})"
        )
