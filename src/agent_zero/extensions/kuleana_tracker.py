"""
Kuleana Tracker Extension for Agent Zero.

Tracks duty activation and fulfillment throughout agent sessions.
"""

import sys
from pathlib import Path
from typing import Any, Dict, List, Optional
from dataclasses import dataclass, field
from datetime import datetime

AGENT_ZERO_PATH = Path(__file__).parent.parent.parent.parent / "vendor" / "agent-zero"
if str(AGENT_ZERO_PATH) not in sys.path:
    sys.path.insert(0, str(AGENT_ZERO_PATH))


@dataclass
class KuleanaSession:
    """Tracks a single kuleana activation session."""
    kuleana_id: str
    kuleana_name: str
    activated_at: datetime
    trigger: str
    status: str = "active"  # active, fulfilled, deferred
    actions_taken: List[str] = field(default_factory=list)
    fulfilled_at: Optional[datetime] = None


class KuleanaTracker:
    """
    Tracks kuleana (duty) activation and fulfillment.

    This extension:
    1. Records when duties are activated
    2. Tracks actions taken toward fulfillment
    3. Marks duties as fulfilled or deferred
    4. Provides reporting on duty performance
    """

    def __init__(self, agent):
        self.agent = agent
        self.bridge = agent.get_data("soul_kiln_bridge")
        self._sessions: Dict[str, KuleanaSession] = {}
        self._history: List[KuleanaSession] = []

    def activate(
        self,
        kuleana_id: str,
        kuleana_name: str,
        trigger: str
    ) -> KuleanaSession:
        """Record a kuleana activation."""
        session = KuleanaSession(
            kuleana_id=kuleana_id,
            kuleana_name=kuleana_name,
            activated_at=datetime.now(),
            trigger=trigger,
        )
        self._sessions[kuleana_id] = session
        return session

    def record_action(self, kuleana_id: str, action: str):
        """Record an action taken toward fulfilling a kuleana."""
        if kuleana_id in self._sessions:
            self._sessions[kuleana_id].actions_taken.append(action)

    def fulfill(self, kuleana_id: str) -> Optional[KuleanaSession]:
        """Mark a kuleana as fulfilled."""
        if kuleana_id in self._sessions:
            session = self._sessions.pop(kuleana_id)
            session.status = "fulfilled"
            session.fulfilled_at = datetime.now()
            self._history.append(session)
            return session
        return None

    def defer(self, kuleana_id: str, reason: str) -> Optional[KuleanaSession]:
        """Defer a kuleana for later."""
        if kuleana_id in self._sessions:
            session = self._sessions[kuleana_id]
            session.status = "deferred"
            session.actions_taken.append(f"Deferred: {reason}")
            return session
        return None

    def get_active(self) -> List[KuleanaSession]:
        """Get all currently active kuleanas."""
        return [s for s in self._sessions.values() if s.status == "active"]

    def get_primary(self) -> Optional[KuleanaSession]:
        """Get the highest priority active kuleana."""
        active = self.get_active()
        if not active:
            return None
        # Sort by kuleana_id (K01 < K02 < etc.)
        active.sort(key=lambda s: s.kuleana_id)
        return active[0]

    def get_report(self) -> Dict[str, Any]:
        """Generate a duty performance report."""
        total_activated = len(self._history) + len(self._sessions)
        fulfilled = len([h for h in self._history if h.status == "fulfilled"])
        deferred = len([h for h in self._history if h.status == "deferred"])
        active = len(self.get_active())

        return {
            "total_activated": total_activated,
            "fulfilled": fulfilled,
            "deferred": deferred,
            "currently_active": active,
            "fulfillment_rate": fulfilled / max(1, total_activated - active),
            "active_kuleanas": [
                {
                    "id": s.kuleana_id,
                    "name": s.kuleana_name,
                    "actions_count": len(s.actions_taken),
                }
                for s in self.get_active()
            ],
        }

    async def on_context_change(self, new_context: str):
        """Called when the conversation context changes."""
        if not self.bridge:
            return

        # Check if new kuleanas should be activated
        activations = self.bridge.activate_kuleanas(new_context)

        for k in activations:
            if k.id not in self._sessions:
                self.activate(k.id, k.name, k.trigger)


def register_kuleana_tracker(agent) -> KuleanaTracker:
    """Register the KuleanaTracker extension with an agent."""
    tracker = KuleanaTracker(agent)
    agent.set_data("kuleana_tracker", tracker)
    return tracker
