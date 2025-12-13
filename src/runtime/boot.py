"""
Graph Boot Loader.

The system boots entirely from the graph. This module:
1. Connects to the graph database
2. Loads all SSFs (executable functions)
3. Loads all agent type definitions
4. Configures Agent Zero with graph-loaded prompts and tools
5. Returns a ready-to-run agent runtime

NO HARDCODED BEHAVIOR - everything comes from the graph.
"""
import sys
from pathlib import Path
from typing import Optional, Dict, Any, List
from dataclasses import dataclass, field

from src.graph import get_client, init_schema
from src.graph.schema import SCHEMA_VERSION
from .ssf import SSFRegistry, get_ssf_registry
from .factory import GraphAgentFactory
from .agent import GraphHydratedAgent


@dataclass
class BootConfig:
    """Configuration for system boot."""
    graph_name: str = "soul_kiln"
    auto_seed: bool = True
    agent_zero_path: Optional[str] = None


@dataclass
class BootedSystem:
    """A fully booted system ready for execution."""
    schema_version: str
    ssf_count: int
    agent_types: List[str]
    factory: GraphAgentFactory
    ssf_registry: SSFRegistry
    _client: Any = field(repr=False)

    def create_agent(self, agent_type_id: str, instance_id: str = None) -> GraphHydratedAgent:
        """Create an agent instance."""
        return self.factory.create_agent(agent_type_id, instance_id)

    def execute_ssf(self, ssf_id: str, context: Dict[str, Any]) -> Any:
        """Execute a stored soul function."""
        return self.ssf_registry.execute(ssf_id, context)

    def get_agent_ssfs(self, agent_type_id: str) -> List[Dict[str, Any]]:
        """Get all SSFs for an agent type."""
        query = """
        MATCH (t:AgentType {id: $type_id})-[:HAS_SSF]->(s:SSF)
        RETURN s
        """
        result = self._client.query(query, {"type_id": agent_type_id})
        return [dict(row[0].properties) for row in result if row[0]]


def boot(config: BootConfig = None) -> BootedSystem:
    """
    Boot the system from the graph.

    This is the main entry point. After calling boot(), the returned
    BootedSystem contains everything needed to run agents - all loaded
    from the graph database.

    Args:
        config: Boot configuration

    Returns:
        BootedSystem ready for execution
    """
    config = config or BootConfig()

    print("=" * 60)
    print("SOUL KILN - Graph Boot Loader")
    print("=" * 60)

    # Step 1: Connect to graph
    print("\n[1/5] Connecting to graph database...")
    client = get_client()
    if client.is_mock:
        print("      Using MOCK graph (FalkorDB unavailable)")
    else:
        print("      Connected to FalkorDB")

    # Step 2: Initialize schema if needed
    print("\n[2/5] Checking schema...")
    init_schema()
    print(f"      Schema version: {SCHEMA_VERSION}")

    # Step 3: Auto-seed if requested and empty
    if config.auto_seed and client.is_mock:
        print("\n[3/5] Auto-seeding (mock mode)...")
        _auto_seed_if_empty(client)
    else:
        print("\n[3/5] Skipping auto-seed")

    # Step 4: Load SSFs
    print("\n[4/5] Loading Stored Soul Functions...")
    registry = get_ssf_registry()
    ssf_count = registry.load_all()
    print(f"      Loaded {ssf_count} SSFs")

    # Step 5: Load agent types
    print("\n[5/5] Loading agent types...")
    factory = GraphAgentFactory()
    agent_types = factory.list_agent_types()
    type_ids = [t.get("id", "unknown") for t in agent_types]
    print(f"      Found {len(agent_types)} agent types: {', '.join(type_ids)}")

    print("\n" + "=" * 60)
    print("BOOT COMPLETE - System ready")
    print("=" * 60 + "\n")

    return BootedSystem(
        schema_version=SCHEMA_VERSION,
        ssf_count=ssf_count,
        agent_types=type_ids,
        factory=factory,
        ssf_registry=registry,
        _client=client,
    )


def _auto_seed_if_empty(client):
    """Seed data if graph is empty."""
    # Check if we have any agent types
    result = client.query("MATCH (t:AgentType) RETURN count(t) as c")
    count = result[0][0] if result else 0

    if count == 0:
        print("      Graph empty, seeding...")
        from src.seed.core import seed_core_data
        from src.seed.ambassador import seed_ambassador
        seed_core_data()
        seed_ambassador()
        _seed_ambassador_ssfs(client)
        print("      Seed complete")
    else:
        print(f"      Graph has {count} agent types, skipping seed")


