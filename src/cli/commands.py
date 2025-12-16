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
# PERSONA CAPSULE COMMANDS
# ============================================================================


@cli.command()
@click.argument("agent_id")
@click.option("--context", "-c", default=None, help="Situation context text")
@click.option("--format", "-f", "output_format", default="text",
              type=click.Choice(["text", "json", "brief"]),
              help="Output format")
def persona(agent_id, context, output_format):
    """Compile a persona capsule for an agent.

    The persona capsule is a structured representation of the agent's
    character suitable for LLM conditioning. It includes:
    - Hard boundaries (taboos, commitments)
    - Ranked values (from virtues)
    - Soft preferences (from tendencies)
    - Community patterns (archetype typical behaviors)
    - Explicit uncertainties
    """
    from ..persona import compile_persona_capsule

    capsule = compile_persona_capsule(agent_id, context)

    if output_format == "json":
        import json
        click.echo(json.dumps(capsule.model_dump(), indent=2, default=str))
    elif output_format == "brief":
        click.echo(f"\n=== PERSONA: {capsule.agent_name or capsule.agent_id} ===\n")
        if capsule.archetype:
            click.echo(f"Archetype: {capsule.archetype}")
        if capsule.values:
            top_values = ", ".join(f"{v.name} ({v.strength:.0%})" for v in capsule.values[:3])
            click.echo(f"Top Values: {top_values}")
        if capsule.boundaries:
            click.echo(f"Boundaries: {len(capsule.boundaries)}")
        if capsule.uncertainties:
            click.echo(f"Uncertainties: {len(capsule.uncertainties)}")
    else:
        # Full text format
        click.echo(capsule.to_prompt_text())


@cli.command()
@click.argument("agent_id")
@click.argument("situation_name")
def persona_for(agent_id, situation_name):
    """Compile a persona capsule tailored to a specific situation.

    Uses the structured situation to filter relevant preferences and roles.
    """
    from ..persona import compile_for_situation
    from ..situations import get_example_situation

    try:
        situation = get_example_situation(situation_name)
    except ValueError as e:
        click.echo(f"Error: {e}")
        return

    capsule = compile_for_situation(agent_id, situation)
    click.echo(capsule.to_prompt_text())


@cli.command()
@click.option("--refresh", is_flag=True, help="Force refresh cached patterns")
def archetype_patterns(refresh):
    """Show community patterns for all archetypes.

    Displays the typical values and tendencies for each archetype,
    computed from the agent population (or from priors if no population).
    """
    from ..persona.community import compute_archetype_patterns, ARCHETYPE_PRIORS

    stats = compute_archetype_patterns(force_refresh=refresh)

    for archetype in ["guardian", "seeker", "servant", "contemplative"]:
        click.echo(f"\n=== {archetype.upper()} ===\n")

        prior = ARCHETYPE_PRIORS.get(archetype, {})
        click.echo(f"Description: {prior.get('description', 'N/A')}")

        if archetype in stats:
            arch_stats = stats[archetype]
            click.echo(f"Agents in cluster: {arch_stats.agent_count}")
            click.echo(f"Cluster coherence: {arch_stats.coherence:.0%}")

            # Top values
            if arch_stats.mean_values:
                from ..virtues.anchors import VIRTUES
                top = sorted(arch_stats.mean_values.items(), key=lambda x: -x[1])[:5]
                click.echo("Top values:")
                for v_id, strength in top:
                    v_name = next((v["name"] for v in VIRTUES if v["id"] == v_id), v_id)
                    click.echo(f"  - {v_name}: {strength:.0%}")

            # Top tendencies
            if arch_stats.mean_tendencies:
                top = sorted(arch_stats.mean_tendencies.items(), key=lambda x: -x[1])[:5]
                click.echo("Top tendencies:")
                for t_name, strength in top:
                    click.echo(f"  - {t_name.replace('_', ' ')}: {strength:.0%}")

        # Characteristic behaviors
        behaviors = prior.get("characteristic_behaviors", [])
        if behaviors:
            click.echo("Typical behaviors:")
            for b in behaviors:
                click.echo(f"  - {b}")


@cli.command()
@click.argument("agent_id")
def archetype_compare(agent_id):
    """Compare an agent to their archetype's typical pattern.

    Shows how the agent differs from the population average
    for their archetype cluster.
    """
    from ..gestalt import compute_gestalt
    from ..persona.community import compare_to_archetype

    gestalt = compute_gestalt(agent_id)
    comparison = compare_to_archetype(gestalt)

    click.echo(f"\n=== {agent_id} vs {comparison['archetype'] or 'untyped'} archetype ===\n")
    click.echo(f"Alignment with archetype: {comparison['alignment']:.0%}")

    if comparison["above_typical"]:
        click.echo("\nAbove typical (distinctive strengths):")
        for item, diff in comparison["above_typical"]:
            click.echo(f"  + {item}: +{diff:.0%}")

    if comparison["below_typical"]:
        click.echo("\nBelow typical:")
        for item, diff in comparison["below_typical"]:
            click.echo(f"  - {item}: {diff:.0%}")


@cli.command()
@click.argument("agent_id")
@click.argument("predicate")
@click.argument("value")
@click.option("--evidence", "-e", default=None, help="Evidence ID (e.g., lesson_123)")
def record_fact(agent_id, predicate, value, evidence):
    """Record a temporal fact about an agent.

    Facts have valid_at timestamps and can be superseded by later facts,
    enabling "who they were vs who they are" queries.

    Example predicates: prefers, has_value, tendency, commitment
    """
    from ..persona.temporal import create_fact, update_fact

    # Check if fact already exists (update vs create)
    from ..persona.temporal import get_store
    store = get_store()
    existing = store.query(subject=agent_id, predicate=predicate)

    if existing:
        old, new = update_fact(
            agent_id, predicate, value,
            evidence_type="declaration" if not evidence else "lesson",
            evidence_id=evidence,
        )
        click.echo(f"Updated fact: {predicate}")
        click.echo(f"  Old: {old.object}")
        click.echo(f"  New: {new.object}")
    else:
        fact = create_fact(
            agent_id, predicate, value,
            evidence_type="declaration" if not evidence else "lesson",
            evidence_id=evidence,
        )
        click.echo(f"Created fact: {fact.id}")
        click.echo(f"  {predicate} = {value}")


@cli.command()
@click.argument("agent_id")
@click.argument("predicate")
def fact_history(agent_id, predicate):
    """Show the history of a fact over time.

    Displays how a fact's value has changed, including when
    each value was valid.
    """
    from ..persona.temporal import get_store

    store = get_store()
    history = store.get_fact_history(agent_id, predicate)

    if not history:
        click.echo(f"No history found for {agent_id}.{predicate}")
        return

    click.echo(f"\n=== History: {agent_id}.{predicate} ===\n")

    for fact in history:
        status = "CURRENT" if fact.is_valid() else "expired"
        click.echo(f"[{status}] {fact.object}")
        click.echo(f"  Valid from: {fact.valid_at}")
        if fact.invalid_at:
            click.echo(f"  Expired at: {fact.invalid_at}")
        if fact.evidence_id:
            click.echo(f"  Evidence: {fact.evidence_type}:{fact.evidence_id}")
        if fact.supersedes:
            click.echo(f"  Supersedes: {fact.supersedes}")
        click.echo()
