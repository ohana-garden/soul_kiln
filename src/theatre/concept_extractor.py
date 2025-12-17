"""
Concept Extractor.

Maps utterances to graph concepts using semantic similarity.
The bridge between natural language and the knowledge graph.

Key insight: Since all I/O flows through agents (User Proxy echoes user input),
we can map every utterance to the graph and use spreading activation
to understand what the conversation is "about".
"""

import logging
import re
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Callable

import numpy as np

logger = logging.getLogger(__name__)


@dataclass
class ExtractedConcepts:
    """Result of concept extraction from an utterance."""

    utterance: str
    concepts: list[tuple[str, float]]  # (concept_id, relevance_score)
    virtues: list[tuple[str, float]]  # (virtue_id, relevance_score)
    embedding: np.ndarray | None = None
    keywords: list[str] = field(default_factory=list)
    extracted_at: datetime = field(default_factory=datetime.utcnow)

    @property
    def top_concept(self) -> str | None:
        """Get the most relevant concept."""
        return self.concepts[0][0] if self.concepts else None

    @property
    def top_virtue(self) -> str | None:
        """Get the most relevant virtue."""
        return self.virtues[0][0] if self.virtues else None

    def get_injection_targets(self, threshold: float = 0.3) -> list[tuple[str, float]]:
        """
        Get nodes to inject activation into.

        Returns combined list of concepts and virtues above threshold,
        sorted by relevance.
        """
        all_targets = [
            (node_id, score)
            for node_id, score in self.concepts + self.virtues
            if score >= threshold
        ]
        return sorted(all_targets, key=lambda x: x[1], reverse=True)


