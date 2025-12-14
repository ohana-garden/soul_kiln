"""
Behavior Adjustment Tool.

Provides runtime behavior modification for agents.
"""

import logging
import threading
import uuid
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any, Callable

logger = logging.getLogger(__name__)


class BehaviorDimension(str, Enum):
    """Dimensions of agent behavior."""

    VERBOSITY = "verbosity"  # How detailed responses are
    CAUTION = "caution"  # Risk aversion level
    CREATIVITY = "creativity"  # Novel vs conventional approaches
    FORMALITY = "formality"  # Formal vs casual tone
    SPEED = "speed"  # Speed vs thoroughness trade-off
    AUTONOMY = "autonomy"  # Independent vs confirmatory
    PERSISTENCE = "persistence"  # Retry behavior on failures


@dataclass
class BehaviorProfile:
    """A behavior profile for an agent."""

    id: str = field(default_factory=lambda: f"bhv_{uuid.uuid4().hex[:8]}")
    name: str = ""
    description: str = ""
    dimensions: dict[str, float] = field(default_factory=dict)  # -1.0 to 1.0
    active: bool = True
    created_at: datetime = field(default_factory=datetime.utcnow)
    updated_at: datetime = field(default_factory=datetime.utcnow)
    metadata: dict = field(default_factory=dict)

    def __post_init__(self):
        # Initialize default dimensions
        for dim in BehaviorDimension:
            if dim.value not in self.dimensions:
                self.dimensions[dim.value] = 0.0

    def get(self, dimension: str | BehaviorDimension) -> float:
        """Get a dimension value."""
        key = dimension.value if isinstance(dimension, BehaviorDimension) else dimension
        return self.dimensions.get(key, 0.0)

    def set(self, dimension: str | BehaviorDimension, value: float) -> None:
        """Set a dimension value."""
        key = dimension.value if isinstance(dimension, BehaviorDimension) else dimension
        self.dimensions[key] = max(-1.0, min(1.0, value))
        self.updated_at = datetime.utcnow()

    def adjust(self, dimension: str | BehaviorDimension, delta: float) -> float:
        """Adjust a dimension by delta."""
        current = self.get(dimension)
        new_value = max(-1.0, min(1.0, current + delta))
        self.set(dimension, new_value)
        return new_value

    def to_dict(self) -> dict:
        """Convert to dictionary."""
        return {
            "id": self.id,
            "name": self.name,
            "description": self.description,
            "dimensions": self.dimensions,
            "active": self.active,
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat(),
        }

    @classmethod
    def from_dict(cls, data: dict) -> "BehaviorProfile":
        """Create from dictionary."""
        profile = cls(
            id=data.get("id", f"bhv_{uuid.uuid4().hex[:8]}"),
            name=data.get("name", ""),
            description=data.get("description", ""),
            dimensions=data.get("dimensions", {}),
            active=data.get("active", True),
        )
        if data.get("created_at"):
            profile.created_at = datetime.fromisoformat(data["created_at"])
        if data.get("updated_at"):
            profile.updated_at = datetime.fromisoformat(data["updated_at"])
        return profile


