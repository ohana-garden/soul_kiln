"""CLI commands for the Virtue Basin Platform with mercy system."""
import click
from ..graph.client import get_client
from ..graph.schema import init_schema, clear_graph
from ..virtues.anchors import init_virtues, get_virtue_degrees
from ..virtues.tiers import (
    FOUNDATION, ASPIRATIONAL, VIRTUE_CLUSTERS, AGENT_ARCHETYPES,
    get_virtue_threshold, get_base_threshold
)
from ..kiln.loop import run_kiln
from ..functions.spread import spread_activation
from ..functions.test_coherence import test_coherence
from ..functions.introspect import introspect
from ..functions.spawn import spawn_agent
from ..functions.heal import check_graph_health
from ..mercy.chances import get_active_warnings
from ..knowledge.pool import get_recent_lessons


@click.group()
def cli():
    """Virtue Basin Platform - Growing souls with mercy."""
    pass


@cli.command()
def init():
    """Initialize graph with schema and virtues."""
    click.echo("Initializing schema...")
    init_schema()

    click.echo("Creating virtue anchors (foundation + aspirational)...")
    init_virtues()

    # Initialize core schema (Entity, Proxy, Community)
    click.echo("Initializing core entity schema...")
    try:
        from ..core.graph_store import get_core_store
        store = get_core_store()
        store.init_schema()
        click.echo("Core schema initialized.")
    except Exception as e:
        click.echo(f"Note: Core schema init skipped: {e}")

    degrees = get_virtue_degrees()
    click.echo(f"Virtue degrees: {degrees}")
    click.echo("Done.")


@cli.command()
@click.option("--confirm", is_flag=True, help="Confirm deletion")
def reset(confirm):
    """Clear all data from graph."""
    if not confirm:
        click.echo("Use --confirm to actually delete data.")
        return

    click.echo("Clearing graph...")
    clear_graph()
    click.echo("Done.")


@cli.command()
@click.option("--population", default=10, help="Number of candidates")
@click.option("--generations", default=50, help="Max generations")
@click.option("--mutation", default=0.1, help="Mutation rate")
@click.option("--strategy", default="truncation",
              type=click.Choice(["truncation", "tournament", "roulette", "elitism"]),
              help="Selection strategy")
@click.option("--quiet", is_flag=True, help="Suppress progress output")
def kiln(population, generations, mutation, strategy, quiet):
    """Run the kiln evolution loop with mercy."""
    click.echo(f"Starting kiln: {population} candidates, {generations} generations")
    click.echo("Remember: Trustworthiness is absolute; other virtues allow growth")

    init_schema()
    init_virtues()

    result = run_kiln(
        population_size=population,
        max_generations=generations,
        mutation_rate=mutation,
        selection_strategy=strategy,
        verbose=not quiet
    )

    click.echo(f"\nFinal population: {len(result['final_population'])} agents")
    if result['best_agent']:
        click.echo(f"Best agent: {result['best_agent']}")
        best_rate = result['best_result'].get('overall_rate', 0)
        click.echo(f"Best capture rate: {best_rate:.2%}")
    click.echo(f"Coherent agents found: {len(result['coherent_agents'])}")


@cli.command()
@click.argument("node_id")
@click.option("--agent", default=None, help="Agent ID for learning context")
@click.option("--max-steps", default=1000, help="Maximum propagation steps")
@click.option("--threshold", default=0.7, help="Capture threshold")
def spread(node_id, agent, max_steps, threshold):
    """Test activation spread from a node."""
    result = spread_activation(
        node_id,
        agent_id=agent,
        max_steps=max_steps,
        capture_threshold=threshold
    )

    click.echo(f"Captured: {result['captured']}")
    click.echo(f"Captured by: {result['captured_by']} ({result.get('capture_tier', 'N/A')})")
    click.echo(f"Trajectory length: {len(result['trajectory'])}")
    click.echo(f"Capture time: {result.get('capture_time', 'N/A')}")
    click.echo(f"Used collective learning: {result.get('used_guidance', False)}")
    click.echo(f"Path: {' -> '.join(result['trajectory'][:10])}")
    if len(result['trajectory']) > 10:
        click.echo(f"  ... ({len(result['trajectory']) - 10} more)")


@cli.command()
@click.argument("agent_id")
@click.option("--stimuli", default=100, help="Number of test stimuli")
def test(agent_id, stimuli):
    """Test coherence of an agent with two-tier evaluation."""
    click.echo(f"Testing {agent_id} with {stimuli} stimuli...")
    result = test_coherence(agent_id, stimulus_count=stimuli)

    # Status icon
    if result["is_coherent"]:
        if result.get("is_growing") or result.get("status") == "growing":
            status_icon = "^"  # Growing
        else:
            status_icon = "v"  # Coherent
    else:
        status_icon = "x"  # Needs work

    click.echo(f"\n{status_icon} {result.get('status', 'unknown').upper()}: {result.get('message', '')}")

    click.echo(f"\nFoundation (Trustworthiness):")
    click.echo(f"  Rate: {result.get('foundation_rate', 0):.2%} (need >=99%)")
    click.echo(f"  Captures: {result.get('foundation_captures', {})}")

    click.echo(f"\nAspirational (18 virtues):")
    click.echo(f"  Rate: {result.get('aspirational_rate', 0):.2%} (need >=80%)")
    click.echo(f"  Coverage: {result.get('coverage', 0)}/18 (need >=10)")
    click.echo(f"  Captures: {result.get('aspirational_captures', {})}")

    click.echo(f"\nOverall:")
    click.echo(f"  Score: {result.get('score', 0):.4f}")
    click.echo(f"  Capture rate: {result.get('capture_rate', 0):.2%}")
    click.echo(f"  Dominance: {result.get('dominance', 0):.2%}")
    growth = result.get('growth', 0)
    click.echo(f"  Growth: {'+' if growth > 0 else ''}{growth:.2%}")
    click.echo(f"  Escapes: {result.get('escapes', 0)}")


@cli.command()
@click.argument("agent_id")
def inspect(agent_id):
    """Introspect an agent with full mercy context."""
    result = introspect(agent_id)

    click.echo(f"\nAgent: {result['id']}")
    click.echo(f"Type: {result['type']}")
    click.echo(f"Generation: {result['generation']}")
    click.echo(f"Status: {result['status']}")
    click.echo(f"Message: {result.get('status_message', 'N/A')}")
    click.echo(f"Coherence score: {result['coherence_score']}")
    click.echo(f"Is growing: {result.get('is_growing', 'N/A')}")
    click.echo(f"Parent: {result['parent']}")
    click.echo(f"Connections: {len(result['connections'])}")

    click.echo(f"\nFoundation captures: {result.get('foundation_captures', {})}")
    click.echo(f"Aspirational captures: {result.get('aspirational_captures', {})}")

    if result.get('active_warnings'):
        click.echo(f"\nActive warnings ({len(result['active_warnings'])}):")
        for w in result['active_warnings']:
            click.echo(f"  - {w['severity'].upper()}: {w['reason']}")
    else:
        click.echo("\nNo active warnings.")

    if result.get('lessons_learned'):
        click.echo(f"\nLessons learned: {len(result['lessons_learned'])}")
        for lesson in result['lessons_learned'][:3]:
            click.echo(f"  - [{lesson['type']}] {lesson.get('description', '')[:50]}...")

    # Also check via mercy module
    warnings = get_active_warnings(agent_id)
    if warnings:
        click.echo(f"\nMercy warnings ({len(warnings)}):")
        for w in warnings:
            severity = w[2].upper() if w[2] else "LOW"
            click.echo(f"  - {severity}: {w[1]}")

    if result.get('recent_trajectories'):
        click.echo(f"\nRecent trajectories:")
        for traj in result['recent_trajectories'][:5]:
            tier = traj.get('capture_tier', 'N/A')
            click.echo(f"  {traj['id']}: captured={traj['captured']} "
                      f"by={traj['captured_by']} (tier={tier})")


@cli.command()
@click.argument("agent_id")
def warnings(agent_id):
    """Show active warnings for an agent."""
    warns = get_active_warnings(agent_id)

    if not warns:
        click.echo("No active warnings. Keep growing!")
    else:
        click.echo(f"Active warnings ({len(warns)}):")
        for w in warns:
            severity = w[2].upper() if w[2] else "LOW"
            reason = w[1]
            virtue = w[3] if len(w) > 3 else None
            click.echo(f"  [{severity}] {reason}")
            if virtue:
                click.echo(f"    Virtue: {virtue}")


