"""Main kiln evolution loop."""
import random
from ..graph.client import get_client
from ..graph.queries import create_node
from ..functions.spawn import spawn_agent, spawn_from_parent
from ..functions.dissolve import dissolve_agent
from ..functions.test_coherence import test_coherence, quick_coherence_check
from ..functions.decay import apply_decay
from ..functions.heal import heal_dead_zones
from ..functions.perturb import perturb
from .selection import select_survivors, elitism_select


def run_kiln(
    population_size: int = 10,
    max_generations: int = 50,
    mutation_rate: float = 0.1,
    selection_strategy: str = "truncation",
    verbose: bool = True
) -> dict:
    """
    Main evolution loop.

    The kiln iteratively:
    1. Tests agents for coherence
    2. Selects survivors based on fitness
    3. Dissolves failed agents
    4. Spawns new agents from survivors
    5. Applies decay and healing

    Args:
        population_size: Number of agents in each generation
        max_generations: Maximum evolution cycles
        mutation_rate: Probability of mutation when spawning
        selection_strategy: How to select survivors
        verbose: Print progress messages

    Returns:
        dict with final population and best results
    """
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

    best_ever = None
    best_score = 0
    coherent_found = []

    # Evolution loop
    for gen in range(max_generations):
        if verbose:
            print(f"\n=== Generation {gen} ===")

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

            if verbose:
                print(f"    Coherent: {result['is_coherent']}, "
                      f"Capture: {result['capture_rate']:.2%}, "
                      f"Coverage: {result['coverage']}/19")

        # Sort by coherence score
        results.sort(key=lambda x: x[1].get("capture_rate", 0), reverse=True)

        # Track best ever
        best_id, best_result = results[0]
        if best_result.get("capture_rate", 0) > best_score:
            best_score = best_result.get("capture_rate", 0)
            best_ever = (best_id, best_result)

        if verbose:
            print(f"\n  Best this generation: {best_id}")
            print(f"    Capture rate: {best_result['capture_rate']:.2%}")
            print(f"    Coverage: {best_result['coverage']}/19")
            print(f"    Virtues: {best_result['virtue_distribution']}")

        # Check for coherent agents
        coherent = [(aid, r) for aid, r in results if r["is_coherent"]]
        if coherent:
            if verbose:
                print(f"\n  Found {len(coherent)} coherent souls!")
                for agent_id, result in coherent:
                    print(f"    {agent_id}: {result['capture_rate']:.2%}")
            coherent_found.extend(coherent)

        # Early termination if we have enough coherent agents
        if len(coherent_found) >= population_size:
            if verbose:
                print(f"\n  Sufficient coherent agents found. Stopping early.")
            break

        # Selection: keep survivors
        survivor_count = population_size // 2
        if selection_strategy == "elitism":
            survivors = elitism_select(results, survivor_count)
        else:
            survivors = select_survivors(results, survivor_count, selection_strategy)

        dissolved = [aid for aid, _ in results if aid not in survivors]

        # Dissolve non-survivors
        for agent_id in dissolved:
            dissolve_agent(agent_id)

        # Spawn new candidates from survivors
        new_candidates = []
        while len(new_candidates) < population_size - len(survivors):
            parent = random.choice(survivors)
            child_id = spawn_from_parent(
                parent_id=parent,
                generation=gen + 1,
                mutation_rate=mutation_rate
            )

            # Random perturbation for exploration
            if random.random() < mutation_rate:
                perturb()

            new_candidates.append(child_id)

        candidates = survivors + new_candidates

        if verbose:
            print(f"  Survivors: {len(survivors)}, New: {len(new_candidates)}")

    if verbose:
        print("\n=== Kiln Complete ===")
        if best_ever:
            print(f"Best agent: {best_ever[0]}")
            print(f"Best capture rate: {best_ever[1]['capture_rate']:.2%}")
        print(f"Total coherent found: {len(coherent_found)}")

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
    apply_decay()
    heal_dead_zones()

    # Test all candidates
    results = []
    for agent_id in candidates:
        result = quick_coherence_check(agent_id)
        results.append((agent_id, result))
        if verbose:
            print(f"  {agent_id}: {result['capture_rate']:.2%} capture, "
                  f"{result['coverage']}/19 coverage")

    # Sort and select
    results.sort(key=lambda x: x[1].get("capture_rate", 0), reverse=True)
    survivor_count = len(candidates) // 2
    survivors = [r[0] for r in results[:survivor_count]]

    # Dissolve non-survivors
    for agent_id, _ in results[survivor_count:]:
        dissolve_agent(agent_id)

    # Spawn new candidates
    new_candidates = []
    for _ in range(len(candidates) - len(survivors)):
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
