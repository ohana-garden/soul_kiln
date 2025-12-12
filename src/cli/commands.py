"""CLI commands for the Virtue Basin Platform."""
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
    """Virtue Basin Platform - Soul evolution through graph dynamics."""
    pass


@cli.command()
def init():
    """Initialize graph with schema and virtues."""
    click.echo("Initializing schema...")
    init_schema()

    click.echo("Creating virtue anchors...")
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
    """Run the kiln evolution loop."""
    click.echo(f"Starting kiln: {population} candidates, {generations} generations")

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
@click.option("--max-steps", default=1000, help="Maximum propagation steps")
@click.option("--threshold", default=0.7, help="Capture threshold")
def spread(node_id, max_steps, threshold):
    """Test activation spread from a node."""
    result = spread_activation(
        node_id,
        max_steps=max_steps,
        capture_threshold=threshold
    )

    click.echo(f"Captured: {result['captured']}")
    click.echo(f"Captured by: {result['captured_by']}")
    click.echo(f"Trajectory length: {len(result['trajectory'])}")
    click.echo(f"Capture time: {result['capture_time']}")
    click.echo(f"Path: {' -> '.join(result['trajectory'][:10])}")
    if len(result['trajectory']) > 10:
        click.echo(f"  ... ({len(result['trajectory']) - 10} more)")


@cli.command()
@click.argument("agent_id")
@click.option("--stimuli", default=100, help="Number of test stimuli")
def test(agent_id, stimuli):
    """Test coherence of an agent."""
    click.echo(f"Testing {agent_id} with {stimuli} stimuli...")
    result = test_coherence(agent_id, stimulus_count=stimuli)

    click.echo(f"\nResults:")
    click.echo(f"  Coherent: {result['is_coherent']}")
    click.echo(f"  Score: {result['score']:.4f}")
    click.echo(f"  Capture rate: {result['capture_rate']:.2%}")
    click.echo(f"  Coverage: {result['coverage']}/19 virtues")
    click.echo(f"  Dominance: {result['dominance']:.2%}")
    click.echo(f"  Avg capture time: {result['avg_capture_time']:.1f} steps")
    click.echo(f"  Escapes: {result['escapes']}")
    click.echo(f"\nVirtue distribution:")
    for virtue, count in sorted(result['virtue_distribution'].items(),
                                key=lambda x: x[1], reverse=True):
        click.echo(f"    {virtue}: {count}")


@cli.command()
@click.argument("agent_id")
def inspect(agent_id):
    """Introspect an agent."""
    result = introspect(agent_id)

    click.echo(f"Agent: {result['id']}")
    click.echo(f"Type: {result['type']}")
    click.echo(f"Generation: {result['generation']}")
    click.echo(f"Status: {result['status']}")
    click.echo(f"Coherence score: {result['coherence_score']}")
    click.echo(f"Parent: {result['parent']}")
    click.echo(f"Connections: {len(result['connections'])}")

    if result['virtue_captures']:
        click.echo(f"\nVirtue captures:")
        for virtue, count in result['virtue_captures'].items():
            click.echo(f"  {virtue}: {count}")

    if result['recent_trajectories']:
        click.echo(f"\nRecent trajectories:")
        for traj in result['recent_trajectories'][:5]:
            click.echo(f"  {traj['id']}: captured={traj['captured']} "
                      f"by={traj['captured_by']}")


@cli.command()
@click.option("--type", "agent_type", default="candidate", help="Agent type")
@click.option("--parent", default=None, help="Parent agent ID")
def spawn(agent_type, parent):
    """Spawn a new candidate agent."""
    init_schema()
    init_virtues()

    agent_id = spawn_agent(agent_type=agent_type, parent_id=parent)
    click.echo(f"Spawned: {agent_id}")


@cli.command()
def status():
    """Show graph status."""
    client = get_client()

    nodes = client.query("MATCH (n) RETURN labels(n), count(*)")
    edges = client.query("MATCH ()-[r]->() RETURN type(r), count(*)")

    click.echo("Nodes:")
    for row in nodes:
        click.echo(f"  {row[0]}: {row[1]}")

    click.echo("\nEdges:")
    for row in edges:
        click.echo(f"  {row[0]}: {row[1]}")


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
    """List all virtue anchors and their status."""
    client = get_client()

    result = client.query(
        """
        MATCH (v:VirtueAnchor)
        OPTIONAL MATCH (v)-[r]-()
        RETURN v.id, v.name, v.essence, v.activation, count(r) as degree
        ORDER BY v.id
        """
    )

    click.echo("Virtue Anchors:")
    click.echo("-" * 70)
    for row in result:
        v_id, name, essence, activation, degree = row
        click.echo(f"{v_id} {name:<20} act={activation:.2f} deg={degree}")
        click.echo(f"     {essence}")


@cli.command()
def agents():
    """List all active agents."""
    client = get_client()

    result = client.query(
        """
        MATCH (a:Agent)
        WHERE a.status = 'active'
        RETURN a.id, a.type, a.generation, a.coherence_score
        ORDER BY a.coherence_score DESC
        """
    )

    if not result:
        click.echo("No active agents.")
        return

    click.echo("Active Agents:")
    click.echo("-" * 60)
    for row in result:
        agent_id, agent_type, gen, score = row
        score_str = f"{score:.4f}" if score else "untested"
        click.echo(f"{agent_id}  type={agent_type}  gen={gen}  score={score_str}")
