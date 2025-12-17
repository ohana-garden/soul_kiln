"""
Graph Store for Core Entities.

Persists Entity, Proxy, and Community to the graph database.
Creates the relationships that make the system coherent:

- (Proxy)-[:PROXY_FOR]->(Entity)
- (Proxy)-[:MEMBER_OF]->(Community)
- (Community)-[:SHARES]->(Lesson)
- (Proxy)-[:NAVIGATES]->(VirtueAnchor)
"""

import json
import logging
from typing import Any

from .entity import Entity, EntityType
from .proxy import Proxy, ProxyType, ProxyStatus
from .community import Community, CommunityPurpose

logger = logging.getLogger(__name__)


class CoreGraphStore:
    """
    Graph storage for core entities.

    All core entities become graph nodes with relationships.
    This enables:
    - Querying by relationship (all proxies in a community)
    - Path finding (how entities relate)
    - Virtue navigation (proxy -> agent -> virtue basins)
    """

    def __init__(self, client=None):
        """
        Initialize the store.

        Args:
            client: Graph client (defaults to singleton)
        """
        self._client = client

    @property
    def client(self):
        """Get the graph client."""
        if self._client is None:
            from ..graph.client import get_client
            self._client = get_client()
        return self._client

    def init_schema(self) -> None:
        """Create indexes for core entities."""
        # Entity indexes
        self.client.execute(
            "CREATE INDEX IF NOT EXISTS FOR (n:Entity) ON (n.id)"
        )
        self.client.execute(
            "CREATE INDEX IF NOT EXISTS FOR (n:Entity) ON (n.type)"
        )

        # Proxy indexes
        self.client.execute(
            "CREATE INDEX IF NOT EXISTS FOR (n:Proxy) ON (n.id)"
        )
        self.client.execute(
            "CREATE INDEX IF NOT EXISTS FOR (n:Proxy) ON (n.status)"
        )
        self.client.execute(
            "CREATE INDEX IF NOT EXISTS FOR (n:Proxy) ON (n.creator_id)"
        )

        # Community indexes
        self.client.execute(
            "CREATE INDEX IF NOT EXISTS FOR (n:Community) ON (n.id)"
        )
        self.client.execute(
            "CREATE INDEX IF NOT EXISTS FOR (n:Community) ON (n.purpose)"
        )

        logger.info("Core schema indexes created")

    # =========================================================================
    # Entity Operations
    # =========================================================================

    def save_entity(self, entity: Entity) -> str:
        """
        Save an entity to the graph.

        Returns:
            Entity ID
        """
        props = {
            "id": entity.id,
            "type": entity.type.value,
            "name": entity.name,
            "description": entity.description,
            "creator_id": entity.creator_id,
            "attributes": json.dumps(entity.attributes),
            "facts": json.dumps(entity.facts),
            "voice_description": entity.voice_description,
            "created_at": entity.created_at.isoformat(),
            "updated_at": entity.updated_at.isoformat(),
        }

        self.client.execute(
            """
            MERGE (e:Entity {id: $id})
            SET e += $props
            """,
            {"id": entity.id, "props": props}
        )

        logger.debug(f"Saved entity {entity.id}")
        return entity.id

    def get_entity(self, entity_id: str) -> Entity | None:
        """Get an entity by ID."""
        result = self.client.query(
            "MATCH (e:Entity {id: $id}) RETURN e",
            {"id": entity_id}
        )

        if not result:
            return None

        return self._node_to_entity(result[0][0])

    def delete_entity(self, entity_id: str) -> bool:
        """Delete an entity and its relationships."""
        self.client.execute(
            "MATCH (e:Entity {id: $id}) DETACH DELETE e",
            {"id": entity_id}
        )
        return True

    def _node_to_entity(self, node: dict) -> Entity:
        """Convert a graph node to Entity."""
        return Entity(
            id=node.get("id", ""),
            type=EntityType(node.get("type", "self")),
            name=node.get("name", ""),
            description=node.get("description", ""),
            creator_id=node.get("creator_id", ""),
            attributes=json.loads(node.get("attributes", "{}")),
            facts=json.loads(node.get("facts", "[]")),
            voice_description=node.get("voice_description", ""),
        )

    # =========================================================================
    # Proxy Operations
    # =========================================================================

    def save_proxy(self, proxy: Proxy) -> str:
        """
        Save a proxy to the graph.

        Also creates relationships:
        - PROXY_FOR -> Entity
        - MEMBER_OF -> Community (for each community)
        - NAVIGATES -> Agent (virtue graph agent)

        Returns:
            Proxy ID
        """
        props = {
            "id": proxy.id,
            "entity_id": proxy.entity_id,
            "creator_id": proxy.creator_id,
            "name": proxy.name,
            "role": proxy.role,
            "type": proxy.type.value,
            "status": proxy.status.value,
            "agent_id": proxy.agent_id,
            "config": json.dumps(proxy.config.to_dict()),
            "created_at": proxy.created_at.isoformat(),
            "activated_at": proxy.activated_at.isoformat() if proxy.activated_at else None,
            "last_active": proxy.last_active.isoformat(),
            "current_session_id": proxy.current_session_id,
            "learned_patterns": json.dumps(proxy.learned_patterns),
            "metadata": json.dumps(proxy.metadata),
        }

        # Create/update proxy node
        self.client.execute(
            """
            MERGE (p:Proxy {id: $id})
            SET p += $props
            """,
            {"id": proxy.id, "props": props}
        )

        # Create PROXY_FOR relationship to entity
        if proxy.entity_id:
            self.client.execute(
                """
                MATCH (p:Proxy {id: $proxy_id})
                MATCH (e:Entity {id: $entity_id})
                MERGE (p)-[:PROXY_FOR]->(e)
                """,
                {"proxy_id": proxy.id, "entity_id": proxy.entity_id}
            )

        # Create MEMBER_OF relationships to communities
        for community_id in proxy.community_ids:
            self.client.execute(
                """
                MATCH (p:Proxy {id: $proxy_id})
                MATCH (c:Community {id: $community_id})
                MERGE (p)-[:MEMBER_OF]->(c)
                """,
                {"proxy_id": proxy.id, "community_id": community_id}
            )

        # Create NAVIGATES relationship to virtue agent
        if proxy.agent_id:
            self.client.execute(
                """
                MATCH (p:Proxy {id: $proxy_id})
                MATCH (a:Agent {id: $agent_id})
                MERGE (p)-[:NAVIGATES]->(a)
                """,
                {"proxy_id": proxy.id, "agent_id": proxy.agent_id}
            )

        logger.debug(f"Saved proxy {proxy.id}")
        return proxy.id

    def get_proxy(self, proxy_id: str) -> Proxy | None:
        """Get a proxy by ID."""
        result = self.client.query(
            """
            MATCH (p:Proxy {id: $id})
            OPTIONAL MATCH (p)-[:MEMBER_OF]->(c:Community)
            RETURN p, collect(c.id) as community_ids
            """,
            {"id": proxy_id}
        )

        if not result:
            return None

        node = result[0][0]
        community_ids = result[0][1] or []

        return self._node_to_proxy(node, community_ids)

    def get_proxies_for_entity(self, entity_id: str) -> list[Proxy]:
        """Get all proxies that represent an entity."""
        result = self.client.query(
            """
            MATCH (p:Proxy)-[:PROXY_FOR]->(e:Entity {id: $entity_id})
            OPTIONAL MATCH (p)-[:MEMBER_OF]->(c:Community)
            RETURN p, collect(c.id) as community_ids
            """,
            {"entity_id": entity_id}
        )

        proxies = []
        for row in result:
            proxy = self._node_to_proxy(row[0], row[1] or [])
            proxies.append(proxy)

        return proxies

    def get_proxies_in_community(self, community_id: str) -> list[Proxy]:
        """Get all proxies in a community."""
        result = self.client.query(
            """
            MATCH (p:Proxy)-[:MEMBER_OF]->(c:Community {id: $community_id})
            OPTIONAL MATCH (p)-[:MEMBER_OF]->(other:Community)
            RETURN p, collect(other.id) as community_ids
            """,
            {"community_id": community_id}
        )

        proxies = []
        for row in result:
            proxy = self._node_to_proxy(row[0], row[1] or [])
            proxies.append(proxy)

        return proxies

    def get_proxies_by_creator(self, creator_id: str) -> list[Proxy]:
        """Get all proxies created by a user."""
        result = self.client.query(
            """
            MATCH (p:Proxy {creator_id: $creator_id})
            OPTIONAL MATCH (p)-[:MEMBER_OF]->(c:Community)
            RETURN p, collect(c.id) as community_ids
            """,
            {"creator_id": creator_id}
        )

        proxies = []
        for row in result:
            proxy = self._node_to_proxy(row[0], row[1] or [])
            proxies.append(proxy)

        return proxies

    def delete_proxy(self, proxy_id: str) -> bool:
        """Delete a proxy and its relationships."""
        self.client.execute(
            "MATCH (p:Proxy {id: $id}) DETACH DELETE p",
            {"id": proxy_id}
        )
        return True

    def _node_to_proxy(self, node: dict, community_ids: list[str]) -> Proxy:
        """Convert a graph node to Proxy."""
        from .proxy import ProxyConfig

        config_data = json.loads(node.get("config", "{}"))

        proxy = Proxy(
            id=node.get("id", ""),
            entity_id=node.get("entity_id", ""),
            creator_id=node.get("creator_id", ""),
            name=node.get("name", ""),
            role=node.get("role", ""),
            type=ProxyType(node.get("type", "voice")),
            status=ProxyStatus(node.get("status", "nascent")),
            community_ids=community_ids,
            agent_id=node.get("agent_id", ""),
            config=ProxyConfig.from_dict(config_data),
            current_session_id=node.get("current_session_id"),
            learned_patterns=json.loads(node.get("learned_patterns", "{}")),
            metadata=json.loads(node.get("metadata", "{}")),
        )

        return proxy

    # =========================================================================
    # Community Operations
    # =========================================================================

    def save_community(self, community: Community) -> str:
        """
        Save a community to the graph.

        Returns:
            Community ID
        """
        props = {
            "id": community.id,
            "name": community.name,
            "description": community.description,
            "purpose": community.purpose.value,
            "virtue_emphasis": json.dumps(community.virtue_emphasis.to_dict()),
            "tool_ids": json.dumps(list(community.tool_ids)),
            "creator_id": community.creator_id,
            "created_at": community.created_at.isoformat(),
            "updated_at": community.updated_at.isoformat(),
            "active": community.active,
            "total_members_ever": community.total_members_ever,
            "total_lessons_shared": community.total_lessons_shared,
            "total_conversations": community.total_conversations,
            "metadata": json.dumps(community.metadata),
        }

        self.client.execute(
            """
            MERGE (c:Community {id: $id})
            SET c += $props
            """,
            {"id": community.id, "props": props}
        )

        logger.debug(f"Saved community {community.id}")
        return community.id

    def get_community(self, community_id: str) -> Community | None:
        """Get a community by ID."""
        result = self.client.query(
            """
            MATCH (c:Community {id: $id})
            OPTIONAL MATCH (p:Proxy)-[:MEMBER_OF]->(c)
            RETURN c, collect(p.id) as member_ids
            """,
            {"id": community_id}
        )

        if not result:
            return None

        node = result[0][0]
        member_ids = result[0][1] or []

        return self._node_to_community(node, member_ids)

    def get_community_by_name(self, name: str) -> Community | None:
        """Get a community by name."""
        result = self.client.query(
            """
            MATCH (c:Community {name: $name})
            OPTIONAL MATCH (p:Proxy)-[:MEMBER_OF]->(c)
            RETURN c, collect(p.id) as member_ids
            """,
            {"name": name}
        )

        if not result:
            return None

        node = result[0][0]
        member_ids = result[0][1] or []

        return self._node_to_community(node, member_ids)

    def list_communities(self, active_only: bool = True) -> list[Community]:
        """List all communities."""
        query = """
            MATCH (c:Community)
            WHERE c.active = true OR $include_inactive
            OPTIONAL MATCH (p:Proxy)-[:MEMBER_OF]->(c)
            RETURN c, collect(p.id) as member_ids
            ORDER BY c.name
        """

        result = self.client.query(
            query,
            {"include_inactive": not active_only}
        )

        communities = []
        for row in result:
            community = self._node_to_community(row[0], row[1] or [])
            communities.append(community)

        return communities

    def delete_community(self, community_id: str) -> bool:
        """Delete a community (soft delete by default)."""
        self.client.execute(
            "MATCH (c:Community {id: $id}) SET c.active = false",
            {"id": community_id}
        )
        return True

    def _node_to_community(self, node: dict, member_ids: list[str]) -> Community:
        """Convert a graph node to Community."""
        from .community import VirtueEmphasis

        virtue_data = json.loads(node.get("virtue_emphasis", "{}"))

        community = Community(
            id=node.get("id", ""),
            name=node.get("name", ""),
            description=node.get("description", ""),
            purpose=CommunityPurpose(node.get("purpose", "general")),
            virtue_emphasis=VirtueEmphasis.from_dict(virtue_data),
            member_ids=set(member_ids),
            tool_ids=set(json.loads(node.get("tool_ids", "[]"))),
            creator_id=node.get("creator_id", ""),
            active=node.get("active", True),
            metadata=json.loads(node.get("metadata", "{}")),
            total_members_ever=node.get("total_members_ever", 0),
            total_lessons_shared=node.get("total_lessons_shared", 0),
            total_conversations=node.get("total_conversations", 0),
        )

        return community

    # =========================================================================
    # Relationship Queries
    # =========================================================================

    def get_entity_for_proxy(self, proxy_id: str) -> Entity | None:
        """Get the entity a proxy represents."""
        result = self.client.query(
            """
            MATCH (p:Proxy {id: $proxy_id})-[:PROXY_FOR]->(e:Entity)
            RETURN e
            """,
            {"proxy_id": proxy_id}
        )

        if not result:
            return None

        return self._node_to_entity(result[0][0])

    def get_communities_for_proxy(self, proxy_id: str) -> list[Community]:
        """Get all communities a proxy belongs to."""
        result = self.client.query(
            """
            MATCH (p:Proxy {id: $proxy_id})-[:MEMBER_OF]->(c:Community)
            OPTIONAL MATCH (other:Proxy)-[:MEMBER_OF]->(c)
            RETURN c, collect(other.id) as member_ids
            """,
            {"proxy_id": proxy_id}
        )

        communities = []
        for row in result:
            community = self._node_to_community(row[0], row[1] or [])
            communities.append(community)

        return communities

    def get_community_lessons(self, community_id: str, limit: int = 50) -> list[dict]:
        """Get lessons shared in a community."""
        result = self.client.query(
            """
            MATCH (c:Community {id: $community_id})<-[:SHARED_IN]-(l:Lesson)
            RETURN l
            ORDER BY l.created_at DESC
            LIMIT $limit
            """,
            {"community_id": community_id, "limit": limit}
        )

        return [dict(row[0]) for row in result]

    def share_lesson_to_community(
        self,
        lesson_id: str,
        community_id: str,
        proxy_id: str,
    ) -> None:
        """Share a lesson with a community."""
        self.client.execute(
            """
            MATCH (l:Lesson {id: $lesson_id})
            MATCH (c:Community {id: $community_id})
            MATCH (p:Proxy {id: $proxy_id})
            MERGE (l)-[:SHARED_IN {shared_by: $proxy_id, shared_at: datetime()}]->(c)
            SET c.total_lessons_shared = c.total_lessons_shared + 1
            """,
            {
                "lesson_id": lesson_id,
                "community_id": community_id,
                "proxy_id": proxy_id,
            }
        )


# Singleton
_store: CoreGraphStore | None = None


def get_core_store() -> CoreGraphStore:
    """Get the singleton core graph store."""
    global _store
    if _store is None:
        _store = CoreGraphStore()
    return _store
