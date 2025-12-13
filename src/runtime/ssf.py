"""
Stored Soul Functions (SSFs).

Executable code stored in the graph. The system boots by reading these
from the database - no hardcoded Python handlers.

SSF Types:
- tool: Callable tool for Agent Zero
- prompt_generator: Dynamic prompt builder
- validator: Input/output validation
- hook: Extension point callback
"""
from typing import Optional, Dict, Any, List, Callable
from datetime import datetime
from uuid import uuid4
import json

from src.graph import get_client


class SSFRegistry:
    """Registry for Stored Soul Functions loaded from graph."""

    def __init__(self):
        self.client = get_client()
        self._functions: Dict[str, Dict[str, Any]] = {}
        self._loaded = False

    def load_all(self):
        """Load all SSFs from the graph into memory."""
        query = """
        MATCH (s:SSF)
        RETURN s
        """
        result = self.client.query(query)

        for row in result:
            if row[0]:
                ssf = dict(row[0].properties)
                self._functions[ssf["id"]] = ssf

        self._loaded = True
        return len(self._functions)

    def get(self, ssf_id: str) -> Optional[Dict[str, Any]]:
        """Get an SSF by ID."""
        if not self._loaded:
            self.load_all()
        return self._functions.get(ssf_id)

    def get_by_type(self, ssf_type: str) -> List[Dict[str, Any]]:
        """Get all SSFs of a given type."""
        if not self._loaded:
            self.load_all()
        return [s for s in self._functions.values() if s.get("ssf_type") == ssf_type]

    def execute(self, ssf_id: str, context: Dict[str, Any]) -> Any:
        """
        Execute an SSF with the given context.

        Args:
            ssf_id: ID of the SSF to execute
            context: Execution context (agent, message, etc.)

        Returns:
            Execution result
        """
        ssf = self.get(ssf_id)
        if not ssf:
            raise ValueError(f"SSF not found: {ssf_id}")

        ssf_type = ssf.get("ssf_type")
        code = ssf.get("code", "")
        prompt_template = ssf.get("prompt_template", "")

        if ssf_type == "tool":
            return self._execute_tool(ssf, context)
        elif ssf_type == "prompt_generator":
            return self._execute_prompt_generator(ssf, context)
        elif ssf_type == "validator":
            return self._execute_validator(ssf, context)
        elif ssf_type == "hook":
            return self._execute_hook(ssf, context)
        else:
            raise ValueError(f"Unknown SSF type: {ssf_type}")

    def _execute_tool(self, ssf: Dict[str, Any], context: Dict[str, Any]) -> Dict[str, Any]:
        """Execute a tool SSF."""
        # Tools return a prompt for the LLM to process
        prompt_template = ssf.get("prompt_template", "")

        # Substitute context variables into the prompt
        result_prompt = self._render_template(prompt_template, context)

        return {
            "type": "tool_result",
            "ssf_id": ssf["id"],
            "prompt": result_prompt,
            "requires_llm": ssf.get("requires_llm", True),
        }

    def _execute_prompt_generator(self, ssf: Dict[str, Any], context: Dict[str, Any]) -> str:
        """Execute a prompt generator SSF."""
        template = ssf.get("prompt_template", "")
        return self._render_template(template, context)

    def _execute_validator(self, ssf: Dict[str, Any], context: Dict[str, Any]) -> Dict[str, Any]:
        """Execute a validator SSF."""
        rules = ssf.get("rules", "")
        # Parse rules as simple conditions
        # Format: "field:condition:value" per line

        errors = []
        input_data = context.get("input", {})

        for rule in rules.split("\n"):
            rule = rule.strip()
            if not rule or rule.startswith("#"):
                continue

            parts = rule.split(":")
            if len(parts) >= 3:
                field, condition, value = parts[0], parts[1], ":".join(parts[2:])
                field_value = input_data.get(field)

                if condition == "required" and not field_value:
                    errors.append(f"{field} is required")
                elif condition == "min_length" and len(str(field_value or "")) < int(value):
                    errors.append(f"{field} must be at least {value} characters")
                elif condition == "pattern" and field_value:
                    import re
                    if not re.match(value, str(field_value)):
                        errors.append(f"{field} does not match required pattern")

        return {
            "valid": len(errors) == 0,
            "errors": errors,
        }

    def _execute_hook(self, ssf: Dict[str, Any], context: Dict[str, Any]) -> Dict[str, Any]:
        """Execute a hook SSF."""
        hook_type = ssf.get("hook_type", "")
        action = ssf.get("action", "")

        # Hooks modify context or perform side effects
        result = {"hook_executed": True, "hook_type": hook_type}

        if action == "log":
            message = ssf.get("message", "Hook executed")
            result["log"] = self._render_template(message, context)
        elif action == "modify_context":
            modifications = ssf.get("modifications", "{}")
            try:
                mods = json.loads(modifications)
                result["context_modifications"] = mods
            except json.JSONDecodeError:
                pass
        elif action == "check_taboo":
            # Run taboo check against context
            result["taboo_check"] = self._check_taboos(context)

        return result

    def _render_template(self, template: str, context: Dict[str, Any]) -> str:
        """Render a template with context variables."""
        result = template

        # Handle {{variable}} syntax
        for key, value in context.items():
            if isinstance(value, (str, int, float, bool)):
                result = result.replace(f"{{{{{key}}}}}", str(value))
            elif isinstance(value, dict):
                # Allow nested access like {{agent.name}}
                for sub_key, sub_value in value.items():
                    result = result.replace(f"{{{{{key}.{sub_key}}}}}", str(sub_value))

        return result

    def _check_taboos(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """Check for taboo violations in context."""
        message = context.get("message", "")
        agent_id = context.get("agent_id", "")

        # Get taboos from graph
        query = """
        MATCH (a:AgentInstance {id: $agent_id})-[:IS_TYPE]->(t:AgentType)
        MATCH (t)-[:OBSERVES_TABOO]->(tb:Taboo)
        RETURN tb
        """
        result = self.client.query(query, {"agent_id": agent_id})

        violations = []
        message_lower = message.lower()

        for row in result:
            if row[0]:
                taboo = dict(row[0].properties)
                patterns = taboo.get("patterns", "").split(",")
                for pattern in patterns:
                    pattern = pattern.strip().lower()
                    if pattern and pattern in message_lower:
                        violations.append({
                            "taboo_id": taboo["id"],
                            "taboo_name": taboo.get("name", ""),
                            "matched_pattern": pattern,
                        })

        return {
            "violated": len(violations) > 0,
            "violations": violations,
        }


def create_ssf(
    ssf_id: str,
    name: str,
    ssf_type: str,
    description: str = "",
    prompt_template: str = "",
    code: str = "",
    rules: str = "",
    hook_type: str = "",
    action: str = "",
    message: str = "",
    modifications: str = "",
    requires_llm: bool = True,
    metadata: Dict[str, Any] = None,
) -> str:
    """
    Create a new SSF in the graph.

    Args:
        ssf_id: Unique identifier
        name: Human-readable name
        ssf_type: tool, prompt_generator, validator, or hook
        description: What this SSF does
        prompt_template: Template for prompt-based SSFs
        code: Optional Python code (for future use)
        rules: Validation rules (for validators)
        hook_type: Type of hook (for hooks)
        action: Action to perform (for hooks)
        message: Message template (for log hooks)
        modifications: JSON modifications (for modify_context hooks)
        requires_llm: Whether execution requires LLM call
        metadata: Additional metadata

    Returns:
        SSF ID
    """
    client = get_client()
    now = datetime.utcnow().isoformat()

    query = """
    MERGE (s:SSF {id: $id})
    ON CREATE SET
        s.name = $name,
        s.ssf_type = $ssf_type,
        s.description = $description,
        s.prompt_template = $prompt_template,
        s.code = $code,
        s.rules = $rules,
        s.hook_type = $hook_type,
        s.action = $action,
        s.message = $message,
        s.modifications = $modifications,
        s.requires_llm = $requires_llm,
        s.created_at = datetime($now)
    ON MATCH SET
        s.name = $name,
        s.ssf_type = $ssf_type,
        s.description = $description,
        s.prompt_template = $prompt_template,
        s.code = $code,
        s.rules = $rules,
        s.hook_type = $hook_type,
        s.action = $action,
        s.message = $message,
        s.modifications = $modifications,
        s.requires_llm = $requires_llm
    RETURN s.id as id
    """

    client.execute(query, {
        "id": ssf_id,
        "name": name,
        "ssf_type": ssf_type,
        "description": description,
        "prompt_template": prompt_template,
        "code": code,
        "rules": rules,
        "hook_type": hook_type,
        "action": action,
        "message": message,
        "modifications": modifications,
        "requires_llm": requires_llm,
        "now": now,
    })

    return ssf_id


def link_ssf_to_agent_type(ssf_id: str, agent_type_id: str):
    """Link an SSF to an agent type."""
    client = get_client()
    now = datetime.utcnow().isoformat()

    query = """
    MATCH (s:SSF {id: $ssf_id})
    MATCH (t:AgentType {id: $agent_type_id})
    MERGE (t)-[r:HAS_SSF]->(s)
    ON CREATE SET r.t_valid = datetime($now), r.t_invalid = null
    """
    client.execute(query, {
        "ssf_id": ssf_id,
        "agent_type_id": agent_type_id,
        "now": now,
    })


# Singleton registry
_registry: Optional[SSFRegistry] = None


def get_ssf_registry() -> SSFRegistry:
    """Get the singleton SSF registry."""
    global _registry
    if _registry is None:
        _registry = SSFRegistry()
    return _registry
