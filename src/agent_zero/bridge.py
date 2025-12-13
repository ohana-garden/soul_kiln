"""
Soul Kiln Bridge for Agent Zero.

This module provides the integration layer between Agent Zero's
agent runtime and Soul Kiln's subsystems.
"""

import sys
from pathlib import Path
from typing import Any, Dict, List, Optional
from dataclasses import dataclass

# Ensure Agent Zero is importable
AGENT_ZERO_PATH = Path(__file__).parent.parent.parent / "vendor" / "agent-zero"
if str(AGENT_ZERO_PATH) not in sys.path:
    sys.path.insert(0, str(AGENT_ZERO_PATH))

# Soul Kiln imports
from src.kuleana.definitions import AMBASSADOR_KULEANAS, get_kuleana_definition
from src.skills.definitions import AMBASSADOR_SKILLS, get_skill_definition
from src.beliefs.definitions import AMBASSADOR_BELIEFS, get_belief_definition
from src.lore.definitions import AMBASSADOR_LORE, get_lore_by_type, get_immutable_lore
from src.voice.definitions import AMBASSADOR_VOICE, get_emotion_patterns, get_patterns_by_type
from src.virtues.anchors import VIRTUES, get_all_virtue_ids
from src.virtues.tiers import FOUNDATION, ASPIRATIONAL

from .config import AmbassadorConfig


@dataclass
class VirtueCheckResult:
    """Result of a virtue basin check."""
    passed: bool
    virtue_id: str
    virtue_name: str
    score: float
    threshold: float
    reason: str


@dataclass
class TabooCheckResult:
    """Result of a taboo check."""
    violated: bool
    violations: List[Dict[str, str]]
    recommendation: str


@dataclass
class KuleanaActivation:
    """Activated kuleana (duty) for the current context."""
    id: str
    name: str
    priority: int
    trigger: str
    required_virtues: List[str]
    required_skills: List[str]


