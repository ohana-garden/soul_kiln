"""
Mock Graph Client for testing without FalkorDB.

Provides an in-memory graph implementation for development and testing
when FalkorDB server is not available.
"""
from typing import Any, Optional, Dict, List
import re
from collections import defaultdict


class MockNode:
    """In-memory node representation."""

    def __init__(self, node_id: str, labels: List[str], properties: Dict[str, Any]):
        self.id = node_id
        self.labels = labels
        self.properties = properties


class MockEdge:
    """In-memory edge representation."""

    def __init__(self, edge_id: str, edge_type: str, from_node: str, to_node: str, properties: Dict[str, Any]):
        self.id = edge_id
        self.type = edge_type
        self.from_node = from_node
        self.to_node = to_node
        self.properties = properties


class MockGraphClient:
    """
    In-memory mock of FalkorDB graph client.

    Supports basic Cypher operations for testing.
    """

    def __init__(self, graph_name: str = "mock_graph"):
        self.graph_name = graph_name
        self.nodes: Dict[str, MockNode] = {}
        self.edges: Dict[str, MockEdge] = {}
        self.indexes: List[str] = []

    def query(self, cypher: str, params: dict = None) -> list:
        """Execute Cypher query and return results."""
        params = params or {}
        cypher = self._substitute_params(cypher, params)

        # Handle different query types
        if "CREATE INDEX" in cypher.upper():
            return self._handle_create_index(cypher)
        elif "MERGE" in cypher.upper() or "CREATE" in cypher.upper():
            return self._handle_create_or_merge(cypher, params)
        elif "MATCH" in cypher.upper():
            return self._handle_match(cypher, params)
        elif "DETACH DELETE" in cypher.upper():
            return self._handle_delete_all()

        return []

    def execute(self, cypher: str, params: dict = None) -> None:
        """Execute Cypher mutation."""
        self.query(cypher, params)

    def node_exists(self, node_id: str) -> bool:
        """Check if a node exists."""
        return node_id in self.nodes

    def _substitute_params(self, cypher: str, params: dict) -> str:
        """Substitute $param with values."""
        for key, value in params.items():
            if isinstance(value, str):
                cypher = cypher.replace(f"${key}", f"'{value}'")
            elif isinstance(value, (int, float)):
                cypher = cypher.replace(f"${key}", str(value))
            elif isinstance(value, bool):
                cypher = cypher.replace(f"${key}", str(value).lower())
            elif value is None:
                cypher = cypher.replace(f"${key}", "null")
        return cypher

    def _handle_create_index(self, cypher: str) -> list:
        """Handle CREATE INDEX queries."""
        self.indexes.append(cypher)
        return []

    def _handle_create_or_merge(self, cypher: str, params: dict) -> list:
        """Handle CREATE and MERGE queries."""
        # Extract node pattern like (n:Label {id: 'value'})
        node_pattern = re.search(r'\((\w+):(\w+)\s*\{([^}]+)\}\)', cypher)
        if node_pattern:
            var_name = node_pattern.group(1)
            label = node_pattern.group(2)
            props_str = node_pattern.group(3)

            # Parse properties from the MERGE pattern
            props = self._parse_properties(props_str)

            # Also parse ON CREATE SET / ON MATCH SET properties
            # This handles patterns like: s.name = $name, s.type = $type
            set_props = self._parse_set_clauses(cypher, var_name, params)
            props.update(set_props)

            node_id = props.get('id', f"{label}_{len(self.nodes)}")

            if node_id not in self.nodes:
                self.nodes[node_id] = MockNode(node_id, [label], props)
            else:
                # Merge - update properties
                self.nodes[node_id].properties.update(props)

        # Handle edge creation
        edge_pattern = re.search(r'\((\w+)\)-\[(\w+):(\w+)\s*(?:\{([^}]*)\})?\]->\((\w+)\)', cypher)
        if edge_pattern:
            from_var = edge_pattern.group(1)
            edge_var = edge_pattern.group(2)
            edge_type = edge_pattern.group(3)
            edge_props_str = edge_pattern.group(4) or ""
            to_var = edge_pattern.group(5)

            edge_props = self._parse_properties(edge_props_str) if edge_props_str else {}
            edge_id = f"{edge_type}_{len(self.edges)}"

            # We'd need to resolve from_var and to_var to actual node IDs
            # For simplicity, store the edge
            self.edges[edge_id] = MockEdge(edge_id, edge_type, from_var, to_var, edge_props)

        return []

    def _parse_set_clauses(self, cypher: str, var_name: str, params: dict) -> Dict[str, Any]:
        """Parse ON CREATE SET / ON MATCH SET clauses."""
        props = {}

        # Find all SET clauses (both ON CREATE SET and ON MATCH SET)
        # Pattern: var.prop = $param or var.prop = value
        pattern = rf'{var_name}\.(\w+)\s*=\s*(\$\w+|\'[^\']*\'|"[^"]*"|\d+\.?\d*|true|false|null|datetime\([^)]+\))'

        for match in re.finditer(pattern, cypher, re.IGNORECASE):
            prop_name = match.group(1)
            raw_value = match.group(2)

            # Resolve value
            if raw_value.startswith('$'):
                param_name = raw_value[1:]
                value = params.get(param_name)
            elif raw_value.startswith(("'", '"')):
                value = raw_value[1:-1]
            elif raw_value.lower() == 'true':
                value = True
            elif raw_value.lower() == 'false':
                value = False
            elif raw_value.lower() == 'null':
                value = None
            elif raw_value.startswith('datetime('):
                value = raw_value  # Keep as string for mock
            else:
                try:
                    value = float(raw_value) if '.' in raw_value else int(raw_value)
                except ValueError:
                    value = raw_value

            if value is not None:
                props[prop_name] = value

        return props

    def _handle_match(self, cypher: str, params: dict) -> list:
        """Handle MATCH queries."""
        results = []

        # Check for multi-node queries with OPTIONAL MATCH
        # e.g., MATCH (a:AgentInstance {id: $agent_id}) OPTIONAL MATCH (a)-[:IS_TYPE]->(t:AgentType) RETURN a, t
        if "OPTIONAL MATCH" in cypher.upper():
            return self._handle_optional_match(cypher, params)

        # Simple pattern matching for (n:Label {id: 'value'})
        match_pattern = re.search(r'MATCH\s+\((\w+):(\w+)\s*(?:\{id:\s*[\'"]([^\'"]+)[\'"]\})?\)', cypher, re.IGNORECASE)
        if match_pattern:
            label = match_pattern.group(2)
            node_id = match_pattern.group(3)

            if node_id and node_id in self.nodes:
                node = self.nodes[node_id]
                if label in node.labels:
                    results.append([node])
            elif not node_id:
                # Return all nodes of this label
                for node in self.nodes.values():
                    if label in node.labels:
                        results.append([node])

        # Handle count queries
        if "count(" in cypher.lower():
            return [[len(results)]]

        # Handle RETURN with specific properties (e.g., RETURN s.id as ssf_id)
        return self._transform_return(cypher, results)

    def _handle_optional_match(self, cypher: str, params: dict) -> list:
        """Handle queries with OPTIONAL MATCH."""
        results = []

        # Parse the primary MATCH
        primary_match = re.search(r'MATCH\s+\((\w+):(\w+)\s*\{id:\s*[\'"]([^\'"]+)[\'"]\}\)', cypher, re.IGNORECASE)
        if not primary_match:
            # Try to match without id filter
            primary_match = re.search(r'MATCH\s+\((\w+):(\w+)\)', cypher, re.IGNORECASE)

        if not primary_match:
            return results

        primary_var = primary_match.group(1)
        primary_label = primary_match.group(2)
        primary_id = primary_match.group(3) if len(primary_match.groups()) > 2 else None

        # Find primary nodes
        primary_nodes = []
        if primary_id and primary_id in self.nodes:
            node = self.nodes[primary_id]
            if primary_label in node.labels:
                primary_nodes.append(node)
        elif not primary_id:
            for node in self.nodes.values():
                if primary_label in node.labels:
                    primary_nodes.append(node)

        # For each primary node, look for optional relationships
        # Parse the OPTIONAL MATCH to find linked node type
        optional_pattern = re.search(
            rf'OPTIONAL MATCH\s+\({primary_var}\)-\[\w*:?(\w+)?\]->\((\w+):(\w+)\)',
            cypher, re.IGNORECASE
        )

        for primary_node in primary_nodes:
            row = [primary_node]

            if optional_pattern:
                rel_type = optional_pattern.group(1)
                linked_var = optional_pattern.group(2)
                linked_label = optional_pattern.group(3)

                # Find edges from this node
                linked_node = None
                for edge in self.edges.values():
                    if edge.from_node == primary_var and (not rel_type or edge.type == rel_type):
                        # Find the target node - need to look up by edge's to_node value
                        # In our simple model, we stored var names not IDs
                        # Let's find a node of the target label
                        for n in self.nodes.values():
                            if linked_label in n.labels:
                                linked_node = n
                                break
                        break

                row.append(linked_node)  # Can be None for OPTIONAL MATCH

            results.append(row)

        return results

    def _transform_return(self, cypher: str, results: list) -> list:
        """Transform results based on RETURN clause."""
        # Parse RETURN clause for property projections
        # e.g., RETURN s.id as ssf_id, s.name as name
        return_match = re.search(r'RETURN\s+(.+?)(?:\s+ORDER|\s+LIMIT|\s*$)', cypher, re.IGNORECASE | re.DOTALL)
        if not return_match:
            return results

        return_clause = return_match.group(1).strip()

        # Check if it's returning properties (e.g., s.id) vs nodes (e.g., s)
        projections = []
        for part in return_clause.split(','):
            part = part.strip()
            # Match patterns like "s.id as ssf_id" or "s.id"
            prop_match = re.match(r'(\w+)\.(\w+)(?:\s+as\s+(\w+))?', part, re.IGNORECASE)
            if prop_match:
                var_name = prop_match.group(1)
                prop_name = prop_match.group(2)
                alias = prop_match.group(3) or prop_name
                projections.append((var_name, prop_name, alias))

        if not projections:
            return results

        # Transform results to return property values
        transformed = []
        for row in results:
            new_row = []
            for var_name, prop_name, alias in projections:
                # Find the node for this variable (assume first node in row)
                value = None
                for item in row:
                    if isinstance(item, MockNode):
                        value = item.properties.get(prop_name)
                        break
                new_row.append(value)
            transformed.append(new_row)

        return transformed

    def _handle_delete_all(self) -> list:
        """Handle DETACH DELETE all."""
        self.nodes.clear()
        self.edges.clear()
        return []

    def _parse_properties(self, props_str: str) -> Dict[str, Any]:
        """Parse property string into dict."""
        props = {}
        if not props_str:
            return props

        # Simple parsing - handles key: 'value' or key: value
        for match in re.finditer(r"(\w+):\s*(?:'([^']*)'|\"([^\"]*)\"|(\d+\.?\d*)|(\w+))", props_str):
            key = match.group(1)
            # Find the value from the groups
            value = match.group(2) or match.group(3) or match.group(4) or match.group(5)
            if value:
                # Try to convert to number
                try:
                    if '.' in str(value):
                        value = float(value)
                    else:
                        value = int(value)
                except (ValueError, TypeError):
                    pass
                props[key] = value

        return props


# Singleton mock client
_mock_client: Optional[MockGraphClient] = None


def get_mock_client(graph_name: str = "soul_kiln") -> MockGraphClient:
    """Get or create singleton mock client."""
    global _mock_client
    if _mock_client is None:
        _mock_client = MockGraphClient(graph_name)
    return _mock_client


def reset_mock_client():
    """Reset the mock client."""
    global _mock_client
    _mock_client = None
