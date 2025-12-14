"""
Document Query Tool.

Provides document querying and content extraction capabilities.
"""

import hashlib
import logging
import os
import re
import tempfile
import urllib.request
import uuid
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Any
from urllib.parse import urlparse

logger = logging.getLogger(__name__)


@dataclass
class QueryResult:
    """Result of a document query."""

    id: str = field(default_factory=lambda: f"qry_{uuid.uuid4().hex[:8]}")
    source: str = ""
    source_type: str = ""  # url, file
    content: str = ""
    answers: dict[str, str] = field(default_factory=dict)  # question -> answer
    metadata: dict = field(default_factory=dict)
    success: bool = False
    error: str | None = None
    queried_at: datetime = field(default_factory=datetime.utcnow)

    def to_dict(self) -> dict:
        """Convert to dictionary."""
        return {
            "id": self.id,
            "source": self.source,
            "source_type": self.source_type,
            "content_length": len(self.content),
            "answers": self.answers,
            "metadata": self.metadata,
            "success": self.success,
            "error": self.error,
            "queried_at": self.queried_at.isoformat(),
        }


class DocumentQuery:
    """
    Document query tool for extracting content from various sources.

    Features:
    - URL and file path support
    - Multi-document processing
    - Content extraction and querying
    - Format support: HTML, PDF, text, etc.
    """

    def __init__(
        self,
        cache_dir: str | None = None,
        cache_ttl: int = 3600,
        max_content_size: int = 1_000_000,
        query_fn: Any | None = None,
    ):
        """
        Initialize document query tool.

        Args:
            cache_dir: Directory for caching fetched documents
            cache_ttl: Cache time-to-live in seconds
            max_content_size: Maximum content size to process
            query_fn: Optional LLM function for intelligent querying
        """
        self.cache_dir = Path(cache_dir) if cache_dir else Path(tempfile.gettempdir()) / "doc_cache"
        self.cache_ttl = cache_ttl
        self.max_content_size = max_content_size
        self.query_fn = query_fn
        self._cache: dict[str, tuple[str, datetime]] = {}

        self.cache_dir.mkdir(parents=True, exist_ok=True)

    def query(
        self,
        sources: str | list[str],
        questions: str | list[str] | None = None,
    ) -> list[QueryResult]:
        """
        Query one or more documents.

        Args:
            sources: URL(s) or file path(s) to query
            questions: Optional question(s) to answer from the documents

        Returns:
            List of QueryResult objects
        """
        if isinstance(sources, str):
            sources = [sources]
        if isinstance(questions, str):
            questions = [questions]

        results = []
        for source in sources:
            result = self._query_single(source, questions)
            results.append(result)

        return results

    def _query_single(
        self,
        source: str,
        questions: list[str] | None,
    ) -> QueryResult:
        """Query a single document."""
        result = QueryResult(source=source)

        try:
            # Determine source type and fetch content
            if source.startswith(("http://", "https://")):
                result.source_type = "url"
                content = self._fetch_url(source)
            elif source.startswith("file://"):
                result.source_type = "file"
                file_path = source[7:]
                content = self._read_file(file_path)
            else:
                # Assume file path
                result.source_type = "file"
                content = self._read_file(source)

            result.content = content
            result.metadata["content_length"] = len(content)

            # Process content based on format
            processed = self._process_content(source, content)
            if processed != content:
                result.content = processed
                result.metadata["processed"] = True

            # Answer questions if provided
            if questions and self.query_fn:
                for question in questions:
                    answer = self._answer_question(processed, question)
                    result.answers[question] = answer

            result.success = True

        except Exception as e:
            result.success = False
            result.error = str(e)
            logger.error(f"Error querying {source}: {e}")

        return result

    def _fetch_url(self, url: str) -> str:
        """Fetch content from URL."""
        # Check cache
        cache_key = hashlib.md5(url.encode()).hexdigest()
        if cache_key in self._cache:
            content, cached_at = self._cache[cache_key]
            age = (datetime.utcnow() - cached_at).total_seconds()
            if age < self.cache_ttl:
                logger.debug(f"Cache hit for {url}")
                return content

        # Fetch
        req = urllib.request.Request(
            url,
            headers={"User-Agent": "Mozilla/5.0 (compatible; DocumentQuery/1.0)"},
        )

        with urllib.request.urlopen(req, timeout=30) as response:
            content = response.read()

            # Detect encoding
            charset = response.headers.get_content_charset() or "utf-8"
            try:
                text = content.decode(charset)
            except UnicodeDecodeError:
                text = content.decode("utf-8", errors="replace")

        # Enforce size limit
        if len(text) > self.max_content_size:
            text = text[: self.max_content_size]
            logger.warning(f"Truncated content from {url}")

        # Cache
        self._cache[cache_key] = (text, datetime.utcnow())

        return text

    def _read_file(self, file_path: str) -> str:
        """Read content from file."""
        path = Path(file_path)
        if not path.exists():
            raise FileNotFoundError(f"File not found: {file_path}")

        # Handle different file types
        suffix = path.suffix.lower()

        if suffix == ".pdf":
            return self._read_pdf(path)
        elif suffix in (".html", ".htm"):
            with open(path, "r", encoding="utf-8") as f:
                return self._html_to_text(f.read())
        elif suffix in (".doc", ".docx"):
            return self._read_docx(path)
        else:
            with open(path, "r", encoding="utf-8") as f:
                return f.read()

    def _process_content(self, source: str, content: str) -> str:
        """Process content based on format."""
        # Detect HTML
        if "<html" in content.lower() or "<!doctype html" in content.lower():
            return self._html_to_text(content)

        return content

    def _html_to_text(self, html: str) -> str:
        """Convert HTML to plain text."""
        # Remove scripts and styles
        html = re.sub(r"<script[^>]*>.*?</script>", "", html, flags=re.DOTALL | re.I)
        html = re.sub(r"<style[^>]*>.*?</style>", "", html, flags=re.DOTALL | re.I)

        # Remove HTML tags
        text = re.sub(r"<[^>]+>", " ", html)

        # Decode entities
        text = text.replace("&nbsp;", " ")
        text = text.replace("&lt;", "<")
        text = text.replace("&gt;", ">")
        text = text.replace("&amp;", "&")
        text = text.replace("&quot;", '"')

        # Clean whitespace
        text = re.sub(r"\s+", " ", text)
        text = text.strip()

        return text

    def _read_pdf(self, path: Path) -> str:
        """Read content from PDF file."""
        try:
            import PyPDF2

            with open(path, "rb") as f:
                reader = PyPDF2.PdfReader(f)
                text = ""
                for page in reader.pages:
                    text += page.extract_text() + "\n"
                return text
        except ImportError:
            logger.warning("PyPDF2 not installed, returning raw content indicator")
            return f"[PDF file: {path.name} - install PyPDF2 to extract content]"

    def _read_docx(self, path: Path) -> str:
        """Read content from Word document."""
        try:
            from docx import Document

            doc = Document(path)
            text = "\n".join(para.text for para in doc.paragraphs)
            return text
        except ImportError:
            logger.warning("python-docx not installed")
            return f"[Word file: {path.name} - install python-docx to extract content]"

    def _answer_question(self, content: str, question: str) -> str:
        """Answer a question about the content."""
        if not self.query_fn:
            return "[No query function configured]"

        try:
            # Truncate content if needed for LLM context
            max_context = 10000
            if len(content) > max_context:
                content = content[:max_context] + "... [truncated]"

            return self.query_fn(content, question)
        except Exception as e:
            return f"[Error answering question: {e}]"

    def extract_content(self, source: str) -> str:
        """
        Extract full content from a document.

        Args:
            source: URL or file path

        Returns:
            Extracted text content
        """
        result = self._query_single(source, None)
        if result.success:
            return result.content
        raise ValueError(result.error or "Failed to extract content")

    def compare_documents(
        self,
        sources: list[str],
        aspects: list[str] | None = None,
    ) -> dict:
        """
        Compare multiple documents.

        Args:
            sources: List of document sources
            aspects: Optional aspects to compare

        Returns:
            Comparison results
        """
        results = self.query(sources)

        comparison = {
            "sources": sources,
            "success_count": sum(1 for r in results if r.success),
            "documents": {},
        }

        for result in results:
            doc_info = {
                "success": result.success,
                "content_length": len(result.content) if result.success else 0,
                "error": result.error,
            }

            if aspects and self.query_fn and result.success:
                doc_info["aspects"] = {}
                for aspect in aspects:
                    answer = self._answer_question(
                        result.content, f"What does this document say about {aspect}?"
                    )
                    doc_info["aspects"][aspect] = answer

            comparison["documents"][result.source] = doc_info

        return comparison

    def clear_cache(self) -> int:
        """Clear the document cache."""
        count = len(self._cache)
        self._cache.clear()
        return count

    def get_stats(self) -> dict:
        """Get query statistics."""
        return {
            "cache_size": len(self._cache),
            "cache_dir": str(self.cache_dir),
            "max_content_size": self.max_content_size,
            "has_query_fn": self.query_fn is not None,
        }