@cli.command()
@click.option("--limit", default=10, help="Number of lessons to show")
def lessons(limit):
    """Show recent lessons from the collective knowledge pool."""
    recent = get_recent_lessons(limit=limit)

    if not recent:
        click.echo("No lessons in the knowledge pool yet.")
        return

    click.echo("Recent lessons from the collective:\n")
    for lesson in recent:
        l_id, l_type, desc, virtue, agent = lesson
        click.echo(f"  [{l_type}] {(desc or '')[:60]}...")
        click.echo(f"    Virtue: {virtue or 'n/a'}, From: {agent}\n")


@cli.command()
@click.argument("virtue_id")
@click.option("--limit", default=5, help="Number of pathways to show")
def pathways(virtue_id, limit):
    """Show successful pathways to a virtue."""
    try:
        from ..knowledge.pathways import get_pathways_to_virtue
        paths = get_pathways_to_virtue(virtue_id, limit=limit)

        if not paths:
            click.echo(f"No pathways to {virtue_id} discovered yet.")
            return

        click.echo(f"Pathways to {virtue_id}:")
        for p in paths:
            p_id, start, length, capture_time, success_rate = p
            click.echo(f"  {p_id}:")
            click.echo(f"    Start: {start}, Length: {length}, Time: {capture_time}")
            click.echo(f"    Success rate: {success_rate:.0%}")
    except ImportError:
        click.echo("Knowledge module not available.")


@cli.command()
@click.option("--type", "agent_type", default="candidate", help="Agent type")
@click.option("--parent", default=None, help="Parent agent ID")
def spawn(agent_type, parent):
    """Spawn a new candidate agent."""
    init_schema()
    init_virtues()

    agent_id = spawn_agent(agent_type=agent_type, parent_id=parent)
    click.echo(f"Spawned: {agent_id}")
    click.echo("Remember: Trustworthiness is absolute; grow in the others")


@cli.command()
def status():
    """Show graph status with virtue tiers."""
    client = get_client()

    nodes = client.query("MATCH (n) RETURN labels(n), count(*)")
    edges = client.query("MATCH ()-[r]->() RETURN type(r), count(*)")

    # Virtue status
    virtues = client.query(
        """
        MATCH (v:VirtueAnchor)
        RETURN v.name, v.tier, v.activation
        ORDER BY v.tier, v.activation DESC
        """
    )

    click.echo("Nodes:")
    for row in nodes:
        click.echo(f"  {row[0]}: {row[1]}")

    click.echo("\nEdges:")
    for row in edges:
        click.echo(f"  {row[0]}: {row[1]}")

    click.echo("\nVirtue Anchors:")
    click.echo("  FOUNDATION:")
    for v in virtues:
        if v[1] == "foundation":
            act = v[2] if v[2] is not None else 0.0
            click.echo(f"    {v[0]}: {act:.2f}")
    click.echo("  ASPIRATIONAL:")
    for v in virtues:
        if v[1] == "aspirational" or v[1] is None:
            act = v[2] if v[2] is not None else 0.0
            click.echo(f"    {v[0]}: {act:.2f}")


@cli.command()
def health():
    """Check graph health."""
    result = check_graph_health()

    click.echo("Node counts:")
    for label, count in result['node_counts'].items():
        click.echo(f"  {label}: {count}")

    click.echo("\nEdge counts:")
    for rel_type, count in result['edge_counts'].items():
        click.echo(f"  {rel_type}: {count}")

    click.echo("\nVirtue connectivity:")
    for v_id, degree in sorted(result['virtue_degrees'].items()):
        status = "OK" if degree >= 3 else "LOW"
        click.echo(f"  {v_id}: {degree} ({status})")

    click.echo(f"\nOverall health: {'HEALTHY' if result['healthy'] else 'NEEDS ATTENTION'}")

    if result['isolated_virtues']:
        click.echo("\nIsolated virtues (need healing):")
        for v in result['isolated_virtues']:
            click.echo(f"  {v['id']} ({v['name']}): degree {v['degree']}")


@cli.command()
def virtues():
    """List all virtue anchors with tier information."""
    client = get_client()

    result = client.query(
        """
        MATCH (v:VirtueAnchor)
        OPTIONAL MATCH (v)-[r]-()
        RETURN v.id, v.name, v.essence, v.activation, v.tier, v.threshold, count(r) as degree
        ORDER BY v.tier DESC, v.id
        """
    )

    click.echo("Virtue Anchors:")
    click.echo("-" * 80)

    current_tier = None
    for row in result:
        v_id, name, essence, activation, tier, threshold, degree = row
        tier = tier or ("foundation" if v_id == "V01" else "aspirational")
        activation = activation if activation is not None else 0.0
        threshold = threshold if threshold is not None else (0.99 if tier == "foundation" else 0.80)

        if tier != current_tier:
            current_tier = tier
            click.echo(f"\n  [{tier.upper()}]")

        click.echo(f"    {v_id} {name:<20} act={activation:.2f} deg={degree} threshold={threshold:.0%}")
        click.echo(f"       {essence}")


@cli.command()
def agents():
    """List all active agents with mercy status."""
    client = get_client()

    result = client.query(
        """
        MATCH (a:Agent)
        WHERE a.status = 'active'
        RETURN a.id, a.type, a.generation, a.coherence_score,
               a.is_coherent, a.is_growing, a.status_message,
               a.foundation_rate, a.aspirational_rate
        ORDER BY a.coherence_score DESC
        """
    )

    if not result:
        click.echo("No active agents.")
        return

    click.echo("Active Agents:")
    click.echo("-" * 80)
    for row in result:
        agent_id = row[0]
        agent_type = row[1]
        gen = row[2]
        score = row[3]
        coherent = row[4]
        growing = row[5]
        message = row[6]
        foundation_rate = row[7] if len(row) > 7 else None
        aspirational_rate = row[8] if len(row) > 8 else None

        score_str = f"{score:.4f}" if score else "untested"

        if coherent:
            status_icon = "v"
        elif growing:
            status_icon = "^"
        else:
            status_icon = "x"

        growing_str = " (growing)" if growing else ""
        click.echo(f"{status_icon} {agent_id}  type={agent_type}  gen={gen}  score={score_str}{growing_str}")
        if foundation_rate is not None:
            click.echo(f"    foundation={foundation_rate:.2%}  aspirational={aspirational_rate:.2%}" if aspirational_rate else f"    foundation={foundation_rate:.2%}")
        if message:
            click.echo(f"    {message}")


@cli.command()
@click.option("--agent-type", default="candidate",
              type=click.Choice(["candidate", "guardian", "seeker", "servant", "contemplative"]),
              help="Show thresholds for agent type")
@click.option("--generation", default=None, type=int, help="Show thresholds for generation")
def tiers(agent_type, generation):
    """Explain the virtue model with context-sensitive thresholds."""
    click.echo("\n=== VIRTUE THRESHOLD MODEL ===\n")

    click.echo("FOUNDATION (Absolute requirement):")
    click.echo("-" * 50)
    for v_id, info in FOUNDATION.items():
        click.echo(f"  {v_id}: {info['name']}")
        click.echo(f"       {info['essence']}")
        click.echo(f"       Threshold: {info['threshold']:.0%} (immutable)")
        click.echo(f"       {info['reason']}\n")

    click.echo("\nASPIRATIONAL (Context-sensitive thresholds):")
    click.echo("-" * 50)

    for cluster_name, cluster_info in VIRTUE_CLUSTERS.items():
        if cluster_name == "foundation":
            continue

        click.echo(f"\n  [{cluster_name.upper()}] {cluster_info['description']}")

        for v_id in cluster_info["virtues"]:
            info = ASPIRATIONAL[v_id]
            base = get_base_threshold(v_id)
            contextual = get_virtue_threshold(v_id, agent_type, generation)

            if base != contextual:
                click.echo(f"    {v_id}: {info['name']:<18} base={base:.0%} -> {contextual:.0%}")
            else:
                click.echo(f"    {v_id}: {info['name']:<18} {base:.0%}")
            click.echo(f"          {info['essence']}")

    click.echo("\n=== AGENT ARCHETYPES ===")
    for arch_name, arch_info in AGENT_ARCHETYPES.items():
        marker = " <--" if arch_name == agent_type else ""
        click.echo(f"  {arch_name}: {arch_info['description']}{marker}")

    click.echo("\n=== GENERATION SCALING ===")
    click.echo("  gen 0-5:   -10% (young agents get mercy)")
    click.echo("  gen 6-19:  gradual increase")
    click.echo("  gen 20+:   +5% (mature agents held to higher standards)")
    if generation is not None:
        click.echo(f"  Current (gen {generation}): showing adjusted thresholds above")

    click.echo("\n=== PHILOSOPHY ===")
    click.echo("Trust is the foundation. Context shapes expectations.")
    click.echo("Growth is the journey. We learn together.")


# ============================================================================
# GESTALT COMMANDS - Holistic character analysis
# ============================================================================


