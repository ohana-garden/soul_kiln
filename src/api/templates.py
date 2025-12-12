"""
Soul template management for the Virtue Basin Simulator.

Provides storage and retrieval of valid soul templates
for deployment to agents.
"""

import json
import logging
import uuid
from datetime import datetime
from pathlib import Path

logger = logging.getLogger(__name__)


class TemplateManager:
    """
    Manages soul templates - valid topology configurations.

    Templates can be stored, retrieved, and deployed to new agents.
    """

    def __init__(self, storage_dir: str | Path | None = None):
        """
        Initialize the template manager.

        Args:
            storage_dir: Directory for template storage
        """
        self.storage_dir = Path(storage_dir) if storage_dir else Path("./templates")
        self._templates: dict[str, dict] = {}
        self._loaded = False

    def _ensure_storage(self) -> None:
        """Ensure storage directory exists."""
        self.storage_dir.mkdir(parents=True, exist_ok=True)

    def _load_templates(self) -> None:
        """Load templates from storage."""
        if self._loaded:
            return

        self._ensure_storage()

        for template_file in self.storage_dir.glob("*.json"):
            try:
                with open(template_file) as f:
                    template = json.load(f)
                    self._templates[template["id"]] = template
            except Exception as e:
                logger.warning(f"Failed to load template {template_file}: {e}")

        self._loaded = True
        logger.info(f"Loaded {len(self._templates)} templates")

    def save_template(self, template: dict) -> str:
        """
        Save a soul template.

        Args:
            template: Template data (must have edges, fitness, character)

        Returns:
            Template ID
        """
        self._ensure_storage()

        template_id = template.get("id") or f"template_{uuid.uuid4().hex[:8]}"
        template["id"] = template_id
        template["saved_at"] = datetime.utcnow().isoformat()

        # Validate template has required fields
        required = ["edges", "fitness"]
        for field in required:
            if field not in template:
                raise ValueError(f"Template missing required field: {field}")

        # Save to file
        output_path = self.storage_dir / f"{template_id}.json"
        with open(output_path, "w") as f:
            json.dump(template, f, indent=2)

        # Update cache
        self._templates[template_id] = template

        logger.info(f"Saved template {template_id}")
        return template_id

    def get_template(self, template_id: str) -> dict | None:
        """
        Get a template by ID.

        Args:
            template_id: The template ID

        Returns:
            Template data, or None if not found
        """
        self._load_templates()
        return self._templates.get(template_id)

    def get_random_valid(self, min_fitness: float = 0.95) -> dict | None:
        """
        Get a random valid template.

        Args:
            min_fitness: Minimum fitness threshold

        Returns:
            Random valid template, or None if none available
        """
        self._load_templates()

        valid = [t for t in self._templates.values() if t.get("fitness", 0) >= min_fitness]
        if not valid:
            return None

        import random
        return random.choice(valid)

    def get_by_character(self, character_type: str) -> list[dict]:
        """
        Get templates by character type.

        Args:
            character_type: Character category (e.g., "Truth-Seeker")

        Returns:
            List of matching templates
        """
        self._load_templates()

        matching = []
        for template in self._templates.values():
            profile = template.get("character_profile", {})
            if profile.get("category") == character_type:
                matching.append(template)

        return matching

    def get_by_dominant_virtue(self, virtue_id: str) -> list[dict]:
        """
        Get templates by dominant virtue.

        Args:
            virtue_id: Virtue ID (e.g., "V01")

        Returns:
            List of matching templates
        """
        self._load_templates()

        matching = []
        for template in self._templates.values():
            profile = template.get("character_profile", {})
            dominant = profile.get("dominant_virtues", [])
            if dominant and dominant[0] == virtue_id:
                matching.append(template)

        return matching

    def list_templates(
        self,
        min_fitness: float | None = None,
        limit: int = 100,
    ) -> list[dict]:
        """
        List available templates.

        Args:
            min_fitness: Optional minimum fitness filter
            limit: Maximum templates to return

        Returns:
            List of template summaries
        """
        self._load_templates()

        templates = list(self._templates.values())

        if min_fitness is not None:
            templates = [t for t in templates if t.get("fitness", 0) >= min_fitness]

        # Sort by fitness (descending)
        templates.sort(key=lambda t: t.get("fitness", 0), reverse=True)

        # Return summaries
        summaries = []
        for t in templates[:limit]:
            summaries.append({
                "id": t["id"],
                "fitness": t.get("fitness", 0),
                "generation": t.get("generation", 0),
                "character_category": t.get("character_profile", {}).get("category"),
                "dominant_virtues": t.get("character_profile", {}).get("dominant_virtues", []),
                "edge_count": len(t.get("edges", [])),
                "saved_at": t.get("saved_at"),
            })

        return summaries

    def delete_template(self, template_id: str) -> bool:
        """
        Delete a template.

        Args:
            template_id: The template ID

        Returns:
            True if deleted, False if not found
        """
        self._load_templates()

        if template_id not in self._templates:
            return False

        # Delete file
        template_file = self.storage_dir / f"{template_id}.json"
        if template_file.exists():
            template_file.unlink()

        # Remove from cache
        del self._templates[template_id]

        logger.info(f"Deleted template {template_id}")
        return True

    def export_for_deployment(self, template_id: str) -> dict | None:
        """
        Export a template for deployment.

        Provides the minimal data needed to initialize an agent.

        Args:
            template_id: The template ID

        Returns:
            Deployment-ready template data
        """
        template = self.get_template(template_id)
        if not template:
            return None

        return {
            "id": template["id"],
            "edges": template["edges"],
            "virtue_degrees": template.get("virtue_degrees", {}),
            "character_category": template.get("character_profile", {}).get("category"),
        }

    def track_deployment(self, template_id: str) -> None:
        """
        Track that a template was deployed.

        Args:
            template_id: The template ID
        """
        template = self.get_template(template_id)
        if template:
            deployments = template.get("deployments", 0)
            template["deployments"] = deployments + 1
            template["last_deployed"] = datetime.utcnow().isoformat()
            self.save_template(template)
