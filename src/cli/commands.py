"""CLI commands for the Virtue Basin Platform with mercy system."""
import click
from ..graph.client import get_client
from ..graph.schema import init_schema, clear_graph
from ..virtues.anchors import init_virtues, get_virtue_degrees
from ..kiln.loop import run_kiln
from ..functions.spread import spread_activation
from ..functions.test_coherence import test_coherence
from ..functions.introspect import introspect
from ..functions.spawn import spawn_agent
from ..functions.heal import check_graph_health


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
        click.echo(f"Best capture rate: {result['best_result']['capture_rate']:.2%}")
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
    click.echo(f"Capture time: {result['capture_time']}")
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
        if result.get("status") == "growing":
            status_icon = "^"  # Growing
        else:
            status_icon = "v"  # Coherent (checkmark approximation)
    else:
        status_icon = "x"  # Needs work

    click.echo(f"\n{status_icon} {result.get('status', 'unknown').upper()}: {result.get('message', '')}")

    click.echo(f"\nFoundation (Trustworthiness):")
    click.echo(f"  Rate: {result.get('foundation_rate', 0):.2%} (need >=99%)")
    click.echo(f"  Captures: {result.get('foundation_captures', {})}")

    click.echo(f"\nAspirational (18 virtues):")
    click.echo(f"  Rate: {result.get('aspirational_rate', 0):.2%} (need >=60%)")
    click.echo(f"  Coverage: {result['coverage']}/18 (need >=10)")
    click.echo(f"  Captures: {result.get('aspirational_captures', {})}")

    click.echo(f"\nOverall:")
    click.echo(f"  Score: {result['score']:.4f}")
    click.echo(f"  Capture rate: {result['capture_rate']:.2%}")
    click.echo(f"  Dominance: {result['dominance']:.2%}")
    click.echo(f"  Growth: {'+' if result.get('growth', 0) > 0 else ''}{result.get('growth', 0):.2%}")
    click.echo(f"  Escapes: {result['escapes']}")


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

    if result['recent_trajectories']:
        click.echo(f"\nRecent trajectories:")
        for traj in result['recent_trajectories'][:5]:
            tier = traj.get('capture_tier', 'N/A')
            click.echo(f"  {traj['id']}: captured={traj['captured']} "
                      f"by={traj['captured_by']} (tier={tier})")


@cli.command()
@click.argument("agent_id")
def warnings(agent_id):
    """Show active warnings for an agent."""
    try:
        from ..mercy.chances import get_active_warnings
        warns = get_active_warnings(agent_id)

        if not warns:
            click.echo("No active warnings. Keep growing!")
        else:
            click.echo(f"Active warnings ({len(warns)}):")
            for w in warns:
                click.echo(f"  [{w[2]}] {w[1]}")
                if w[3]:  # virtue
                    click.echo(f"    Related virtue: {w[3]}")
    except ImportError:
        click.echo("Mercy module not available.")


@cli.command()
@click.option("--limit", default=10, help="Number of lessons to show")
def lessons(limit):
    """Show recent lessons from the collective knowledge pool."""
    try:
        from ..knowledge.pool import get_recent_lessons
        recent = get_recent_lessons(limit=limit)

        if not recent:
            click.echo("No lessons in the knowledge pool yet.")
            return

        click.echo("Recent lessons from the collective:\n")
        for lesson in recent:
            l_id, l_type, desc, virtue, agent = lesson
            click.echo(f"  [{l_type}] {(desc or '')[:60]}...")
            click.echo(f"    Virtue: {virtue}, From: {agent}\n")
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
        tier = tier or "aspirational"
        activation = activation if activation is not None else 0.0
        threshold = threshold if threshold is not None else 0.60

        if tier != current_tier:
            current_tier = tier
            click.echo(f"\n  [{tier.upper()}]")

        click.echo(f"    {v_id} {name:<20} act={activation:.2f} deg={degree} threshold={threshold:.2f}")
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
               a.is_growing, a.foundation_rate, a.aspirational_rate
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
        is_growing = row[4] if len(row) > 4 else None
        foundation_rate = row[5] if len(row) > 5 else None
        aspirational_rate = row[6] if len(row) > 6 else None

        score_str = f"{score:.4f}" if score else "untested"
        growing_str = " (growing)" if is_growing else ""

        click.echo(f"{agent_id}  type={agent_type}  gen={gen}  score={score_str}{growing_str}")
        if foundation_rate is not None:
            click.echo(f"  foundation={foundation_rate:.2%}  aspirational={aspirational_rate:.2%}" if aspirational_rate else f"  foundation={foundation_rate:.2%}")


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
