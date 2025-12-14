"""
Gestalt embedding - encode characters into a latent vector space.

This enables:
- Character similarity comparison
- Interpolation between characters
- Clustering of character types
- Foundation for diffusion-based generation
"""

import math
from dataclasses import dataclass
from typing import List, Tuple

from ..models import Gestalt
from ..virtues.anchors import VIRTUES
from .tendencies import TENDENCY_DEFINITIONS


# Embedding dimensions
VIRTUE_DIM = 19  # One per virtue
TENDENCY_DIM = len(TENDENCY_DEFINITIONS)  # One per tendency
RELATION_DIM = 8  # Compressed relation patterns
META_DIM = 4  # Coherence, stability, archetype encoding

TOTAL_DIM = VIRTUE_DIM + TENDENCY_DIM + RELATION_DIM + META_DIM


@dataclass
class GestaltEmbedding:
    """
    A vector representation of a gestalt in latent space.

    The embedding captures:
    - Virtue activation pattern (19d)
    - Behavioral tendencies (10d)
    - Relational structure summary (8d)
    - Meta-properties (4d)
    """
    agent_id: str
    vector: List[float]

    @property
    def virtue_slice(self) -> List[float]:
        """Get the virtue activation portion."""
        return self.vector[:VIRTUE_DIM]

    @property
    def tendency_slice(self) -> List[float]:
        """Get the tendency portion."""
        start = VIRTUE_DIM
        return self.vector[start:start + TENDENCY_DIM]

    @property
    def relation_slice(self) -> List[float]:
        """Get the relation pattern portion."""
        start = VIRTUE_DIM + TENDENCY_DIM
        return self.vector[start:start + RELATION_DIM]

    @property
    def meta_slice(self) -> List[float]:
        """Get the meta-properties portion."""
        start = VIRTUE_DIM + TENDENCY_DIM + RELATION_DIM
        return self.vector[start:]

    def distance(self, other: "GestaltEmbedding") -> float:
        """Euclidean distance to another embedding."""
        return math.sqrt(sum(
            (a - b) ** 2 for a, b in zip(self.vector, other.vector)
        ))

    def cosine_similarity(self, other: "GestaltEmbedding") -> float:
        """Cosine similarity to another embedding."""
        dot = sum(a * b for a, b in zip(self.vector, other.vector))
        norm_a = math.sqrt(sum(a ** 2 for a in self.vector))
        norm_b = math.sqrt(sum(b ** 2 for b in other.vector))
        if norm_a == 0 or norm_b == 0:
            return 0.0
        return dot / (norm_a * norm_b)


# Archetype to vector encoding
ARCHETYPE_ENCODING = {
    "guardian": [1.0, 0.0, 0.0, 0.0],
    "seeker": [0.0, 1.0, 0.0, 0.0],
    "servant": [0.0, 0.0, 1.0, 0.0],
    "contemplative": [0.0, 0.0, 0.0, 1.0],
    None: [0.25, 0.25, 0.25, 0.25],  # Unknown = uniform
}


def encode_gestalt(gestalt: Gestalt) -> GestaltEmbedding:
    """
    Encode a gestalt into a latent vector.

    The encoding preserves semantic structure:
    - Similar characters → nearby vectors
    - Virtue patterns → virtue dimensions
    - Tendencies → tendency dimensions
    """
    vector = []

    # 1. Virtue activations (19d)
    virtue_ids = [v["id"] for v in VIRTUES]
    for v_id in virtue_ids:
        vector.append(gestalt.virtue_activations.get(v_id, 0.0))

    # 2. Tendencies (10d)
    for t_name in TENDENCY_DEFINITIONS.keys():
        vector.append(gestalt.tendencies.get(t_name, 0.5))

    # 3. Relation patterns (8d) - compressed representation
    # Count relation types
    reinforces_count = 0
    tensions_count = 0
    conditions_count = 0
    total_strength = 0.0

    for rel in gestalt.virtue_relations:
        if rel.relation_type == "reinforces":
            reinforces_count += 1
        elif rel.relation_type == "tensions":
            tensions_count += 1
        elif rel.relation_type == "conditions":
            conditions_count += 1
        total_strength += rel.strength

    total_rels = len(gestalt.virtue_relations) or 1
    vector.extend([
        reinforces_count / total_rels,  # Proportion reinforcing
        tensions_count / total_rels,     # Proportion tensioning
        conditions_count / total_rels,   # Proportion conditioning
        total_strength / total_rels,     # Average strength
        min(1.0, total_rels / 20),       # Relation density
        gestalt.internal_coherence,      # How coherent
        gestalt.stability,               # How stable
        len(gestalt.dominant_traits) / 5,  # Trait concentration
    ])

    # 4. Meta (4d) - archetype encoding
    archetype_vec = ARCHETYPE_ENCODING.get(gestalt.archetype, ARCHETYPE_ENCODING[None])
    # Blend archetype encoding with coherence/stability
    meta = [
        archetype_vec[0] * gestalt.internal_coherence,
        archetype_vec[1] * gestalt.internal_coherence,
        archetype_vec[2] * gestalt.internal_coherence,
        archetype_vec[3] * gestalt.internal_coherence,
    ]
    vector.extend(meta)

    return GestaltEmbedding(agent_id=gestalt.agent_id, vector=vector)


