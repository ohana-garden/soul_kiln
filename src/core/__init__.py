"""
Core domain models for Soul Kiln.

Soul_kiln provides graph operations for Agent Zero (A0).
A0 is the runtime/orchestrator. Soul_kiln provides:
- Entity/Proxy/Community models
- Developmental biology (biomimicry)
- Virtue basins
- Graph operations (Cypher → FalkorDB)

The core flow:
1. A0 receives human input
2. A0 decides to spawn an agent → calls spawn_agent()
3. Agent node created in graph (Entity → Proxy → Agent)
4. A0 processes conversations → calls develop_agent()
5. Differentiation signals accumulate in graph
6. A0 triggers metamorphosis when ready → calls metamorphose_agent()
7. Mature agents can spawn offspring → calls spawn_offspring()

Everything bottoms out at Cypher queries against FalkorDB.
"""

from .entity import Entity, EntityType
from .proxy import Proxy, ProxyType, ProxyConfig, ProxyStatus
from .community import Community, CommunityPurpose, VirtueEmphasis
from .graph_store import CoreGraphStore, get_core_store
from .creation import ProxyCreator, CreationState, create_proxy_conversation
from .sharing import CommunitySharing, get_sharing, share_learning
from .seeding import (
    EntitySeeder,
    SeedStrategy,
    SeedConfig,
    SeedState,
    get_seeder,
    seed_curious_entity,
    list_seed_templates,
    SEED_TEMPLATES,
)
from .biomimicry import (
    Potency,
    LifeStage,
    DifferentiationSignal,
    DifferentiationPressure,
    CommunityNiche,
    QuorumState,
    ChrysalisState,
    MetamorphosisPhase,
    FusionProposal,
    DevelopmentalState,
    VIRTUE_TYPE_ASSOCIATIONS,
    ENTITY_CATEGORIES,
)
from .development import (
    DevelopmentalManager,
    get_dev_manager,
    TOPIC_TYPE_ASSOCIATIONS,
)
from .instruments import (
    # Result type
    Result,
    # Foundation
    cypher,
    # Entity operations
    create_entity,
    get_entity,
    # Proxy operations
    create_proxy,
    # Agent node operations
    create_agent_node,
    join_community,
    # Development operations
    add_differentiation_signal,
    get_differentiation_signals,
    update_life_stage,
    set_entity_type,
    # Sharing operations
    share_lesson,
    # Virtue operations
    record_virtue_activation,
    # Composite operations (A0 tools)
    spawn_agent,
    develop_agent,
    metamorphose_agent,
    spawn_offspring,
    fuse_agents,
)

__all__ = [
    # Entity
    "Entity",
    "EntityType",
    # Proxy
    "Proxy",
    "ProxyType",
    "ProxyConfig",
    "ProxyStatus",
    # Community
    "Community",
    "CommunityPurpose",
    "VirtueEmphasis",
    # Storage
    "CoreGraphStore",
    "get_core_store",
    # Creation
    "ProxyCreator",
    "CreationState",
    "create_proxy_conversation",
    # Sharing
    "CommunitySharing",
    "get_sharing",
    "share_learning",
    # Seeding
    "EntitySeeder",
    "SeedStrategy",
    "SeedConfig",
    "SeedState",
    "get_seeder",
    "seed_curious_entity",
    "list_seed_templates",
    "SEED_TEMPLATES",
    # Biomimicry
    "Potency",
    "LifeStage",
    "DifferentiationSignal",
    "DifferentiationPressure",
    "CommunityNiche",
    "QuorumState",
    "ChrysalisState",
    "MetamorphosisPhase",
    "FusionProposal",
    "DevelopmentalState",
    "VIRTUE_TYPE_ASSOCIATIONS",
    "ENTITY_CATEGORIES",
    # Development
    "DevelopmentalManager",
    "get_dev_manager",
    "TOPIC_TYPE_ASSOCIATIONS",
    # Graph operations (for A0)
    "Result",
    "cypher",
    "create_entity",
    "get_entity",
    "create_proxy",
    "create_agent_node",
    "join_community",
    "add_differentiation_signal",
    "get_differentiation_signals",
    "update_life_stage",
    "set_entity_type",
    "share_lesson",
    "record_virtue_activation",
    # A0 tools
    "spawn_agent",
    "develop_agent",
    "metamorphose_agent",
    "spawn_offspring",
    "fuse_agents",
]
