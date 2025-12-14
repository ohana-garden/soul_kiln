"""
Anthropic LLM Client for Soul Kiln.

Provides a simple interface to Claude for agent responses.
"""
import logging
from typing import Optional, List, Dict, Any
from dataclasses import dataclass

from src.settings import settings

logger = logging.getLogger(__name__)

# Try to import Anthropic
try:
    import anthropic
    ANTHROPIC_AVAILABLE = True
except ImportError:
    ANTHROPIC_AVAILABLE = False
    logger.warning("Anthropic package not installed")


@dataclass
class LLMResponse:
    """Response from LLM."""
    content: str
    model: str
    input_tokens: int
    output_tokens: int
    stop_reason: str


class LLMClient:
    """Client for Anthropic Claude API."""

    def __init__(self):
        self._client = None
        self._configured = False

        if not ANTHROPIC_AVAILABLE:
            logger.warning("Anthropic not available - LLM calls will fail")
            return

        if not settings.llm.is_configured:
            logger.warning("Anthropic API key not configured - LLM calls will fail")
            return

        try:
            self._client = anthropic.Anthropic(api_key=settings.llm.api_key)
            self._configured = True
            logger.info(f"LLM client initialized (model={settings.llm.model})")
        except Exception as e:
            logger.error(f"Failed to initialize Anthropic client: {e}")

    @property
    def is_configured(self) -> bool:
        """Check if the LLM client is properly configured."""
        return self._configured and self._client is not None

    def generate(
        self,
        system_prompt: str,
        user_message: str,
        max_tokens: int = None,
        temperature: float = 0.7,
        stop_sequences: List[str] = None,
    ) -> LLMResponse:
        """
        Generate a response from Claude.

        Args:
            system_prompt: The system prompt defining agent behavior
            user_message: The user's message
            max_tokens: Maximum tokens to generate (default from settings)
            temperature: Sampling temperature (0-1)
            stop_sequences: Optional stop sequences

        Returns:
            LLMResponse with generated content and metadata

        Raises:
            RuntimeError: If LLM is not configured
            Exception: For API errors
        """
        if not self.is_configured:
            raise RuntimeError(
                "LLM not configured. Set ANTHROPIC_API_KEY environment variable."
            )

        max_tokens = max_tokens or settings.llm.max_tokens

        try:
            response = self._client.messages.create(
                model=settings.llm.model,
                max_tokens=max_tokens,
                temperature=temperature,
                system=system_prompt,
                messages=[
                    {"role": "user", "content": user_message}
                ],
                stop_sequences=stop_sequences or [],
            )

            content = response.content[0].text if response.content else ""

            return LLMResponse(
                content=content,
                model=response.model,
                input_tokens=response.usage.input_tokens,
                output_tokens=response.usage.output_tokens,
                stop_reason=response.stop_reason,
            )

        except anthropic.APIConnectionError as e:
            logger.error(f"API connection error: {e}")
            raise
        except anthropic.RateLimitError as e:
            logger.error(f"Rate limit exceeded: {e}")
            raise
        except anthropic.APIStatusError as e:
            logger.error(f"API status error: {e}")
            raise

    def generate_with_tools(
        self,
        system_prompt: str,
        user_message: str,
        tools: List[Dict[str, Any]],
        max_tokens: int = None,
        temperature: float = 0.7,
    ) -> Dict[str, Any]:
        """
        Generate a response that may include tool calls.

        Args:
            system_prompt: The system prompt
            user_message: The user's message
            tools: List of tool definitions in Claude format
            max_tokens: Maximum tokens
            temperature: Sampling temperature

        Returns:
            Dict with 'content', 'tool_calls', and 'metadata'
        """
        if not self.is_configured:
            raise RuntimeError("LLM not configured")

        max_tokens = max_tokens or settings.llm.max_tokens

        try:
            response = self._client.messages.create(
                model=settings.llm.model,
                max_tokens=max_tokens,
                temperature=temperature,
                system=system_prompt,
                messages=[
                    {"role": "user", "content": user_message}
                ],
                tools=tools if tools else [],
            )

            # Parse response content
            text_content = ""
            tool_calls = []

            for block in response.content:
                if block.type == "text":
                    text_content += block.text
                elif block.type == "tool_use":
                    tool_calls.append({
                        "id": block.id,
                        "name": block.name,
                        "input": block.input,
                    })

            return {
                "content": text_content,
                "tool_calls": tool_calls,
                "metadata": {
                    "model": response.model,
                    "input_tokens": response.usage.input_tokens,
                    "output_tokens": response.usage.output_tokens,
                    "stop_reason": response.stop_reason,
                },
            }

        except Exception as e:
            logger.error(f"Tool-based generation failed: {e}")
            raise

    def continue_with_tool_results(
        self,
        system_prompt: str,
        messages: List[Dict[str, Any]],
        max_tokens: int = None,
        temperature: float = 0.7,
    ) -> LLMResponse:
        """
        Continue a conversation after tool execution.

        Args:
            system_prompt: The system prompt
            messages: Full conversation including tool results
            max_tokens: Maximum tokens
            temperature: Sampling temperature

        Returns:
            LLMResponse with final content
        """
        if not self.is_configured:
            raise RuntimeError("LLM not configured")

        max_tokens = max_tokens or settings.llm.max_tokens

        try:
            response = self._client.messages.create(
                model=settings.llm.model,
                max_tokens=max_tokens,
                temperature=temperature,
                system=system_prompt,
                messages=messages,
            )

            content = response.content[0].text if response.content else ""

            return LLMResponse(
                content=content,
                model=response.model,
                input_tokens=response.usage.input_tokens,
                output_tokens=response.usage.output_tokens,
                stop_reason=response.stop_reason,
            )

        except Exception as e:
            logger.error(f"Continuation failed: {e}")
            raise


# Singleton instance
_llm_client: Optional[LLMClient] = None


def get_llm_client() -> LLMClient:
    """Get singleton LLM client instance."""
    global _llm_client
    if _llm_client is None:
        _llm_client = LLMClient()
    return _llm_client
