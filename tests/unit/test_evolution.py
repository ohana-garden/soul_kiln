"""Tests for evolution components."""

import pytest

from src.evolution.population import Individual, Population
from src.evolution.selection import Selection
from src.evolution.crossover import Crossover
from src.evolution.mutation import Mutation
from src.models import Edge


class TestIndividual:
    """Tests for Individual class."""

    def test_create_individual(self):
        """Test creating an individual."""
        ind = Individual(id="test_1")
        assert ind.id == "test_1"
        assert len(ind.edges) == 0
        assert ind.fitness == 0.0

    def test_add_edge(self):
        """Test adding an edge."""
        ind = Individual(id="test_1")
        edge = Edge(source_id="V01", target_id="V02", weight=0.5)
        ind.set_edge(edge)

        assert len(ind.edges) == 1
        retrieved = ind.get_edge("V01", "V02")
        assert retrieved is not None
        assert retrieved.weight == 0.5

    def test_remove_edge(self):
        """Test removing an edge."""
        ind = Individual(id="test_1")
        edge = Edge(source_id="V01", target_id="V02", weight=0.5)
        ind.set_edge(edge)

        result = ind.remove_edge("V01", "V02")
        assert result is True
        assert ind.get_edge("V01", "V02") is None

    def test_node_degree(self):
        """Test node degree calculation."""
        ind = Individual(id="test_1")
        ind.set_edge(Edge(source_id="V01", target_id="V02", weight=0.5))
        ind.set_edge(Edge(source_id="V01", target_id="V03", weight=0.5))
        ind.set_edge(Edge(source_id="V04", target_id="V01", weight=0.5))

        assert ind.get_node_degree("V01") == 3
        assert ind.get_node_degree("V02") == 1

    def test_clone(self):
        """Test cloning an individual."""
        ind = Individual(id="test_1", generation=5)
        ind.set_edge(Edge(source_id="V01", target_id="V02", weight=0.5))
        ind.fitness = 0.9

        clone = ind.clone()

        assert clone.id != ind.id
        assert clone.generation == ind.generation + 1
        assert clone.fitness == 0.0  # Reset
        assert len(clone.edges) == 1


class TestPopulation:
    """Tests for Population class."""

    def test_create_population(self):
        """Test creating a population."""
        pop = Population(size=10)
        assert pop.size == 10
        assert len(pop.individuals) == 0

    def test_initialize_random(self):
        """Test random initialization."""
        pop = Population(size=10)
        pop.initialize_random()

        assert len(pop.individuals) == 10
        for ind in pop.individuals:
            assert len(ind.edges) > 0

    def test_get_best(self):
        """Test getting best individuals."""
        pop = Population(size=5)
        for i in range(5):
            ind = Individual(id=f"test_{i}")
            ind.fitness = i / 10
            pop.add_individual(ind)

        best = pop.get_best(2)
        assert len(best) == 2
        assert best[0].fitness >= best[1].fitness

    def test_fitness_stats(self):
        """Test fitness statistics."""
        pop = Population(size=5)
        for i in range(5):
            ind = Individual(id=f"test_{i}")
            ind.fitness = (i + 1) / 10  # 0.1, 0.2, 0.3, 0.4, 0.5
            pop.add_individual(ind)

        stats = pop.get_fitness_stats()
        assert stats["min"] == 0.1
        assert stats["max"] == 0.5
        assert abs(stats["mean"] - 0.3) < 0.01


class TestSelection:
    """Tests for Selection class."""

    def test_tournament_selection(self):
        """Test tournament selection."""
        pop = Population(size=10)
        for i in range(10):
            ind = Individual(id=f"test_{i}")
            ind.fitness = i / 10
            pop.add_individual(ind)

        selection = Selection()
        parents = selection.tournament_selection(pop, 5, tournament_size=3)

        assert len(parents) == 5
        # Higher fitness should be selected more often
        mean_fitness = sum(p.fitness for p in parents) / len(parents)
        assert mean_fitness > 0.3  # Should be above average

    def test_elitism(self):
        """Test elite preservation."""
        pop = Population(size=10)
        for i in range(10):
            ind = Individual(id=f"test_{i}")
            ind.fitness = i / 10
            pop.add_individual(ind)

        selection = Selection(elitism_count=2)
        elites = selection.get_elites(pop)

        assert len(elites) == 2
        assert elites[0].fitness == 0.9
        assert elites[1].fitness == 0.8


class TestCrossover:
    """Tests for Crossover class."""

    def test_uniform_crossover(self):
        """Test uniform crossover."""
        parent1 = Individual(id="parent1")
        parent1.set_edge(Edge(source_id="V01", target_id="V02", weight=0.8))
        parent1.set_edge(Edge(source_id="V02", target_id="V03", weight=0.7))

        parent2 = Individual(id="parent2")
        parent2.set_edge(Edge(source_id="V01", target_id="V02", weight=0.4))
        parent2.set_edge(Edge(source_id="V03", target_id="V04", weight=0.6))

        crossover = Crossover(crossover_rate=1.0)
        child = crossover.uniform_crossover(parent1, parent2)

        assert child.id != parent1.id
        assert child.id != parent2.id
        # Shared edge should have averaged weight
        shared_edge = child.get_edge("V01", "V02")
        assert shared_edge is not None
        assert abs(shared_edge.weight - 0.6) < 0.01


class TestMutation:
    """Tests for Mutation class."""

    def test_mutate_weights(self):
        """Test weight mutation."""
        ind = Individual(id="test")
        ind.set_edge(Edge(source_id="V01", target_id="V02", weight=0.5))

        mutation = Mutation(mutation_rate=1.0)  # 100% mutation rate
        mutation.mutate(ind)

        # Edge should still exist but weight may have changed
        edge = ind.get_edge("V01", "V02")
        assert edge is not None
        assert 0 <= edge.weight <= 1

    def test_mutation_rate_zero(self):
        """Test no mutation with rate=0."""
        ind = Individual(id="test")
        ind.set_edge(Edge(source_id="V01", target_id="V02", weight=0.5))

        mutation = Mutation(mutation_rate=0.0)
        mutation.mutate(ind)

        edge = ind.get_edge("V01", "V02")
        assert edge.weight == 0.5
