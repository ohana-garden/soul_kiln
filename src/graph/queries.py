"""Common Cypher queries for graph operations."""
from datetime import datetime
from typing import Optional
from .client import get_client


def create_node(label: str, properties: dict) -> str:
    """Create node, return id."""
    client = get_client()
    props = {**properties, "created_at": datetime.utcnow().isoformat()}

    # Build property string
    prop_str = ", ".join(f"{k}: ${k}" for k in props.keys())

    client.execute(
        f"CREATE (n:{label} {{{prop_str}}})",
        props
    )
    return properties["id"]


def create_edge(
    from_id: str,
    to_id: str,
    rel_type: str,
    properties: dict = None
) -> None:
    """Create edge between nodes."""
    client = get_client()
    props = properties or {}
    props["created_at"] = datetime.utcnow().isoformat()
    props["last_used"] = props["created_at"]

    if "use_count" not in props:
        props["use_count"] = 0

    if "weight" not in props:
        props["weight"] = 0.5

    prop_str = ", ".join(f"{k}: ${k}" for k in props.keys())

    client.execute(
        f"""
        MATCH (a {{id: $from_id}}), (b {{id: $to_id}})
        CREATE (a)-[r:{rel_type} {{{prop_str}}}]->(b)
        """,
        {"from_id": from_id, "to_id": to_id, **props}
    )


def get_neighbors(node_id: str) -> list:
    """Get all nodes connected to node_id with edge weights."""
    client = get_client()
    return client.query(
        """
        MATCH (n {id: $id})-[r]-(m)
        RETURN m.id as id, m.type as type, r.weight as weight, type(r) as rel
        """,
        {"id": node_id}
    )


def update_edge_weight(from_id: str, to_id: str, new_weight: float) -> None:
    """Update edge weight and last_used."""
    client = get_client()
    client.execute(
        """
        MATCH (a {id: $from_id})-[r]-(b {id: $to_id})
        SET r.weight = $weight,
            r.last_used = $now,
            r.use_count = r.use_count + 1
        """,
        {
            "from_id": from_id,
            "to_id": to_id,
            "weight": min(1.0, max(0.0, new_weight)),
            "now": datetime.utcnow().isoformat()
        }
    )


def get_node_activation(node_id: str) -> float:
    """Get current activation level."""
    client = get_client()
    result = client.query(
        "MATCH (n {id: $id}) RETURN n.activation as activation",
        {"id": node_id}
    )
    if result:
        return result[0][0] or 0.0
    return 0.0


def set_node_activation(node_id: str, activation: float) -> None:
    """Set activation level."""
    client = get_client()
    client.execute(
        """
        MATCH (n {id: $id})
        SET n.activation = $activation,
            n.last_activated = $now
        """,
        {
            "id": node_id,
            "activation": activation,
            "now": datetime.utcnow().isoformat()
        }
    )


def get_all_edges() -> list:
    """Get all edges with their properties."""
    client = get_client()
    return client.query(
        """
        MATCH (a)-[r]->(b)
        RETURN a.id, b.id, r.weight, r.last_used, type(r) as rel_type,
               labels(a) as a_labels, labels(b) as b_labels
        """
    )


def delete_edge(from_id: str, to_id: str) -> None:
    """Delete edge between two nodes."""
    client = get_client()
    client.execute(
        """
        MATCH (a {id: $from})-[r]->(b {id: $to})
        DELETE r
        """,
        {"from": from_id, "to": to_id}
    )


def set_edge_weight(from_id: str, to_id: str, weight: float) -> None:
    """Set edge weight without updating use count."""
    client = get_client()
    client.execute(
        """
        MATCH (a {id: $from})-[r]->(b {id: $to})
        SET r.weight = $weight
        """,
        {"from": from_id, "to": to_id, "weight": weight}
    )
