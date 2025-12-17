"""
Core domain models for Soul Kiln.

The essential entities:
- Entity: What a proxy represents (human, org, concept, object)
- Proxy: The personified agent that speaks for an entity
- Community: A group that shares everything

All behavior flows through virtue basins toward emergent ethics.

The core flow:
1. User starts a conversation (smartphone, CLI, web)
2. Conversation guides creation of a Proxy
3. Proxy represents an Entity (human, org, concept, object)
4. Proxy joins a Community
5. Community members share everything (lessons, patterns, pathways)
6. All behavior navigates virtue basins toward emergent good
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
]