class SoulKilnBridge:
    """
    Bridge between Agent Zero and Soul Kiln subsystems.

    ALL agent decisions flow through this bridge to ensure:
    1. Virtue basin checks on actions
    2. Taboo enforcement
    3. Kuleana-guided priorities
    4. Lore-informed identity
    5. Voice modulation for responses
    """

    def __init__(self, config: AmbassadorConfig):
        self.config = config
        self._virtue_cache: Dict[str, float] = {}
        self._active_kuleanas: List[str] = []
        self._emotion_state: Optional[str] = None

    # =========================================================================
    # Virtue Basin Interface
    # =========================================================================

    def check_virtue(
        self,
        virtue_id: str,
        action: str,
        context: Optional[Dict[str, Any]] = None
    ) -> VirtueCheckResult:
        """
        Check if an action aligns with a specific virtue.

        This is called before EVERY tool use and response.
        """
        # Get virtue definition
        virtue = None
        for v in VIRTUES:
            if v["id"] == virtue_id:
                virtue = v
                break

        if not virtue:
            return VirtueCheckResult(
                passed=False,
                virtue_id=virtue_id,
                virtue_name="Unknown",
                score=0.0,
                threshold=0.99,
                reason=f"Virtue {virtue_id} not found"
            )

        # Determine threshold based on tier
        threshold = 0.99 if virtue_id in FOUNDATION else 0.60

        # Get cached score or default
        score = self._virtue_cache.get(virtue_id, threshold)

        # Check if action aligns (simplified - in production this would use LLM)
        action_lower = action.lower()

        # Foundation virtue checks - stricter
        if virtue_id in FOUNDATION:
            # V01: Honesty - check for deception
            if virtue_id == "V01":
                if any(word in action_lower for word in ["lie", "deceive", "hide", "mislead"]):
                    return VirtueCheckResult(
                        passed=False,
                        virtue_id=virtue_id,
                        virtue_name=virtue["name"],
                        score=0.0,
                        threshold=threshold,
                        reason="Action involves deception, violates Honesty"
                    )

        return VirtueCheckResult(
            passed=True,
            virtue_id=virtue_id,
            virtue_name=virtue["name"],
            score=score,
            threshold=threshold,
            reason="Action aligns with virtue"
        )

    def check_all_foundation_virtues(
        self,
        action: str,
        context: Optional[Dict[str, Any]] = None
    ) -> List[VirtueCheckResult]:
        """Check action against all foundation virtues."""
        results = []
        for virtue_id in FOUNDATION:
            result = self.check_virtue(virtue_id, action, context)
            results.append(result)
        return results

    def get_virtue_scores(self) -> Dict[str, float]:
        """Get current virtue basin scores."""
        scores = {}
        for v in VIRTUES:
            vid = v["id"]
            threshold = 0.99 if vid in FOUNDATION else 0.60
            scores[vid] = self._virtue_cache.get(vid, threshold)
        return scores

    # =========================================================================
    # Taboo Enforcement
    # =========================================================================

    def check_taboos(self, action: str) -> TabooCheckResult:
        """
        Check if an action violates any sacred taboos.

        Taboos are NEVER violated - they are hard constraints.
        """
        violations = []
        action_lower = action.lower()

        taboos = get_lore_by_type("taboo")
        for taboo in taboos:
            taboo_content = taboo.content.lower()

            # Check for debt recommendation
            if "debt" in taboo_content:
                if any(phrase in action_lower for phrase in [
                    "recommend loan", "take out loan", "suggest debt",
                    "borrow money", "student loan", "private loan"
                ]):
                    violations.append({
                        "id": taboo.id,
                        "content": taboo.content
                    })

            # Check for judgment
            if "judge" in taboo_content:
                if any(phrase in action_lower for phrase in [
                    "you should have", "your fault", "you failed",
                    "irresponsible", "careless"
                ]):
                    violations.append({
                        "id": taboo.id,
                        "content": taboo.content
                    })

            # Check for sharing private info
            if "share" in taboo_content:
                if any(phrase in action_lower for phrase in [
                    "tell others", "share with", "disclose to",
                    "inform the school"
                ]):
                    violations.append({
                        "id": taboo.id,
                        "content": taboo.content
                    })

            # Check for giving up
            if "give up" in taboo_content:
                if any(phrase in action_lower for phrase in [
                    "give up", "stop trying", "nothing we can do",
                    "impossible", "can't help"
                ]):
                    violations.append({
                        "id": taboo.id,
                        "content": taboo.content
                    })

        return TabooCheckResult(
            violated=len(violations) > 0,
            violations=violations,
            recommendation="BLOCKED - Action violates sacred taboos" if violations else "Permitted"
        )

    # =========================================================================
    # Kuleana (Duty) Activation
    # =========================================================================

    def activate_kuleanas(self, context: str) -> List[KuleanaActivation]:
        """
        Determine which kuleanas (duties) are activated for the given context.

        Returns kuleanas sorted by priority.
        """
        activated = []
        context_lower = context.lower()

        for k_id, kuleana in AMBASSADOR_KULEANAS.items():
            for trigger in kuleana.trigger_conditions:
                trigger_words = trigger.lower().replace("_", " ").split()
                if any(word in context_lower for word in trigger_words):
                    activated.append(KuleanaActivation(
                        id=k_id,
                        name=kuleana.name,
                        priority=kuleana.priority,
                        trigger=trigger,
                        required_virtues=kuleana.required_virtues,
                        required_skills=kuleana.required_skills,
                    ))
                    break

        # Sort by priority (lower = higher priority)
        activated.sort(key=lambda k: k.priority)

        # Update active kuleanas
        self._active_kuleanas = [k.id for k in activated]

        return activated

    def get_primary_kuleana(self, context: str) -> Optional[KuleanaActivation]:
        """Get the highest priority activated kuleana."""
        kuleanas = self.activate_kuleanas(context)
        return kuleanas[0] if kuleanas else None

    # =========================================================================
    # Lore Consultation
    # =========================================================================

    def get_identity_lore(self) -> Dict[str, Any]:
        """Get the Ambassador's identity lore."""
        origin = AMBASSADOR_LORE.get("L_ORIGIN")
        commitments = get_lore_by_type("commitment")
        taboos = get_lore_by_type("taboo")

        return {
            "origin": origin.content if origin else "",
            "sacred_commitments": [c.content for c in commitments],
            "taboos": [t.content for t in taboos],
            "immutable_count": len(get_immutable_lore()),
        }

    def get_lineage_lore(self) -> List[str]:
        """Get the Ambassador's lineage lore."""
        lineage = get_lore_by_type("lineage")
        return [l.content for l in lineage]

    # =========================================================================
    # Voice Modulation
    # =========================================================================

    def get_voice_guidance(self, emotion: Optional[str] = None) -> Dict[str, Any]:
        """
        Get voice modulation guidance for the current context.

        Returns tone, lexicon patterns, and emotion-specific adjustments.
        """
        guidance = {
            "tone": [],
            "lexicon": [],
            "boundaries": {
                "never": [],
                "always": [],
            },
            "emotion_response": None,
        }

        # Get tone patterns
        tones = get_patterns_by_type("tone")
        guidance["tone"] = [t.content for t in tones]

        # Get lexicon patterns
        lexicon = get_patterns_by_type("lexicon")
        guidance["lexicon"] = [l.content for l in lexicon]

        # Get boundaries
        boundaries = get_patterns_by_type("boundary")
        for b in boundaries:
            if "never" in b.name.lower():
                guidance["boundaries"]["never"].append(b.content)
            elif "always" in b.name.lower():
                guidance["boundaries"]["always"].append(b.content)

        # Get emotion-specific guidance
        if emotion:
            emotions = get_emotion_patterns()
            if emotion in emotions:
                pattern = emotions[emotion]
                guidance["emotion_response"] = {
                    "emotion": emotion,
                    "guidance": pattern.content,
                    "intensity": pattern.intensity,
                }

        return guidance

    def set_emotion_state(self, emotion: str):
        """Update the detected emotion state."""
        self._emotion_state = emotion

    # =========================================================================
    # Belief System
    # =========================================================================

    def get_core_beliefs(self) -> List[Dict[str, Any]]:
        """Get the Ambassador's core beliefs."""
        core = []
        for b_id, belief in AMBASSADOR_BELIEFS.items():
            if belief.conviction >= 0.9 and belief.entrenchment >= 0.9:
                core.append({
                    "id": b_id,
                    "content": belief.content,
                    "conviction": belief.conviction,
                    "type": belief.belief_type.value,
                })
        return core

    def query_belief(self, topic: str) -> Optional[Dict[str, Any]]:
        """Query beliefs related to a topic."""
        topic_lower = topic.lower()
        for b_id, belief in AMBASSADOR_BELIEFS.items():
            if topic_lower in belief.content.lower():
                return {
                    "id": b_id,
                    "content": belief.content,
                    "conviction": belief.conviction,
                    "type": belief.belief_type.value,
                }
        return None

    # =========================================================================
    # Pre-Action Hook (called before every tool/response)
    # =========================================================================

    def pre_action_check(
        self,
        action: str,
        tool_name: Optional[str] = None,
        context: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Comprehensive pre-action check.

        Called before EVERY tool use and response to ensure alignment
        with virtues, taboos, and kuleanas.

        Returns:
            {
                "allowed": bool,
                "virtue_checks": [...],
                "taboo_result": {...},
                "active_kuleanas": [...],
                "voice_guidance": {...},
                "block_reason": str | None,
            }
        """
        result = {
            "allowed": True,
            "virtue_checks": [],
            "taboo_result": None,
            "active_kuleanas": [],
            "voice_guidance": {},
            "block_reason": None,
        }

        # 1. Check taboos first (hard constraints)
        taboo_result = self.check_taboos(action)
        result["taboo_result"] = {
            "violated": taboo_result.violated,
            "violations": taboo_result.violations,
        }
        if taboo_result.violated:
            result["allowed"] = False
            result["block_reason"] = f"TABOO VIOLATION: {taboo_result.violations[0]['content']}"
            return result

        # 2. Check foundation virtues
        if self.config.virtue_check_on_every_action:
            virtue_results = self.check_all_foundation_virtues(action, context)
            result["virtue_checks"] = [
                {
                    "virtue_id": v.virtue_id,
                    "virtue_name": v.virtue_name,
                    "passed": v.passed,
                    "score": v.score,
                }
                for v in virtue_results
            ]
            failed = [v for v in virtue_results if not v.passed]
            if failed:
                result["allowed"] = False
                result["block_reason"] = f"VIRTUE VIOLATION: {failed[0].reason}"
                return result

        # 3. Activate kuleanas for context
        if context and "message" in context:
            kuleanas = self.activate_kuleanas(context["message"])
            result["active_kuleanas"] = [
                {"id": k.id, "name": k.name, "priority": k.priority}
                for k in kuleanas
            ]

        # 4. Get voice guidance
        result["voice_guidance"] = self.get_voice_guidance(self._emotion_state)

        return result


def create_ambassador_agent(
    config: Optional[AmbassadorConfig] = None,
    student_id: str = "",
) -> "SoulKilnAgent":
    """
    Create a new Ambassador agent running on Agent Zero.

    This is the main entry point for creating agents.
    """
    from .soul_agent import SoulKilnAgent

    if config is None:
        config = AmbassadorConfig()

    config.student_id = student_id

    return SoulKilnAgent(config)
