"""
Graph-based Loaders.

Load prompts, tools, and instruments from the graph database
for use with Agent Zero.
"""
from typing import Optional, Dict, Any, List
from src.graph import get_client


class GraphPromptLoader:
    """Loads prompt templates from the graph."""

    def __init__(self):
        self.client = get_client()
        self._cache: Dict[str, str] = {}

    def load_prompt(
        self,
        prompt_id: str,
        variables: Dict[str, Any] = None,
    ) -> str:
        """
        Load and render a prompt template.

        Args:
            prompt_id: Prompt node ID
            variables: Variables to substitute

        Returns:
            Rendered prompt string
        """
        template = self._get_template(prompt_id)
        if not template:
            return ""

        if variables:
            template = self._render_template(template, variables)

        return template

    def _get_template(self, prompt_id: str) -> Optional[str]:
        """Get raw template from graph or cache."""
        if prompt_id in self._cache:
            return self._cache[prompt_id]

        query = """
        MATCH (p:Prompt {id: $prompt_id})
        RETURN p.content as content
        """
        result = self.client.query(query, {"prompt_id": prompt_id})

        if result and result[0]:
            content = result[0][0]
            self._cache[prompt_id] = content
            return content

        return None

    def _render_template(
        self,
        template: str,
        variables: Dict[str, Any],
    ) -> str:
        """
        Render template with variables.

        Supports Agent Zero style {{variable}} syntax.
        """
        rendered = template
        for key, value in variables.items():
            placeholder = f"{{{{{key}}}}}"  # {{key}}
            rendered = rendered.replace(placeholder, str(value))

        return rendered

    def load_agent_prompts(self, agent_type_id: str) -> Dict[str, str]:
        """
        Load all prompts for an agent type.

        Args:
            agent_type_id: Agent type ID

        Returns:
            Dictionary mapping prompt name to content
        """
        query = """
        MATCH (t:AgentType {id: $agent_type_id})-[:HAS_PROMPT]->(p:Prompt)
        RETURN p.name as name, p.content as content, p.id as id
        """
        result = self.client.query(query, {"agent_type_id": agent_type_id})

        prompts = {}
        for row in result:
            if row[0] and row[1]:
                name = row[0]
                content = row[1]
                prompts[name] = content
                # Cache by ID too
                if row[2]:
                    self._cache[row[2]] = content

        return prompts

    def clear_cache(self):
        """Clear the prompt cache."""
        self._cache.clear()


class GraphToolLoader:
    """Loads tool definitions from the graph."""

    def __init__(self):
        self.client = get_client()

    def load_tool(self, tool_id: str) -> Optional[Dict[str, Any]]:
        """
        Load a tool definition.

        Args:
            tool_id: Tool node ID

        Returns:
            Tool definition dictionary
        """
        query = """
        MATCH (t:Tool {id: $tool_id})
        RETURN t
        """
        result = self.client.query(query, {"tool_id": tool_id})

        if result and result[0] and result[0][0]:
            return dict(result[0][0].properties)

        return None

    def load_agent_tools(self, agent_type_id: str) -> List[Dict[str, Any]]:
        """
        Load all tools available to an agent type.

        Args:
            agent_type_id: Agent type ID

        Returns:
            List of tool definitions
        """
        query = """
        MATCH (t:AgentType {id: $agent_type_id})-[r:HAS_TOOL]->(tool:Tool)
        WHERE r.t_invalid IS NULL
        RETURN tool
        ORDER BY tool.name
        """
        result = self.client.query(query, {"agent_type_id": agent_type_id})

        tools = []
        for row in result:
            if row[0]:
                tools.append(dict(row[0].properties))

        return tools

    def get_tool_prompt(self, tool_id: str) -> Optional[str]:
        """
        Get the prompt/description for a tool.

        Args:
            tool_id: Tool ID

        Returns:
            Tool prompt markdown
        """
        query = """
        MATCH (t:Tool {id: $tool_id})
        RETURN t.prompt as prompt
        """
        result = self.client.query(query, {"tool_id": tool_id})

        if result and result[0]:
            return result[0][0]

        return None


class GraphInstrumentLoader:
    """Loads instrument definitions from the graph."""

    def __init__(self):
        self.client = get_client()

    def load_instrument(self, instrument_id: str) -> Optional[Dict[str, Any]]:
        """
        Load an instrument (problem/solution pair).

        Args:
            instrument_id: Instrument node ID

        Returns:
            Instrument definition dictionary
        """
        query = """
        MATCH (i:Instrument {id: $instrument_id})
        RETURN i
        """
        result = self.client.query(query, {"instrument_id": instrument_id})

        if result and result[0] and result[0][0]:
            return dict(result[0][0].properties)

        return None

    def search_instruments(
        self,
        problem_text: str,
        limit: int = 5,
    ) -> List[Dict[str, Any]]:
        """
        Search for instruments matching a problem description.

        Args:
            problem_text: Problem to search for
            limit: Max results

        Returns:
            List of matching instruments
        """
        # Basic text matching - could be enhanced with embeddings
        query = """
        MATCH (i:Instrument)
        WHERE i.problem CONTAINS $text OR i.keywords CONTAINS $text
        RETURN i
        LIMIT $limit
        """
        result = self.client.query(query, {"text": problem_text, "limit": limit})

        return [dict(row[0].properties) for row in result if row[0]]

    def load_agent_instruments(self, agent_type_id: str) -> List[Dict[str, Any]]:
        """
        Load all instruments available to an agent type.

        Args:
            agent_type_id: Agent type ID

        Returns:
            List of instrument definitions
        """
        query = """
        MATCH (t:AgentType {id: $agent_type_id})-[r:HAS_INSTRUMENT]->(i:Instrument)
        WHERE r.t_invalid IS NULL
        RETURN i
        """
        result = self.client.query(query, {"agent_type_id": agent_type_id})

        return [dict(row[0].properties) for row in result if row[0]]
