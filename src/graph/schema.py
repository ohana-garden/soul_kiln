"""Graph schema initialization."""
from .client import get_client


def init_schema():
    """Create indexes and constraints."""
    client = get_client()

    # Node indexes
    client.execute("CREATE INDEX IF NOT EXISTS FOR (n:VirtueAnchor) ON (n.id)")
    client.execute("CREATE INDEX IF NOT EXISTS FOR (n:Concept) ON (n.id)")
    client.execute("CREATE INDEX IF NOT EXISTS FOR (n:Agent) ON (n.id)")
    client.execute("CREATE INDEX IF NOT EXISTS FOR (n:SSF) ON (n.id)")
    client.execute("CREATE INDEX IF NOT EXISTS FOR (n:File) ON (n.id)")
    client.execute("CREATE INDEX IF NOT EXISTS FOR (n:Trajectory) ON (n.id)")
    client.execute("CREATE INDEX IF NOT EXISTS FOR (n:DissolvedAgent) ON (n.id)")

    # Knowledge pool and mercy system indexes
    client.execute("CREATE INDEX IF NOT EXISTS FOR (n:Lesson) ON (n.id)")
    client.execute("CREATE INDEX IF NOT EXISTS FOR (n:Pathway) ON (n.id)")
    client.execute("CREATE INDEX IF NOT EXISTS FOR (n:Warning) ON (n.id)")

    # Persona graph node indexes (KG-persona pattern)
    client.execute("CREATE INDEX IF NOT EXISTS FOR (n:Trait) ON (n.id)")
    client.execute("CREATE INDEX IF NOT EXISTS FOR (n:StyleRule) ON (n.id)")
    client.execute("CREATE INDEX IF NOT EXISTS FOR (n:Boundary) ON (n.id)")
    client.execute("CREATE INDEX IF NOT EXISTS FOR (n:Preference) ON (n.id)")
    client.execute("CREATE INDEX IF NOT EXISTS FOR (n:Role) ON (n.id)")
    client.execute("CREATE INDEX IF NOT EXISTS FOR (n:Definition) ON (n.id)")


def clear_graph():
    """Delete all nodes and edges. Use carefully."""
    client = get_client()
    client.execute("MATCH (n) DETACH DELETE n")
