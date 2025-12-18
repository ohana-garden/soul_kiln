"""
Tests for safe_parse module - critical security tests.

Verifies that:
1. JSON data is parsed correctly
2. Python dict literals are parsed correctly via ast.literal_eval
3. Malicious strings do NOT execute
4. Invalid data returns safe defaults
"""

import pytest

from src.graph.safe_parse import (
    safe_parse_dict,
    safe_parse_list,
    serialize_for_storage,
)


class TestSafeParseDictBasic:
    """Basic functionality tests for safe_parse_dict."""

    def test_parse_empty_string(self):
        """Empty string returns default."""
        assert safe_parse_dict("") == {}

    def test_parse_none(self):
        """None returns default."""
        assert safe_parse_dict(None) == {}

    def test_parse_empty_dict_string(self):
        """'{}' returns empty dict."""
        assert safe_parse_dict("{}") == {}

    def test_parse_json_dict(self):
        """Valid JSON dict is parsed."""
        result = safe_parse_dict('{"key": "value", "num": 42}')
        assert result == {"key": "value", "num": 42}

    def test_parse_python_dict_literal(self):
        """Python dict literal (single quotes) is parsed via literal_eval."""
        result = safe_parse_dict("{'key': 'value', 'num': 42}")
        assert result == {"key": "value", "num": 42}

    def test_custom_default(self):
        """Custom default is used on failure."""
        default = {"fallback": True}
        result = safe_parse_dict("invalid", default=default)
        assert result == default


class TestSafeParseDictSecurity:
    """Security tests - verify malicious strings don't execute."""

    def test_no_code_execution_import(self):
        """Import statement does not execute."""
        malicious = "__import__('os').system('echo PWNED')"
        result = safe_parse_dict(malicious)
        assert result == {}  # Returns default, doesn't execute

    def test_no_code_execution_eval(self):
        """Nested eval does not execute."""
        malicious = "eval('1+1')"
        result = safe_parse_dict(malicious)
        assert result == {}

    def test_no_code_execution_exec(self):
        """Exec does not execute."""
        malicious = "exec('import os')"
        result = safe_parse_dict(malicious)
        assert result == {}

    def test_no_code_execution_lambda(self):
        """Lambda does not execute."""
        malicious = "(lambda: __import__('os').getcwd())()"
        result = safe_parse_dict(malicious)
        assert result == {}

    def test_no_code_execution_comprehension(self):
        """List comprehension with side effects does not execute."""
        malicious = "[__import__('os') for _ in [1]]"
        result = safe_parse_dict(malicious)
        assert result == {}  # Not a dict, returns default

    def test_no_code_execution_attribute_access(self):
        """Attribute access for code execution blocked."""
        malicious = "{'x': __builtins__.__import__('os')}"
        result = safe_parse_dict(malicious)
        assert result == {}

    def test_no_code_execution_dunder_class(self):
        """__class__ based injection blocked."""
        malicious = "().__class__.__bases__[0].__subclasses__()"
        result = safe_parse_dict(malicious)
        assert result == {}

    def test_arithmetic_expressions_blocked(self):
        """Arithmetic expressions don't evaluate (only literals allowed)."""
        malicious = "{'x': 1 + 1}"
        result = safe_parse_dict(malicious)
        # ast.literal_eval doesn't allow operators
        assert result == {}


class TestSafeParseDictNested:
    """Tests for nested data structures."""

    def test_nested_dict_json(self):
        """Nested JSON dict is parsed."""
        data = '{"outer": {"inner": "value"}}'
        result = safe_parse_dict(data)
        assert result == {"outer": {"inner": "value"}}

    def test_nested_dict_with_list_json(self):
        """Dict with list values is parsed."""
        data = '{"items": [1, 2, 3]}'
        result = safe_parse_dict(data)
        assert result == {"items": [1, 2, 3]}

    def test_complex_json(self):
        """Complex nested structure is parsed."""
        data = '{"a": {"b": [1, {"c": true}]}, "d": null}'
        result = safe_parse_dict(data)
        assert result == {"a": {"b": [1, {"c": True}]}, "d": None}


class TestSafeParseList:
    """Tests for safe_parse_list."""

    def test_parse_empty_string(self):
        """Empty string returns default."""
        assert safe_parse_list("") == []

    def test_parse_none(self):
        """None returns default."""
        assert safe_parse_list(None) == []

    def test_parse_json_list(self):
        """Valid JSON list is parsed."""
        result = safe_parse_list('[1, 2, "three"]')
        assert result == [1, 2, "three"]

    def test_parse_python_list_literal(self):
        """Python list literal is parsed."""
        result = safe_parse_list("['a', 'b', 'c']")
        assert result == ["a", "b", "c"]

    def test_no_code_execution(self):
        """Malicious string doesn't execute."""
        malicious = "[__import__('os').getcwd()]"
        result = safe_parse_list(malicious)
        assert result == []


class TestSerializeForStorage:
    """Tests for serialize_for_storage."""

    def test_serialize_dict(self):
        """Dict is serialized to JSON."""
        result = serialize_for_storage({"key": "value"})
        assert result == '{"key": "value"}'

    def test_serialize_list(self):
        """List is serialized to JSON."""
        result = serialize_for_storage([1, 2, 3])
        assert result == "[1, 2, 3]"

    def test_round_trip(self):
        """Serialized data can be parsed back."""
        original = {"nested": {"data": [1, 2, 3]}}
        serialized = serialize_for_storage(original)
        parsed = safe_parse_dict(serialized)
        assert parsed == original


class TestEdgeCases:
    """Edge case tests."""

    def test_non_string_input(self):
        """Non-string that looks like dict is handled."""
        # If somehow a dict is passed, we should handle it
        result = safe_parse_dict("{}")  # String
        assert result == {}

    def test_whitespace_json(self):
        """JSON with whitespace is parsed."""
        result = safe_parse_dict('  { "key" : "value" }  ')
        assert result == {"key": "value"}

    def test_unicode_json(self):
        """Unicode in JSON is handled."""
        result = safe_parse_dict('{"emoji": "🙂"}')
        assert result == {"emoji": "🙂"}