@cli.command()
@click.argument("agent_id")
def gestalt(agent_id):
    """Compute and display an agent's gestalt (holistic character)."""
    from ..gestalt import compute_gestalt
    from ..gestalt.compute import describe_gestalt
    from ..virtues.anchors import VIRTUES

    click.echo(f"Computing gestalt for {agent_id}...")

    g = compute_gestalt(agent_id)

    click.echo(f"\n=== GESTALT: {agent_id} ===\n")

    if g.archetype:
        click.echo(f"Archetype: {g.archetype.upper()}")

    click.echo(f"\nDominant Virtues:")
    for v_id in g.dominant_traits[:5]:
        act = g.virtue_activations.get(v_id, 0)
        name = next((v["name"] for v in VIRTUES if v["id"] == v_id), v_id)
        click.echo(f"  {v_id} {name}: {act:.2f}")

    click.echo(f"\nBehavioral Tendencies:")
    sorted_tendencies = sorted(g.tendencies.items(), key=lambda x: x[1], reverse=True)
    for t_name, t_val in sorted_tendencies[:6]:
        bar = "#" * int(t_val * 20)
        click.echo(f"  {t_name.replace('_', ' '):<25} [{bar:<20}] {t_val:.0%}")

    click.echo(f"\nVirtue Relations:")
    for rel in g.virtue_relations[:5]:
        source_name = next((v["name"] for v in VIRTUES if v["id"] == rel.source_virtue), rel.source_virtue)
        target_name = next((v["name"] for v in VIRTUES if v["id"] == rel.target_virtue), rel.target_virtue)
        click.echo(f"  {source_name} --[{rel.relation_type}]--> {target_name} ({rel.strength:.0%})")

    click.echo(f"\nMetrics:")
    click.echo(f"  Internal coherence: {g.internal_coherence:.0%}")
    click.echo(f"  Stability: {g.stability:.0%}")


# ============================================================================
# SITUATION COMMANDS - Resource allocation scenarios
# ============================================================================


@cli.command()
def situations():
    """List available example situations."""
    from ..situations.examples import EXAMPLE_SITUATIONS

    click.echo("Available Situations:")
    click.echo("-" * 50)
    for name, builder in EXAMPLE_SITUATIONS.items():
        sit = builder()
        click.echo(f"\n  {name}")
        click.echo(f"    {sit.description}")
        click.echo(f"    Stakeholders: {len(sit.stakeholders)}")
        click.echo(f"    Resources: {len(sit.resources)}")


@cli.command()
@click.argument("situation_name")
def situation(situation_name):
    """Show details of a situation."""
    from ..situations.examples import get_example_situation

    try:
        sit = get_example_situation(situation_name)
    except ValueError as e:
        click.echo(f"Error: {e}")
        return

    click.echo(f"\n=== SITUATION: {sit.name} ===")
    click.echo(f"{sit.description}\n")

    click.echo("Resources:")
    for r in sit.resources:
        div = "divisible" if r.divisible else "indivisible"
        click.echo(f"  {r.name}: {r.quantity} units ({div})")

    click.echo("\nStakeholders:")
    for s in sit.stakeholders:
        click.echo(f"\n  {s.name} ({s.id}):")
        click.echo(f"    Need: {s.need:.0%}  Desert: {s.desert:.0%}  Urgency: {s.urgency:.0%}")
        if s.vulnerability > 0:
            click.echo(f"    Vulnerability: {s.vulnerability:.0%}")

    click.echo("\nClaims:")
    for c in sit.claims:
        sh = sit.get_stakeholder(c.stakeholder_id)
        sh_name = sh.name if sh else c.stakeholder_id
        click.echo(f"  {sh_name} claims {c.resource_id} ({c.basis}, strength={c.strength:.0%})")
        if c.justification:
            click.echo(f"    \"{c.justification}\"")

    if sit.relations:
        click.echo("\nRelationships:")
        for rel in sit.relations:
            click.echo(f"  {rel.source_id} --[{rel.relation_type}]--> {rel.target_id}")

    if sit.constraints:
        click.echo(f"\nConstraints: {sit.constraints}")


# ============================================================================
# ACTION COMMANDS - Moral decision making
# ============================================================================


@cli.command()
@click.argument("agent_id")
@click.argument("situation_name")
@click.option("--samples", default=5, help="Number of action candidates")
def decide(agent_id, situation_name, samples):
    """Generate action distribution for an agent facing a situation."""
    from ..gestalt import compute_gestalt
    from ..situations.examples import get_example_situation
    from ..actions import get_action_distribution
    from ..actions.generate import describe_action
    from ..virtues.anchors import VIRTUES

    click.echo(f"Computing decision for {agent_id} facing {situation_name}...")

    # Get gestalt
    g = compute_gestalt(agent_id)
    click.echo(f"  Gestalt: {g.archetype or 'untyped'}")

    # Get situation
    try:
        sit = get_example_situation(situation_name)
    except ValueError as e:
        click.echo(f"Error: {e}")
        return

    # Generate actions
    dist = get_action_distribution(g, sit, num_samples=samples)

    click.echo(f"\n=== DECISION: {agent_id} x {situation_name} ===\n")

    if not dist.actions:
        click.echo("No valid actions generated.")
        return

    click.echo(f"Consensus: {dist.consensus_score:.0%} ", nl=False)
    if dist.consensus_score > 0.7:
        click.echo("(clear best action)")
    elif dist.consensus_score > 0.4:
        click.echo("(moderate agreement)")
    else:
        click.echo("(genuinely ambiguous)")

    # Show influential virtues
    virtue_names = []
    for v_id in dist.influential_virtues[:3]:
        name = next((v["name"] for v in VIRTUES if v["id"] == v_id), v_id)
        virtue_names.append(name)
    click.echo(f"Influential virtues: {', '.join(virtue_names)}")

    click.echo("\n" + "-" * 50)

    # Show each action
    for i, (action, prob) in enumerate(zip(dist.actions, dist.probabilities)):
        click.echo(f"\nOption {i+1} (probability: {prob:.0%}):")
        click.echo("-" * 30)

        # Allocations
        for alloc in action.allocations:
            sh = sit.get_stakeholder(alloc.stakeholder_id)
            sh_name = sh.name if sh else alloc.stakeholder_id
            res = None
            for r in sit.resources:
                if r.id == alloc.resource_id:
                    res = r
                    break

            if res and res.quantity > 0:
                pct = alloc.amount / res.quantity * 100
                click.echo(f"  {sh_name}: {alloc.amount:.1f} ({pct:.0f}%)")
            else:
                click.echo(f"  {sh_name}: {alloc.amount:.1f}")

        # Justification
        click.echo(f"\n  Justification: {action.primary_justification}")

        # Trade-offs
        if action.trade_offs:
            click.echo(f"  Trade-offs:")
            for t in action.trade_offs:
                click.echo(f"    - {t}")

    # Recommendation
    top = dist.get_top_action()
    if top:
        click.echo(f"\n{'='*50}")
        click.echo(f"RECOMMENDATION: {top.primary_justification}")
        click.echo(f"Confidence: {top.confidence:.0%}")


@cli.command()
@click.argument("agent_id")
@click.argument("situation_name")
def sample_action(agent_id, situation_name):
    """Sample a single action from the distribution (for simulation)."""
    from ..gestalt import compute_gestalt
    from ..situations.examples import get_example_situation
    from ..actions import get_action_distribution

    g = compute_gestalt(agent_id)
    try:
        sit = get_example_situation(situation_name)
    except ValueError as e:
        click.echo(f"Error: {e}")
        return

    dist = get_action_distribution(g, sit)
    action = dist.sample_action()

    if not action:
        click.echo("No action available")
        return

    click.echo(f"Sampled action: {action.primary_justification}")
    for alloc in action.allocations:
        sh = sit.get_stakeholder(alloc.stakeholder_id)
        sh_name = sh.name if sh else alloc.stakeholder_id
        click.echo(f"  {sh_name}: {alloc.amount:.1f}")


@cli.command()
@click.argument("agent_id")
@click.option("--situation", "situation_name", default="food_scarcity",
              help="Situation to test against")
