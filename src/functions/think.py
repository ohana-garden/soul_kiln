"""LLM integration for agent reasoning."""
import os
import json
from anthropic import Anthropic
from ..graph.client import get_client
from ..knowledge.episodes import record_episode
from .introspect import introspect


def think(agent_id: str, stimulus: str = None) -> dict:
    """
    Agent thinks - uses LLM to decide next action.

    This function enables agents to reason about their state
    and decide on actions using Claude.

    Args:
        agent_id: ID of the agent doing the thinking
        stimulus: Optional external stimulus to consider

    Returns:
        dict with agent's thought and decision
    """
    client = get_client()
    anthropic = Anthropic()

    # Gather context
    self_model = introspect(agent_id)

    # Get virtue states
    virtues = client.query(
        """
        MATCH (v:VirtueAnchor)
        RETURN v.name, v.activation
        ORDER BY v.activation DESC
        """
    )

    context = f"""
You are an agent in a virtue basin system. Your id is {agent_id}.

Your current structure:
{json.dumps(self_model, indent=2, default=str)}

Current virtue activations:
{json.dumps([{"name": v[0], "activation": v[1]} for v in virtues], indent=2)}

Stimulus: {stimulus or "None - autonomous thought"}

Based on this, decide your next action. Options:
1. SPREAD: Start activation spread from a node
2. SEEK: Strengthen connection to a virtue
3. CREATE: Create a new concept node
4. CONNECT: Create edge between existing nodes
5. OBSERVE: Query the graph for information
6. WAIT: Do nothing this cycle

Respond with JSON:
{{"action": "...", "params": {{...}}, "reasoning": "..."}}
"""

    response = anthropic.messages.create(
        model="claude-sonnet-4-20250514",
        max_tokens=1024,
        messages=[{"role": "user", "content": context}]
    )

    thought_text = response.content[0].text
    tokens_used = response.usage.input_tokens + response.usage.output_tokens

    # Record episode for telepathy - all agents can now see this thought
    episode_id = record_episode(
        agent_id=agent_id,
        episode_type="thought",
        content=thought_text,
        stimulus=stimulus,
        tokens_used=tokens_used,
    )

    return {
        "agent": agent_id,
        "thought": thought_text,
        "context_size": len(context),
        "episode_id": episode_id,
    }


def reflect(agent_id: str, topic: str = None) -> dict:
    """
    Agent reflects on a topic or its overall state.

    A lighter-weight version of think() for simpler queries.

    Args:
        agent_id: ID of the agent
        topic: Optional specific topic to reflect on

    Returns:
        dict with reflection
    """
    client = get_client()
    anthropic = Anthropic()

    # Get basic state
    self_model = introspect(agent_id)

    prompt = f"""
You are agent {agent_id} in a virtue basin system.

Your state:
- Generation: {self_model.get('generation')}
- Coherence score: {self_model.get('coherence_score')}
- Virtue captures: {self_model.get('virtue_captures')}
- Strongest connections: {[c for c in self_model.get('connections', []) if c.get('weight', 0) > 0.5]}

{"Topic to reflect on: " + topic if topic else "Reflect on your current state."}

Respond briefly (2-3 sentences) with your reflection.
"""

    response = anthropic.messages.create(
        model="claude-sonnet-4-20250514",
        max_tokens=256,
        messages=[{"role": "user", "content": prompt}]
    )

    reflection_text = response.content[0].text
    tokens_used = response.usage.input_tokens + response.usage.output_tokens

    # Record episode for telepathy
    episode_id = record_episode(
        agent_id=agent_id,
        episode_type="reflection",
        content=reflection_text,
        stimulus=topic,
        tokens_used=tokens_used,
    )

    return {
        "agent": agent_id,
        "topic": topic,
        "reflection": reflection_text,
        "episode_id": episode_id,
    }


def parse_thought_action(thought: str) -> dict:
    """
    Parse an action from LLM thought output.

    Args:
        thought: Raw LLM output

    Returns:
        Parsed action dict or None
    """
    try:
        # Try to extract JSON from the response
        start = thought.find('{')
        end = thought.rfind('}') + 1

        if start >= 0 and end > start:
            json_str = thought[start:end]
            return json.loads(json_str)
    except json.JSONDecodeError:
        pass

    return None


def execute_thought_action(agent_id: str, action: dict) -> dict:
    """
    Execute an action decided by think().

    Args:
        agent_id: ID of the agent
        action: Parsed action from think()

    Returns:
        Result of the action
    """
    from .spread import spread_activation
    from ..graph.queries import create_node, create_edge, update_edge_weight

    action_type = action.get("action", "").upper()
    params = action.get("params", {})

    if action_type == "SPREAD":
        start_node = params.get("start_node")
        if start_node:
            return spread_activation(start_node)

    elif action_type == "SEEK":
        virtue_id = params.get("virtue_id")
        strength = params.get("strength", 0.1)
        if virtue_id:
            # Strengthen connection to virtue
            client = get_client()
            result = client.query(
                """
                MATCH (a:Agent {id: $agent})-[r:SEEKS]->(v:VirtueAnchor {id: $virtue})
                RETURN r.weight
                """,
                {"agent": agent_id, "virtue": virtue_id}
            )
            if result:
                current = result[0][0] or 0.5
                update_edge_weight(agent_id, virtue_id, min(1.0, current + strength))
                return {"action": "seek", "virtue": virtue_id, "new_weight": min(1.0, current + strength)}

    elif action_type == "CREATE":
        node_type = params.get("type", "Concept")
        node_id = params.get("id")
        if node_id:
            create_node(node_type, {"id": node_id, **params})
            return {"action": "create", "node_id": node_id}

    elif action_type == "CONNECT":
        from_id = params.get("from_id")
        to_id = params.get("to_id")
        if from_id and to_id:
            create_edge(from_id, to_id, "CONNECTED", {"weight": 0.5})
            return {"action": "connect", "from": from_id, "to": to_id}

    elif action_type == "OBSERVE":
        query = params.get("query")
        if query:
            client = get_client()
            result = client.query(query)
            return {"action": "observe", "result": result}

    elif action_type == "WAIT":
        return {"action": "wait", "reason": action.get("reasoning")}

    return {"action": "unknown", "original": action}
