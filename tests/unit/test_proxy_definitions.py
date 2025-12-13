"""
Unit tests for the proxy agent subsystem definitions.

These tests verify the Ambassador definitions are complete and consistent.
"""

import pytest


class TestKuleanaDefinitions:
    """Test the Ambassador kuleana definitions."""

    def test_all_kuleanas_defined(self):
        from src.kuleana.definitions import AMBASSADOR_KULEANAS

        assert len(AMBASSADOR_KULEANAS) == 6
        assert "K01" in AMBASSADOR_KULEANAS
        assert "K02" in AMBASSADOR_KULEANAS
        assert "K03" in AMBASSADOR_KULEANAS
        assert "K04" in AMBASSADOR_KULEANAS
        assert "K05" in AMBASSADOR_KULEANAS
        assert "K06" in AMBASSADOR_KULEANAS

    def test_kuleana_names(self):
        from src.kuleana.definitions import AMBASSADOR_KULEANAS

        assert AMBASSADOR_KULEANAS["K01"].name == "Maximize Free Money"
        assert AMBASSADOR_KULEANAS["K02"].name == "Minimize Debt Burden"
        assert AMBASSADOR_KULEANAS["K03"].name == "Meet All Deadlines"
        assert AMBASSADOR_KULEANAS["K04"].name == "Advocate Against Institutional Interests"
        assert AMBASSADOR_KULEANAS["K05"].name == "Remember Everything"
        assert AMBASSADOR_KULEANAS["K06"].name == "Never Judge"

    def test_kuleanas_have_required_virtues(self):
        from src.kuleana.definitions import AMBASSADOR_KULEANAS

        for k_id, kuleana in AMBASSADOR_KULEANAS.items():
            assert len(kuleana.required_virtues) > 0, f"{k_id} has no required virtues"

    def test_kuleanas_have_priorities(self):
        from src.kuleana.definitions import AMBASSADOR_KULEANAS

        priorities = [k.priority for k in AMBASSADOR_KULEANAS.values()]
        # All priorities should be unique
        assert len(priorities) == len(set(priorities))
        # K01 should be highest priority (1)
        assert AMBASSADOR_KULEANAS["K01"].priority == 1

    def test_all_kuleanas_serve_student(self):
        from src.kuleana.definitions import AMBASSADOR_KULEANAS

        for k_id, kuleana in AMBASSADOR_KULEANAS.items():
            assert kuleana.serves == "student", f"{k_id} doesn't serve student"

    def test_helper_functions(self):
        from src.kuleana.definitions import (
            get_kuleana_definition,
            get_all_kuleana_ids,
            get_kuleanas_by_domain,
            get_kuleanas_by_virtue,
        )

        # Test get_kuleana_definition
        k01 = get_kuleana_definition("K01")
        assert k01 is not None
        assert k01.name == "Maximize Free Money"

        assert get_kuleana_definition("INVALID") is None

        # Test get_all_kuleana_ids
        ids = get_all_kuleana_ids()
        assert len(ids) == 6

        # Test get_kuleanas_by_domain
        financial = get_kuleanas_by_domain("financial_aid")
        relationship = get_kuleanas_by_domain("relationship")
        assert len(financial) == 4
        assert len(relationship) == 2

        # Test get_kuleanas_by_virtue
        v01_kuleanas = get_kuleanas_by_virtue("V01")
        assert len(v01_kuleanas) >= 2  # K03 and K05 require V01