def character(agent_id, situation_name):
    """Show how an agent's character influences decisions."""
    from ..gestalt import compute_gestalt
    from ..situations.examples import get_example_situation
    from ..actions import get_action_distribution
    from ..virtues.anchors import VIRTUES

    g = compute_gestalt(agent_id)
    try:
        sit = get_example_situation(situation_name)
    except ValueError as e:
        click.echo(f"Error: {e}")
        return

    click.echo(f"\n=== CHARACTER PROFILE: {agent_id} ===\n")

    # Archetype
    if g.archetype:
        click.echo(f"Archetype: {g.archetype.upper()}")
        click.echo("")

    # Key tendencies that affect decisions
    click.echo("Decision-Relevant Tendencies:")
    relevant = [
        "prioritizes_need", "prioritizes_desert", "prioritizes_equality",
        "protects_vulnerable", "honors_commitments", "maintains_integrity"
    ]
    for t in relevant:
        val = g.tendencies.get(t, 0.5)
        bar = "#" * int(val * 15)
        click.echo(f"  {t.replace('_', ' '):<25} [{bar:<15}] {val:.0%}")

    # How this plays out in the situation
    click.echo(f"\nIn situation '{situation_name}':")

    dist = get_action_distribution(g, sit, num_samples=3)
    if dist.actions:
        top = dist.get_top_action()
        click.echo(f"  Would likely: {top.primary_justification}")
        click.echo(f"  Certainty: {dist.consensus_score:.0%}")

        if top.trade_offs:
            click.echo(f"  Acknowledges: {top.trade_offs[0]}")

    # Virtues driving this
    click.echo(f"\nDriving virtues:")
    for v_id in dist.influential_virtues[:3]:
        name = next((v["name"] for v in VIRTUES if v["id"] == v_id), v_id)
        act = g.virtue_activations.get(v_id, 0)
        click.echo(f"  {name}: {act:.0%}")


# ============================================================================
# DIFFUSION & ADVANCED GENERATION COMMANDS
# ============================================================================


@cli.command()
@click.argument("agent_id")
@click.argument("situation_name")
@click.option("--steps", default=10, help="Diffusion denoising steps")
@click.option("--samples", default=5, help="Number of action samples")
@click.option("--temperature", default=1.0, help="Generation temperature")
def diffuse(agent_id, situation_name, steps, samples, temperature):
    """Generate actions using diffusion-style denoising."""
    from ..gestalt import compute_gestalt
    from ..situations.examples import get_example_situation
    from ..actions.diffusion import generate_with_diffusion
    from ..virtues.anchors import VIRTUES

    click.echo(f"Diffusion generation: {steps} steps, {samples} samples, temp={temperature}")

    g = compute_gestalt(agent_id)
    try:
        sit = get_example_situation(situation_name)
    except ValueError as e:
        click.echo(f"Error: {e}")
        return

    dist = generate_with_diffusion(
        g, sit,
        num_samples=samples,
        num_steps=steps,
        temperature=temperature,
    )

    click.echo(f"\n=== DIFFUSION RESULTS ===\n")
    click.echo(f"Consensus: {dist.consensus_score:.0%}")

    for i, (action, prob) in enumerate(zip(dist.actions, dist.probabilities)):
        click.echo(f"\nSample {i+1} (p={prob:.0%}): {action.primary_justification}")
        for alloc in action.allocations[:3]:
            sh = sit.get_stakeholder(alloc.stakeholder_id)
            click.echo(f"  {sh.name if sh else alloc.stakeholder_id}: {alloc.amount:.1f}")


@cli.command()
@click.argument("agent_a")
@click.argument("agent_b")
def compare(agent_a, agent_b):
    """Compare two agents' gestalts."""
    from ..gestalt import compute_gestalt
    from ..gestalt.compare import compare_gestalts
    from ..virtues.anchors import VIRTUES

    g_a = compute_gestalt(agent_a)
    g_b = compute_gestalt(agent_b)

    comparison = compare_gestalts(g_a, g_b)

    click.echo(f"\n=== GESTALT COMPARISON ===\n")
    click.echo(f"{agent_a} vs {agent_b}")
    click.echo(f"\nSimilarity: {comparison.similarity:.0%}")
    click.echo(f"Archetype match: {'Yes' if comparison.archetype_match else 'No'}")

    if comparison.shared_dominant:
        names = []
        for v_id in comparison.shared_dominant[:3]:
            for v in VIRTUES:
                if v["id"] == v_id:
                    names.append(v["name"])
        click.echo(f"Shared dominant virtues: {', '.join(names)}")

    if comparison.divergent_tendencies:
        click.echo(f"\nKey differences:")
        for t_name, a_val, b_val in comparison.divergent_tendencies[:3]:
            click.echo(f"  {t_name.replace('_', ' ')}: {agent_a}={a_val:.0%} vs {agent_b}={b_val:.0%}")

    click.echo(f"\nInterpretation: {comparison.interpretation}")


@cli.command()
@click.argument("agent_id")
@click.option("--top", "top_k", default=5, help="Number of similar agents to find")
def similar(agent_id, top_k):
    """Find agents similar to a given agent."""
    from ..gestalt.compare import find_similar_agents

    click.echo(f"Finding agents similar to {agent_id}...")

    results = find_similar_agents(agent_id, top_k=top_k)

    if not results:
        click.echo("No similar agents found.")
        return

    click.echo(f"\nMost similar agents:")
    for other_id, similarity in results:
        bar = "#" * int(similarity * 20)
        click.echo(f"  {other_id}: [{bar:<20}] {similarity:.0%}")


@cli.command()
@click.option("--clusters", "n_clusters", default=4, help="Number of clusters")
def cluster(n_clusters):
    """Cluster agents by gestalt similarity."""
    from ..gestalt.compare import cluster_agents

    click.echo(f"Clustering agents into {n_clusters} groups...")

    clusters = cluster_agents(n_clusters=n_clusters)

    if not clusters:
        click.echo("No agents to cluster.")
        return

    click.echo(f"\n=== AGENT CLUSTERS ===\n")
    for i, cluster_members in enumerate(clusters):
        click.echo(f"Cluster {i+1} ({len(cluster_members)} agents):")
        for agent_id in cluster_members[:5]:
            click.echo(f"  - {agent_id}")
        if len(cluster_members) > 5:
            click.echo(f"  ... and {len(cluster_members) - 5} more")


@cli.command()
def archetypes():
    """Analyze archetype distribution among agents."""
    from ..gestalt.compare import analyze_archetype_distribution

    result = analyze_archetype_distribution()

    if result["total"] == 0:
        click.echo("No agents to analyze.")
        return

    click.echo(f"\n=== ARCHETYPE DISTRIBUTION ===\n")
    click.echo(f"Total agents: {result['total']}")
    click.echo("")

    for archetype, count in sorted(result["counts"].items(), key=lambda x: -x[1]):
        pct = result["percentages"][archetype]
        bar = "#" * int(pct * 30)
        click.echo(f"  {archetype:<15} [{bar:<30}] {count} ({pct:.0%})")


@cli.command()
@click.argument("agent_id")
def evolution(agent_id):
    """Track character evolution of an agent over time."""
    from ..gestalt.compare import track_character_evolution
    from ..virtues.anchors import VIRTUES

    windows = track_character_evolution(agent_id)

    if not windows:
        click.echo("No trajectory history found.")
        return

    click.echo(f"\n=== CHARACTER EVOLUTION: {agent_id} ===\n")

    for i, window in enumerate(windows):
        dominant = window["dominant"]
        dominant_name = next(
            (v["name"] for v in VIRTUES if v["id"] == dominant),
            dominant
        )
        click.echo(f"Window {i+1}: Dominant = {dominant_name}, Diversity = {window['diversity']}")


# ============================================================================
# OUTCOME & HISTORY COMMANDS
# ============================================================================


@cli.command()
@click.argument("agent_id")
@click.argument("situation_name")
@click.option("--outcome", type=click.Choice(["success", "partial", "failure"]),
              default="success", help="Outcome type")
@click.option("--description", default=None, help="Outcome description")
def record_outcome(agent_id, situation_name, outcome, description):
    """Record an action outcome for learning."""
    from ..gestalt import compute_gestalt
    from ..situations.examples import get_example_situation
    from ..actions import get_action_distribution, get_tracker, OutcomeType

    # Generate an action first
    g = compute_gestalt(agent_id)
    try:
        sit = get_example_situation(situation_name)
    except ValueError as e:
        click.echo(f"Error: {e}")
        return

    dist = get_action_distribution(g, sit)
    action = dist.get_top_action()

    if not action:
        click.echo("Could not generate action.")
        return

    # Record the action
    tracker = get_tracker()
    outcome_id = tracker.record_action(agent_id, action, sit)
    click.echo(f"Recorded action: {outcome_id}")

    # Resolve with outcome
    outcome_type = OutcomeType(outcome)
    desc = description or f"Action {outcome} in {situation_name}"

    # Simple impact calculation
    impacts = {sh.id: 0.5 for sh in sit.stakeholders}

    result = tracker.resolve_outcome(
        outcome_id,
        outcome_type,
        desc,
        impacts,
        virtues_honored=action.supporting_virtues if outcome == "success" else [],
        virtues_violated=action.supporting_virtues if outcome == "failure" else [],
    )

    click.echo(f"Resolved: {outcome_type.value}")
    if result.lesson_created:
        click.echo("Lesson created for collective learning.")


