"""Gestalt computation - holistic character from topology."""
from .compute import compute_gestalt, get_gestalt
from .tendencies import compute_tendencies, TENDENCY_DEFINITIONS
from .embedding import (
    GestaltEmbedding,
    encode_gestalt,
    decode_embedding,
    interpolate_embeddings,
    find_nearest,
    cluster_embeddings,
    add_noise,
    sample_random_embedding,
)
from .compare import (
    compare_gestalts,
    find_similar_agents,
    cluster_agents,
    analyze_archetype_distribution,
    track_character_evolution,
    interpolate_characters,
)

__all__ = [
    # Core
    "compute_gestalt",
    "get_gestalt",
    "compute_tendencies",
    "TENDENCY_DEFINITIONS",
    # Embedding
    "GestaltEmbedding",
    "encode_gestalt",
    "decode_embedding",
    "interpolate_embeddings",
    "find_nearest",
    "cluster_embeddings",
    "add_noise",
    "sample_random_embedding",
    # Comparison
    "compare_gestalts",
    "find_similar_agents",
    "cluster_agents",
    "analyze_archetype_distribution",
    "track_character_evolution",
    "interpolate_characters",
]
