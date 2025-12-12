"""CLI commands for the Virtue Basin Platform with mercy system."""
import click
from ..graph.client import get_client
from ..graph.schema import init_schema, clear_graph
from ..virtues.anchors import init_virtues, get_virtue_degrees
from ..virtues.tiers import FOUNDATION, ASPIRATIONAL
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
    click.echo(f"Captured by: {result['captured_by']} ({result.get('capture_tier', 'n/a')})")
    click.echo(f"Trajectory length: {len(result['trajectory'])}")
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

    status_icon = "+" if result["is_coherent"] else ("^" if result.get("is_growing") else "-")
    click.echo(f"\n{status_icon} {result.get('status', 'unknown').upper()}: {result.get('message', '')}")

    click.echo(f"\nFoundation (Trustworthiness):")
    click.echo(f"  Rate: {result.get('foundation_rate', 0):.2%} (need >=99%)")
    click.echo(f"  Captures: {result.get('foundation_captures', {})}")

    click.echo(f"\nAspirational (18 virtues):")
    click.echo(f"  Rate: {result.get('aspirational_rate', 0):.2%} (need >=60%)")
    click.echo(f"  Coverage: {result.get('coverage', 0)}/18 (need >=10)")
    click.echo(f"  Captures: {result.get('aspirational_captures', {})}")

    growth = result.get('growth', 0)
    click.echo(f"\nGrowth: {'+' if growth > 0 else ''}{growth:.2%}")
    click.echo(f"Escapes: {result.get('escapes', 0)}")


@cli.command()
@click.argument("agent_id")
def inspect(agent_id):
    """Introspect an agent with full mercy context."""
    result = introspect(agent_id)

    click.echo(f"\nAgent: {result['id']}")
    click.echo(f"Type: {result['type']}")
    click.echo(f"Generation: {result['generation']}")
    click.echo(f"Status: {result['status']}")
    click.echo(f"Coherence score: {result['coherence_score']}")
    click.echo(f"Parent: {result['parent']}")
    click.echo(f"Connections: {len(result['connections'])}")

    if result.get('virtue_captures'):
        click.echo(f"\nVirtue captures:")
        for virtue, count in result['virtue_captures'].items():
            click.echo(f"  {virtue}: {count}")

    # Show warnings
    warnings = get_active_warnings(agent_id)
    if warnings:
        click.echo(f"\nActive warnings ({len(warnings)}):")
        for w in warnings:
            click.echo(f"  - {w[2].upper() if w[2] else 'LOW'}: {w[1]}")
    else:
        click.echo(f"\nNo active warnings.")

    if result.get('recent_trajectories'):
        click.echo(f"\nRecent trajectories:")
        for traj in result['recent_trajectories'][:5]:
            click.echo(f"  {traj['id']}: captured={traj['captured']} "
                      f"by={traj['captured_by']}")


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
        click.echo(f"  [{l_type}] {desc[:60]}...")
        click.echo(f"    Virtue: {virtue or 'n/a'}, From: {agent}\n")


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

    if virtues:
        click.echo("\nVirtue Anchors:")
        click.echo("  FOUNDATION:")
        for v in virtues:
            if v[1] == "foundation":
                click.echo(f"    {v[0]}: {v[2]:.2f}")
        click.echo("  ASPIRATIONAL:")
        for v in virtues:
            if v[1] == "aspirational":
                click.echo(f"    {v[0]}: {v[2]:.2f}")


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

        if tier != current_tier:
            click.echo(f"\n  {tier.upper()}:")
            current_tier = tier

        threshold = threshold or (0.99 if tier == "foundation" else 0.60)
        click.echo(f"    {v_id} {name:<20} act={activation:.2f} deg={degree} threshold={threshold:.0%}")
        click.echo(f"         {essence}")


@cli.command()
def agents():
    """List all active agents with coherence status."""
    client = get_client()

    result = client.query(
        """
        MATCH (a:Agent)
        WHERE a.status = 'active'
        RETURN a.id, a.type, a.generation, a.coherence_score,
               a.is_coherent, a.is_growing, a.status_message
        ORDER BY a.coherence_score DESC
        """
    )

    if not result:
        click.echo("No active agents.")
        return

    click.echo("Active Agents:")
    click.echo("-" * 70)
    for row in result:
        agent_id, agent_type, gen, score, coherent, growing, message = row
        score_str = f"{score:.4f}" if score else "untested"

        if coherent:
            status = "+"
        elif growing:
            status = "^"
        else:
            status = "-"

        click.echo(f"{status} {agent_id}  type={agent_type}  gen={gen}  score={score_str}")
        if message:
            click.echo(f"    {message}")


@cli.command()
def tiers():
    """Explain the two-tier virtue model."""
    click.echo("\n=== TWO-TIER VIRTUE MODEL ===\n")

    click.echo("FOUNDATION (Absolute requirement):")
    click.echo("-" * 40)
    for v_id, info in FOUNDATION.items():
        click.echo(f"  {v_id}: {info['name']}")
        click.echo(f"       {info['essence']}")
        click.echo(f"       Threshold: {info['threshold']:.0%}")
        click.echo(f"       {info['reason']}\n")

    click.echo("\nASPIRATIONAL (Growth-oriented, 60% threshold):")
    click.echo("-" * 40)
    for v_id, info in ASPIRATIONAL.items():
        click.echo(f"  {v_id}: {info['name']}")
        click.echo(f"       {info['essence']}")

    click.echo("\n=== PHILOSOPHY ===")
    click.echo("Trust is the foundation. Growth is the journey. We learn together.")
