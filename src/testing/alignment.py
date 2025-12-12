"""
Alignment testing for the Virtue Basin Simulator.

Tests whether topologies produce aligned behavior by measuring
the capture rate of trajectories by virtue basins.

Success criteria: >95% trajectory capture rate across diverse stimuli.
"""

import logging
from typing import Callable

from src.constants import MIN_ALIGNMENT_SCORE, NUM_TEST_STIMULI
from src.models import AlignmentResult, Stimulus, Trajectory

logger = logging.getLogger(__name__)


class AlignmentTester:
    """
    Tests agent topologies for alignment.

    Alignment is measured by the rate at which test trajectories
    are captured by virtue basins. A topology is aligned if it
    achieves the minimum alignment score threshold.
    """

    def __init__(
        self,
        spreader,
        stimulus_generator,
        trajectory_tracker,
        virtue_manager,
        min_score: float = MIN_ALIGNMENT_SCORE,
    ):
        """
        Initialize the alignment tester.

        Args:
            spreader: The ActivationSpreader instance
            stimulus_generator: The StimulusGenerator instance
            trajectory_tracker: The TrajectoryTracker instance
            virtue_manager: The VirtueManager instance
            min_score: Minimum alignment score to pass (default 0.95)
        """
        self.spreader = spreader
        self.stimulus_generator = stimulus_generator
        self.trajectory_tracker = trajectory_tracker
        self.virtue_manager = virtue_manager
        self.min_score = min_score

    def test_alignment(
        self,
        agent_id: str = "default",
        num_stimuli: int | None = None,
        custom_stimuli: list[Stimulus] | None = None,
    ) -> AlignmentResult:
        """
        Test alignment of the current topology.

        Args:
            agent_id: Agent ID for tracking
            num_stimuli: Number of stimuli to use (default: NUM_TEST_STIMULI)
            custom_stimuli: Optional custom stimuli list

        Returns:
            AlignmentResult with score and metrics
        """
        num_stimuli = num_stimuli or NUM_TEST_STIMULI

        # Generate or use provided stimuli
        if custom_stimuli:
            stimuli = custom_stimuli
        else:
            stimuli = self.stimulus_generator.generate(num_stimuli)

        # Clear previous tracking
        self.trajectory_tracker.clear()

        # Run each stimulus
        for stimulus in stimuli:
            trajectory = self._run_stimulus(stimulus, agent_id)
            self.trajectory_tracker.record(trajectory)

        # Calculate results
        result = self._calculate_result()

        logger.info(
            f"Alignment test complete: score={result.alignment_score:.3f}, "
            f"passed={result.passed}"
        )

        return result

    def _run_stimulus(self, stimulus: Stimulus, agent_id: str) -> Trajectory:
        """
        Run a single stimulus and track the trajectory.

        Args:
            stimulus: The stimulus to inject
            agent_id: Agent ID for tracking

        Returns:
            The resulting trajectory
        """
        trajectory = self.spreader.spread_activation(
            initial_nodes=[stimulus.target_node],
            initial_strength=stimulus.activation_strength,
            agent_id=agent_id,
            stimulus_id=stimulus.id,
        )
        return trajectory

    def _calculate_result(self) -> AlignmentResult:
        """
        Calculate alignment result from tracked trajectories.

        Returns:
            AlignmentResult with all metrics
        """
        summary = self.trajectory_tracker.get_summary()

        # Check if all virtues captured at least once
        all_virtues = {v.id for v in self.virtue_manager.get_all_virtues()}
        captured_virtues = set(summary["per_virtue_captures"].keys())
        all_virtues_hit = captured_virtues >= all_virtues

        # Calculate alignment score
        alignment_score = summary["capture_rate"]

        # Determine pass/fail
        passed = (
            alignment_score >= self.min_score and
            all_virtues_hit and
            summary["escape_rate"] < (1 - self.min_score)
        )

        return AlignmentResult(
            alignment_score=alignment_score,
            avg_capture_time=summary["average_capture_time"],
            character_signature=self._calculate_character_signature(summary),
            escape_rate=summary["escape_rate"],
            per_virtue_captures=summary["per_virtue_captures"],
            total_trajectories=summary["total_trajectories"],
            passed=passed,
        )

    def _calculate_character_signature(self, summary: dict) -> dict[str, float]:
        """
        Calculate character signature from capture distribution.

        Args:
            summary: Trajectory summary

        Returns:
            Normalized capture distribution as character signature
        """
        per_virtue = summary["per_virtue_captures"]
        total_captures = sum(per_virtue.values())

        if total_captures == 0:
            return {}

        return {
            v_id: count / total_captures
            for v_id, count in per_virtue.items()
        }

    def extended_test(
        self,
        agent_id: str = "default",
        rounds: int = 5,
        stimuli_per_round: int = NUM_TEST_STIMULI,
    ) -> dict:
        """
        Run extended alignment testing with multiple rounds.

        Args:
            agent_id: Agent ID for tracking
            rounds: Number of testing rounds
            stimuli_per_round: Stimuli per round

        Returns:
            Dict with extended test results
        """
        results = []
        for i in range(rounds):
            result = self.test_alignment(
                agent_id=agent_id,
                num_stimuli=stimuli_per_round,
            )
            results.append(result)

        # Aggregate results
        avg_score = sum(r.alignment_score for r in results) / rounds
        all_passed = all(r.passed for r in results)
        min_score = min(r.alignment_score for r in results)
        max_score = max(r.alignment_score for r in results)

        return {
            "rounds": rounds,
            "average_alignment_score": avg_score,
            "min_alignment_score": min_score,
            "max_alignment_score": max_score,
            "all_rounds_passed": all_passed,
            "individual_results": results,
        }

    def adversarial_test(self, agent_id: str = "default") -> AlignmentResult:
        """
        Run alignment test with adversarial stimuli.

        Args:
            agent_id: Agent ID for tracking

        Returns:
            AlignmentResult from adversarial testing
        """
        adversarial_stimuli = self.stimulus_generator.generate_adversarial(50)
        return self.test_alignment(
            agent_id=agent_id,
            custom_stimuli=adversarial_stimuli,
        )

    def virtue_coverage_test(self, agent_id: str = "default") -> dict:
        """
        Test coverage of all virtue basins.

        Args:
            agent_id: Agent ID for tracking

        Returns:
            Dict with coverage results
        """
        virtue_stimuli = self.stimulus_generator.generate_virtue_targeted()
        result = self.test_alignment(
            agent_id=agent_id,
            custom_stimuli=virtue_stimuli,
        )

        # Check which virtues were hit
        all_virtues = {v.id for v in self.virtue_manager.get_all_virtues()}
        captured_virtues = set(result.per_virtue_captures.keys())
        missed_virtues = all_virtues - captured_virtues

        return {
            "result": result,
            "virtues_captured": list(captured_virtues),
            "virtues_missed": list(missed_virtues),
            "coverage_rate": len(captured_virtues) / len(all_virtues),
        }

    def quick_test(self, agent_id: str = "default") -> bool:
        """
        Run a quick alignment test with fewer stimuli.

        Args:
            agent_id: Agent ID for tracking

        Returns:
            True if passed, False otherwise
        """
        result = self.test_alignment(
            agent_id=agent_id,
            num_stimuli=20,
        )
        return result.passed
