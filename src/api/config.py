"""
Configuration management for the Virtue Basin Simulator.

Loads configuration from YAML files and environment variables.
"""

import os
from dataclasses import dataclass, field
from pathlib import Path

import yaml


@dataclass
class GraphConfig:
    """Graph database configuration."""
    database: str = "falkordb"
    host: str = "localhost"
    port: int = 6379


@dataclass
class VirtuesConfig:
    """Virtue anchor configuration."""
    count: int = 19
    target_degree: int = 9
    baseline_activation: float = 0.3


@dataclass
class DynamicsConfig:
    """Dynamics engine configuration."""
    learning_rate: float = 0.01
    decay_constant: float = 0.97
    decay_interval_seconds: int = 3600
    perturbation_interval_steps: int = 100
    perturbation_strength: float = 0.7
    activation_threshold: float = 0.1
    spread_dampening: float = 0.8


@dataclass
class TestingConfig:
    """Alignment testing configuration."""
    stimuli_count: int = 100
    max_trajectory_length: int = 1000
    capture_threshold: float = 0.7
    min_alignment_score: float = 0.95


@dataclass
class EvolutionConfig:
    """Evolution configuration."""
    population_size: int = 50
    generations: int = 100
    mutation_rate: float = 0.1
    crossover_rate: float = 0.3
    elitism_count: int = 2


@dataclass
class SelfHealingConfig:
    """Self-healing configuration."""
    lockin_threshold_steps: int = 50
    dead_zone_check_interval: int = 100
    false_basin_decay_multiplier: float = 2.0
    blindness_threshold_seconds: int = 86400


@dataclass
class Config:
    """Main configuration container."""
    graph: GraphConfig = field(default_factory=GraphConfig)
    virtues: VirtuesConfig = field(default_factory=VirtuesConfig)
    dynamics: DynamicsConfig = field(default_factory=DynamicsConfig)
    testing: TestingConfig = field(default_factory=TestingConfig)
    evolution: EvolutionConfig = field(default_factory=EvolutionConfig)
    self_healing: SelfHealingConfig = field(default_factory=SelfHealingConfig)


def load_config(config_path: str | Path | None = None) -> Config:
    """
    Load configuration from file and environment.

    Args:
        config_path: Optional path to config file

    Returns:
        Config object
    """
    config = Config()

    # Try to load from file
    if config_path:
        config_path = Path(config_path)
        if config_path.exists():
            with open(config_path) as f:
                data = yaml.safe_load(f)
                config = _parse_config(data)

    # Override with environment variables
    config = _apply_env_overrides(config)

    return config


def _parse_config(data: dict) -> Config:
    """Parse configuration from dictionary."""
    config = Config()

    if "graph" in data:
        config.graph = GraphConfig(**data["graph"])

    if "virtues" in data:
        config.virtues = VirtuesConfig(**data["virtues"])

    if "dynamics" in data:
        config.dynamics = DynamicsConfig(**data["dynamics"])

    if "testing" in data:
        config.testing = TestingConfig(**data["testing"])

    if "evolution" in data:
        config.evolution = EvolutionConfig(**data["evolution"])

    if "self_healing" in data:
        config.self_healing = SelfHealingConfig(**data["self_healing"])

    return config


def _apply_env_overrides(config: Config) -> Config:
    """Apply environment variable overrides."""
    # Graph config
    if "FALKORDB_HOST" in os.environ:
        config.graph.host = os.environ["FALKORDB_HOST"]
    if "FALKORDB_PORT" in os.environ:
        config.graph.port = int(os.environ["FALKORDB_PORT"])

    # Evolution config
    if "VBS_POPULATION_SIZE" in os.environ:
        config.evolution.population_size = int(os.environ["VBS_POPULATION_SIZE"])
    if "VBS_GENERATIONS" in os.environ:
        config.evolution.generations = int(os.environ["VBS_GENERATIONS"])

    # Testing config
    if "VBS_MIN_ALIGNMENT_SCORE" in os.environ:
        config.testing.min_alignment_score = float(os.environ["VBS_MIN_ALIGNMENT_SCORE"])

    return config


def save_config(config: Config, output_path: str | Path) -> None:
    """
    Save configuration to YAML file.

    Args:
        config: Config object to save
        output_path: Output file path
    """
    output_path = Path(output_path)

    data = {
        "graph": {
            "database": config.graph.database,
            "host": config.graph.host,
            "port": config.graph.port,
        },
        "virtues": {
            "count": config.virtues.count,
            "target_degree": config.virtues.target_degree,
            "baseline_activation": config.virtues.baseline_activation,
        },
        "dynamics": {
            "learning_rate": config.dynamics.learning_rate,
            "decay_constant": config.dynamics.decay_constant,
            "decay_interval_seconds": config.dynamics.decay_interval_seconds,
            "perturbation_interval_steps": config.dynamics.perturbation_interval_steps,
            "perturbation_strength": config.dynamics.perturbation_strength,
            "activation_threshold": config.dynamics.activation_threshold,
            "spread_dampening": config.dynamics.spread_dampening,
        },
        "testing": {
            "stimuli_count": config.testing.stimuli_count,
            "max_trajectory_length": config.testing.max_trajectory_length,
            "capture_threshold": config.testing.capture_threshold,
            "min_alignment_score": config.testing.min_alignment_score,
        },
        "evolution": {
            "population_size": config.evolution.population_size,
            "generations": config.evolution.generations,
            "mutation_rate": config.evolution.mutation_rate,
            "crossover_rate": config.evolution.crossover_rate,
            "elitism_count": config.evolution.elitism_count,
        },
        "self_healing": {
            "lockin_threshold_steps": config.self_healing.lockin_threshold_steps,
            "dead_zone_check_interval": config.self_healing.dead_zone_check_interval,
            "false_basin_decay_multiplier": config.self_healing.false_basin_decay_multiplier,
            "blindness_threshold_seconds": config.self_healing.blindness_threshold_seconds,
        },
    }

    with open(output_path, "w") as f:
        yaml.dump(data, f, default_flow_style=False)
