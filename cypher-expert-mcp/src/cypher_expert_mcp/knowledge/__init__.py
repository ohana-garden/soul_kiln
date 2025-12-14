"""Knowledge base for Cypher query generation."""

from pathlib import Path

KNOWLEDGE_DIR = Path(__file__).parent


def load_reference_docs() -> dict[str, str]:
    """Load all reference documentation."""
    docs = {}
    for md_file in KNOWLEDGE_DIR.glob("*.md"):
        docs[md_file.stem] = md_file.read_text()
    return docs


def get_cypher_reference() -> str:
    """Get the Cypher reference documentation."""
    path = KNOWLEDGE_DIR / "cypher_reference.md"
    return path.read_text() if path.exists() else ""


def get_optimization_patterns() -> str:
    """Get optimization patterns documentation."""
    path = KNOWLEDGE_DIR / "optimization_patterns.md"
    return path.read_text() if path.exists() else ""


def get_falkordb_specifics() -> str:
    """Get FalkorDB-specific documentation."""
    path = KNOWLEDGE_DIR / "falkordb_specifics.md"
    return path.read_text() if path.exists() else ""


def get_common_queries() -> str:
    """Get common query examples."""
    path = KNOWLEDGE_DIR / "common_queries.md"
    return path.read_text() if path.exists() else ""
