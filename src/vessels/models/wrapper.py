"""
Model Wrapper with Rate Limiting.

Provides a unified interface for LLM interactions with
automatic rate limiting and provider abstraction.
"""

import logging
import threading
import time
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
from typing import Any, AsyncIterator, Callable, Iterator

logger = logging.getLogger(__name__)


class ModelType(str, Enum):
    """Types of models."""

    CHAT = "chat"
    EMBEDDING = "embedding"
    COMPLETION = "completion"


@dataclass
class ModelConfig:
    """Configuration for a model."""

    name: str
    provider: str
    model_type: ModelType = ModelType.CHAT
    api_base: str | None = None
    api_key: str | None = None
    context_length: int = 8192
    max_output: int = 4096
    supports_vision: bool = False
    supports_streaming: bool = True
    rate_limit_requests: int = 60  # per minute
    rate_limit_tokens: int = 100000  # per minute
    temperature: float = 0.7
    extra_kwargs: dict = field(default_factory=dict)

    def build_kwargs(self) -> dict:
        """Build kwargs for API call."""
        kwargs = {
            "model": self.name,
            "temperature": self.temperature,
            "max_tokens": self.max_output,
        }
        if self.api_base:
            kwargs["api_base"] = self.api_base
        if self.api_key:
            kwargs["api_key"] = self.api_key
        kwargs.update(self.extra_kwargs)
        return kwargs


class RateLimiter:
    """Token bucket rate limiter."""

    def __init__(
        self,
        requests_per_minute: int = 60,
        tokens_per_minute: int = 100000,
    ):
        """
        Initialize rate limiter.

        Args:
            requests_per_minute: Max requests per minute
            tokens_per_minute: Max tokens per minute
        """
        self.requests_per_minute = requests_per_minute
        self.tokens_per_minute = tokens_per_minute
        self._request_times: list[datetime] = []
        self._token_usage: list[tuple[datetime, int]] = []
        self._lock = threading.Lock()

    def acquire(self, estimated_tokens: int = 0) -> float:
        """
        Acquire permission to make a request.

        Args:
            estimated_tokens: Estimated tokens for the request

        Returns:
            Wait time in seconds (0 if no wait needed)
        """
        with self._lock:
            now = datetime.utcnow()
            minute_ago = now - timedelta(minutes=1)

            # Clean old entries
            self._request_times = [t for t in self._request_times if t > minute_ago]
            self._token_usage = [(t, n) for t, n in self._token_usage if t > minute_ago]

            # Check request limit
            wait_time = 0.0
            if len(self._request_times) >= self.requests_per_minute:
                oldest = self._request_times[0]
                wait_time = max(wait_time, (oldest - minute_ago).total_seconds())

            # Check token limit
            total_tokens = sum(n for _, n in self._token_usage)
            if total_tokens + estimated_tokens > self.tokens_per_minute:
                if self._token_usage:
                    oldest = self._token_usage[0][0]
                    wait_time = max(wait_time, (oldest - minute_ago).total_seconds())

            return wait_time

    def record_usage(self, tokens: int) -> None:
        """Record token usage."""
        with self._lock:
            now = datetime.utcnow()
            self._request_times.append(now)
            self._token_usage.append((now, tokens))

    def get_usage(self) -> dict:
        """Get current usage stats."""
        with self._lock:
            now = datetime.utcnow()
            minute_ago = now - timedelta(minutes=1)

            requests = len([t for t in self._request_times if t > minute_ago])
            tokens = sum(n for t, n in self._token_usage if t > minute_ago)

            return {
                "requests_used": requests,
                "requests_limit": self.requests_per_minute,
                "tokens_used": tokens,
                "tokens_limit": self.tokens_per_minute,
            }


