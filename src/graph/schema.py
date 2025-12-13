"""
Graph Schema Initialization.

The graph is the single source of truth for the entire platform.
All agents, prompts, tools, and behavioral definitions live here.
"""
from .client import get_client

SCHEMA_VERSION = "2.0.0"


def init_schema():
    """Create indexes and constraints for all node types."""
    client = get_client()

    # ===== Core Agent System =====
    client.execute("CREATE INDEX IF NOT EXISTS FOR (n:AgentType) ON (n.id)")
    client.execute("CREATE INDEX IF NOT EXISTS FOR (n:AgentInstance) ON (n.id)")
    client.execute("CREATE INDEX IF NOT EXISTS FOR (n:Prompt) ON (n.id)")
    client.execute("CREATE INDEX IF NOT EXISTS FOR (n:Tool) ON (n.id)")
    client.execute("CREATE INDEX IF NOT EXISTS FOR (n:Instrument) ON (n.id)")

    # ===== Proxy Agent Subsystems =====
    # Kuleana (Responsibilities)
    client.execute("CREATE INDEX IF NOT EXISTS FOR (n:Kuleana) ON (n.id)")
    client.execute("CREATE INDEX IF NOT EXISTS FOR (n:Responsibility) ON (n.id)")

    # Virtues (Ethical Anchors)
    client.execute("CREATE INDEX IF NOT EXISTS FOR (n:Virtue) ON (n.id)")
    client.execute("CREATE INDEX IF NOT EXISTS FOR (n:VirtueAnchor) ON (n.id)")

    # Beliefs (Values & Principles)
    client.execute("CREATE INDEX IF NOT EXISTS FOR (n:Belief) ON (n.id)")
    client.execute("CREATE INDEX IF NOT EXISTS FOR (n:BeliefContext) ON (n.id)")

    # Lore (Origin Stories & Cultural Context)
    client.execute("CREATE INDEX IF NOT EXISTS FOR (n:Lore) ON (n.id)")
    client.execute("CREATE INDEX IF NOT EXISTS FOR (n:LoreEvent) ON (n.id)")

    # Voice (Communication Style)
    client.execute("CREATE INDEX IF NOT EXISTS FOR (n:VoicePattern) ON (n.id)")
    client.execute("CREATE INDEX IF NOT EXISTS FOR (n:EmotionResponse) ON (n.id)")

    # Skills (Capabilities)
    client.execute("CREATE INDEX IF NOT EXISTS FOR (n:Skill) ON (n.id)")
    client.execute("CREATE INDEX IF NOT EXISTS FOR (n:SkillLevel) ON (n.id)")

    # Taboos (Forbidden Actions)
    client.execute("CREATE INDEX IF NOT EXISTS FOR (n:Taboo) ON (n.id)")
    client.execute("CREATE INDEX IF NOT EXISTS FOR (n:TabooCategory) ON (n.id)")

    # ===== Memory & Conversation =====
    client.execute("CREATE INDEX IF NOT EXISTS FOR (n:Memory) ON (n.id)")
    client.execute("CREATE INDEX IF NOT EXISTS FOR (n:Conversation) ON (n.id)")
    client.execute("CREATE INDEX IF NOT EXISTS FOR (n:Message) ON (n.id)")
    client.execute("CREATE INDEX IF NOT EXISTS FOR (n:Episode) ON (n.id)")

    # ===== Knowledge & Learning =====
    client.execute("CREATE INDEX IF NOT EXISTS FOR (n:Concept) ON (n.id)")
    client.execute("CREATE INDEX IF NOT EXISTS FOR (n:Lesson) ON (n.id)")
    client.execute("CREATE INDEX IF NOT EXISTS FOR (n:Pathway) ON (n.id)")
    client.execute("CREATE INDEX IF NOT EXISTS FOR (n:Warning) ON (n.id)")

    # ===== Student Financial Context =====
    client.execute("CREATE INDEX IF NOT EXISTS FOR (n:Student) ON (n.id)")
    client.execute("CREATE INDEX IF NOT EXISTS FOR (n:FinancialAidType) ON (n.id)")
    client.execute("CREATE INDEX IF NOT EXISTS FOR (n:Institution) ON (n.id)")
    client.execute("CREATE INDEX IF NOT EXISTS FOR (n:Deadline) ON (n.id)")

    # ===== Legacy/Migration Support =====
    client.execute("CREATE INDEX IF NOT EXISTS FOR (n:Agent) ON (n.id)")
    client.execute("CREATE INDEX IF NOT EXISTS FOR (n:SSF) ON (n.id)")
    client.execute("CREATE INDEX IF NOT EXISTS FOR (n:File) ON (n.id)")
    client.execute("CREATE INDEX IF NOT EXISTS FOR (n:Trajectory) ON (n.id)")
    client.execute("CREATE INDEX IF NOT EXISTS FOR (n:DissolvedAgent) ON (n.id)")


def clear_graph():
    """Delete all nodes and edges. Use carefully."""
    client = get_client()
    client.execute("MATCH (n) DETACH DELETE n")


def get_schema_version() -> str:
    """Get the current schema version."""
    return SCHEMA_VERSION
