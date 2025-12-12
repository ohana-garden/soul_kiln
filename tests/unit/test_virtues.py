"""Tests for virtue definitions and management."""

import pytest

from src.graph.virtues import VIRTUE_DEFINITIONS, VirtueManager
from src.constants import NUM_VIRTUES, TARGET_CONNECTIVITY


class TestVirtueDefinitions:
    """Tests for virtue anchor definitions."""

    def test_correct_number_of_virtues(self):
        """Test that we have exactly 19 virtues."""
        assert len(VIRTUE_DEFINITIONS) == NUM_VIRTUES
        assert len(VIRTUE_DEFINITIONS) == 19

    def test_virtue_ids_sequential(self):
        """Test virtue IDs are V01-V19."""
        expected_ids = [f"V{i:02d}" for i in range(1, 20)]
        actual_ids = [v.id for v in VIRTUE_DEFINITIONS]
        assert actual_ids == expected_ids

    def test_virtue_names_unique(self):
        """Test all virtue names are unique."""
        names = [v.name for v in VIRTUE_DEFINITIONS]
        assert len(names) == len(set(names))

    def test_virtue_relationships_valid(self):
        """Test all relationship references are valid virtue IDs."""
        valid_ids = {v.id for v in VIRTUE_DEFINITIONS}
        for virtue in VIRTUE_DEFINITIONS:
            for rel_id in virtue.key_relationships:
                assert rel_id in valid_ids, f"Invalid relationship {rel_id} in {virtue.id}"

    def test_mathematical_impossibility(self):
        """Test that 19 nodes with 9 edges each is impossible."""
        # A k-regular graph requires n*k to be even
        # 19 * 9 = 171, which is odd
        total_degree = NUM_VIRTUES * TARGET_CONNECTIVITY
        edges_required = total_degree / 2
        assert edges_required != int(edges_required), "19x9 should be mathematically impossible"

    def test_specific_virtues_present(self):
        """Test specific virtues are present."""
        virtue_names = {v.name for v in VIRTUE_DEFINITIONS}
        expected = {
            "Trustworthiness",
            "Truthfulness",
            "Justice",
            "Fairness",
            "Wisdom",
            "Unity",
            "Service",
        }
        assert expected.issubset(virtue_names)

    def test_trustworthiness_is_first(self):
        """Test Trustworthiness is V01 (goodliest vesture)."""
        v01 = VIRTUE_DEFINITIONS[0]
        assert v01.id == "V01"
        assert v01.name == "Trustworthiness"
        assert "goodliest vesture" in v01.description.lower()


class TestVirtueRelationships:
    """Tests for virtue relationship structure."""

    def test_relationships_not_self_referential(self):
        """Test virtues don't reference themselves."""
        for virtue in VIRTUE_DEFINITIONS:
            assert virtue.id not in virtue.key_relationships

    def test_relationships_have_three_each(self):
        """Test each virtue has exactly 3 key relationships."""
        for virtue in VIRTUE_DEFINITIONS:
            assert len(virtue.key_relationships) == 3, f"{virtue.id} has {len(virtue.key_relationships)} relationships"

    def test_relationship_symmetry(self):
        """Test some key relationships are symmetric."""
        # Build relationship map
        rel_map = {v.id: set(v.key_relationships) for v in VIRTUE_DEFINITIONS}

        # Check some expected symmetric pairs
        assert "V02" in rel_map["V01"]  # Trustworthiness <-> Truthfulness
        assert "V01" in rel_map["V02"]
        assert "V04" in rel_map["V03"]  # Justice <-> Fairness
        assert "V03" in rel_map["V04"]
