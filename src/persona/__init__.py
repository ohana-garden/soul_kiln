"""
Persona module for KG-Persona compilation.

Compiles agent topology/gestalt into PersonaCapsules suitable for
LLM conditioning. Implements the "persona as structured, queryable state"
pattern from GraphRAG persona research.

Key concepts:
- Persona is data first, prose second
- Capsule is ephemeral (regenerated per context); graph is durable
- Hard boundaries filter before soft preferences rank
- Community patterns provide population-level defaults
- Explicit uncertainties enable honest reasoning
"""

from .capsule import (
    compile_persona_capsule,
    compile_for_situation,
    PersonaCompiler,
)
from .community import (
    compute_archetype_patterns,
    get_community_patterns,
    ArchetypeStatistics,
)
from .temporal import (
    TemporalFactStore,
    create_fact,
    update_fact,
    expire_fact,
)

__all__ = [
    # Capsule compilation
    "compile_persona_capsule",
    "compile_for_situation",
    "PersonaCompiler",
    # Community patterns
    "compute_archetype_patterns",
    "get_community_patterns",
    "ArchetypeStatistics",
    # Temporal facts
    "TemporalFactStore",
    "create_fact",
    "update_fact",
    "expire_fact",
]