class BehaviorAdjuster:
    """
    Behavior adjustment tool for runtime agent modification.

    Features:
    - Create and manage behavior profiles
    - Adjust behavior dimensions at runtime
    - Apply profiles to agents
    - Track behavior history
    """

    # Preset profiles
    PRESETS = {
        "careful": {
            BehaviorDimension.CAUTION.value: 0.8,
            BehaviorDimension.SPEED.value: -0.5,
            BehaviorDimension.AUTONOMY.value: -0.3,
        },
        "creative": {
            BehaviorDimension.CREATIVITY.value: 0.8,
            BehaviorDimension.CAUTION.value: -0.3,
            BehaviorDimension.AUTONOMY.value: 0.5,
        },
        "fast": {
            BehaviorDimension.SPEED.value: 0.8,
            BehaviorDimension.VERBOSITY.value: -0.5,
            BehaviorDimension.CAUTION.value: -0.3,
        },
        "thorough": {
            BehaviorDimension.VERBOSITY.value: 0.7,
            BehaviorDimension.SPEED.value: -0.5,
            BehaviorDimension.CAUTION.value: 0.3,
        },
        "autonomous": {
            BehaviorDimension.AUTONOMY.value: 0.9,
            BehaviorDimension.PERSISTENCE.value: 0.5,
        },
        "conservative": {
            BehaviorDimension.CAUTION.value: 0.9,
            BehaviorDimension.CREATIVITY.value: -0.5,
            BehaviorDimension.AUTONOMY.value: -0.5,
        },
    }

    def __init__(self):
        """Initialize behavior adjuster."""
        self._profiles: dict[str, BehaviorProfile] = {}
        self._agent_profiles: dict[str, str] = {}  # agent_id -> profile_id
        self._history: list[dict] = []
        self._max_history = 1000
        self._lock = threading.RLock()
        self._callbacks: list[Callable[[str, BehaviorProfile], None]] = []

    def create_profile(
        self,
        name: str,
        description: str = "",
        dimensions: dict[str, float] | None = None,
        preset: str | None = None,
    ) -> BehaviorProfile:
        """
        Create a new behavior profile.

        Args:
            name: Profile name
            description: Profile description
            dimensions: Initial dimension values
            preset: Optional preset name to use as base

        Returns:
            Created profile
        """
        profile = BehaviorProfile(name=name, description=description)

        # Apply preset if specified
        if preset and preset in self.PRESETS:
            for dim, value in self.PRESETS[preset].items():
                profile.dimensions[dim] = value

        # Apply custom dimensions
        if dimensions:
            for dim, value in dimensions.items():
                profile.dimensions[dim] = max(-1.0, min(1.0, value))

        with self._lock:
            self._profiles[profile.id] = profile

        logger.info(f"Created behavior profile {profile.id}: {name}")
        return profile

    def get_profile(self, profile_id: str) -> BehaviorProfile | None:
        """Get a profile by ID."""
        return self._profiles.get(profile_id)

    def get_profile_by_name(self, name: str) -> BehaviorProfile | None:
        """Get a profile by name."""
        for profile in self._profiles.values():
            if profile.name == name:
                return profile
        return None

    def list_profiles(self, active_only: bool = True) -> list[BehaviorProfile]:
        """List all profiles."""
        profiles = list(self._profiles.values())
        if active_only:
            profiles = [p for p in profiles if p.active]
        return profiles

    def update_profile(
        self,
        profile_id: str,
        dimensions: dict[str, float] | None = None,
        name: str | None = None,
        description: str | None = None,
    ) -> BehaviorProfile | None:
        """Update a profile."""
        profile = self._profiles.get(profile_id)
        if not profile:
            return None

        if name is not None:
            profile.name = name
        if description is not None:
            profile.description = description
        if dimensions:
            for dim, value in dimensions.items():
                profile.dimensions[dim] = max(-1.0, min(1.0, value))

        profile.updated_at = datetime.utcnow()
        return profile

    def delete_profile(self, profile_id: str) -> bool:
        """Delete a profile."""
        with self._lock:
            if profile_id in self._profiles:
                del self._profiles[profile_id]
                # Remove from agent assignments
                self._agent_profiles = {
                    k: v for k, v in self._agent_profiles.items() if v != profile_id
                }
                return True
        return False

    def assign_profile(self, agent_id: str, profile_id: str) -> bool:
        """Assign a profile to an agent."""
        if profile_id not in self._profiles:
            return False

        with self._lock:
            old_profile = self._agent_profiles.get(agent_id)
            self._agent_profiles[agent_id] = profile_id

            # Record history
            self._record_change(agent_id, old_profile, profile_id, "assign")

            # Notify callbacks
            profile = self._profiles[profile_id]
            for callback in self._callbacks:
                try:
                    callback(agent_id, profile)
                except Exception as e:
                    logger.error(f"Callback error: {e}")

        logger.debug(f"Assigned profile {profile_id} to agent {agent_id}")
        return True

    def get_agent_profile(self, agent_id: str) -> BehaviorProfile | None:
        """Get the profile assigned to an agent."""
        profile_id = self._agent_profiles.get(agent_id)
        if profile_id:
            return self._profiles.get(profile_id)
        return None

    def adjust_agent_behavior(
        self,
        agent_id: str,
        dimension: str | BehaviorDimension,
        delta: float,
    ) -> float | None:
        """
        Adjust a dimension for an agent's profile.

        Args:
            agent_id: Agent ID
            dimension: Dimension to adjust
            delta: Adjustment amount

        Returns:
            New value or None if no profile assigned
        """
        profile = self.get_agent_profile(agent_id)
        if not profile:
            # Create default profile for agent
            profile = self.create_profile(f"agent_{agent_id}_profile")
            self.assign_profile(agent_id, profile.id)

        old_value = profile.get(dimension)
        new_value = profile.adjust(dimension, delta)

        self._record_change(
            agent_id,
            profile.id,
            profile.id,
            "adjust",
            {
                "dimension": dimension.value
                if isinstance(dimension, BehaviorDimension)
                else dimension,
                "old_value": old_value,
                "new_value": new_value,
                "delta": delta,
            },
        )

        return new_value

    def get_behavior_value(
        self,
        agent_id: str,
        dimension: str | BehaviorDimension,
        default: float = 0.0,
    ) -> float:
        """Get a behavior dimension value for an agent."""
        profile = self.get_agent_profile(agent_id)
        if profile:
            return profile.get(dimension)
        return default

    def apply_preset(self, agent_id: str, preset: str) -> bool:
        """Apply a preset to an agent."""
        if preset not in self.PRESETS:
            return False

        profile = self.get_agent_profile(agent_id)
        if not profile:
            profile = self.create_profile(
                f"agent_{agent_id}_profile",
                preset=preset,
            )
            self.assign_profile(agent_id, profile.id)
        else:
            for dim, value in self.PRESETS[preset].items():
                profile.dimensions[dim] = value
            profile.updated_at = datetime.utcnow()

        self._record_change(agent_id, profile.id, profile.id, "preset", {"preset": preset})
        return True

    def _record_change(
        self,
        agent_id: str,
        old_profile: str | None,
        new_profile: str,
        action: str,
        details: dict | None = None,
    ) -> None:
        """Record a behavior change."""
        with self._lock:
            self._history.append(
                {
                    "timestamp": datetime.utcnow().isoformat(),
                    "agent_id": agent_id,
                    "old_profile": old_profile,
                    "new_profile": new_profile,
                    "action": action,
                    "details": details or {},
                }
            )

            if len(self._history) > self._max_history:
                self._history = self._history[-self._max_history // 2 :]

    def register_callback(
        self,
        callback: Callable[[str, BehaviorProfile], None],
    ) -> None:
        """Register a callback for profile changes."""
        self._callbacks.append(callback)

    def get_history(
        self,
        agent_id: str | None = None,
        limit: int = 100,
    ) -> list[dict]:
        """Get behavior change history."""
        with self._lock:
            history = self._history
            if agent_id:
                history = [h for h in history if h["agent_id"] == agent_id]
            return history[-limit:]

    def get_stats(self) -> dict:
        """Get behavior statistics."""
        with self._lock:
            return {
                "total_profiles": len(self._profiles),
                "active_profiles": len([p for p in self._profiles.values() if p.active]),
                "assigned_agents": len(self._agent_profiles),
                "history_size": len(self._history),
                "available_presets": list(self.PRESETS.keys()),
            }

    def export_profiles(self) -> list[dict]:
        """Export all profiles."""
        return [p.to_dict() for p in self._profiles.values()]

    def import_profiles(self, data: list[dict]) -> int:
        """Import profiles from dictionaries."""
        imported = 0
        for item in data:
            profile = BehaviorProfile.from_dict(item)
            self._profiles[profile.id] = profile
            imported += 1
        return imported