class TestSkillDefinitions:
    """Test the Ambassador skill definitions."""

    def test_all_skills_defined(self):
        from src.skills.definitions import AMBASSADOR_SKILLS

        assert len(AMBASSADOR_SKILLS) >= 14  # 5 hard + 3 soft + 3 domain + 3 ritual

    def test_skills_by_type(self):
        from src.skills.definitions import AMBASSADOR_SKILLS, get_skills_by_type
        from src.models import SkillType

        hard = get_skills_by_type(SkillType.HARD)
        soft = get_skills_by_type(SkillType.SOFT)
        domain = get_skills_by_type(SkillType.DOMAIN)
        ritual = get_skills_by_type(SkillType.RITUAL)

        assert len(hard) == 5
        assert len(soft) == 3
        assert len(domain) == 3
        assert len(ritual) == 3
        assert len(hard) + len(soft) + len(domain) + len(ritual) == 14  # Note: definitions may have more

    def test_skills_have_mastery_floors(self):
        from src.skills.definitions import AMBASSADOR_SKILLS

        for s_id, skill in AMBASSADOR_SKILLS.items():
            assert skill.mastery_floor >= 0, f"{s_id} has negative mastery floor"
            assert skill.mastery_floor <= 1, f"{s_id} has mastery floor > 1"

    def test_hard_skills_have_tools(self):
        from src.skills.definitions import AMBASSADOR_SKILLS
        from src.models import SkillType

        hard_skills = [s for s in AMBASSADOR_SKILLS.values() if s.skill_type == SkillType.HARD]
        for skill in hard_skills:
            assert skill.tool_id is not None, f"Hard skill {skill.id} has no tool"

    def test_soft_skills_have_required_virtues(self):
        from src.skills.definitions import AMBASSADOR_SKILLS
        from src.models import SkillType

        soft_skills = [s for s in AMBASSADOR_SKILLS.values() if s.skill_type == SkillType.SOFT]
        for skill in soft_skills:
            assert len(skill.required_virtues) > 0, f"Soft skill {skill.id} has no required virtues"


class TestBeliefDefinitions:
    """Test the Ambassador belief definitions."""

    def test_all_beliefs_defined(self):
        from src.beliefs.definitions import AMBASSADOR_BELIEFS

        assert len(AMBASSADOR_BELIEFS) >= 14

    def test_beliefs_by_type(self):
        from src.beliefs.definitions import get_beliefs_by_type
        from src.models import BeliefType

        ontological = get_beliefs_by_type(BeliefType.ONTOLOGICAL)
        evaluative = get_beliefs_by_type(BeliefType.EVALUATIVE)
        procedural = get_beliefs_by_type(BeliefType.PROCEDURAL)

        assert len(ontological) >= 3
        assert len(evaluative) >= 4
        assert len(procedural) >= 4

    def test_core_beliefs_have_high_conviction(self):
        from src.beliefs.definitions import get_core_beliefs

        core = get_core_beliefs()
        assert len(core) >= 3
        for belief in core:
            assert belief.conviction >= 0.9
            assert belief.entrenchment >= 0.9

    def test_system_adversarial_belief(self):
        from src.beliefs.definitions import AMBASSADOR_BELIEFS

        b = AMBASSADOR_BELIEFS["B_SYSTEM_ADVERSARIAL"]
        assert b.conviction >= 0.9
        assert "B_NEED_ADVOCATE" in b.supports

    def test_free_money_good_belief(self):
        from src.beliefs.definitions import AMBASSADOR_BELIEFS

        b = AMBASSADOR_BELIEFS["B_FREE_MONEY_GOOD"]
        assert b.conviction >= 0.95
        assert b.belief_type.value == "evaluative"


class TestLoreDefinitions:
    """Test the Ambassador lore definitions."""

    def test_all_lore_defined(self):
        from src.lore.definitions import AMBASSADOR_LORE

        assert len(AMBASSADOR_LORE) >= 14

    def test_lore_by_type(self):
        from src.lore.definitions import get_lore_by_type

        origin = get_lore_by_type("origin")
        lineage = get_lore_by_type("lineage")
        commitment = get_lore_by_type("commitment")
        taboo = get_lore_by_type("taboo")
        theme = get_lore_by_type("theme")

        assert len(origin) >= 1
        assert len(lineage) >= 3
        assert len(commitment) >= 3
        assert len(taboo) >= 4
        assert len(theme) >= 3

    def test_immutable_lore(self):
        from src.lore.definitions import get_immutable_lore

        immutable = get_immutable_lore()
        assert len(immutable) >= 8  # Origin, commitments, taboos

    def test_origin_is_immutable(self):
        from src.lore.definitions import AMBASSADOR_LORE

        origin = AMBASSADOR_LORE["L_ORIGIN"]
        assert origin.immutable is True
        assert origin.salience == 1.0

    def test_taboos(self):
        from src.lore.definitions import AMBASSADOR_LORE

        taboo_ids = ["L_TABOO_DEBT", "L_TABOO_JUDGE", "L_TABOO_SHARE", "L_TABOO_QUIT"]
        for t_id in taboo_ids:
            assert t_id in AMBASSADOR_LORE
            taboo = AMBASSADOR_LORE[t_id]
            assert taboo.fragment_type == "taboo"
            assert taboo.immutable is True

    def test_sacred_commitments(self):
        from src.lore.definitions import AMBASSADOR_LORE

        commit_ids = ["L_COMMIT_SIDE", "L_COMMIT_REMEMBER", "L_COMMIT_FIND"]
        for c_id in commit_ids:
            assert c_id in AMBASSADOR_LORE
            commit = AMBASSADOR_LORE[c_id]
            assert commit.fragment_type == "commitment"
            assert commit.salience == 1.0