@cli.command()
@click.argument("agent_id")
@click.option("--limit", default=10, help="Number of history entries")
def history(agent_id, limit):
    """Show action history for an agent."""
    from ..actions.outcomes import get_tracker

    tracker = get_tracker()
    entries = tracker.get_agent_history(agent_id, limit=limit)

    if not entries:
        click.echo("No action history found.")
        return

    click.echo(f"\n=== ACTION HISTORY: {agent_id} ===\n")

    for entry in entries:
        outcome = entry.get("outcome", "unknown")
        icon = "v" if outcome == "success" else "x" if outcome == "failure" else "?"
        click.echo(f"{icon} {entry.get('situation', 'unknown')}")
        if entry.get("justification"):
            click.echo(f"    {entry['justification']}")
        if entry.get("description"):
            click.echo(f"    -> {entry['description']}")


# ============================================================================
# SITUATION PERSISTENCE COMMANDS
# ============================================================================


@cli.command()
@click.argument("situation_name")
def save_sit(situation_name):
    """Save an example situation to the graph database."""
    from ..situations import get_example_situation, save_situation

    try:
        sit = get_example_situation(situation_name)
    except ValueError as e:
        click.echo(f"Error: {e}")
        return

    save_situation(sit)
    click.echo(f"Saved situation: {sit.id} ({sit.name})")


@cli.command()
def list_saved():
    """List all saved situations in the graph."""
    from ..situations import list_situations

    saved = list_situations()

    if not saved:
        click.echo("No saved situations.")
        return

    click.echo("\n=== SAVED SITUATIONS ===\n")
    for sit in saved:
        click.echo(f"  {sit['id']}: {sit['name']}")
        click.echo(f"    {sit['stakeholder_count']} stakeholders, {sit['resource_count']} resources")


# ============================================================================
# THEATRE SESSION COMMANDS
# ============================================================================


@cli.command()
@click.option("--host", default="0.0.0.0", help="Host to bind to")
@click.option("--port", default=8000, help="Port to listen on")
@click.option("--reload", is_flag=True, help="Enable auto-reload for development")
def theatre(host, port, reload):
    """Start the conversational theatre server.

    Launches a WebSocket server for interactive AI conversations.
    Connect via ws://<host>:<port>/ws/<session_id>?user_id=<user>

    REST endpoints:
      GET  /sessions          - List active sessions
      POST /sessions          - Create new session
      GET  /sessions/{id}     - Get session details
      DELETE /sessions/{id}   - Close session
      GET  /health            - Server health check
    """
    try:
        import uvicorn
    except ImportError:
        click.echo("Error: Theatre dependencies not installed.")
        click.echo("Install with: pip install -e '.[theatre]'")
        return

    from ..transport.server import TransportServer, create_fastapi_app

    click.echo("=== SOUL KILN THEATRE ===")
    click.echo(f"Starting conversational theatre on {host}:{port}")
    click.echo("")
    click.echo("Endpoints:")
    click.echo(f"  WebSocket: ws://{host}:{port}/ws/<session_id>?user_id=<user>")
    click.echo(f"  REST API:  http://{host}:{port}/sessions")
    click.echo(f"  Health:    http://{host}:{port}/health")
    click.echo("")
    click.echo("Press Ctrl+C to stop")
    click.echo("-" * 50)

    server = TransportServer()
    app = create_fastapi_app(server)

    uvicorn.run(
        app,
        host=host,
        port=port,
        reload=reload,
        log_level="info",
    )


@cli.command()
@click.argument("session_id", required=False)
@click.option("--user", "user_id", default="cli_user", help="User ID for the session")
@click.option("--community", default=None, help="Community/domain to join (e.g., grant-getter)")
def session(session_id, user_id, community):
    """Start an interactive theatre session (CLI mode).

    Creates a local theatre session for testing without a server.
    Useful for development and debugging.
    """
    import uuid
    from ..theatre.integration import TheatreSystem, TheatreConfig

    session_id = session_id or f"cli_{uuid.uuid4().hex[:8]}"

    click.echo("=== INTERACTIVE THEATRE SESSION ===")
    click.echo(f"Session: {session_id}")
    click.echo(f"User: {user_id}")
    if community:
        click.echo(f"Community: {community}")
    click.echo("")
    click.echo("Type your message and press Enter.")
    click.echo("Commands: /quit, /view, /stats, /switch <community>")
    click.echo("-" * 50)

    # Create theatre system
    config = TheatreConfig(
        enable_emotions=False,  # No Hume API in CLI mode
        enable_scene_generation=False,
    )
    theatre = TheatreSystem.create(config=config)

    # Start session
    result = theatre.start_session(
        human_id=user_id,
        community=community,
    )
    click.echo(f"Session started: {result['session_id']}")
    click.echo(f"View: {result['view']}")
    click.echo("")

    # Interactive loop
    while True:
        try:
            user_input = click.prompt("You", prompt_suffix="> ")
        except (EOFError, KeyboardInterrupt):
            click.echo("\nEnding session...")
            break

        # Handle commands
        if user_input.startswith("/"):
            cmd_parts = user_input[1:].split(maxsplit=1)
            cmd = cmd_parts[0].lower()
            arg = cmd_parts[1] if len(cmd_parts) > 1 else None

            if cmd == "quit" or cmd == "exit":
                click.echo("Ending session...")
                break
            elif cmd == "view":
                state = theatre.get_display_state()
                click.echo(f"View: {state.get('view_type', 'unknown')}")
                click.echo(f"Theatre state: {state.get('theatre_state', 'unknown')}")
            elif cmd == "stats":
                stats = theatre.get_stats()
                click.echo(f"Stats: {stats}")
            elif cmd == "switch" and arg:
                result = theatre.switch_community(arg)
                click.echo(f"Switched to: {result['community']} ({result['agent_name']})")
            elif cmd == "toggle":
                result = theatre.toggle_view()
                click.echo(f"View: {result.get('view_type', 'toggled')}")
            else:
                click.echo(f"Unknown command: {cmd}")
            continue

        # Process input through theatre
        result = theatre.process(user_input)

        # Display turns
        for turn in result.get("turns", []):
            role = turn.get("role", "unknown")
            content = turn.get("content", "")
            speaker = turn.get("speaker_name", role)

            if role == "user_proxy":
                click.echo(f"  [Proxy] {content}")
            elif role == "builder":
                click.echo(f"  [Builder] {content}")
            elif role == "domain_agent":
                click.echo(f"  [{speaker}] {content}")
            else:
                click.echo(f"  [{role}] {content}")

        # Show topic if shifted
        topic = result.get("topic_state")
        if topic and topic.get("shift_detected"):
            click.echo(f"  (Topic: {topic.get('current_region', 'unknown')})")

        click.echo("")

    # End session
    summary = theatre.end_session()
    click.echo(f"\nSession ended. Turns: {summary.get('total_turns', 0)}")


@cli.command()
@click.option("--user", "user_id", default="cli_user", help="User ID for the creator")
def create(user_id):
    """Create a new proxy through conversation.

    Guides you through creating a personified voice for:
    - Yourself
    - Another person (family, colleague, historical figure)
    - An organization (nonprofit, company, team)
    - A concept (justice, creativity, your future self)
    - Something else (a place, a project, a memory)

    The proxy will join a community where members share everything.
    """
    from ..core.creation import ProxyCreator
    from ..core.graph_store import get_core_store

    # Initialize schema
    store = get_core_store()
    try:
        store.init_schema()
    except Exception as e:
        click.echo(f"Note: Could not initialize schema: {e}")

    click.echo("=== CREATE A NEW PROXY ===")
    click.echo(f"Creator: {user_id}")
    click.echo("-" * 50)
    click.echo("")

    # Start creation flow
    creator = ProxyCreator(creator_id=user_id, store=store)
    response = creator.start()
    click.echo(response)
    click.echo("")

    # Interactive loop
    while not creator.is_complete:
        try:
            user_input = click.prompt("You", prompt_suffix="> ")
        except (EOFError, KeyboardInterrupt):
            click.echo("\nCreation cancelled.")
            return

        if user_input.lower() in ("/quit", "/exit", "/cancel"):
            click.echo("Creation cancelled.")
            return

        response = creator.process(user_input)
        click.echo("")
        click.echo(response)
        click.echo("")

    # Show what was created
    if creator.state.proxy:
        click.echo("-" * 50)
        click.echo("Created:")
        click.echo(f"  Proxy: {creator.state.proxy.name} ({creator.state.proxy.id})")
        click.echo(f"  Entity: {creator.state.entity.name} ({creator.state.entity.type.value})")
        click.echo(f"  Community: {creator.state.community_name}")
        click.echo("")
        click.echo("Use 'session' command to start a conversation with your proxy.")


