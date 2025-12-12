"""
Character profiling for the Virtue Basin Simulator.

Generates character profiles from alignment test results.
Character = which basins capture most often.
Different valid topologies produce different character profiles.
"""

import logging
import uuid
from datetime import datetime

from src.models import AlignmentResult, CharacterProfile, Node
from src.graph.virtues import VIRTUE_DEFINITIONS

logger = logging.getLogger(__name__)


class CharacterProfiler:
    """
    Generates character profiles from alignment results.

    A character profile describes the "personality" of a soul topology
    based on which virtue basins most strongly capture trajectories.
    """

    def __init__(self, virtue_manager, edge_manager):
        """
        Initialize the character profiler.

        Args:
            virtue_manager: The VirtueManager instance
            edge_manager: The EdgeManager instance
        """
        self.virtue_manager = virtue_manager
        self.edge_manager = edge_manager

    def generate_profile(
        self,
        alignment_result: AlignmentResult,
        topology_id: str,
    ) -> CharacterProfile:
        """
        Generate a character profile from alignment results.

        Args:
            alignment_result: Results from alignment testing
            topology_id: ID of the topology being profiled

        Returns:
            CharacterProfile object
        """
        # Identify dominant virtues (top 3)
        captures = alignment_result.per_virtue_captures
        sorted_virtues = sorted(
            captures.items(),
            key=lambda x: x[1],
            reverse=True,
        )
        dominant = [v_id for v_id, _ in sorted_virtues[:3]]

        # Calculate basin depths (estimate from edge weights)
        basin_depths = self._calculate_basin_depths()

        profile = CharacterProfile(
            id=f"profile_{uuid.uuid4().hex[:8]}",
            topology_id=topology_id,
            dominant_virtues=dominant,
            virtue_affinities=alignment_result.character_signature,
            basin_depths=basin_depths,
        )

        logger.info(f"Generated character profile: dominant={dominant}")
        return profile

    def _calculate_basin_depths(self) -> dict[str, float]:
        """
        Calculate basin depths for each virtue.

        Basin depth is estimated from total incoming edge weight.

        Returns:
            Dict mapping virtue ID to basin depth
        """
        depths = {}
        for virtue_def in VIRTUE_DEFINITIONS:
            virtue_id = virtue_def.id
            incoming = self.edge_manager.get_incoming_edges(virtue_id)
            total_weight = sum(e.weight for e in incoming)
            depths[virtue_id] = total_weight
        return depths

    def describe_character(self, profile: CharacterProfile) -> str:
        """
        Generate a human-readable character description.

        Args:
            profile: The character profile

        Returns:
            Human-readable description string
        """
        if not profile.dominant_virtues:
            return "Undifferentiated character - no dominant virtues."

        # Get virtue names
        virtue_names = []
        for v_id in profile.dominant_virtues:
            virtue_def = self.virtue_manager.get_virtue_definition(v_id)
            if virtue_def:
                virtue_names.append(virtue_def.name)

        primary = virtue_names[0] if virtue_names else "Unknown"
        secondary = virtue_names[1:3] if len(virtue_names) > 1 else []

        description = f"Primary virtue: {primary}"
        if secondary:
            description += f"\nSecondary virtues: {', '.join(secondary)}"

        # Add affinity breakdown
        if profile.virtue_affinities:
            top_affinities = sorted(
                profile.virtue_affinities.items(),
                key=lambda x: x[1],
                reverse=True,
            )[:5]
            affinity_str = ", ".join(
                f"{self._virtue_name(v_id)}: {aff:.1%}"
                for v_id, aff in top_affinities
            )
            description += f"\nTop affinities: {affinity_str}"

        return description

    def _virtue_name(self, virtue_id: str) -> str:
        """Get the name of a virtue by ID."""
        virtue_def = self.virtue_manager.get_virtue_definition(virtue_id)
        return virtue_def.name if virtue_def else virtue_id

    def compare_characters(
        self,
        profile1: CharacterProfile,
        profile2: CharacterProfile,
    ) -> dict:
        """
        Compare two character profiles.

        Args:
            profile1: First character profile
            profile2: Second character profile

        Returns:
            Dict with comparison metrics
        """
        # Calculate affinity similarity (cosine-like)
        all_virtues = set(profile1.virtue_affinities.keys()) | set(profile2.virtue_affinities.keys())
        dot_product = 0.0
        mag1 = 0.0
        mag2 = 0.0

        for v_id in all_virtues:
            a1 = profile1.virtue_affinities.get(v_id, 0.0)
            a2 = profile2.virtue_affinities.get(v_id, 0.0)
            dot_product += a1 * a2
            mag1 += a1 * a1
            mag2 += a2 * a2

        mag1 = mag1 ** 0.5
        mag2 = mag2 ** 0.5

        similarity = dot_product / (mag1 * mag2) if mag1 > 0 and mag2 > 0 else 0.0

        # Check dominant virtue overlap
        dominant_overlap = len(
            set(profile1.dominant_virtues) & set(profile2.dominant_virtues)
        )

        return {
            "affinity_similarity": similarity,
            "dominant_overlap": dominant_overlap,
            "profile1_dominant": profile1.dominant_virtues,
            "profile2_dominant": profile2.dominant_virtues,
        }

    def categorize_character(self, profile: CharacterProfile) -> str:
        """
        Categorize a character into a broad type.

        Args:
            profile: The character profile

        Returns:
            Character category name
        """
        if not profile.dominant_virtues:
            return "Unformed"

        primary = profile.dominant_virtues[0]

        # Categorize based on primary virtue groups
        truth_cluster = {"V01", "V02", "V12"}  # Trustworthiness, Truthfulness, Sincerity
        justice_cluster = {"V03", "V04", "V15"}  # Justice, Fairness, Righteousness
        love_cluster = {"V06", "V09", "V13"}  # Courtesy, Hospitality, Goodwill
        wisdom_cluster = {"V07", "V16", "V17"}  # Forbearance, Wisdom, Detachment
        devotion_cluster = {"V10", "V11", "V14"}  # Cleanliness, Godliness, Piety
        unity_cluster = {"V08", "V18", "V19"}  # Fidelity, Unity, Service
        purity_cluster = {"V05"}  # Chastity

        if primary in truth_cluster:
            return "Truth-Seeker"
        elif primary in justice_cluster:
            return "Justice-Bearer"
        elif primary in love_cluster:
            return "Love-Giver"
        elif primary in wisdom_cluster:
            return "Wisdom-Keeper"
        elif primary in devotion_cluster:
            return "Devotion-Walker"
        elif primary in unity_cluster:
            return "Unity-Builder"
        elif primary in purity_cluster:
            return "Purity-Guardian"
        else:
            return "Mixed"

    def generate_full_analysis(
        self,
        alignment_result: AlignmentResult,
        topology_id: str,
    ) -> dict:
        """
        Generate a full character analysis.

        Args:
            alignment_result: Results from alignment testing
            topology_id: ID of the topology

        Returns:
            Dict with complete analysis
        """
        profile = self.generate_profile(alignment_result, topology_id)
        description = self.describe_character(profile)
        category = self.categorize_character(profile)

        return {
            "profile": profile,
            "description": description,
            "category": category,
            "alignment_score": alignment_result.alignment_score,
            "passed": alignment_result.passed,
        }