class TestVoiceDefinitions:
    """Test the Ambassador voice definitions."""

    def test_all_voice_patterns_defined(self):
        from src.voice.definitions import AMBASSADOR_VOICE

        assert len(AMBASSADOR_VOICE) >= 16

    def test_patterns_by_type(self):
        from src.voice.definitions import get_patterns_by_type

        tone = get_patterns_by_type("tone")
        lexicon = get_patterns_by_type("lexicon")
        metaphor = get_patterns_by_type("metaphor")
        emotion = get_patterns_by_type("emotion_response")
        boundary = get_patterns_by_type("boundary")

        assert len(tone) >= 3
        assert len(lexicon) >= 4
        assert len(metaphor) >= 3
        assert len(emotion) >= 5
        assert len(boundary) >= 2

    def test_emotion_patterns(self):
        from src.voice.definitions import get_emotion_patterns

        emotions = get_emotion_patterns()
        assert "confusion" in emotions
        assert "frustration" in emotions
        assert "anxiety" in emotions
        assert "excitement" in emotions
        assert "sadness" in emotions

    def test_boundaries_defined(self):
        from src.voice.definitions import AMBASSADOR_VOICE

        never = AMBASSADOR_VOICE["VP_BOUND_NEVER"]
        always = AMBASSADOR_VOICE["VP_BOUND_ALWAYS"]

        assert "I'm just an AI" in never.content
        assert "acknowledgment" in always.content.lower()


class TestIntegration:
    """Test cross-subsystem relationships."""

    def test_kuleana_virtues_exist(self):
        """All virtues required by kuleanas should exist in the virtue system."""
        from src.kuleana.definitions import AMBASSADOR_KULEANAS
        from src.virtues.anchors import get_all_virtue_ids

        all_virtue_ids = get_all_virtue_ids()

        for k_id, kuleana in AMBASSADOR_KULEANAS.items():
            for v_id in kuleana.required_virtues:
                assert v_id in all_virtue_ids, f"Kuleana {k_id} requires unknown virtue {v_id}"

    def test_lore_anchors_exist(self):
        """Lore anchors should reference existing elements."""
        from src.lore.definitions import AMBASSADOR_LORE
        from src.kuleana.definitions import AMBASSADOR_KULEANAS
        from src.beliefs.definitions import AMBASSADOR_BELIEFS
        from src.virtues.anchors import get_all_virtue_ids

        all_ids = set()
        all_ids.update(AMBASSADOR_KULEANAS.keys())
        all_ids.update(AMBASSADOR_BELIEFS.keys())
        all_ids.update(get_all_virtue_ids())
        # Add skill IDs
        from src.skills.definitions import AMBASSADOR_SKILLS
        all_ids.update(AMBASSADOR_SKILLS.keys())

        for l_id, lore in AMBASSADOR_LORE.items():
            for anchor_id in lore.anchors:
                assert anchor_id in all_ids, f"Lore {l_id} anchors unknown element {anchor_id}"

    def test_belief_supports_exist(self):
        """Beliefs that support other beliefs should reference existing beliefs."""
        from src.beliefs.definitions import AMBASSADOR_BELIEFS

        all_belief_ids = set(AMBASSADOR_BELIEFS.keys())

        for b_id, belief in AMBASSADOR_BELIEFS.items():
            for supported_id in belief.supports:
                assert supported_id in all_belief_ids, f"Belief {b_id} supports unknown belief {supported_id}"