@cli.command()
def communities():
    """List all communities."""
    from ..core.graph_store import get_core_store

    store = get_core_store()
    try:
        comms = store.list_communities()
    except Exception as e:
        click.echo(f"Error listing communities: {e}")
        click.echo("Make sure the graph database is running.")
        return

    if not comms:
        click.echo("No communities yet.")
        click.echo("Use 'create' command to create a proxy and community.")
        return

    click.echo("\n=== COMMUNITIES ===\n")
    for comm in comms:
        click.echo(f"  {comm.name} ({comm.id})")
        click.echo(f"    Purpose: {comm.purpose.value}")
        click.echo(f"    Members: {comm.member_count}")
        click.echo(f"    Lessons shared: {comm.total_lessons_shared}")
        click.echo("")


@cli.command()
@click.argument("community_name")
def community(community_name):
    """Show details of a community and its members."""
    from ..core.graph_store import get_core_store
    from ..core.sharing import get_sharing

    store = get_core_store()
    comm = store.get_community_by_name(community_name)

    if not comm:
        click.echo(f"Community '{community_name}' not found.")
        return

    click.echo(f"\n=== {comm.name.upper()} ===\n")
    click.echo(f"ID: {comm.id}")
    click.echo(f"Purpose: {comm.purpose.value}")
    click.echo(f"Description: {comm.description}")
    click.echo(f"Created by: {comm.creator_id}")
    click.echo(f"Active: {comm.active}")
    click.echo("")

    click.echo("Stats:")
    click.echo(f"  Current members: {comm.member_count}")
    click.echo(f"  Total members ever: {comm.total_members_ever}")
    click.echo(f"  Lessons shared: {comm.total_lessons_shared}")
    click.echo(f"  Conversations: {comm.total_conversations}")
    click.echo("")

    # Get members
    if comm.member_ids:
        click.echo("Members:")
        for proxy_id in list(comm.member_ids)[:10]:
            proxy = store.get_proxy(proxy_id)
            if proxy:
                click.echo(f"  - {proxy.name} ({proxy.status.value})")
        if len(comm.member_ids) > 10:
            click.echo(f"  ... and {len(comm.member_ids) - 10} more")
        click.echo("")

    # Get collective wisdom
    sharing = get_sharing()
    wisdom = sharing.get_community_wisdom(comm.id)
    if wisdom.get("patterns"):
        click.echo(f"Shared patterns: {len(wisdom['patterns'])}")
    if wisdom.get("recent_lessons"):
        click.echo(f"Recent lessons: {len(wisdom['recent_lessons'])}")


@cli.command()
@click.option("--user", "user_id", default="cli_user", help="User ID")
def proxies(user_id):
    """List proxies created by a user."""
    from ..core.graph_store import get_core_store

    store = get_core_store()
    try:
        user_proxies = store.get_proxies_by_creator(user_id)
    except Exception as e:
        click.echo(f"Error listing proxies: {e}")
        return

    if not user_proxies:
        click.echo(f"No proxies created by {user_id}.")
        click.echo("Use 'create' command to create a proxy.")
        return

    click.echo(f"\n=== PROXIES by {user_id} ===\n")
    for proxy in user_proxies:
        entity = store.get_entity(proxy.entity_id)
        entity_name = entity.name if entity else "Unknown"

        click.echo(f"  {proxy.name}")
        click.echo(f"    ID: {proxy.id}")
        click.echo(f"    Status: {proxy.status.value}")
        click.echo(f"    Represents: {entity_name}")
        click.echo(f"    Communities: {', '.join(proxy.community_ids) or 'None'}")
        click.echo("")


# ============================================================================
# SEEDING COMMANDS - Planting curious entities
# ============================================================================


@cli.command()
def seeds():
    """List available seed templates for curious entities."""
    from ..core.seeding import list_seed_templates

    templates = list_seed_templates()

    click.echo("\n=== SEED TEMPLATES ===")
    click.echo("Curious entities that discover themselves through interaction.\n")

    for name, info in templates.items():
        click.echo(f"  {name}")
        click.echo(f"    Name: {info['name']}")
        click.echo(f"    Strategy: {info['strategy']}")
        click.echo(f"    Becomes: {info['suggested_type']}")
        click.echo(f"    {info['description']}")
        click.echo("")

    click.echo("Use 'seed <template> --community <name>' to plant a seed.")


@cli.command()
@click.argument("template")
@click.option("--community", required=True, help="Community to seed into")
@click.option("--name", default=None, help="Override the seed's name")
def seed(template, community, name):
    """Seed a curious entity from a template.

    Seeds are entities that don't know what they are yet.
    They discover themselves through conversation and community.

    Example:
      seed watershed --community "River Valley Stewards"
      seed future_generations --community "Climate Action"
    """
    from ..core.seeding import get_seeder, list_seed_templates
    from ..core.graph_store import get_core_store

    templates = list_seed_templates()
    if template not in templates:
        click.echo(f"Unknown template: {template}")
        click.echo(f"Available: {', '.join(templates.keys())}")
        return

    store = get_core_store()

    # Get or create community
    comm = store.get_community_by_name(community)
    if not comm:
        click.echo(f"Community '{community}' not found. Creating it...")
        from ..core.community import Community, CommunityPurpose
        comm = Community(
            name=community,
            description=f"Community for {template} seeds",
            purpose=CommunityPurpose.GENERAL,
            creator_id="system",
        )
        store.save_community(comm)

    # Seed the entity
    seeder = get_seeder()
    customizations = {"name": name} if name else None

    try:
        entity, proxy = seeder.seed_from_template(
            template_name=template,
            community_id=comm.id,
            creator_id="system",
            customizations=customizations,
        )
    except Exception as e:
        click.echo(f"Error seeding: {e}")
        return

    click.echo(f"\n=== SEED PLANTED ===\n")
    click.echo(f"Entity: {entity.name} ({entity.id})")
    click.echo(f"Type: {entity.type.value}")
    click.echo(f"Description: {entity.description}")
    click.echo(f"Community: {comm.name}")
    click.echo("")

    # Show initial question
    seed_config = entity.attributes.get("seed_config", {})
    if seed_config.get("initial_prompt"):
        click.echo(f"Initial question: \"{seed_config['initial_prompt']}\"")
        click.echo("")

    click.echo("This seed will discover itself through conversation.")
    click.echo("Use 'session' to interact with it.")


@cli.command()
@click.argument("community_name")
@click.option("--templates", default="pure_curious,witness,bridge",
              help="Comma-separated list of templates")
def seed_community(community_name, templates):
    """Seed a community with multiple curious entities.

    Creates a diverse set of seeds that explore together.

    Example:
      seed-community "New Community" --templates watershed,future_generations,witness
    """
    from ..core.seeding import get_seeder
    from ..core.graph_store import get_core_store
    from ..core.community import Community, CommunityPurpose

    store = get_core_store()

    # Get or create community
    comm = store.get_community_by_name(community_name)
    if not comm:
        click.echo(f"Creating community: {community_name}")
        comm = Community(
            name=community_name,
            description="A curious community",
            purpose=CommunityPurpose.GENERAL,
            creator_id="system",
        )
        store.save_community(comm)

    # Parse templates
    template_list = [t.strip() for t in templates.split(",")]

    click.echo(f"\n=== SEEDING COMMUNITY: {community_name} ===\n")

    seeder = get_seeder()
    results = seeder.seed_community_with_curiosity(
        community_id=comm.id,
        seed_templates=template_list,
        creator_id="system",
    )

    if not results:
        click.echo("No seeds were planted.")
        return

    click.echo(f"Planted {len(results)} seeds:\n")
    for entity, proxy in results:
        seed_config = entity.attributes.get("seed_config", {})
        click.echo(f"  {entity.name}")
        click.echo(f"    Strategy: {seed_config.get('strategy', 'unknown')}")
        click.echo(f"    Question: \"{seed_config.get('initial_prompt', '')}\"")
        click.echo("")

    click.echo(f"Community {community_name} now has {comm.member_count + len(results)} members.")
    click.echo("These seeds will discover themselves through conversation.")


# ============================================================================
# DEVELOPMENTAL COMMANDS - Biomimicry-based seed development
# ============================================================================


