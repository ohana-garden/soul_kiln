"""Graph schema initialization."""
from .client import get_client


def init_schema():
    """Create indexes and constraints."""
    client = get_client()

    # Core node indexes
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

    # Proxy agent subsystem indexes (kuleana, skills, beliefs, etc.)
    client.execute("CREATE INDEX IF NOT EXISTS FOR (n:Kuleana) ON (n.id)")
    client.execute("CREATE INDEX IF NOT EXISTS FOR (n:Skill) ON (n.id)")
    client.execute("CREATE INDEX IF NOT EXISTS FOR (n:Belief) ON (n.id)")
    client.execute("CREATE INDEX IF NOT EXISTS FOR (n:LoreFragment) ON (n.id)")
    client.execute("CREATE INDEX IF NOT EXISTS FOR (n:VoicePattern) ON (n.id)")
    client.execute("CREATE INDEX IF NOT EXISTS FOR (n:EpisodicMemory) ON (n.id)")
    client.execute("CREATE INDEX IF NOT EXISTS FOR (n:Tool) ON (n.id)")
    client.execute("CREATE INDEX IF NOT EXISTS FOR (n:KnowledgeDomain) ON (n.id)")
    client.execute("CREATE INDEX IF NOT EXISTS FOR (n:Fact) ON (n.id)")
    client.execute("CREATE INDEX IF NOT EXISTS FOR (n:Source) ON (n.id)")

    # Situation and action indexes
    client.execute("CREATE INDEX IF NOT EXISTS FOR (n:Situation) ON (n.id)")
    client.execute("CREATE INDEX IF NOT EXISTS FOR (n:Stakeholder) ON (n.id)")
    client.execute("CREATE INDEX IF NOT EXISTS FOR (n:Resource) ON (n.id)")
    client.execute("CREATE INDEX IF NOT EXISTS FOR (n:Action) ON (n.id)")


def clear_graph():
    """Delete all nodes and edges. Use carefully."""
    client = get_client()
    client.execute("MATCH (n) DETACH DELETE n")