def decode_embedding(embedding: GestaltEmbedding) -> dict:
    """
    Decode an embedding back to interpretable components.

    Note: This is lossy - we can't fully reconstruct the gestalt,
    but we can get approximate values for comparison.
    """
    virtue_ids = [v["id"] for v in VIRTUES]
    tendency_names = list(TENDENCY_DEFINITIONS.keys())

    return {
        "virtue_activations": {
            v_id: embedding.virtue_slice[i]
            for i, v_id in enumerate(virtue_ids)
        },
        "tendencies": {
            t_name: embedding.tendency_slice[i]
            for i, t_name in enumerate(tendency_names)
        },
        "relation_summary": {
            "reinforcement_ratio": embedding.relation_slice[0],
            "tension_ratio": embedding.relation_slice[1],
            "conditioning_ratio": embedding.relation_slice[2],
            "avg_strength": embedding.relation_slice[3],
            "density": embedding.relation_slice[4],
            "coherence": embedding.relation_slice[5],
            "stability": embedding.relation_slice[6],
        },
        "archetype_weights": {
            "guardian": embedding.meta_slice[0],
            "seeker": embedding.meta_slice[1],
            "servant": embedding.meta_slice[2],
            "contemplative": embedding.meta_slice[3],
        },
    }


def interpolate_embeddings(
    emb_a: GestaltEmbedding,
    emb_b: GestaltEmbedding,
    t: float,
) -> GestaltEmbedding:
    """
    Linear interpolation between two embeddings.

    t=0 → emb_a, t=1 → emb_b

    Useful for:
    - Generating intermediate characters
    - Smooth transitions between character states
    """
    vector = [
        a * (1 - t) + b * t
        for a, b in zip(emb_a.vector, emb_b.vector)
    ]
    return GestaltEmbedding(
        agent_id=f"interpolated_{t:.2f}",
        vector=vector,
    )


def find_nearest(
    query: GestaltEmbedding,
    candidates: List[GestaltEmbedding],
    top_k: int = 5,
) -> List[Tuple[GestaltEmbedding, float]]:
    """
    Find the k nearest embeddings to a query.

    Returns list of (embedding, distance) tuples.
    """
    distances = [
        (emb, query.distance(emb))
        for emb in candidates
        if emb.agent_id != query.agent_id
    ]
    distances.sort(key=lambda x: x[1])
    return distances[:top_k]


def cluster_embeddings(
    embeddings: List[GestaltEmbedding],
    n_clusters: int = 4,
) -> List[List[GestaltEmbedding]]:
    """
    Simple k-means-style clustering of embeddings.

    Groups similar characters together.
    """
    if len(embeddings) <= n_clusters:
        return [[e] for e in embeddings]

    # Initialize centroids (simple: use first n embeddings)
    centroids = [e.vector[:] for e in embeddings[:n_clusters]]

    for _ in range(10):  # Iterations
        # Assign to clusters
        clusters = [[] for _ in range(n_clusters)]
        for emb in embeddings:
            # Find nearest centroid
            min_dist = float('inf')
            min_idx = 0
            for i, centroid in enumerate(centroids):
                dist = math.sqrt(sum((a - b) ** 2 for a, b in zip(emb.vector, centroid)))
                if dist < min_dist:
                    min_dist = dist
                    min_idx = i
            clusters[min_idx].append(emb)

        # Update centroids
        for i, cluster in enumerate(clusters):
            if cluster:
                centroids[i] = [
                    sum(e.vector[d] for e in cluster) / len(cluster)
                    for d in range(TOTAL_DIM)
                ]

    return clusters


def add_noise(embedding: GestaltEmbedding, noise_level: float) -> GestaltEmbedding:
    """
    Add Gaussian noise to an embedding.

    This is the "forward process" in diffusion:
    - noise_level=0: original embedding
    - noise_level=1: mostly noise

    Used for diffusion-style generation.
    """
    import random

    noisy_vector = [
        v * (1 - noise_level) + random.gauss(0, 1) * noise_level
        for v in embedding.vector
    ]

    return GestaltEmbedding(
        agent_id=f"{embedding.agent_id}_noisy_{noise_level:.2f}",
        vector=noisy_vector,
    )


def sample_random_embedding() -> GestaltEmbedding:
    """
    Sample a random embedding from the latent space.

    This is pure noise - the starting point for diffusion generation.
    """
    import random

    vector = [random.gauss(0.5, 0.2) for _ in range(TOTAL_DIM)]
    # Clamp to reasonable range
    vector = [max(0.0, min(1.0, v)) for v in vector]

    return GestaltEmbedding(
        agent_id="random_sample",
        vector=vector,
    )
