"""
Prompt Loading Utilities.

Loads and processes markdown prompts for intake and agent personas.
"""

import logging
import re
from pathlib import Path
from typing import Any

logger = logging.getLogger(__name__)

# Base path for prompts
PROMPTS_DIR = Path(__file__).parent.parent / "prompts"


def load_prompt(prompt_path: str) -> str:
    """
    Load a prompt from file.

    Args:
        prompt_path: Relative path from prompts directory (e.g., "intake.system.md")

    Returns:
        Prompt content as string
    """
    full_path = PROMPTS_DIR / prompt_path
    if not full_path.exists():
        logger.warning(f"Prompt not found: {full_path}")
        return ""

    with open(full_path) as f:
        return f.read()


def load_community_prompts(community_name: str) -> dict[str, str]:
    """
    Load all prompts for a community.

    Args:
        community_name: Community name (e.g., "grant_getter")

    Returns:
        Dict of prompt_name -> content
    """
    community_dir = PROMPTS_DIR / community_name
    if not community_dir.exists():
        logger.warning(f"Community prompts not found: {community_dir}")
        return {}

    prompts = {}
    for prompt_file in community_dir.glob("*.md"):
        prompt_name = prompt_file.stem  # e.g., "agent.system" from "agent.system.md"
        with open(prompt_file) as f:
            prompts[prompt_name] = f.read()

    return prompts


def render_prompt(template: str, context: dict[str, Any]) -> str:
    """
    Render a prompt template with context.

    Supports simple Handlebars-style templating:
    - {{variable}} - replaced with value
    - {{#if variable}}...{{/if}} - conditional blocks
    - {{context.nested}} - nested access

    Args:
        template: Prompt template string
        context: Context dict for rendering

    Returns:
        Rendered prompt
    """
    result = template

    # Handle conditionals first: {{#if variable}}content{{/if}}
    def replace_conditional(match):
        var_name = match.group(1).strip()
        content = match.group(2)

        # Check if variable is truthy
        value = _get_nested(context, var_name)
        if value:
            # Recursively render the content
            return render_prompt(content, context)
        return ""

    conditional_pattern = r'\{\{#if\s+([^}]+)\}\}(.*?)\{\{/if\}\}'
    result = re.sub(conditional_pattern, replace_conditional, result, flags=re.DOTALL)

    # Handle simple variable replacement: {{variable}}
    def replace_variable(match):
        var_name = match.group(1).strip()
        value = _get_nested(context, var_name)
        return str(value) if value is not None else ""

    variable_pattern = r'\{\{([^#/][^}]*)\}\}'
    result = re.sub(variable_pattern, replace_variable, result)

    return result


def _get_nested(data: dict, path: str) -> Any:
    """Get a nested value from a dict using dot notation."""
    keys = path.split(".")
    value = data

    for key in keys:
        if isinstance(value, dict) and key in value:
            value = value[key]
        else:
            return None

    return value


def get_intake_prompt() -> str:
    """Get the intake system prompt."""
    return load_prompt("intake.system.md")


def get_agent_prompt(community_name: str, context: dict[str, Any] | None = None) -> str:
    """
    Get the rendered agent system prompt for a community.

    Args:
        community_name: Community name (e.g., "grant_getter")
        context: Context for rendering (org info, preferences, etc.)

    Returns:
        Rendered system prompt
    """
    prompts = load_community_prompts(community_name)
    template = prompts.get("agent.system", "")

    if context:
        return render_prompt(template, context)
    return template


def get_tool_prompts(community_name: str) -> dict[str, str]:
    """
    Get all tool guidance prompts for a community.

    Args:
        community_name: Community name

    Returns:
        Dict of tool_name -> guidance content
    """
    prompts = load_community_prompts(community_name)
    return {
        name.replace("tool.", ""): content
        for name, content in prompts.items()
        if name.startswith("tool.")
    }
