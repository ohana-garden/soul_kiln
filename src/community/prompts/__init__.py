"""
Community Prompts.

Markdown-based prompts that define agent behavior.

Structure:
- intake.system.md - The intake conversation guide
- {community_name}/
  - agent.system.md - The agent's persona and instructions
  - tool.{tool_name}.md - Guidance for using specific tools
"""

from pathlib import Path

PROMPTS_DIR = Path(__file__).parent


def list_communities() -> list[str]:
    """List available community prompt directories."""
    return [
        d.name for d in PROMPTS_DIR.iterdir()
        if d.is_dir() and not d.name.startswith("_")
    ]


def list_prompts(community_name: str) -> list[str]:
    """List available prompts for a community."""
    community_dir = PROMPTS_DIR / community_name
    if not community_dir.exists():
        return []
    return [f.stem for f in community_dir.glob("*.md")]
