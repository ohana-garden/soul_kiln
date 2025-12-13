"""
Graph Agent Factory.

Creates and hydrates agents from graph definitions.
"""
from typing import Optional, Dict, Any, List
from datetime import datetime
from uuid import uuid4

from src.graph import get_client
from src.graphiti import ContextRetriever
from .loaders import GraphPromptLoader, GraphToolLoader, GraphInstrumentLoader


class GraphAgentFactory:
    """Factory for creating agents from graph definitions."""

    def __init__(self):
        self.client = get_client()
        self.prompt_loader = GraphPromptLoader()
        self.tool_loader = GraphToolLoader()
        self.instrument_loader = GraphInstrumentLoader()
        self.context_retriever = ContextRetriever()

    def create_agent(
        self,
        agent_type_id: str,
        instance_id: str = None,
        metadata: Dict[str, Any] = None,
    ) -> "GraphHydratedAgent":
        """
        Create a new agent instance from a type definition.

        Args:
            agent_type_id: ID of the AgentType node
            instance_id: Optional custom instance ID
            metadata: Additional instance metadata

        Returns:
            Hydrated agent instance
        """
        from .agent import GraphHydratedAgent

        # Verify agent type exists
        agent_type = self._get_agent_type(agent_type_id)
        if not agent_type:
            raise ValueError(f"Agent type not found: {agent_type_id}")

        # Create instance in graph
        instance_id = instance_id or str(uuid4())
        self._create_instance_node(instance_id, agent_type_id, metadata)

        # Hydrate the agent
        return self.hydrate_agent(instance_id)

    def hydrate_agent(self, instance_id: str) -> "GraphHydratedAgent":
        """
        Hydrate an existing agent instance with all its context.

        Args:
            instance_id: Agent instance ID

        Returns:
            Fully hydrated agent
        """
        from .agent import GraphHydratedAgent

        # Get instance info
        instance = self._get_instance(instance_id)
        if not instance:
            raise ValueError(f"Agent instance not found: {instance_id}")

        # Get agent type
        agent_type_id = instance.get("agent_type_id")
        agent_type = self._get_agent_type(agent_type_id) if agent_type_id else {}

        # Load all components
        prompts = self.prompt_loader.load_agent_prompts(agent_type_id)
        tools = self.tool_loader.load_agent_tools(agent_type_id)
        instruments = self.instrument_loader.load_agent_instruments(agent_type_id)

        # Get behavioral context
        context = self.context_retriever.get_agent_context(instance_id)

        # Create hydrated agent
        return GraphHydratedAgent(
            instance_id=instance_id,
            agent_type=agent_type,
            prompts=prompts,
            tools=tools,
            instruments=instruments,
            virtues=context.get("virtues", []),
            kuleanas=context.get("kuleanas", []),
            beliefs=context.get("beliefs", []),
            taboos=context.get("taboos", []),
            voice=context.get("voice", {}),
            memories=context.get("recent_memories", []),
        )

    def _get_agent_type(self, agent_type_id: str) -> Optional[Dict[str, Any]]:
        """Get agent type definition from graph."""
        query = """
        MATCH (t:AgentType {id: $agent_type_id})
        RETURN t
        """
        result = self.client.query(query, {"agent_type_id": agent_type_id})

        if result and result[0] and result[0][0]:
            return dict(result[0][0].properties)

        return None

    def _get_instance(self, instance_id: str) -> Optional[Dict[str, Any]]:
        """Get agent instance from graph."""
        query = """
        MATCH (a:AgentInstance {id: $instance_id})
        OPTIONAL MATCH (a)-[:IS_TYPE]->(t:AgentType)
        RETURN a, t.id as agent_type_id
        """
        result = self.client.query(query, {"instance_id": instance_id})

        if result and result[0] and result[0][0]:
            instance = dict(result[0][0].properties)
            instance["agent_type_id"] = result[0][1] if len(result[0]) > 1 else None
            return instance

        return None

    def _create_instance_node(
        self,
        instance_id: str,
        agent_type_id: str,
        metadata: Dict[str, Any] = None,
    ):
        """Create agent instance node in graph."""
        now = datetime.utcnow().isoformat()
        meta = metadata or {}

        # Create instance node
        query = """
        CREATE (a:AgentInstance {
            id: $instance_id,
            created_at: datetime($now),
            status: 'active'
        })
        RETURN a.id as id
        """
        self.client.execute(query, {"instance_id": instance_id, "now": now})

        # Link to agent type
        link_query = """
        MATCH (a:AgentInstance {id: $instance_id})
        MATCH (t:AgentType {id: $agent_type_id})
        CREATE (a)-[:IS_TYPE {t_valid: datetime($now), t_invalid: null}]->(t)
        """
        self.client.execute(link_query, {
            "instance_id": instance_id,
            "agent_type_id": agent_type_id,
            "now": now,
        })

    def list_agent_types(self) -> List[Dict[str, Any]]:
        """
        List all available agent types.

        Returns:
            List of agent type definitions
        """
        query = """
        MATCH (t:AgentType)
        RETURN t
        ORDER BY t.name
        """
        result = self.client.query(query)

        return [dict(row[0].properties) for row in result if row[0]]

    def list_instances(
        self,
        agent_type_id: str = None,
        status: str = None,
    ) -> List[Dict[str, Any]]:
        """
        List agent instances.

        Args:
            agent_type_id: Optional filter by type
            status: Optional filter by status

        Returns:
            List of instance info
        """
        filters = []
        params = {}

        if agent_type_id:
            filters.append("t.id = $agent_type_id")
            params["agent_type_id"] = agent_type_id

        if status:
            filters.append("a.status = $status")
            params["status"] = status

        where_clause = "WHERE " + " AND ".join(filters) if filters else ""

        query = f"""
        MATCH (a:AgentInstance)
        OPTIONAL MATCH (a)-[:IS_TYPE]->(t:AgentType)
        {where_clause}
        RETURN a, t.id as agent_type_id, t.name as agent_type_name
        ORDER BY a.created_at DESC
        """
        result = self.client.query(query, params)

        instances = []
        for row in result:
            if row[0]:
                instance = dict(row[0].properties)
                instance["agent_type_id"] = row[1] if len(row) > 1 else None
                instance["agent_type_name"] = row[2] if len(row) > 2 else None
                instances.append(instance)

        return instances

    def delete_instance(self, instance_id: str) -> bool:
        """
        Delete an agent instance (soft delete).

        Args:
            instance_id: Instance ID to delete

        Returns:
            True if instance was found and deleted
        """
        now = datetime.utcnow().isoformat()

        # Soft delete - mark as inactive
        query = """
        MATCH (a:AgentInstance {id: $instance_id})
        SET a.status = 'deleted',
            a.deleted_at = datetime($now)
        RETURN a.id as id
        """
        result = self.client.query(query, {"instance_id": instance_id, "now": now})

        return len(result) > 0
