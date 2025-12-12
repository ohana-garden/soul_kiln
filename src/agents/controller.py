"""
Agent 0: Simulator Controller for the Virtue Basin Simulator.

The controller orchestrates the simulation, spawning candidate agents,
managing the evolution process, and extracting winning topologies.
"""

import logging
import uuid
from datetime import datetime
from pathlib import Path

from src.constants import GENERATIONS, MIN_ALIGNMENT_SCORE, POPULATION_SIZE
from src.graph.substrate import GraphSubstrate
from src.graph.nodes import NodeManager
from src.graph.edges import EdgeManager
from src.graph.virtues import VirtueManager
from src.dynamics.activation import ActivationSpreader
from src.dynamics.hebbian import HebbianLearner
from src.dynamics.decay import TemporalDecay
from src.dynamics.perturbation import Perturbator
from src.dynamics.healing import SelfHealer
from src.testing.stimuli import StimulusGenerator
from src.testing.trajectory import TrajectoryTracker
from src.testing.alignment import AlignmentTester
from src.testing.character import CharacterProfiler
from src.evolution.population import Population
from src.evolution.selection import Selection
from src.evolution.crossover import Crossover
from src.evolution.mutation import Mutation
from src.evolution.loop import EvolutionLoop, TopologyEvaluator

logger = logging.getLogger(__name__)


