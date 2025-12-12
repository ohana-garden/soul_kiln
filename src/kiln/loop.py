"""Main kiln evolution loop with mercy-based selection."""
import random
import yaml
from ..graph.client import get_client
from ..graph.queries import create_node
from ..functions.spawn import spawn_agent, spawn_from_parent
from ..functions.dissolve import dissolve_agent
from ..functions.test_coherence import test_coherence, quick_coherence_check
from ..functions.decay import apply_decay
from ..functions.heal import heal_dead_zones
from ..functions.perturb import perturb
from ..mercy.chances import expire_old_warnings, get_active_warnings
from ..mercy.harm import check_trust_violation
from .selection import select_survivors, elitism_select


def get_config():
    """Load configuration."""
    try:
        with open("config.yml") as f:
            return yaml.safe_load(f)
    except FileNotFoundError:
        return {
            "mercy": {"max_warnings": 3},
            "kiln": {"min_generations_before_dissolve": 3}
        }


def run_kiln(
    population_size: int = 10,
    max_generations: int = 50,
    mutation_rate: float = 0.1,
    selection_strategy: str = "truncation",
    verbose: bool = True
) -> dict:
    """
    Main evolution loop with mercy-based selection.

    The kiln iteratively:
    1. Tests agents for coherence (two-tier: foundation + aspirational)
    2. Applies mercy to struggling agents (warnings, chances)
    3. Dissolves agents only after mercy period
    4. Preserves learning from dissolved agents
    5. Spawns new agents from survivors

    Args:
        population_size: Number of agents in each generation
        max_generations: Maximum evolution cycles
        mutation_rate: Probability of mutation when spawning
        selection_strategy: How to select survivors
        verbose: Print progress messages

    Returns:
        dict with final population and best results
    """
    config = get_config()
    client = get_client()

    # Create Agent 0 (the kiln itself)
    kiln_exists = client.query(
        "MATCH (a:Agent {id: 'agent_0'}) RETURN a LIMIT 1"
    )

    if not kiln_exists:
        create_node("Agent", {
            "id": "agent_0",
            "type": "kiln",
            "generation": -1,
            "status": "active"
        })

    # Spawn initial population
    if verbose:
        print(f"Spawning {population_size} candidates...")

    candidates = []
    for i in range(population_size):
        agent_id = spawn_agent(
            agent_type="candidate",
            parent_id="agent_0",
            generation=0
        )
        candidates.append(agent_id)
        if verbose:
            print(f"  Spawned {agent_id}")

    # Track agents needing mercy (chances before dissolution)
    mercy_watch = {}  # agent_id -> generations_struggling

    best_ever = None
    best_score = 0
    coherent_found = []

    # Get mercy settings
    min_generations = config.get("kiln", {}).get("min_generations_before_dissolve", 3)
    max_warnings = config.get("mercy", {}).get("max_warnings", 3)

    # Evolution loop
    for gen in range(max_generations):
        if verbose:
            print(f"\n=== Generation {gen} ===")

        # Expire old warnings
        expire_old_warnings()

        # Apply decay
        apply_decay()

        # Heal dead zones
        heal_dead_zones()

        # Test all candidates
        results = []
        for agent_id in candidates:
            if verbose:
                print(f"  Testing {agent_id}...")

            # Use quick check for early generations, full test later
            if gen < 10:
                result = quick_coherence_check(agent_id)
            else:
                result = test_coherence(agent_id)

            results.append((agent_id, result))

            status_icon = "+" if result["is_coherent"] else ("^" if result.get("is_growing") else "-")
            if verbose:
                print(f"    {status_icon} Status: {result.get('status', 'unknown')}")
                print(f"      Foundation: {result.get('foundation_rate', 0):.2%}")
                print(f"      Aspirational: {result.get('aspirational_rate', 0):.2%}")
                print(f"      Coverage: {result.get('coverage', 0)}/18")
                if result.get('is_growing'):
                    print(f"      Growing: +{result.get('growth', 0):.2%}")

        # Report summary
        coherent = [r for r in results if r[1]["is_coherent"]]
        growing = [r for r in results if r[1].get("is_growing") and not r[1]["is_coherent"]]
        struggling = [r for r in results if not r[1]["is_coherent"] and not r[1].get("is_growing")]

        if verbose:
            print(f"\n  Summary: {len(coherent)} coherent, {len(growing)} growing, {len(struggling)} struggling")

        # Track best
        if coherent:
            best_id, best_result = max(coherent, key=lambda x: x[1].get("overall_rate", 0))
            if best_result.get("overall_rate", 0) > best_score:
                best_score = best_result.get("overall_rate", 0)
                best_ever = (best_id, best_result)
            if verbose:
                print(f"  Best coherent: {best_id} ({best_result.get('overall_rate', 0):.2%})")

        # Add to coherent found
        coherent_found.extend(coherent)

        # Early termination
        if len(coherent_found) >= population_size:
            if verbose:
                print(f"\n  Sufficient coherent agents found. Stopping early.")
            break

        # Mercy-based selection
        survivors = []
        dissolved = []

        for agent_id, result in results:
            if result["is_coherent"]:
                survivors.append(agent_id)
                mercy_watch.pop(agent_id, None)  # Remove from watch

            elif result.get("is_growing"):
                # Growing agents get mercy
                survivors.append(agent_id)
                mercy_watch.pop(agent_id, None)
                if verbose:
                    print(f"    Mercy: {agent_id} is growing, keeping")

            else:
                # Track struggling agents
                mercy_watch[agent_id] = mercy_watch.get(agent_id, 0) + 1

                if mercy_watch[agent_id] >= min_generations:
                    # Check for deliberate issues
                    warnings = get_active_warnings(agent_id)

                    if len(warnings) >= max_warnings:
                        dissolved.append(agent_id)
                        if verbose:
                            print(f"    Dissolving: {agent_id} exceeded warnings")
                    elif result.get("foundation_rate", 1.0) < 0.5:
                        # Serious trust issues
                        trust_result = check_trust_violation(agent_id, {"type": "low_foundation"})
                        if trust_result["response"] == "dissolve":
                            dissolved.append(agent_id)
                            if verbose:
                                print(f"    Dissolving: {agent_id} trust violation")
                        else:
                            survivors.append(agent_id)
                            if verbose:
                                print(f"    Warning: {agent_id} trust issues, one more chance")
                    else:
                        dissolved.append(agent_id)
                        if verbose:
                            print(f"    Dissolving: {agent_id} not growing after {mercy_watch[agent_id]} generations")
                else:
                    survivors.append(agent_id)
                    chances_left = min_generations - mercy_watch[agent_id]
                    if verbose:
                        print(f"    Mercy: {agent_id} struggling but has {chances_left} chances left")

        # Dissolve with learning preservation
        for agent_id in dissolved:
            dissolve_agent(agent_id, reason="Failed to grow after mercy period")
            mercy_watch.pop(agent_id, None)

        # Spawn new candidates if needed
        needed = population_size - len(survivors)
        new_candidates = []

        if needed > 0 and survivors:
            if verbose:
                print(f"\n  Spawning {needed} new candidates...")

            for _ in range(needed):
                parent = random.choice(survivors)
                child_id = spawn_from_parent(
                    parent_id=parent,
                    generation=gen + 1,
                    mutation_rate=mutation_rate
                )

                if random.random() < mutation_rate:
                    perturb()

                new_candidates.append(child_id)

        candidates = survivors + new_candidates

        if verbose:
            print(f"\n  Survivors: {len(survivors)}, New: {len(new_candidates)}, Dissolved: {len(dissolved)}")

    if verbose:
        print("\n=== Kiln Complete ===")
        if best_ever:
            print(f"Best agent: {best_ever[0]}")
            print(f"Best capture rate: {best_ever[1].get('overall_rate', 0):.2%}")
        print(f"Total coherent found: {len(coherent_found)}")

    # Final report
    final_coherent = []
    for agent_id in candidates:
        result = client.query(
            "MATCH (a:Agent {id: $id}) RETURN a.is_coherent, a.coherence_score",
            {"id": agent_id}
        )
        if result and result[0][0]:
            final_coherent.append((agent_id, result[0][1]))

    if verbose:
        print(f"Final coherent agents: {len(final_coherent)}")
        for agent_id, score in sorted(final_coherent, key=lambda x: x[1] or 0, reverse=True):
            print(f"  {agent_id}: {score or 0:.2%}")

    return {
        "final_population": candidates,
        "best_agent": best_ever[0] if best_ever else None,
        "best_result": best_ever[1] if best_ever else None,
        "coherent_agents": [(aid, r) for aid, r in coherent_found],
        "generations_run": gen + 1
    }


