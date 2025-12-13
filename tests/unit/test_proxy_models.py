"""
Unit tests for the proxy agent subsystem models.

These tests verify the data models and definitions without
requiring a database connection.
"""

import pytest
from datetime import datetime


class TestNodeTypes:
    """Test the extended NodeType enum."""

    def test_all_node_types_exist(self):
        from src.models import NodeType

        # Core types
        assert NodeType.VIRTUE_ANCHOR.value == "virtue_anchor"
        assert NodeType.AGENT.value == "agent"

        # New proxy agent types
        assert NodeType.KULEANA.value == "kuleana"
        assert NodeType.SKILL.value == "skill"
        assert NodeType.BELIEF.value == "belief"
        assert NodeType.LORE_FRAGMENT.value == "lore_fragment"
        assert NodeType.VOICE_PATTERN.value == "voice_pattern"
        assert NodeType.EPISODIC_MEMORY.value == "episodic_memory"
        assert NodeType.TOOL.value == "tool"
        assert NodeType.KNOWLEDGE_DOMAIN.value == "knowledge_domain"
        assert NodeType.FACT.value == "fact"
        assert NodeType.SOURCE.value == "source"


class TestEdgeTypes:
    """Test the EdgeType enum."""

    def test_all_edge_types_exist(self):
        from src.models import EdgeType

        # Core types
        assert EdgeType.CONNECTS.value == "connects"
        assert EdgeType.AFFINITY.value == "affinity"

        # Subsystem relationship types
        assert EdgeType.VIRTUE_REQUIRES.value == "virtue_requires"
        assert EdgeType.DUTY_REQUIRES.value == "duty_requires"
        assert EdgeType.SKILL_USES.value == "skill_uses"
        assert EdgeType.BELIEF_GROUNDS.value == "belief_grounds"
        assert EdgeType.LORE_ANCHORS.value == "lore_anchors"
        assert EdgeType.VOICE_MODULATES.value == "voice_modulates"
        assert EdgeType.MEMORY_REINFORCES.value == "memory_reinforces"
        assert EdgeType.CONFLICTS_WITH.value == "conflicts_with"


class TestKuleanaModel:
    """Test the Kuleana model."""

    def test_kuleana_creation(self):
        from src.models import Kuleana

        k = Kuleana(
            id="K_TEST",
            name="Test Duty",
            description="A test duty",
            domain="test",
            priority=1,
            serves="student",
            required_virtues=["V01", "V02"],
        )

        assert k.id == "K_TEST"
        assert k.name == "Test Duty"
        assert k.priority == 1
        assert "V01" in k.required_virtues
        assert k.is_active is False
        assert k.fulfillment_count == 0

    def test_kuleana_defaults(self):
        from src.models import Kuleana

        k = Kuleana(
            id="K_MIN",
            name="Minimal",
            description="Minimal duty",
        )

        assert k.domain == ""
        assert k.authority_level == 0.5
        assert k.priority == 5
        assert k.can_delegate is False


class TestSkillModel:
    """Test the Skill model."""

    def test_skill_creation(self):
        from src.models import Skill, SkillType

        s = Skill(
            id="S_TEST",
            name="Test Skill",
            description="A test skill",
            skill_type=SkillType.HARD,
            domain="test",
            mastery_level=0.5,
            tool_id="test_tool",
        )

        assert s.id == "S_TEST"
        assert s.skill_type == SkillType.HARD
        assert s.mastery_level == 0.5
        assert s.tool_id == "test_tool"

    def test_skill_types(self):
        from src.models import SkillType

        assert SkillType.HARD.value == "hard"
        assert SkillType.SOFT.value == "soft"
        assert SkillType.DOMAIN.value == "domain"
        assert SkillType.RITUAL.value == "ritual"

    def test_skill_decay_bounds(self):
        from src.models import Skill

        s = Skill(
            id="S_DECAY",
            name="Decay Test",
            description="Test",
            decay_rate=0.5,
            mastery_floor=0.3,
        )

        assert 0 <= s.decay_rate <= 1
        assert 0 <= s.mastery_floor <= 1


class TestBeliefModel:
    """Test the Belief model."""

    def test_belief_creation(self):
        from src.models import Belief, BeliefType

        b = Belief(
            id="B_TEST",
            content="Test belief content",
            belief_type=BeliefType.EVALUATIVE,
            conviction=0.9,
            entrenchment=0.8,
        )

        assert b.id == "B_TEST"
        assert b.belief_type == BeliefType.EVALUATIVE
        assert b.conviction == 0.9
        assert b.entrenchment == 0.8

    def test_belief_types(self):
        from src.models import BeliefType

        assert BeliefType.ONTOLOGICAL.value == "ontological"
        assert BeliefType.EVALUATIVE.value == "evaluative"
        assert BeliefType.PROCEDURAL.value == "procedural"

    def test_belief_revision_threshold(self):
        from src.models import Belief

        b = Belief(
            id="B_REV",
            content="Revisable belief",
            revision_threshold=0.3,
        )

        assert b.revision_threshold == 0.3
        assert b.times_challenged == 0
        assert b.times_confirmed == 0