class ModelWrapper:
    """
    Unified model wrapper with rate limiting.

    Provides a consistent interface for different LLM providers
    with automatic rate limiting, retry logic, and error handling.
    """

    def __init__(
        self,
        config: ModelConfig,
        call_fn: Callable[..., Any] | None = None,
        stream_fn: Callable[..., Iterator] | None = None,
        async_call_fn: Callable[..., Any] | None = None,
        async_stream_fn: Callable[..., AsyncIterator] | None = None,
    ):
        """
        Initialize model wrapper.

        Args:
            config: Model configuration
            call_fn: Synchronous call function
            stream_fn: Synchronous streaming function
            async_call_fn: Async call function
            async_stream_fn: Async streaming function
        """
        self.config = config
        self._call_fn = call_fn
        self._stream_fn = stream_fn
        self._async_call_fn = async_call_fn
        self._async_stream_fn = async_stream_fn
        self._rate_limiter = RateLimiter(
            requests_per_minute=config.rate_limit_requests,
            tokens_per_minute=config.rate_limit_tokens,
        )
        self._stats = {
            "total_calls": 0,
            "total_tokens": 0,
            "errors": 0,
            "total_latency": 0.0,
        }
        self._lock = threading.Lock()

    def call(
        self,
        messages: list[dict],
        temperature: float | None = None,
        max_tokens: int | None = None,
        **kwargs,
    ) -> dict:
        """
        Make a synchronous LLM call.

        Args:
            messages: Chat messages
            temperature: Optional temperature override
            max_tokens: Optional max tokens override
            **kwargs: Additional arguments

        Returns:
            Response dictionary
        """
        if not self._call_fn:
            raise NotImplementedError("No call function configured")

        # Estimate tokens
        estimated = self._estimate_tokens(messages)

        # Wait for rate limit
        wait_time = self._rate_limiter.acquire(estimated)
        if wait_time > 0:
            logger.debug(f"Rate limited, waiting {wait_time:.2f}s")
            time.sleep(wait_time)

        # Build kwargs
        call_kwargs = self.config.build_kwargs()
        call_kwargs["messages"] = messages
        if temperature is not None:
            call_kwargs["temperature"] = temperature
        if max_tokens is not None:
            call_kwargs["max_tokens"] = max_tokens
        call_kwargs.update(kwargs)

        # Make call
        start = time.time()
        try:
            response = self._call_fn(**call_kwargs)

            # Extract usage
            tokens = self._extract_tokens(response)
            self._rate_limiter.record_usage(tokens)

            # Update stats
            with self._lock:
                self._stats["total_calls"] += 1
                self._stats["total_tokens"] += tokens
                self._stats["total_latency"] += time.time() - start

            return response

        except Exception as e:
            with self._lock:
                self._stats["errors"] += 1
            logger.error(f"Model call failed: {e}")
            raise

    def stream(
        self,
        messages: list[dict],
        temperature: float | None = None,
        max_tokens: int | None = None,
        **kwargs,
    ) -> Iterator[dict]:
        """
        Make a streaming LLM call.

        Args:
            messages: Chat messages
            temperature: Optional temperature override
            max_tokens: Optional max tokens override
            **kwargs: Additional arguments

        Yields:
            Response chunks
        """
        if not self._stream_fn:
            raise NotImplementedError("No stream function configured")

        # Estimate tokens
        estimated = self._estimate_tokens(messages)

        # Wait for rate limit
        wait_time = self._rate_limiter.acquire(estimated)
        if wait_time > 0:
            logger.debug(f"Rate limited, waiting {wait_time:.2f}s")
            time.sleep(wait_time)

        # Build kwargs
        call_kwargs = self.config.build_kwargs()
        call_kwargs["messages"] = messages
        call_kwargs["stream"] = True
        if temperature is not None:
            call_kwargs["temperature"] = temperature
        if max_tokens is not None:
            call_kwargs["max_tokens"] = max_tokens
        call_kwargs.update(kwargs)

        # Stream
        start = time.time()
        total_tokens = 0

        try:
            for chunk in self._stream_fn(**call_kwargs):
                tokens = self._extract_chunk_tokens(chunk)
                total_tokens += tokens
                yield chunk

            # Record usage after complete
            self._rate_limiter.record_usage(total_tokens)

            with self._lock:
                self._stats["total_calls"] += 1
                self._stats["total_tokens"] += total_tokens
                self._stats["total_latency"] += time.time() - start

        except Exception as e:
            with self._lock:
                self._stats["errors"] += 1
            logger.error(f"Stream failed: {e}")
            raise

    async def acall(
        self,
        messages: list[dict],
        temperature: float | None = None,
        max_tokens: int | None = None,
        **kwargs,
    ) -> dict:
        """Make an async LLM call."""
        if not self._async_call_fn:
            raise NotImplementedError("No async call function configured")

        # Similar logic to sync call...
        estimated = self._estimate_tokens(messages)
        wait_time = self._rate_limiter.acquire(estimated)
        if wait_time > 0:
            import asyncio

            await asyncio.sleep(wait_time)

        call_kwargs = self.config.build_kwargs()
        call_kwargs["messages"] = messages
        if temperature is not None:
            call_kwargs["temperature"] = temperature
        if max_tokens is not None:
            call_kwargs["max_tokens"] = max_tokens
        call_kwargs.update(kwargs)

        start = time.time()
        try:
            response = await self._async_call_fn(**call_kwargs)
            tokens = self._extract_tokens(response)
            self._rate_limiter.record_usage(tokens)

            with self._lock:
                self._stats["total_calls"] += 1
                self._stats["total_tokens"] += tokens
                self._stats["total_latency"] += time.time() - start

            return response

        except Exception as e:
            with self._lock:
                self._stats["errors"] += 1
            raise

    async def astream(
        self,
        messages: list[dict],
        temperature: float | None = None,
        max_tokens: int | None = None,
        **kwargs,
    ) -> AsyncIterator[dict]:
        """Make an async streaming LLM call."""
        if not self._async_stream_fn:
            raise NotImplementedError("No async stream function configured")

        estimated = self._estimate_tokens(messages)
        wait_time = self._rate_limiter.acquire(estimated)
        if wait_time > 0:
            import asyncio

            await asyncio.sleep(wait_time)

        call_kwargs = self.config.build_kwargs()
        call_kwargs["messages"] = messages
        call_kwargs["stream"] = True
        if temperature is not None:
            call_kwargs["temperature"] = temperature
        if max_tokens is not None:
            call_kwargs["max_tokens"] = max_tokens
        call_kwargs.update(kwargs)

        start = time.time()
        total_tokens = 0

        try:
            async for chunk in self._async_stream_fn(**call_kwargs):
                tokens = self._extract_chunk_tokens(chunk)
                total_tokens += tokens
                yield chunk

            self._rate_limiter.record_usage(total_tokens)

            with self._lock:
                self._stats["total_calls"] += 1
                self._stats["total_tokens"] += total_tokens
                self._stats["total_latency"] += time.time() - start

        except Exception as e:
            with self._lock:
                self._stats["errors"] += 1
            raise

    def _estimate_tokens(self, messages: list[dict]) -> int:
        """Estimate tokens for messages."""
        # Simple estimation: ~4 chars per token
        total_chars = sum(len(str(m.get("content", ""))) for m in messages)
        return total_chars // 4 + 100  # Add buffer for formatting

    def _extract_tokens(self, response: dict) -> int:
        """Extract token count from response."""
        if isinstance(response, dict):
            usage = response.get("usage", {})
            return usage.get("total_tokens", 0)
        return 0

    def _extract_chunk_tokens(self, chunk: dict) -> int:
        """Extract tokens from a stream chunk."""
        # Most streaming APIs don't include token counts in chunks
        # Estimate based on content
        if isinstance(chunk, dict):
            content = ""
            if "choices" in chunk:
                for choice in chunk.get("choices", []):
                    delta = choice.get("delta", {})
                    content += delta.get("content", "")
            return len(content) // 4
        return 0

    def get_stats(self) -> dict:
        """Get wrapper statistics."""
        with self._lock:
            stats = self._stats.copy()
            stats["avg_latency"] = (
                stats["total_latency"] / stats["total_calls"]
                if stats["total_calls"] > 0
                else 0
            )
            stats["rate_limit"] = self._rate_limiter.get_usage()
            return stats

    def reset_stats(self) -> None:
        """Reset statistics."""
        with self._lock:
            self._stats = {
                "total_calls": 0,
                "total_tokens": 0,
                "errors": 0,
                "total_latency": 0.0,
            }


# Registry for model wrappers
_model_registry: dict[str, ModelWrapper] = {}
_registry_lock = threading.Lock()


def register_model(name: str, wrapper: ModelWrapper) -> None:
    """Register a model wrapper."""
    with _registry_lock:
        _model_registry[name] = wrapper


def get_model(name: str) -> ModelWrapper | None:
    """Get a registered model wrapper."""
    return _model_registry.get(name)


def list_models() -> list[str]:
    """List registered model names."""
    return list(_model_registry.keys())