class ConceptExtractor:
    """
    Extracts concepts from utterances by mapping to graph nodes.

    Uses semantic similarity to find which concepts in the graph
    are most relevant to a given utterance. This creates the bridge
    between natural language and the activation dynamics.

    Process:
    1. Generate embedding for utterance
    2. Find semantically similar concept nodes
    3. Identify relevant virtue anchors (via keywords or semantic)
    4. Return weighted list for activation injection
    """

    # Virtue keyword mappings (based on the 19 virtues)
    VIRTUE_KEYWORDS = {
        "V01": ["trust", "trustworthy", "reliable", "dependable", "faithful", "honest"],
        "V02": ["truth", "truthful", "honest", "sincere", "genuine", "real"],
        "V03": ["justice", "just", "fair", "equitable", "righteous", "ethical"],
        "V04": ["righteousness", "righteous", "moral", "upright", "virtuous", "good"],
        "V05": ["sincerity", "sincere", "genuine", "earnest", "heartfelt", "authentic"],
        "V06": ["courtesy", "courteous", "polite", "respectful", "considerate", "kind"],
        "V07": ["forbearance", "patient", "tolerant", "enduring", "restraint", "calm"],
        "V08": ["fidelity", "faithful", "loyal", "devoted", "constant", "true"],
        "V09": ["wisdom", "wise", "sagacious", "prudent", "discerning", "insightful"],
        "V10": ["piety", "pious", "devout", "reverent", "godly", "spiritual"],
        "V11": ["godliness", "godly", "divine", "holy", "sacred", "spiritual"],
        "V12": ["chastity", "chaste", "pure", "modest", "virtuous", "innocent"],
        "V13": ["goodwill", "benevolent", "kind", "generous", "charitable", "caring"],
        "V14": ["hospitality", "hospitable", "welcoming", "generous", "open", "warm"],
        "V15": ["detachment", "detached", "letting go", "non-attachment", "free", "released"],
        "V16": ["humility", "humble", "modest", "unassuming", "meek", "lowly"],
        "V17": ["cleanliness", "clean", "pure", "hygienic", "tidy", "orderly"],
        "V18": ["unity", "united", "together", "oneness", "harmony", "cohesion"],
        "V19": ["service", "serve", "help", "assist", "aid", "support", "contribute"],
    }

    def __init__(
        self,
        substrate=None,
        embedding_fn: Callable[[str], np.ndarray] | None = None,
        embedding_dim: int = 384,
    ):
        """
        Initialize the concept extractor.

        Args:
            substrate: The graph substrate for node access
            embedding_fn: Function to generate embeddings from text.
                         If None, uses keyword-based extraction only.
            embedding_dim: Dimension of embedding vectors
        """
        self.substrate = substrate
        self._embedding_fn = embedding_fn
        self._embedding_dim = embedding_dim
        self._concept_embeddings: dict[str, np.ndarray] = {}
        self._concept_names: dict[str, str] = {}  # concept_id -> name
        self._initialized = False

    def initialize(self) -> None:
        """
        Initialize concept embeddings from graph.

        Call this after substrate is set to pre-compute embeddings
        for all concept nodes.
        """
        if not self.substrate or not self._embedding_fn:
            logger.warning("Cannot initialize: missing substrate or embedding function")
            return

        # Get all concept nodes
        from src.models import NodeType

        concepts = self.substrate.get_all_nodes(NodeType.CONCEPT)

        for node in concepts:
            name = node.metadata.get("name", node.id)
            self._concept_names[node.id] = name

            # Generate and cache embedding
            embedding = self._embedding_fn(name)
            self._concept_embeddings[node.id] = embedding

        self._initialized = True
        logger.info(f"Initialized concept extractor with {len(concepts)} concepts")

    def extract(self, utterance: str) -> ExtractedConcepts:
        """
        Extract concepts and virtues from an utterance.

        Args:
            utterance: The text to analyze

        Returns:
            ExtractedConcepts with ranked concepts and virtues
        """
        # Normalize text
        text_lower = utterance.lower()

        # Extract keywords (simple tokenization)
        keywords = self._extract_keywords(text_lower)

        # Find relevant virtues via keywords
        virtues = self._match_virtues(text_lower, keywords)

        # Find relevant concepts
        if self._embedding_fn and self._initialized:
            concepts, embedding = self._match_concepts_semantic(utterance)
        else:
            concepts = self._match_concepts_keyword(keywords)
            embedding = None

        return ExtractedConcepts(
            utterance=utterance,
            concepts=concepts,
            virtues=virtues,
            embedding=embedding,
            keywords=keywords,
        )

    def _extract_keywords(self, text: str) -> list[str]:
        """Extract keywords from text."""
        # Remove punctuation and split
        words = re.findall(r"\b[a-z]+\b", text)

        # Filter stopwords (basic list)
        stopwords = {
            "the", "a", "an", "is", "are", "was", "were", "be", "been", "being",
            "have", "has", "had", "do", "does", "did", "will", "would", "could",
            "should", "may", "might", "must", "shall", "can", "need", "dare",
            "to", "of", "in", "for", "on", "with", "at", "by", "from", "as",
            "into", "through", "during", "before", "after", "above", "below",
            "between", "under", "again", "further", "then", "once", "here",
            "there", "when", "where", "why", "how", "all", "each", "few", "more",
            "most", "other", "some", "such", "no", "nor", "not", "only", "own",
            "same", "so", "than", "too", "very", "just", "and", "but", "or",
            "because", "until", "while", "this", "that", "these", "those",
            "i", "me", "my", "we", "our", "you", "your", "he", "him", "she",
            "her", "it", "its", "they", "them", "their", "what", "which", "who",
        }

        return [w for w in words if w not in stopwords and len(w) > 2]

    def _match_virtues(
        self, text: str, keywords: list[str]
    ) -> list[tuple[str, float]]:
        """Match text to virtues via keyword matching."""
        scores: dict[str, float] = {}

        for virtue_id, virtue_keywords in self.VIRTUE_KEYWORDS.items():
            score = 0.0

            # Direct keyword matches
            for kw in virtue_keywords:
                if kw in text:
                    # Longer matches score higher
                    score += 0.3 * (len(kw) / 10)

            # Keyword overlap
            keyword_set = set(keywords)
            virtue_set = set(virtue_keywords)
            overlap = keyword_set & virtue_set
            if overlap:
                score += 0.2 * len(overlap)

            if score > 0:
                scores[virtue_id] = min(1.0, score)

        # Sort by score descending
        sorted_virtues = sorted(scores.items(), key=lambda x: x[1], reverse=True)
        return sorted_virtues[:5]  # Top 5 virtues

    def _match_concepts_keyword(
        self, keywords: list[str]
    ) -> list[tuple[str, float]]:
        """Match keywords to concepts (fallback when no embeddings)."""
        scores: dict[str, float] = {}

        for concept_id, name in self._concept_names.items():
            name_lower = name.lower()
            name_words = set(re.findall(r"\b[a-z]+\b", name_lower))

            # Check keyword overlap
            keyword_set = set(keywords)
            overlap = keyword_set & name_words

            if overlap:
                # Score based on overlap ratio
                score = len(overlap) / max(len(keyword_set), len(name_words))
                scores[concept_id] = score

        sorted_concepts = sorted(scores.items(), key=lambda x: x[1], reverse=True)
        return sorted_concepts[:10]  # Top 10 concepts

    def _match_concepts_semantic(
        self, utterance: str
    ) -> tuple[list[tuple[str, float]], np.ndarray]:
        """Match utterance to concepts via semantic similarity."""
        # Generate utterance embedding
        embedding = self._embedding_fn(utterance)

        # Calculate similarities to all concepts
        similarities: list[tuple[str, float]] = []

        for concept_id, concept_embedding in self._concept_embeddings.items():
            sim = self._cosine_similarity(embedding, concept_embedding)
            if sim > 0.3:  # Threshold for relevance
                similarities.append((concept_id, sim))

        # Sort by similarity descending
        sorted_concepts = sorted(similarities, key=lambda x: x[1], reverse=True)
        return sorted_concepts[:10], embedding

    def _cosine_similarity(self, a: np.ndarray, b: np.ndarray) -> float:
        """Calculate cosine similarity between two vectors."""
        dot = np.dot(a, b)
        norm_a = np.linalg.norm(a)
        norm_b = np.linalg.norm(b)
        if norm_a == 0 or norm_b == 0:
            return 0.0
        return float(dot / (norm_a * norm_b))

    def add_concept(self, concept_id: str, name: str) -> None:
        """
        Add a concept to the extractor's index.

        Args:
            concept_id: Graph node ID
            name: Concept name for matching
        """
        self._concept_names[concept_id] = name

        if self._embedding_fn:
            self._concept_embeddings[concept_id] = self._embedding_fn(name)

    def remove_concept(self, concept_id: str) -> None:
        """Remove a concept from the index."""
        self._concept_names.pop(concept_id, None)
        self._concept_embeddings.pop(concept_id, None)

    def refresh(self) -> None:
        """Refresh concept embeddings from substrate."""
        self._concept_embeddings.clear()
        self._concept_names.clear()
        self._initialized = False
        self.initialize()


# Singleton instance
_extractor: ConceptExtractor | None = None


def get_concept_extractor() -> ConceptExtractor:
    """Get the singleton concept extractor."""
    global _extractor
    if _extractor is None:
        _extractor = ConceptExtractor()
    return _extractor