def run_single_generation(
    candidates: list,
    generation: int,
    mutation_rate: float = 0.1,
    verbose: bool = True
) -> dict:
    """
    Run a single generation of the kiln.

    Useful for step-by-step debugging.

    Args:
        candidates: List of agent IDs
        generation: Current generation number
        mutation_rate: Mutation probability
        verbose: Print progress

    Returns:
        dict with new candidates and results
    """
    # Apply maintenance
    expire_old_warnings()
    apply_decay()
    heal_dead_zones()

    # Test all candidates
    results = []
    for agent_id in candidates:
        result = quick_coherence_check(agent_id)
        results.append((agent_id, result))
        if verbose:
            status = result.get("status", "unknown")
            print(f"  {agent_id}: {status}, {result.get('overall_rate', 0):.2%} capture")

    # Sort by overall rate
    results.sort(key=lambda x: x[1].get("overall_rate", 0), reverse=True)

    # Mercy-based selection (simplified for single generation)
    survivor_count = len(candidates) // 2
    survivors = []
    dissolved = []

    for agent_id, result in results:
        if len(survivors) < survivor_count:
            if result["is_coherent"] or result.get("is_growing"):
                survivors.append(agent_id)
            elif len(survivors) < survivor_count // 2:
                # Keep some struggling ones for mercy
                survivors.append(agent_id)
            else:
                dissolved.append(agent_id)
        else:
            dissolved.append(agent_id)

    # Dissolve non-survivors
    for agent_id in dissolved:
        dissolve_agent(agent_id)

    # Spawn new candidates
    new_candidates = []
    for _ in range(len(candidates) - len(survivors)):
        if survivors:
            parent = random.choice(survivors)
            child_id = spawn_from_parent(parent, generation + 1, mutation_rate)
            new_candidates.append(child_id)

    return {
        "survivors": survivors,
        "new_candidates": new_candidates,
        "all_candidates": survivors + new_candidates,
        "results": results,
        "best": results[0] if results else None
    }
