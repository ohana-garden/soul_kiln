"""
Safe parsing utilities for graph data.

Provides safe alternatives to eval() for parsing data stored in the graph.
"""

import ast
import json
import logging
from typing import Any

logger = logging.getLogger(__name__)


def safe_parse_dict(data: str | None, default: dict | None = None) -> dict:
    """
    Safely parse a string representation of a dict.

    Attempts JSON parsing first (preferred), then falls back to
    ast.literal_eval for Python dict literals. Never uses eval().

    Args:
        data: String to parse, or None
        default: Default value if parsing fails (defaults to empty dict)

    Returns:
        Parsed dict or default value

    Security:
        - JSON.loads only parses JSON, cannot execute code
        - ast.literal_eval only evaluates literals, cannot execute code
        - Never uses eval() which could execute arbitrary code
    """
    if default is None:
        default = {}

    if not data:
        return default

    if data == "{}":
        return default

    # Try JSON first (preferred format)
    try:
        result = json.loads(data)
        if isinstance(result, dict):
            return result
        logger.warning(f"JSON parsed but not a dict: {type(result)}")
        return default
    except json.JSONDecodeError:
        pass

    # Fall back to ast.literal_eval for Python dict literals
    # This is safe - only parses literals, no code execution
    try:
        result = ast.literal_eval(data)
        if isinstance(result, dict):
            return result
        logger.warning(f"literal_eval parsed but not a dict: {type(result)}")
        return default
    except (ValueError, SyntaxError) as e:
        logger.warning(f"Failed to parse dict string: {e}")
        return default


def safe_parse_list(data: str | None, default: list | None = None) -> list:
    """
    Safely parse a string representation of a list.

    Args:
        data: String to parse, or None
        default: Default value if parsing fails (defaults to empty list)

    Returns:
        Parsed list or default value
    """
    if default is None:
        default = []

    if not data:
        return default

    if data == "[]":
        return default

    # Try JSON first
    try:
        result = json.loads(data)
        if isinstance(result, list):
            return result
        logger.warning(f"JSON parsed but not a list: {type(result)}")
        return default
    except json.JSONDecodeError:
        pass

    # Fall back to ast.literal_eval
    try:
        result = ast.literal_eval(data)
        if isinstance(result, list):
            return result
        logger.warning(f"literal_eval parsed but not a list: {type(result)}")
        return default
    except (ValueError, SyntaxError) as e:
        logger.warning(f"Failed to parse list string: {e}")
        return default


def serialize_for_storage(data: Any) -> str:
    """
    Serialize data for storage in the graph.

    Uses JSON for consistent serialization.

    Args:
        data: Data to serialize

    Returns:
        JSON string representation
    """
    return json.dumps(data)
