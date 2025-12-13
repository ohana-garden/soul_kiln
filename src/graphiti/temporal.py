"""
Temporal Edge Management.

Implements Graphiti-style bi-temporal edges with t_valid and t_invalid timestamps.
This enables point-in-time queries and soft deletion of relationships.
"""
from datetime import datetime
from typing import Optional, Dict, Any, List
from uuid import uuid4

from src.graph import get_client


class TemporalEdgeManager:
    """Manages temporal edges in the graph."""

    def __init__(self):
        self.client = get_client()

    def create_edge(
        self,
        from_id: str,
        from_label: str,
        to_id: str,
        to_label: str,
        edge_type: str,
        properties: Dict[str, Any] = None,
        valid_at: datetime = None,
    ) -> str:
        """
        Create a temporal edge between two nodes.

        Args:
            from_id: Source node ID
            from_label: Source node label
            to_id: Target node ID
            to_label: Target node label
            edge_type: Type of relationship
            properties: Additional edge properties
            valid_at: When the edge becomes valid (defaults to now)

        Returns:
            Edge ID
        """
        edge_id = str(uuid4())
        valid_at = valid_at or datetime.utcnow()
        props = properties or {}

        # Build property string for Cypher
        prop_parts = [
            f"id: '{edge_id}'",
            f"t_valid: datetime('{valid_at.isoformat()}')",
            "t_invalid: null",
        ]
        for key, value in props.items():
            if isinstance(value, str):
                prop_parts.append(f"{key}: '{value}'")
            elif isinstance(value, bool):
                prop_parts.append(f"{key}: {str(value).lower()}")
            elif isinstance(value, (int, float)):
                prop_parts.append(f"{key}: {value}")

        prop_str = ", ".join(prop_parts)

        query = f"""
        MATCH (a:{from_label} {{id: $from_id}})
        MATCH (b:{to_label} {{id: $to_id}})
        CREATE (a)-[r:{edge_type} {{{prop_str}}}]->(b)
        RETURN r.id as edge_id
        """

        self.client.execute(query, {"from_id": from_id, "to_id": to_id})
        return edge_id

    def invalidate_edge(
        self,
        edge_id: str,
        invalid_at: datetime = None,
    ) -> bool:
        """
        Soft-delete an edge by setting t_invalid timestamp.

        Args:
            edge_id: ID of the edge to invalidate
            invalid_at: When the edge becomes invalid (defaults to now)

        Returns:
            True if edge was found and invalidated
        """
        invalid_at = invalid_at or datetime.utcnow()

        query = """
        MATCH ()-[r {id: $edge_id}]->()
        WHERE r.t_invalid IS NULL
        SET r.t_invalid = datetime($invalid_at)
        RETURN r.id as edge_id
        """

        result = self.client.query(
            query,
            {"edge_id": edge_id, "invalid_at": invalid_at.isoformat()}
        )
        return len(result) > 0

    def get_valid_edges(
        self,
        node_id: str,
        node_label: str,
        edge_type: str = None,
        as_of: datetime = None,
        direction: str = "outgoing",
    ) -> List[Dict[str, Any]]:
        """
        Get all valid edges for a node at a point in time.

        Args:
            node_id: Node ID
            node_label: Node label
            edge_type: Optional edge type filter
            as_of: Point in time (defaults to now)
            direction: 'outgoing', 'incoming', or 'both'

        Returns:
            List of edge dictionaries with properties
        """
        as_of = as_of or datetime.utcnow()

        edge_filter = f":{edge_type}" if edge_type else ""

        if direction == "outgoing":
            pattern = f"(n:{node_label} {{id: $node_id}})-[r{edge_filter}]->(m)"
        elif direction == "incoming":
            pattern = f"(m)-[r{edge_filter}]->(n:{node_label} {{id: $node_id}})"
        else:
            pattern = f"(n:{node_label} {{id: $node_id}})-[r{edge_filter}]-(m)"

        query = f"""
        MATCH {pattern}
        WHERE r.t_valid <= datetime($as_of)
        AND (r.t_invalid IS NULL OR r.t_invalid > datetime($as_of))
        RETURN r, m, labels(m) as target_labels
        """

        result = self.client.query(query, {
            "node_id": node_id,
            "as_of": as_of.isoformat()
        })

        edges = []
        for row in result:
            edge_props = dict(row[0].properties) if row[0] else {}
            target_node = dict(row[1].properties) if row[1] else {}
            target_labels = row[2] if len(row) > 2 else []
            edges.append({
                "edge": edge_props,
                "target": target_node,
                "target_labels": target_labels,
            })

        return edges


# Module-level convenience functions
_manager: Optional[TemporalEdgeManager] = None


def _get_manager() -> TemporalEdgeManager:
    """Get singleton manager instance."""
    global _manager
    if _manager is None:
        _manager = TemporalEdgeManager()
    return _manager


def create_temporal_edge(
    from_id: str,
    from_label: str,
    to_id: str,
    to_label: str,
    edge_type: str,
    properties: Dict[str, Any] = None,
    valid_at: datetime = None,
) -> str:
    """Create a temporal edge. See TemporalEdgeManager.create_edge."""
    return _get_manager().create_edge(
        from_id, from_label, to_id, to_label, edge_type, properties, valid_at
    )


def invalidate_edge(edge_id: str, invalid_at: datetime = None) -> bool:
    """Invalidate an edge. See TemporalEdgeManager.invalidate_edge."""
    return _get_manager().invalidate_edge(edge_id, invalid_at)
