#!/usr/bin/env python3
"""
Run the topology evolution process.

Usage:
    python -m scripts.run_evolution [options]
"""

import argparse
import json
import logging
import sys
from pathlib import Path

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


def main():
    """Run evolution."""
    parser = argparse.ArgumentParser(description="Run virtue basin evolution")
    parser.add_argument("--host", default="localhost", help="FalkorDB host")
    parser.add_argument("--port", type=int, default=6379, help="FalkorDB port")
    parser.add_argument("--graph", default="virtue_basin", help="Graph name")
    parser.add_argument("--population", type=int, default=50, help="Population size")
    parser.add_argument("--generations", type=int, default=100, help="Max generations")
    parser.add_argument("--concepts", type=int, default=30, help="Number of concept nodes")
    parser.add_argument("--output", default="./output", help="Output directory")
    parser.add_argument("--checkpoint-dir", help="Checkpoint directory")
    parser.add_argument("--config", help="Path to config file")
    args = parser.parse_args()

    try:
        from src.agents.controller import SimulatorController
        from src.api.config import load_config
        from src.api.templates import TemplateManager

        # Load config if provided
        config = None
        if args.config:
            config = load_config(args.config)
            logger.info(f"Loaded config from {args.config}")

        # Initialize controller
        logger.info("Initializing simulator controller...")
        controller = SimulatorController(
            host=args.host,
            port=args.port,
            graph_name=args.graph,
        )
        controller.setup()

        # Run evolution
        logger.info(f"Starting evolution: population={args.population}, generations={args.generations}")
        result = controller.run_evolution(
            population_size=args.population,
            generations=args.generations,
            checkpoint_dir=args.checkpoint_dir,
        )

        # Save results
        output_dir = Path(args.output)
        output_dir.mkdir(parents=True, exist_ok=True)

        result_file = output_dir / "evolution_result.json"
        with open(result_file, "w") as f:
            json.dump(result, f, indent=2)
        logger.info(f"Saved evolution result to {result_file}")

        # Save template if successful
        if result.get("success") and result.get("best_topology"):
            template_manager = TemplateManager(output_dir / "templates")
            template = {
                **result["best_topology"],
                "character_profile": result.get("character_profile", {}),
            }
            template_id = template_manager.save_template(template)
            logger.info(f"Saved valid template: {template_id}")

        # Report
        logger.info("=" * 50)
        logger.info("Evolution Complete")
        logger.info(f"  Success: {result.get('success')}")
        logger.info(f"  Best Fitness: {result.get('best_fitness', 0):.4f}")
        logger.info(f"  Generations: {result.get('generations_run')}")
        logger.info(f"  Converged: {result.get('converged')}")
        if result.get("character_profile"):
            profile = result["character_profile"]
            logger.info(f"  Character: {profile.get('category')}")
            logger.info(f"  Dominant Virtues: {profile.get('dominant_virtues')}")
        logger.info("=" * 50)

        controller.teardown()
        return 0 if result.get("success") else 1

    except Exception as e:
        logger.error(f"Evolution failed: {e}")
        import traceback
        traceback.print_exc()
        return 1


if __name__ == "__main__":
    sys.exit(main())
