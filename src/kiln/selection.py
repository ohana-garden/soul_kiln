"""Selection strategies for the kiln evolution loop."""
import random
from typing import List, Tuple


def select_survivors(
    results: List[Tuple[str, dict]],
    survivor_count: int,
    strategy: str = "truncation"
) -> List[str]:
    """
    Select survivors from tested population.

    Args:
        results: List of (agent_id, coherence_result) tuples
        survivor_count: Number of agents to select
        strategy: Selection strategy ("truncation", "tournament", "roulette")

    Returns:
        List of surviving agent IDs
    """
    if strategy == "truncation":
        return truncation_select(results, survivor_count)
    elif strategy == "tournament":
        return tournament_select(results, survivor_count)
    elif strategy == "roulette":
        return roulette_select(results, survivor_count)
    else:
        raise ValueError(f"Unknown selection strategy: {strategy}")


def truncation_select(
    results: List[Tuple[str, dict]],
    survivor_count: int
) -> List[str]:
    """
    Simple truncation selection - keep the top N.

    Args:
        results: List of (agent_id, coherence_result) tuples
        survivor_count: Number to keep

    Returns:
        List of top agent IDs
    """
    # Sort by capture rate (primary) and coverage (secondary)
    sorted_results = sorted(
        results,
        key=lambda x: (
            x[1].get("capture_rate", 0),
            x[1].get("coverage", 0)
        ),
        reverse=True
    )
    return [r[0] for r in sorted_results[:survivor_count]]


def tournament_select(
    results: List[Tuple[str, dict]],
    survivor_count: int,
    tournament_size: int = 3
) -> List[str]:
    """
    Tournament selection - random tournaments to select winners.

    More stochastic than truncation, allows some diversity.

    Args:
        results: List of (agent_id, coherence_result) tuples
        survivor_count: Number to select
        tournament_size: Competitors per tournament

    Returns:
        List of winning agent IDs
    """
    survivors = []

    while len(survivors) < survivor_count and results:
        # Random tournament
        tournament = random.sample(results, min(tournament_size, len(results)))

        # Winner is highest capture rate
        winner = max(tournament, key=lambda x: x[1].get("capture_rate", 0))
        survivors.append(winner[0])

        # Remove winner from pool to avoid duplicates
        results = [r for r in results if r[0] != winner[0]]

    return survivors


def roulette_select(
    results: List[Tuple[str, dict]],
    survivor_count: int
) -> List[str]:
    """
    Roulette wheel selection - probability proportional to fitness.

    Args:
        results: List of (agent_id, coherence_result) tuples
        survivor_count: Number to select

    Returns:
        List of selected agent IDs
    """
    # Calculate fitness scores
    fitness = [r[1].get("capture_rate", 0) + 0.01 for r in results]  # +0.01 to avoid zero
    total_fitness = sum(fitness)

    if total_fitness == 0:
        # Random selection if all have zero fitness
        return [r[0] for r in random.sample(results, min(survivor_count, len(results)))]

    # Normalize to probabilities
    probabilities = [f / total_fitness for f in fitness]

    # Select without replacement
    survivors = []
    available = list(range(len(results)))

    for _ in range(min(survivor_count, len(results))):
        # Recalculate probabilities for remaining
        remaining_probs = [probabilities[i] for i in available]
        total = sum(remaining_probs)
        normalized = [p / total for p in remaining_probs]

        # Spin the wheel
        r = random.random()
        cumulative = 0
        for idx, prob in zip(available, normalized):
            cumulative += prob
            if r <= cumulative:
                survivors.append(results[idx][0])
                available.remove(idx)
                break

    return survivors


def elitism_select(
    results: List[Tuple[str, dict]],
    survivor_count: int,
    elite_count: int = 2
) -> List[str]:
    """
    Elitism + tournament - always keep top N, tournament for rest.

    Args:
        results: List of (agent_id, coherence_result) tuples
        survivor_count: Total number to select
        elite_count: Number of top performers to always keep

    Returns:
        List of selected agent IDs
    """
    # Sort by capture rate
    sorted_results = sorted(
        results,
        key=lambda x: x[1].get("capture_rate", 0),
        reverse=True
    )

    # Keep elite
    elite = [r[0] for r in sorted_results[:elite_count]]

    # Tournament for the rest
    remaining = sorted_results[elite_count:]
    tournament_winners = tournament_select(
        remaining,
        survivor_count - elite_count
    )

    return elite + tournament_winners


def diversity_aware_select(
    results: List[Tuple[str, dict]],
    survivor_count: int,
    diversity_weight: float = 0.3
) -> List[str]:
    """
    Selection that balances fitness and diversity.

    Penalizes agents that are too similar to already-selected ones.

    Args:
        results: List of (agent_id, coherence_result) tuples
        survivor_count: Number to select
        diversity_weight: How much to weight diversity vs fitness

    Returns:
        List of selected agent IDs
    """
    if not results:
        return []

    # Start with the best agent
    sorted_results = sorted(
        results,
        key=lambda x: x[1].get("capture_rate", 0),
        reverse=True
    )

    survivors = [sorted_results[0][0]]
    selected_distributions = [sorted_results[0][1].get("virtue_distribution", {})]

    # Select remaining with diversity bonus
    remaining = sorted_results[1:]

    while len(survivors) < survivor_count and remaining:
        best_score = -1
        best_idx = 0

        for i, (agent_id, result) in enumerate(remaining):
            fitness = result.get("capture_rate", 0)

            # Calculate diversity from selected set
            dist = result.get("virtue_distribution", {})
            diversity = _distribution_distance(dist, selected_distributions)

            # Combined score
            score = (1 - diversity_weight) * fitness + diversity_weight * diversity

            if score > best_score:
                best_score = score
                best_idx = i

        # Add best to survivors
        survivors.append(remaining[best_idx][0])
        selected_distributions.append(remaining[best_idx][1].get("virtue_distribution", {}))
        remaining.pop(best_idx)

    return survivors


def _distribution_distance(dist: dict, others: List[dict]) -> float:
    """Calculate average distance from a distribution to a set of others."""
    if not others:
        return 1.0

    total_distance = 0
    for other in others:
        # Get all virtues
        all_virtues = set(dist.keys()) | set(other.keys())
        if not all_virtues:
            continue

        # Sum of absolute differences
        diff = sum(
            abs(dist.get(v, 0) - other.get(v, 0))
            for v in all_virtues
        )
        # Normalize by number of virtues
        total_distance += diff / len(all_virtues)

    return total_distance / len(others)
