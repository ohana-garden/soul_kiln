#!/usr/bin/env python3
"""
Export a soul template to a file.

Usage:
    python -m scripts.export_template [--template-id ID] [--output FILE]
"""

import argparse
import json
import logging
import sys
from pathlib import Path

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def main():
    """Export template."""
    parser = argparse.ArgumentParser(description="Export soul template")
    parser.add_argument("--template-id", help="Template ID to export")
    parser.add_argument("--template-dir", default="./output/templates", help="Template directory")
    parser.add_argument("--output", default="./soul_template.json", help="Output file")
    parser.add_argument("--list", action="store_true", help="List available templates")
    parser.add_argument("--random", action="store_true", help="Export random valid template")
    parser.add_argument("--character", help="Filter by character type")
    parser.add_argument("--virtue", help="Filter by dominant virtue")
    args = parser.parse_args()

    try:
        from src.api.templates import TemplateManager

        template_manager = TemplateManager(args.template_dir)

        if args.list:
            # List templates
            templates = template_manager.list_templates()
            if not templates:
                logger.info("No templates found")
                return 0

            logger.info(f"Found {len(templates)} templates:")
            for t in templates:
                logger.info(
                    f"  {t['id']}: fitness={t['fitness']:.4f}, "
                    f"character={t.get('character_category', 'unknown')}, "
                    f"edges={t['edge_count']}"
                )
            return 0

        # Get template
        template = None

        if args.random:
            template = template_manager.get_random_valid()
            if template:
                logger.info(f"Selected random template: {template['id']}")

        elif args.character:
            templates = template_manager.get_by_character(args.character)
            if templates:
                template = templates[0]
                logger.info(f"Found template with character {args.character}: {template['id']}")

        elif args.virtue:
            templates = template_manager.get_by_dominant_virtue(args.virtue)
            if templates:
                template = templates[0]
                logger.info(f"Found template with virtue {args.virtue}: {template['id']}")

        elif args.template_id:
            template = template_manager.get_template(args.template_id)
            if template:
                logger.info(f"Found template: {args.template_id}")

        if not template:
            logger.error("No template found matching criteria")
            return 1

        # Export for deployment
        deployment = template_manager.export_for_deployment(template["id"])

        output_path = Path(args.output)
        with open(output_path, "w") as f:
            json.dump(deployment, f, indent=2)

        logger.info(f"Exported template to {output_path}")
        logger.info(f"  ID: {deployment['id']}")
        logger.info(f"  Edges: {len(deployment['edges'])}")
        logger.info(f"  Character: {deployment.get('character_category', 'unknown')}")

        return 0

    except Exception as e:
        logger.error(f"Export failed: {e}")
        return 1


if __name__ == "__main__":
    sys.exit(main())