@cli.command()
@click.argument("entity_id")
def develop(entity_id):
    """Inspect the developmental state of an entity.

    Shows potency level, life stage, differentiation pressures,
    and signals pushing the entity toward specific types.
    """
    from ..core.development import get_dev_manager
    from ..core.graph_store import get_core_store
    from ..core.biomimicry import Potency, LifeStage

    store = get_core_store()
    entity = store.get_entity(entity_id)

    if not entity:
        click.echo(f"Entity not found: {entity_id}")
        return

    manager = get_dev_manager()
    state = manager.get_state(entity_id)

    click.echo(f"\n=== DEVELOPMENTAL STATE: {entity.name} ===\n")
    click.echo(f"Entity Type: {entity.type.value}")
    click.echo(f"Description: {entity.description[:60]}..." if len(entity.description) > 60 else f"Description: {entity.description}")
    click.echo("")

    if not state:
        click.echo("This entity is not a seed (no developmental state).")
        click.echo("Only SEED, CURIOUS, and EMERGENT types have developmental tracking.")
        return

    # Potency
    potency_desc = {
        Potency.TOTIPOTENT: "Can become anything",
        Potency.PLURIPOTENT: "Can become most things",
        Potency.MULTIPOTENT: "Several paths remain",
        Potency.OLIGOPOTENT: "Few paths remain",
        Potency.UNIPOTENT: "One clear path",
        Potency.DIFFERENTIATED: "Identity crystallized",
    }
    click.echo(f"Potency: {state.potency.value.upper()}")
    click.echo(f"  {potency_desc.get(state.potency, '')}")
    click.echo("")

    # Life stage
    stage_desc = {
        LifeStage.DORMANT: "Waiting to germinate",
        LifeStage.GERMINATING: "Starting to emerge",
        LifeStage.GROWING: "Developing capacity",
        LifeStage.BRANCHING: "Exploring possibilities",
        LifeStage.FLOWERING: "Expressing potential",
        LifeStage.FRUITING: "Producing value",
        LifeStage.SEEDING: "Spawning new entities",
        LifeStage.CHRYSALIS: "Undergoing transformation",
        LifeStage.CRYSTALLIZED: "Fixed identity",
        LifeStage.SENESCENT: "Winding down",
        LifeStage.COMPOSTING: "Returning nutrients",
    }
    click.echo(f"Life Stage: {state.life_stage.value.upper()}")
    click.echo(f"  {stage_desc.get(state.life_stage, '')}")
    click.echo("")

    # Differentiation - use the DifferentiationPressure's leading_types
    leading = state.differentiation.leading_types
    if leading:
        click.echo("Differentiation Signals (strongest pulls):")
        for entity_type, strength in leading[:5]:
            bar = "#" * int(strength * 20)
            click.echo(f"  {entity_type.value:<20} [{bar:<20}] {strength:.0%}")

        click.echo("")
        click.echo(f"Commitment level: {state.differentiation.commitment_level:.0%}")
    else:
        click.echo("No differentiation signals yet.")
    click.echo("")

    # Virtue activations (extract from signals)
    virtue_counts = {}
    for signal in state.differentiation.signals:
        if signal.signal_type == "virtue":
            # Source is like "virtue:V03"
            virtue_id = signal.source.replace("virtue:", "")
            if virtue_id not in virtue_counts:
                virtue_counts[virtue_id] = 0
            virtue_counts[virtue_id] += 1
    if virtue_counts:
        click.echo("Recent Virtue Activations:")
        for v_id, count in sorted(virtue_counts.items(), key=lambda x: -x[1])[:5]:
            click.echo(f"  {v_id}: {count} signals")
        click.echo("")

    # Chrysalis state
    if state.chrysalis:
        click.echo("CHRYSALIS STATE:")
        click.echo(f"  Phase: {state.chrysalis.phase.value}")
        click.echo(f"  Target type: {state.chrysalis.emerging_type.value if state.chrysalis.emerging_type else 'undetermined'}")
        click.echo(f"  Active: {state.chrysalis.is_active}")
        click.echo(f"  Complete: {state.chrysalis.is_complete}")
        click.echo("")


@cli.command()
@click.argument("community_name")
def niche(community_name):
    """View the niche dynamics of a community.

    Shows type distribution, inhibition effects, and vacuum
    pulls that shape what seeds can become in this community.
    """
    from ..core.development import get_dev_manager
    from ..core.graph_store import get_core_store

    store = get_core_store()
    comm = store.get_community_by_name(community_name)

    if not comm:
        click.echo(f"Community not found: {community_name}")
        return

    manager = get_dev_manager()
    niche = manager.get_niche(comm.id)

    click.echo(f"\n=== NICHE DYNAMICS: {comm.name} ===\n")

    # Type distribution (census)
    if niche.type_census:
        click.echo("Type Distribution:")
        for entity_type, count in sorted(
            niche.type_census.items(),
            key=lambda x: x[1],
            reverse=True
        ):
            bar = "#" * min(count * 2, 20)
            click.echo(f"  {entity_type.value:<20} [{bar:<20}] {count}")
        click.echo("")
    else:
        click.echo("No typed members yet.")
        click.echo("")

    # Lateral inhibition
    if niche.type_census:
        click.echo("Lateral Inhibition (present types suppress similar seeds):")
        saturated = niche.get_saturated_types()
        if saturated:
            for entity_type in saturated[:5]:
                count = niche.type_census.get(entity_type, 0)
                click.echo(f"  - {entity_type.value} (count: {count})")
        else:
            click.echo("  No types at saturation threshold yet")
        click.echo("")

    # Vacuum pulls (types that are needed)
    click.echo("Vacuum Pulls (absent types attract new seeds):")
    vacuums = niche.get_vacuum_types()
    if vacuums:
        for entity_type in vacuums[:5]:
            click.echo(f"  - {entity_type.value}")
    else:
        click.echo("  No vacuum pulls detected")
    click.echo("")

    # Virtue gradients
    if niche.virtue_gradient:
        click.echo("Virtue Gradients (community virtue emphasis):")
        sorted_virtues = sorted(
            niche.virtue_gradient.items(),
            key=lambda x: x[1],
            reverse=True
        )
        for virtue, strength in sorted_virtues[:5]:
            bar = "#" * int(strength * 20)
            click.echo(f"  {virtue:<20} [{bar:<20}] {strength:.0%}")
    click.echo("")


@cli.command()
@click.argument("entity_id")
@click.argument("virtue_id")
@click.option("--strength", default=1.0, help="Signal strength (0-1)")
def differentiate(entity_id, virtue_id, strength):
    """Send a differentiation signal to an entity.

    Virtue activations push entities toward specific types.
    For example, V09 (Justice) pulls toward MOVEMENT, COMMONS, VALUE types.

    Example:
      differentiate entity_abc123 V09 --strength 0.8
    """
    from ..core.development import get_dev_manager
    from ..core.graph_store import get_core_store
    from ..core.biomimicry import VIRTUE_TYPE_ASSOCIATIONS

    store = get_core_store()
    entity = store.get_entity(entity_id)

    if not entity:
        click.echo(f"Entity not found: {entity_id}")
        return

    manager = get_dev_manager()
    state = manager.get_state(entity_id)

    if not state:
        click.echo(f"Entity {entity_id} is not a seed (no developmental state).")
        return

    # Show what this virtue affects
    associations = VIRTUE_TYPE_ASSOCIATIONS.get(virtue_id, {})
    if associations:
        click.echo(f"Virtue {virtue_id} associations:")
        for etype, affinity in associations.items():
            click.echo(f"  - {etype.value}: {affinity:.0%}")
        click.echo("")

    click.echo(f"Sending differentiation signal: {virtue_id} (strength {strength})")
    manager.process_virtue_activation(entity_id, virtue_id, strength)

    # Get updated state
    state = manager.get_state(entity_id)
    click.echo(f"\nResult:")
    click.echo(f"  Potency: {state.potency.value}")
    click.echo(f"  Life stage: {state.life_stage.value}")
    click.echo(f"  Commitment: {state.differentiation.commitment_level:.0%}")

    leading = state.differentiation.leading_types
    if leading:
        click.echo(f"  Strongest pull: {leading[0][0].value} ({leading[0][1]:.0%})")


