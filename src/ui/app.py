"""
Soul Kiln - AI Generated UI.

Every pixel is decided by the AI based on conversation context.
Run with: streamlit run src/ui/app.py
"""

import os
import sys

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

import json
import streamlit as st

from src.ui.generator import UIGenerator, UISpec, get_ui_generator
from src.ui.renderer import StreamlitRenderer, get_renderer
from src.ui.theatre_bridge import TheatreBridge, get_theatre_bridge


def create_ui_llm():
    """
    Create the LLM function for UI generation.

    This is where you'd integrate your actual LLM (Claude, GPT, etc.)
    For now, uses a smart mock that parses context.
    """

    def ui_llm(system_prompt: str, user_prompt: str) -> str:
        """Generate UI specification based on context."""

        # Parse the context to understand what we're working with
        context_lower = user_prompt.lower()

        components = []
        layout = "wide"
        theme = {"primary_color": "#FF6B6B", "background": "#0E1117"}

        # Detect domain and adjust theme/header
        if "garden" in context_lower or "plant" in context_lower:
            components.append({"type": "header", "content": "🌱 Garden Assistant"})
            theme = {"primary_color": "#4CAF50", "background": "#0E1117"}
        elif "grant" in context_lower or "funding" in context_lower:
            components.append({"type": "header", "content": "📋 Grant Helper"})
            theme = {"primary_color": "#2196F3", "background": "#0E1117"}
        elif "virtue" in context_lower or "trust" in context_lower:
            components.append({"type": "header", "content": "🔥 Virtue Explorer"})
            theme = {"primary_color": "#9C27B0", "background": "#0E1117"}
        else:
            components.append({"type": "header", "content": "🔥 Soul Kiln"})

        # Parse topic state if present
        topic_state = None
        if "TOPIC STATE:" in user_prompt:
            try:
                start = user_prompt.find("TOPIC STATE:") + len("TOPIC STATE:")
                end = user_prompt.find("\n\n", start)
                if end == -1:
                    end = len(user_prompt)
                topic_json = user_prompt[start:end].strip()
                topic_state = json.loads(topic_json)
            except:
                pass

        # Add topic indicator if we have topic state
        if topic_state and topic_state.get("primary_region") != "unknown":
            components.append({
                "type": "topic_indicator",
                "content": topic_state
            })

        # Parse artifacts if present
        artifacts = []
        if "AVAILABLE ARTIFACTS:" in user_prompt:
            try:
                start = user_prompt.find("AVAILABLE ARTIFACTS:") + len("AVAILABLE ARTIFACTS:")
                end = user_prompt.find("\n\n", start)
                if end == -1:
                    end = len(user_prompt)
                artifacts_json = user_prompt[start:end].strip()
                artifacts = json.loads(artifacts_json)
            except:
                pass

        # Show artifacts prominently if available
        if artifacts:
            # Create columns for artifacts
            artifact_children = []
            for artifact in artifacts[:3]:
                artifact_children.append({
                    "type": "artifact",
                    "content": artifact.get("id"),
                    "props": artifact
                })

            if artifact_children:
                components.append({
                    "type": "columns",
                    "props": {"ratio": [1] * len(artifact_children)},
                    "children": [
                        {"type": "container", "children": [ac]}
                        for ac in artifact_children
                    ]
                })

        components.append({"type": "divider"})

        # Parse conversation if present
        conversation = []
        if "RECENT CONVERSATION:" in user_prompt:
            try:
                start = user_prompt.find("RECENT CONVERSATION:") + len("RECENT CONVERSATION:")
                end = user_prompt.find("\n\n", start)
                if end == -1:
                    end = len(user_prompt)
                conv_json = user_prompt[start:end].strip()
                conversation = json.loads(conv_json)
            except:
                pass

        # Conversation display
        components.append({
            "type": "conversation",
            "content": conversation,
            "props": {"show_last": 10}
        })

        # Input area (handled specially by renderer)
        components.append({
            "type": "text_input",
            "props": {
                "placeholder": "What's on your mind?",
                "key": "user_input"
            }
        })

        return json.dumps({
            "layout": layout,
            "title": "Soul Kiln",
            "theme": theme,
            "components": components
        })

    return ui_llm


def create_response_llm():
    """
    Create the LLM function for generating responses.

    Replace with actual LLM integration.
    """

    def response_llm(system_prompt: str, user_prompt: str) -> str:
        """Generate response to user input."""
        # Mock implementation - replace with real LLM
        return f"I understand you're asking about: {user_prompt}. Let me help you explore this further."

    return response_llm


def init_session_state():
    """Initialize Streamlit session state."""

    if "bridge" not in st.session_state:
        bridge = get_theatre_bridge()
        bridge.initialize(
            graph_client=None,  # Add graph client if available
            llm_fn=create_response_llm()
        )
        st.session_state.bridge = bridge

    if "ui_generator" not in st.session_state:
        generator = get_ui_generator()
        generator.set_llm(create_ui_llm())
        st.session_state.ui_generator = generator

    if "renderer" not in st.session_state:
        renderer = get_renderer()
        # Wire artifact resolver
        renderer.set_artifact_resolver(st.session_state.bridge.resolve_artifact)
        st.session_state.renderer = renderer


def process_user_input(user_input: str):
    """Process user input through the theatre bridge."""
    if not user_input.strip():
        return

    bridge: TheatreBridge = st.session_state.bridge
    result = bridge.process_input(user_input)

    # Result contains: response, topic_state, artifacts, conversation
    # These will be used on next render cycle


def main():
    """Main application entry point."""
    # Must be first Streamlit command
    st.set_page_config(
        page_title="Soul Kiln",
        page_icon="🔥",
        layout="wide",
        initial_sidebar_state="collapsed"
    )

    init_session_state()

    bridge: TheatreBridge = st.session_state.bridge
    generator: UIGenerator = st.session_state.ui_generator
    renderer: StreamlitRenderer = st.session_state.renderer

    # Get current state from bridge
    topic_state = bridge.get_topic_state()
    artifacts = bridge.get_artifacts()
    conversation = bridge.get_conversation()

    # Generate UI based on current state
    ui_spec = generator.generate(
        topic_state=topic_state,
        artifacts=artifacts,
        conversation=conversation,
    )

    # Apply theme
    if ui_spec.theme:
        renderer._apply_theme(ui_spec.theme)

    # Render components
    for component in ui_spec.components:
        # Special handling for text_input to capture value
        if component.type.value == "text_input":
            placeholder = component.props.get("placeholder", "What's on your mind?")

            user_input = st.chat_input(placeholder)

            if user_input:
                process_user_input(user_input)
                st.rerun()
        else:
            renderer._render_component(component)


if __name__ == "__main__":
    main()
