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
            "kiln": {
                "dissolve_immediately": False,
                "min_generations_before_dissolve": 3
            },
            "mercy": {
                "max_warnings": 3
            }
        }


def run_kiln(
    population_size: int = 10,
    max_generations: int = 50,
    mutation_rate: float = 0.1,
    selection_strategy: str = "truncation",
    verbose: bool = True
) -> dict:
    """
    Main evolution loop with mercy.

    The kiln iteratively:
    1. Expires old warnings
    2. Tests agents for coherence (two-tier evaluation)
    3. Selects survivors with mercy (growth counts)
    4. Dissolves failed agents after grace period
    5. Spawns new agents from survivors
    6. Applies decay and healing

    Key mercy features:
    - Growing agents are considered coherent
    - Agents get multiple generations to improve
    - Warnings track issues but don't immediately dissolve
    - Trust violations are serious but still get one chance

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
    kiln_config = config.get("kiln", {})
    mercy_config = config.get("mercy", {})
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
        print("Remember: Trustworthiness is absolute; other virtues allow growth\n")

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
    min_gens_before_dissolve = kiln_config.get("min_generations_before_dissolve", 3)
    max_warnings = mercy_config.get("max_warnings", 3)

    # Evolution loop
    for gen in range(max_generations):
        if verbose:
            print(f"\n=== Generation {gen} ===")

        # Expire old warnings
        try:
            expire_old_warnings()
        except Exception:
            pass

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

            # Status icon based on two-tier evaluation
            if result["is_coherent"]:
                if result.get("status") == "growing":
                    status_icon = "^"  # Growing
                else:
                    status_icon = "v"  # Coherent
            else:
                status_icon = "x"  # Needs work

            if verbose:
                print(f"    {status_icon} Status: {result.get('status', 'unknown')}")
                if result.get("foundation_rate") is not None:
                    print(f"      Foundation: {result['foundation_rate']:.2%}")
                if result.get("aspirational_rate") is not None:
                    print(f"      Aspirational: {result['aspirational_rate']:.2%}")
                print(f"      Coverage: {result.get('coverage', 0)}/18")
                if result.get("is_growing"):
                    print(f"      Growing: +{result.get('growth', 0):.2%}")

        # Report summary
        coherent = [r for r in results if r[1]["is_coherent"] and r[1].get("status") != "growing"]
        growing = [r for r in results if r[1].get("is_growing") and r[1].get("status") == "growing"]
        struggling = [r for r in results if not r[1]["is_coherent"]]

        if verbose:
            print(f"\n  Summary: {len(coherent)} coherent, {len(growing)} growing, {len(struggling)} struggling")

        # Track best ever
        results.sort(key=lambda x: x[1].get("capture_rate", x[1].get("overall_rate", 0)), reverse=True)
        best_id, best_result = results[0]
        if best_result.get("capture_rate", best_result.get("overall_rate", 0)) > best_score:
            best_score = best_result.get("capture_rate", best_result.get("overall_rate", 0))
            best_ever = (best_id, best_result)

        if verbose and coherent:
            best_coherent = max(coherent, key=lambda x: x[1].get("capture_rate", x[1].get("overall_rate", 0)))
            print(f"  Best coherent: {best_coherent[0]} ({best_coherent[1].get('capture_rate', best_coherent[1].get('overall_rate', 0)):.2%})")

        # Add to coherent found list
        coherent_this_gen = [(aid, r) for aid, r in results if r["is_coherent"]]
        for item in coherent_this_gen:
            if item not in coherent_found:
                coherent_found.append(item)

        # Early termination if we have enough coherent agents
        if len([c for c in coherent_found if c[1].get("status") == "coherent"]) >= population_size:
            if verbose:
                print(f"\n  Sufficient coherent agents found. Stopping early.")
            break

        # Mercy-based selection
        survivors = []
        dissolved = []

        for agent_id, result in results:
            if result["is_coherent"]:
                # Coherent (including growing) - survive
                survivors.append(agent_id)
                mercy_watch.pop(agent_id, None)  # Remove from watch

            elif result.get("is_growing"):
                # Growing agents get mercy even if not fully coherent
                survivors.append(agent_id)
                mercy_watch.pop(agent_id, None)
                if verbose:
                    print(f"    Mercy: {agent_id} is growing, keeping")

            else:
                # Track struggling agents
                mercy_watch[agent_id] = mercy_watch.get(agent_id, 0) + 1

                if mercy_watch[agent_id] >= min_gens_before_dissolve:
                    # Check for deliberate issues
                    try:
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
                    except ImportError:
                        # Mercy module not available, use simple dissolution
                        dissolved.append(agent_id)
                        if verbose:
                            print(f"    Dissolving: {agent_id} (no mercy module)")
                else:
                    survivors.append(agent_id)
                    remaining = min_gens_before_dissolve - mercy_watch[agent_id]
                    if verbose:
                        print(f"    Mercy: {agent_id} struggling but has {remaining} chances left")

        # Dissolve with learning preservation
        for agent_id in dissolved:
            dissolve_agent(agent_id, reason="Failed to grow after mercy period")
            mercy_watch.pop(agent_id, None)

        # Ensure we have at least some survivors
        if not survivors and results:
            # Keep the best one even if struggling
            best_struggling = max(results, key=lambda x: x[1].get("capture_rate", x[1].get("overall_rate", 0)))
            survivors.append(best_struggling[0])
            if verbose:
                print(f"    Keeping best struggling agent: {best_struggling[0]}")

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

                # Random perturbation for exploration
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
            print(f"Best capture rate: {best_ever[1].get('capture_rate', best_ever[1].get('overall_rate', 0)):.2%}")

        # Final coherent count (excluding just "growing")
        truly_coherent = [c for c in coherent_found if c[1].get("status") == "coherent"]
        print(f"Total coherent found: {len(truly_coherent)}")
        print(f"Total growing: {len([c for c in coherent_found if c[1].get('status') == 'growing'])}")

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
    # Expire old warnings
    try:
        expire_old_warnings()
    except Exception:
        pass

    # Apply maintenance
    apply_decay()
    heal_dead_zones()

    # Test all candidates
    results = []
    for agent_id in candidates:
        result = quick_coherence_check(agent_id)
        results.append((agent_id, result))
        if verbose:
            status = result.get("status", "unknown")
            rate = result.get("capture_rate", result.get("overall_rate", 0))
            print(f"  {agent_id}: {rate:.2%} capture, "
                  f"{result.get('coverage', 0)}/18 coverage, status={status}")

    # Sort by coherence score (not just capture rate)
    results.sort(key=lambda x: x[1].get("score", 0), reverse=True)

    # Select survivors with mercy
    survivors = []
    for agent_id, result in results:
        if result["is_coherent"] or result.get("is_growing"):
            survivors.append(agent_id)

    # If no one qualifies, keep top half
    if not survivors:
        survivor_count = len(candidates) // 2
        survivors = [r[0] for r in results[:survivor_count]]

    # Dissolve non-survivors
    dissolved = [aid for aid, _ in results if aid not in survivors]
    for agent_id in dissolved:
        dissolve_agent(agent_id, reason="Did not meet coherence threshold")

    # Spawn new candidates
    new_candidates = []
    for _ in range(len(candidates) - len(survivors)):
        if survivors:
            parent = random.choice(survivors)
            child_id = spawn_from_parent(parent, generation + 1, mutation_rate)
            new_candidates.append(child_id)

    return {
        "survivors": survivors,
        "dissolved": dissolved,
        "new_candidates": new_candidates,
        "all_candidates": survivors + new_candidates,
        "results": results,
        "best": results[0] if results else None
    }