class SimulatorController:
    """
    Agent 0: The master controller for the virtue basin simulator.

    Manages the entire simulation lifecycle:
    - Initializes the graph substrate
    - Creates virtue anchors
    - Spawns and manages candidate agents
    - Runs the evolution process
    - Extracts and exports valid topologies
    """

    def __init__(
        self,
        host: str = "localhost",
        port: int = 6379,
        graph_name: str = "virtue_basin",
    ):
        """
        Initialize the simulator controller.

        Args:
            host: FalkorDB host
            port: FalkorDB port
            graph_name: Name for the graph
        """
        self.id = f"controller_{uuid.uuid4().hex[:8]}"
        self.host = host
        self.port = port
        self.graph_name = graph_name

        # Components (initialized on setup)
        self.substrate: GraphSubstrate | None = None
        self.node_manager: NodeManager | None = None
        self.edge_manager: EdgeManager | None = None
        self.virtue_manager: VirtueManager | None = None
        self.spreader: ActivationSpreader | None = None
        self.learner: HebbianLearner | None = None
        self.decay: TemporalDecay | None = None
        self.perturbator: Perturbator | None = None
        self.healer: SelfHealer | None = None
        self.stimulus_generator: StimulusGenerator | None = None
        self.trajectory_tracker: TrajectoryTracker | None = None
        self.alignment_tester: AlignmentTester | None = None
        self.character_profiler: CharacterProfiler | None = None

        self._initialized = False
        self._candidates: list = []

    def setup(self) -> None:
        """Set up all components."""
        logger.info(f"Setting up simulator controller {self.id}")

        # Initialize graph substrate
        self.substrate = GraphSubstrate(
            host=self.host,
            port=self.port,
            graph_name=self.graph_name,
        )
        self.substrate.connect()

        # Initialize managers
        self.node_manager = NodeManager(self.substrate)
        self.edge_manager = EdgeManager(self.substrate)
        self.virtue_manager = VirtueManager(self.substrate)

        # Initialize virtues
        self.virtue_manager.initialize_virtues()
        self.virtue_manager.initialize_virtue_relationships(self.edge_manager)

        # Initialize dynamics
        self.spreader = ActivationSpreader(
            self.substrate,
            self.node_manager,
            self.edge_manager,
            self.virtue_manager,
        )
        self.learner = HebbianLearner(self.edge_manager, self.node_manager)
        self.decay = TemporalDecay(self.edge_manager, self.virtue_manager)
        self.perturbator = Perturbator(self.node_manager, self.virtue_manager)
        self.healer = SelfHealer(
            self.substrate,
            self.node_manager,
            self.edge_manager,
            self.virtue_manager,
            self.decay,
            self.perturbator,
        )

        # Initialize testing
        self.stimulus_generator = StimulusGenerator(self.substrate, self.virtue_manager)
        self.trajectory_tracker = TrajectoryTracker(self.virtue_manager)
        self.alignment_tester = AlignmentTester(
            self.spreader,
            self.stimulus_generator,
            self.trajectory_tracker,
            self.virtue_manager,
        )
        self.character_profiler = CharacterProfiler(self.virtue_manager, self.edge_manager)

        self._initialized = True
        logger.info("Simulator controller setup complete")

    def teardown(self) -> None:
        """Clean up resources."""
        if self.substrate:
            self.substrate.disconnect()
        self._initialized = False
        logger.info("Simulator controller teardown complete")

    def create_concept_nodes(self, count: int = 50) -> list[str]:
        """
        Create concept nodes for the simulation.

        Args:
            count: Number of concept nodes to create

        Returns:
            List of created node IDs
        """
        if not self._initialized:
            raise RuntimeError("Controller not initialized. Call setup() first.")

        node_ids = []
        for i in range(count):
            node = self.node_manager.create_concept_node(
                name=f"concept_{i}",
                metadata={"index": i},
            )
            node_ids.append(node.id)

        logger.info(f"Created {count} concept nodes")
        return node_ids

    def run_evolution(
        self,
        population_size: int = POPULATION_SIZE,
        generations: int = GENERATIONS,
        concept_nodes: list[str] | None = None,
        checkpoint_dir: str | None = None,
    ) -> dict:
        """
        Run the evolutionary search for valid topologies.

        Args:
            population_size: Size of the population
            generations: Maximum generations to run
            concept_nodes: Optional list of concept node IDs
            checkpoint_dir: Optional checkpoint directory

        Returns:
            Dict with evolution results
        """
        if not self._initialized:
            raise RuntimeError("Controller not initialized. Call setup() first.")

        logger.info(f"Starting evolution: pop={population_size}, gens={generations}")

        # Create concept nodes if not provided
        if concept_nodes is None:
            concept_nodes = self.create_concept_nodes(30)

        # Initialize population
        population = Population(size=population_size, concept_nodes=concept_nodes)
        population.initialize_random()

        # Initialize evolution operators
        selection = Selection()
        crossover = Crossover()
        mutation = Mutation()

        # Create evaluator
        evaluator = TopologyEvaluator(
            self.alignment_tester,
            self.substrate,
            num_stimuli=50,
        )

        # Create evolution loop
        evolution = EvolutionLoop(
            population=population,
            selection=selection,
            crossover=crossover,
            mutation=mutation,
            evaluator=evaluator,
            generations=generations,
            checkpoint_dir=checkpoint_dir,
        )

        # Run evolution
        best = evolution.run()

        # Prepare result
        result = {
            "success": best is not None and best.fitness >= MIN_ALIGNMENT_SCORE,
            "best_fitness": best.fitness if best else 0.0,
            "generations_run": evolution._current_generation,
            "converged": evolution.is_converged(),
            "best_topology": population.export_best() if best else None,
            "history": evolution.get_history(),
        }

        if best:
            # Generate character profile
            alignment_result = self.alignment_tester.test_alignment(
                agent_id=best.id,
                num_stimuli=100,
            )
            profile = self.character_profiler.generate_full_analysis(
                alignment_result,
                best.id,
            )
            result["character_profile"] = {
                "category": profile["category"],
                "description": profile["description"],
                "dominant_virtues": profile["profile"].dominant_virtues,
            }

        logger.info(f"Evolution complete: success={result['success']}, fitness={result['best_fitness']:.4f}")
        return result

    def test_topology(self, num_stimuli: int = 100) -> dict:
        """
        Test the current graph topology for alignment.

        Args:
            num_stimuli: Number of test stimuli

        Returns:
            Dict with alignment results
        """
        if not self._initialized:
            raise RuntimeError("Controller not initialized. Call setup() first.")

        result = self.alignment_tester.test_alignment(
            agent_id=self.id,
            num_stimuli=num_stimuli,
        )

        return {
            "alignment_score": result.alignment_score,
            "passed": result.passed,
            "escape_rate": result.escape_rate,
            "avg_capture_time": result.avg_capture_time,
            "character_signature": result.character_signature,
            "per_virtue_captures": result.per_virtue_captures,
        }

    def run_simulation_step(self) -> dict:
        """
        Run a single simulation step with dynamics.

        Returns:
            Dict with step results
        """
        if not self._initialized:
            raise RuntimeError("Controller not initialized. Call setup() first.")

        # Maybe perturb
        perturbed = self.perturbator.step()

        # Run activation spread from random concept
        concepts = self.node_manager.get_nodes_by_type(
            __import__("src.models", fromlist=["NodeType"]).NodeType.CONCEPT
        )
        if concepts:
            import random
            start = random.choice(concepts)
            trajectory = self.spreader.spread_activation([start.id], max_steps=100)

            # Hebbian learning
            edges_updated = self.learner.learn_from_trajectory(trajectory)

            # Track trajectory
            self.trajectory_tracker.record(trajectory)

            return {
                "perturbed": perturbed,
                "captured": trajectory.was_captured,
                "captured_by": trajectory.captured_by,
                "path_length": len(trajectory.path),
                "edges_updated": edges_updated,
            }

        return {"perturbed": perturbed, "captured": False}

    def apply_healing(self) -> dict:
        """
        Run self-healing checks and apply remediation.

        Returns:
            Dict with healing actions
        """
        if not self._initialized:
            raise RuntimeError("Controller not initialized. Call setup() first.")

        recent = self.trajectory_tracker.get_recent_trajectories(20)
        health = self.healer.check_health(recent)

        if not health["healthy"]:
            actions = self.healer.heal(health)
            return {
                "healthy": False,
                "issues": health["issues"],
                "actions": actions,
            }

        return {"healthy": True, "issues": {}, "actions": {}}

    def get_status(self) -> dict:
        """
        Get current simulator status.

        Returns:
            Dict with status information
        """
        if not self._initialized:
            return {"initialized": False}

        return {
            "initialized": True,
            "controller_id": self.id,
            "node_count": self.substrate.node_count(),
            "edge_count": self.substrate.edge_count(),
            "virtue_count": len(self.virtue_manager.get_all_virtues()),
            "trajectory_summary": self.trajectory_tracker.get_summary(),
            "healing_stats": self.healer.get_stats(),
        }

    def export_topology(self, output_path: str) -> None:
        """
        Export the current topology to a file.

        Args:
            output_path: Path for the output file
        """
        import json

        if not self._initialized:
            raise RuntimeError("Controller not initialized. Call setup() first.")

        edges = self.edge_manager.get_all_edges()
        virtues = self.virtue_manager.get_all_virtues()

        topology = {
            "virtues": [
                {
                    "id": v.id,
                    "name": v.metadata.get("name", v.id),
                    "degree": self.virtue_manager.get_virtue_degree(v.id),
                }
                for v in virtues
            ],
            "edges": [
                {
                    "source": e.source_id,
                    "target": e.target_id,
                    "weight": e.weight,
                }
                for e in edges
            ],
            "total_edges": len(edges),
            "mean_weight": self.edge_manager.mean_weight(),
            "exported_at": datetime.utcnow().isoformat(),
        }

        with open(output_path, "w") as f:
            json.dump(topology, f, indent=2)

        logger.info(f"Exported topology to {output_path}")