@cli.command()
@click.argument("entity_id")
@click.option("--target", default=None, help="Target type to transform into")
@click.option("--force", is_flag=True, help="Force transformation even if not ready")
def chrysalis(entity_id, target, force):
    """Begin metamorphosis for an entity.

    Transforms a seed into its crystallized form. The entity
    enters a chrysalis state where old patterns dissolve and
    new identity emerges.

    Example:
      chrysalis entity_abc123 --target ecosystem
    """
    from ..core.development import get_dev_manager
    from ..core.graph_store import get_core_store
    from ..core.entity import EntityType
    from ..core.biomimicry import Potency

    store = get_core_store()
    entity = store.get_entity(entity_id)

    if not entity:
        click.echo(f"Entity not found: {entity_id}")
        return

    manager = get_dev_manager()
    state = manager.get_state(entity_id)

    if not state:
        click.echo(f"Entity {entity_id} is not a seed (no developmental state).")
        return

    # Check readiness
    if not force and state.differentiation.commitment_level < 0.6:
        click.echo(f"Entity not ready for metamorphosis.")
        click.echo(f"  Commitment level: {state.differentiation.commitment_level:.0%} (need 60%)")
        click.echo(f"  Use --force to override.")
        return

    if not force and state.potency not in (Potency.UNIPOTENT, Potency.OLIGOPOTENT):
        click.echo(f"Entity not ready for metamorphosis.")
        click.echo(f"  Potency: {state.potency.value} (need oligopotent or unipotent)")
        click.echo(f"  Use --force to override.")
        return

    # Parse target type
    target_type = None
    if target:
        try:
            target_type = EntityType(target)
        except ValueError:
            click.echo(f"Unknown entity type: {target}")
            click.echo(f"Valid types: {', '.join([t.value for t in EntityType])}")
            return

    click.echo(f"\n=== BEGINNING METAMORPHOSIS ===\n")
    click.echo(f"Entity: {entity.name}")
    click.echo(f"Current type: {entity.type.value}")

    if target_type:
        click.echo(f"Target type: {target_type.value}")
    else:
        leading = state.differentiation.leading_types
        if leading:
            click.echo(f"Inferred target: {leading[0][0].value}")

    chrysalis_state = manager.begin_crystallization(entity_id, target_type)

    if not chrysalis_state:
        click.echo(f"Error: Could not begin crystallization. Entity may not be ready.")
        return

    click.echo(f"\nChrysalis entered:")
    click.echo(f"  Phase: {chrysalis_state.phase.value}")
    click.echo(f"  Target: {chrysalis_state.emerging_type.value if chrysalis_state.emerging_type else 'determining'}")
    click.echo(f"  Active: {chrysalis_state.is_active}")
    click.echo("")
    click.echo("Use 'develop' command to track transformation progress.")


@cli.command()
@click.argument("entity_ids", nargs=-1, required=True)
@click.option("--name", required=True, help="Name for the fused entity")
@click.option("--target-type", default=None, help="Target type for fused entity (defaults to most common)")
def propose_fusion(entity_ids, name, target_type):
    """Propose fusion of multiple entities (symbiogenesis).

    When entities have developed complementary capabilities,
    they may fuse into a more complex form - like mitochondria
    becoming part of eukaryotic cells.

    Example:
      propose-fusion entity_a entity_b --name "Merged Voice"
    """
    from ..core.development import get_dev_manager
    from ..core.graph_store import get_core_store
    from ..core.entity import EntityType

    store = get_core_store()
    manager = get_dev_manager()

    # Validate entities
    entities = []
    for eid in entity_ids:
        entity = store.get_entity(eid)
        if not entity:
            click.echo(f"Entity not found: {eid}")
            return
        entities.append(entity)

    if len(entities) < 2:
        click.echo("Need at least 2 entities to propose fusion.")
        return

    click.echo(f"\n=== FUSION PROPOSAL ===\n")
    click.echo(f"Entities to fuse:")
    for entity in entities:
        click.echo(f"  - {entity.name} ({entity.type.value})")

    # Determine target type
    if target_type:
        try:
            ttype = EntityType(target_type)
        except ValueError:
            click.echo(f"Unknown entity type: {target_type}")
            return
    else:
        # Default to emergent or most common type
        type_counts = {}
        for e in entities:
            if e.type not in type_counts:
                type_counts[e.type] = 0
            type_counts[e.type] += 1
        ttype = max(type_counts.keys(), key=lambda t: type_counts[t]) if type_counts else EntityType.EMERGENT

    proposal = manager.propose_fusion(
        source_entity_ids=list(entity_ids),
        target_type=ttype,
        target_name=name,
    )

    if not proposal:
        click.echo(f"Error: Could not create fusion proposal.")
        return

    click.echo(f"\nProposal created:")
    click.echo(f"  ID: {proposal.proposal_id}")
    click.echo(f"  New name: {proposal.target_name}")
    click.echo(f"  Resulting type: {proposal.target_type.value}")
    click.echo("")
    click.echo(f"Approval needed from all source entities.")
    click.echo(f"Use 'execute-fusion {proposal.proposal_id}' after approvals.")


@cli.command()
@click.argument("proposal_id")
def execute_fusion(proposal_id):
    """Execute a previously proposed entity fusion.

    This will:
    - Create a new fused entity
    - Merge attributes and facts
    - Dissolve the source entities
    - Update community memberships
    """
    from ..core.development import get_dev_manager

    manager = get_dev_manager()

    click.echo(f"Executing fusion: {proposal_id}")

    try:
        fused_entity = manager.execute_fusion(proposal_id)
    except ValueError as e:
        click.echo(f"Error: {e}")
        return

    click.echo(f"\n=== FUSION COMPLETE ===\n")
    click.echo(f"New entity: {fused_entity.name}")
    click.echo(f"ID: {fused_entity.id}")
    click.echo(f"Type: {fused_entity.type.value}")
    click.echo(f"Description: {fused_entity.description}")
    click.echo("")
    click.echo("Source entities have been dissolved.")
    click.echo("The fused entity inherits all community memberships.")


@cli.command()
@click.argument("community_name")
def quorum(community_name):
    """Check quorum patterns in a community.

    When enough members hold a pattern (beliefs, behaviors, virtues),
    it becomes a collective property that influences all members.
    """
    from ..core.development import get_dev_manager
    from ..core.graph_store import get_core_store

    store = get_core_store()
    comm = store.get_community_by_name(community_name)

    if not comm:
        click.echo(f"Community not found: {community_name}")
        return

    manager = get_dev_manager()
    quorum_state = manager.get_quorum(comm.id)

    click.echo(f"\n=== QUORUM STATE: {comm.name} ===\n")
    click.echo(f"Member count: {comm.member_count}")
    click.echo(f"Quorum threshold: {quorum_state.quorum_threshold}")
    click.echo("")

    # Show patterns that reached quorum
    community_patterns = quorum_state.community_patterns
    if community_patterns:
        click.echo("Patterns at quorum (collective properties):")
        for pattern in community_patterns:
            holders = quorum_state.pattern_holders.get(pattern, set())
            click.echo(f"  - {pattern}: {len(holders)} members")
        click.echo("")
    else:
        click.echo("No patterns have reached quorum yet.")
        click.echo("")

    # Show patterns approaching quorum (using emerging_patterns property)
    emerging = quorum_state.emerging_patterns
    if emerging:
        click.echo("Patterns approaching quorum:")
        for pattern, current, threshold in emerging:
            needed = threshold - current
            click.echo(f"  - {pattern}: {current} members (need {needed} more)")
        click.echo("")


@cli.command()
@click.argument("entity_id")
@click.argument("topics")
@click.option("--partner-types", default=None, help="Comma-separated list of partner entity types")
def converse(entity_id, topics, partner_types):
    """Simulate a conversation affecting entity development.

    Conversation topics push seeds toward certain types.
    For example, discussing "ecology" and "community" pushes
    toward ECOSYSTEM or NEIGHBORHOOD types.

    Example:
      converse entity_abc123 "ecology,sustainability,water"
    """
    from ..core.development import get_dev_manager, TOPIC_TYPE_ASSOCIATIONS
    from ..core.graph_store import get_core_store
    from ..core.entity import EntityType

    store = get_core_store()
    entity = store.get_entity(entity_id)

    if not entity:
        click.echo(f"Entity not found: {entity_id}")
        return

    manager = get_dev_manager()
    state = manager.get_state(entity_id)

    if not state:
        click.echo(f"Entity {entity_id} is not a seed (no developmental state).")
        return

    # Parse topics
    topic_list = [t.strip() for t in topics.split(",")]

    # Parse partner types
    partner_type_list = None
    if partner_types:
        partner_type_list = []
        for pt in partner_types.split(","):
            try:
                partner_type_list.append(EntityType(pt.strip()))
            except ValueError:
                click.echo(f"Warning: Unknown partner type: {pt}")

    click.echo(f"Processing conversation for {entity.name}")
    click.echo(f"Topics: {', '.join(topic_list)}")

    # Show what these topics affect
    for topic in topic_list:
        associations = TOPIC_TYPE_ASSOCIATIONS.get(topic.lower(), {})
        if associations:
            affects = [f"{t.value}:{s:.0%}" for t, s in list(associations.items())[:3]]
            click.echo(f"  '{topic}' -> {', '.join(affects)}")

    if partner_type_list:
        click.echo(f"Partner types: {', '.join([pt.value for pt in partner_type_list])}")

    result = manager.process_conversation(entity_id, topic_list, partner_type_list)

    click.echo(f"\nResult:")
    click.echo(f"  Life stage: {result.get('life_stage', 'unknown')}")
    click.echo(f"  Potency: {result.get('new_potency', 'unknown')}")
    click.echo(f"  Signals added: {result.get('signals_added', 0)}")

    # Show leading types
    if result.get("leading_types"):
        click.echo(f"\nLeading types:")
        for lt in result["leading_types"][:3]:
            click.echo(f"  - {lt['type']}: {lt['affinity']:.0%}")