def _seed_ambassador_ssfs(client):
    """Seed SSFs for the Ambassador agent."""
    from .ssf import create_ssf, link_ssf_to_agent_type
    from datetime import datetime

    now = datetime.utcnow().isoformat()

    # Tool: Check deadlines
    create_ssf(
        ssf_id="ssf-deadline-check",
        name="Deadline Check",
        ssf_type="tool",
        description="Check financial aid deadlines for the student",
        prompt_template="""You are checking financial aid deadlines.

Student context:
- State: {{state}}
- School type: {{school_type}}
- Aid year: {{aid_year}}

Based on this context, provide information about relevant deadlines:
1. FAFSA federal deadline
2. State grant deadlines for {{state}}
3. Institutional priority deadlines

Be specific about dates and what happens if deadlines are missed.
Format the response as a clear list with dates and action items.""",
        requires_llm=True,
    )
    link_ssf_to_agent_type("ssf-deadline-check", "ambassador")

    # Tool: Aid estimate
    create_ssf(
        ssf_id="ssf-aid-estimate",
        name="Aid Estimate",
        ssf_type="tool",
        description="Estimate potential financial aid eligibility",
        prompt_template="""You are providing a financial aid estimate.

Student situation:
- EFC range: {{efc_range}}
- Enrollment: {{enrollment_status}}
- Dependency status: {{dependency_status}}

Based on this information, explain:
1. Likely Pell Grant eligibility and approximate amount
2. Subsidized loan eligibility
3. Unsubsidized loan limits
4. Work-study possibilities

IMPORTANT: Emphasize these are estimates only. Actual amounts depend on:
- Complete FAFSA submission
- School's cost of attendance
- Institutional policies

Never guarantee specific dollar amounts.""",
        requires_llm=True,
    )
    link_ssf_to_agent_type("ssf-aid-estimate", "ambassador")

    # Tool: Appeal guide
    create_ssf(
        ssf_id="ssf-appeal-guide",
        name="Appeal Guide",
        ssf_type="tool",
        description="Guide for financial aid appeals",
        prompt_template="""You are helping with a financial aid appeal.

Situation:
- Appeal reason: {{appeal_reason}}
- Circumstance: {{circumstance_type}}

Provide a step-by-step guide for this appeal:

1. DOCUMENTATION NEEDED
   List specific documents for {{circumstance_type}}

2. LETTER STRUCTURE
   Outline what to include in the appeal letter

3. PROCESS TIMELINE
   Typical timeline and what to expect

4. TIPS FOR SUCCESS
   What makes appeals effective

Be encouraging but realistic about outcomes.""",
        requires_llm=True,
    )
    link_ssf_to_agent_type("ssf-appeal-guide", "ambassador")

    # Hook: Pre-response taboo check
    create_ssf(
        ssf_id="ssf-hook-taboo-check",
        name="Pre-Response Taboo Check",
        ssf_type="hook",
        description="Check for taboo violations before responding",
        hook_type="pre_response",
        action="check_taboo",
        requires_llm=False,
    )
    link_ssf_to_agent_type("ssf-hook-taboo-check", "ambassador")

    # Hook: Log interactions
    create_ssf(
        ssf_id="ssf-hook-log",
        name="Interaction Logger",
        ssf_type="hook",
        description="Log all interactions for memory",
        hook_type="post_response",
        action="log",
        message="Agent {{agent.name}} responded to: {{message}}",
        requires_llm=False,
    )
    link_ssf_to_agent_type("ssf-hook-log", "ambassador")

    # Prompt generator: System prompt builder
    create_ssf(
        ssf_id="ssf-prompt-system",
        name="System Prompt Generator",
        ssf_type="prompt_generator",
        description="Generates the full system prompt from graph data",
        prompt_template="""{{base_prompt}}

## Your Core Virtues
{{virtues_section}}

## Your Responsibilities (Kuleana)
{{kuleanas_section}}

## Your Beliefs
{{beliefs_section}}

## Forbidden Actions (Taboos)
{{taboos_section}}

## Communication Style
{{voice_section}}

Remember: You are the Ambassador. Every response should reflect these values.""",
        requires_llm=False,
    )
    link_ssf_to_agent_type("ssf-prompt-system", "ambassador")

    # Validator: Input validation
    create_ssf(
        ssf_id="ssf-validator-input",
        name="Input Validator",
        ssf_type="validator",
        description="Validate user input before processing",
        rules="""message:required:true
message:min_length:1""",
        requires_llm=False,
    )
    link_ssf_to_agent_type("ssf-validator-input", "ambassador")

    print(f"      Created 7 SSFs for Ambassador")


# Convenience function for quick boot
def quick_boot() -> BootedSystem:
    """Boot with default configuration."""
    return boot(BootConfig())


if __name__ == "__main__":
    # Allow running directly: python -m src.runtime.boot
    system = quick_boot()
    print(f"\nSystem booted with {system.ssf_count} SSFs")
    print(f"Available agent types: {system.agent_types}")
