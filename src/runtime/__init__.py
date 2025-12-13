"""
Runtime Module.

The system boots entirely from the graph database. This module provides:
- Boot loader: Initializes everything from graph
- SSF Registry: Manages Stored Soul Functions (executable code in graph)
- Agent Factory: Creates agents from graph definitions
- Bridge: Connects to Agent Zero for execution
"""
from .loaders import GraphPromptLoader, GraphToolLoader, GraphInstrumentLoader
from .factory import GraphAgentFactory
from .agent import GraphHydratedAgent
from .bridge import AgentZeroBridge, get_bridge
from .ssf import SSFRegistry, get_ssf_registry, create_ssf, link_ssf_to_agent_type
from .boot import boot, quick_boot, BootConfig, BootedSystem

__all__ = [
    # Boot
    "boot",
    "quick_boot",
    "BootConfig",
    "BootedSystem",
    # SSF
    "SSFRegistry",
    "get_ssf_registry",
    "create_ssf",
    "link_ssf_to_agent_type",
    # Loaders
    "GraphPromptLoader",
    "GraphToolLoader",
    "GraphInstrumentLoader",
    # Factory & Agent
    "GraphAgentFactory",
    "GraphHydratedAgent",
    # Bridge
    "AgentZeroBridge",
    "get_bridge",
]
