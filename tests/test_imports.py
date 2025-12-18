"""
Import tests - verify all modules can be imported without errors.

These tests ensure that:
1. No circular import issues
2. No missing dependencies
3. Type hints don't cause import errors
4. Package structure is correct
"""

import pytest


class TestCoreImports:
    """Test core module imports."""

    def test_import_src(self):
        """Can import src package."""
        import src
        assert src is not None

    def test_import_main(self):
        """Can import main entry point."""
        from src.main import cli
        assert callable(cli)

    def test_import_constants(self):
        """Can import constants."""
        from src.constants import NUM_VIRTUES, TARGET_CONNECTIVITY
        assert NUM_VIRTUES == 19
        assert TARGET_CONNECTIVITY == 9

    def test_import_models(self):
        """Can import models."""
        from src.models import Node, Edge, NodeType
        assert Node is not None
        assert Edge is not None


class TestGraphImports:
    """Test graph module imports."""

    def test_import_graph_client(self):
        """Can import graph client."""
        from src.graph import GraphClient, get_client, reset_client
        assert GraphClient is not None
        assert callable(get_client)
        assert callable(reset_client)

    def test_import_graph_store(self):
        """Can import graph store interface."""
        from src.graph import GraphStore, MockGraphStore, get_store
        assert GraphStore is not None
        assert MockGraphStore is not None
        assert callable(get_store)

    def test_import_safe_parse(self):
        """Can import safe parse utilities."""
        from src.graph import safe_parse_dict, safe_parse_list, serialize_for_storage
        assert callable(safe_parse_dict)
        assert callable(safe_parse_list)
        assert callable(serialize_for_storage)

    def test_import_schema(self):
        """Can import schema functions."""
        from src.graph import init_schema, clear_graph
        assert callable(init_schema)
        assert callable(clear_graph)


class TestVesselsImports:
    """Test vessels module imports."""

    def test_import_vessels(self):
        """Can import vessels package."""
        from src.vessels import (
            AgentContext,
            ContextRegistry,
            DeferredTaskManager,
        )
        assert AgentContext is not None
        assert ContextRegistry is not None
        assert DeferredTaskManager is not None

    def test_import_vessels_context(self):
        """Can import context module (was broken before fix)."""
        from src.vessels.agents.context import (
            AgentContext,
            ContextRegistry,
            ContextState,
            ContextTask,
        )
        assert AgentContext is not None
        assert ContextState.IDLE is not None

    def test_import_vessels_deferred(self):
        """Can import deferred task module."""
        from src.vessels.runtime.deferred import (
            DeferredTask,
            DeferredTaskManager,
            TaskStatus,
            TaskPriority,
        )
        assert DeferredTask is not None
        assert TaskStatus.PENDING is not None


class TestCLIImports:
    """Test CLI module imports."""

    def test_import_cli_commands(self):
        """Can import CLI commands."""
        from src.cli.commands import cli
        import click
        assert isinstance(cli, click.Group)

    def test_import_cli_module(self):
        """Can import CLI module."""
        from src.cli import commands
        assert commands is not None


class TestFunctionsImports:
    """Test functions module imports."""

    def test_import_spread(self):
        """Can import spread activation."""
        from src.functions.spread import spread_activation
        assert callable(spread_activation)

    def test_import_test_coherence(self):
        """Can import coherence testing."""
        from src.functions.test_coherence import test_coherence
        assert callable(test_coherence)


class TestKilnImports:
    """Test kiln module imports."""

    def test_import_kiln_loop(self):
        """Can import kiln loop."""
        from src.kiln.loop import run_kiln
        assert callable(run_kiln)


class TestSituationsImports:
    """Test situations module imports."""

    def test_import_situations_persistence(self):
        """Can import situation persistence."""
        from src.situations.persistence import (
            save_situation,
            load_situation,
            list_situations,
        )
        assert callable(save_situation)
        assert callable(load_situation)


class TestSubstrateImports:
    """Test substrate imports."""

    def test_import_graph_substrate(self):
        """Can import GraphSubstrate."""
        from src.graph.substrate import GraphSubstrate
        assert GraphSubstrate is not None

    def test_substrate_has_query_method(self):
        """GraphSubstrate has query method for GraphStore compatibility."""
        from src.graph.substrate import GraphSubstrate
        assert hasattr(GraphSubstrate, "query")
        assert hasattr(GraphSubstrate, "execute")