class TestLoreFragmentModel:
    """Test the LoreFragment model."""

    def test_lore_creation(self):
        from src.models import LoreFragment

        l = LoreFragment(
            id="L_TEST",
            content="Test lore content",
            fragment_type="origin",
            salience=0.9,
            immutable=True,
        )

        assert l.id == "L_TEST"
        assert l.fragment_type == "origin"
        assert l.salience == 0.9
        assert l.immutable is True

    def test_lore_fragment_types(self):
        from src.models import LoreFragment

        valid_types = ["origin", "lineage", "theme", "commitment", "taboo", "prophecy"]
        for ft in valid_types:
            l = LoreFragment(id=f"L_{ft}", content="test", fragment_type=ft)
            assert l.fragment_type == ft


class TestVoicePatternModel:
    """Test the VoicePattern model."""

    def test_voice_pattern_creation(self):
        from src.models import VoicePattern

        v = VoicePattern(
            id="VP_TEST",
            name="Test Pattern",
            pattern_type="tone",
            content="Warm and supportive",
            intensity=0.7,
        )

        assert v.id == "VP_TEST"
        assert v.pattern_type == "tone"
        assert v.intensity == 0.7

    def test_voice_pattern_types(self):
        valid_types = ["tone", "lexicon", "metaphor", "emotion_response", "boundary"]
        from src.models import VoicePattern

        for pt in valid_types:
            v = VoicePattern(id=f"VP_{pt}", name="Test", content="test", pattern_type=pt)
            assert v.pattern_type == pt


class TestEpisodicMemoryModel:
    """Test the EpisodicMemory model."""

    def test_memory_creation(self):
        from src.models import EpisodicMemory, MemoryType, MemoryDecayClass

        m = EpisodicMemory(
            id="M_TEST",
            content="Test memory content",
            memory_type=MemoryType.EPISODIC,
            decay_class=MemoryDecayClass.NORMAL,
            salience=0.7,
            emotional_weight=0.5,
        )

        assert m.id == "M_TEST"
        assert m.memory_type == MemoryType.EPISODIC
        assert m.decay_class == MemoryDecayClass.NORMAL
        assert m.salience == 0.7
        assert m.emotional_weight == 0.5

    def test_memory_types(self):
        from src.models import MemoryType

        assert MemoryType.EPISODIC.value == "episodic"
        assert MemoryType.SEMANTIC.value == "semantic"
        assert MemoryType.EMOTIONAL.value == "emotional"
        assert MemoryType.SACRED.value == "sacred"

    def test_decay_classes(self):
        from src.models import MemoryDecayClass

        assert MemoryDecayClass.EPHEMERAL.value == "ephemeral"
        assert MemoryDecayClass.NORMAL.value == "normal"
        assert MemoryDecayClass.PERSISTENT.value == "persistent"
        assert MemoryDecayClass.SACRED.value == "sacred"

    def test_sacred_memory(self):
        from src.models import EpisodicMemory, MemoryDecayClass

        m = EpisodicMemory(
            id="M_SACRED",
            content="Sacred memory",
            decay_class=MemoryDecayClass.SACRED,
        )

        assert m.decay_class == MemoryDecayClass.SACRED


class TestIdentityCoreModel:
    """Test the IdentityCore model."""

    def test_identity_creation(self):
        from src.models import IdentityCore

        i = IdentityCore(
            id="I_TEST",
            agent_id="agent_123",
            primary_archetype="Ambassador",
            self_narrative="I am an advocate",
        )

        assert i.id == "I_TEST"
        assert i.agent_id == "agent_123"
        assert i.primary_archetype == "Ambassador"

    def test_identity_defaults(self):
        from src.models import IdentityCore

        i = IdentityCore(
            id="I_MIN",
            agent_id="agent_456",
        )

        # Check default subsystem weights
        assert "soul_kiln" in i.subsystem_weights
        assert "lore" in i.subsystem_weights
        assert i.subsystem_weights["soul_kiln"] == 0.9
        assert i.subsystem_weights["lore"] == 0.95
        assert i.conflict_resolution_strategy == "priority"


class TestToolModel:
    """Test the Tool model."""

    def test_tool_creation(self):
        from src.models import Tool

        t = Tool(
            id="T_TEST",
            name="Test Tool",
            description="A test tool",
            mcp_server="test_mcp",
            capabilities=["search", "query"],
            data_access_layer="layer_2",
        )

        assert t.id == "T_TEST"
        assert t.mcp_server == "test_mcp"
        assert "search" in t.capabilities
        assert t.data_access_layer == "layer_2"
        assert t.is_available is True


class TestEdgeWithType:
    """Test Edge model with edge_type."""

    def test_edge_with_type(self):
        from src.models import Edge, EdgeType, EdgeDirection

        e = Edge(
            source_id="A",
            target_id="B",
            weight=0.8,
            edge_type=EdgeType.VIRTUE_REQUIRES,
            direction=EdgeDirection.FORWARD,
        )

        assert e.edge_type == EdgeType.VIRTUE_REQUIRES
        assert e.weight == 0.8
        assert e.edge_id == "A->B"

    def test_edge_default_type(self):
        from src.models import Edge, EdgeType

        e = Edge(source_id="A", target_id="B")

        assert e.edge_type == EdgeType.CONNECTS
