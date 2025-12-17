"""
Soul Kiln - AI Generated UI.

Every pixel is decided by the AI based on conversation context.
Run with: streamlit run src/ui/app.py
"""

import os
import sys

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

import streamlit as st

from src.ui.generator import UIGenerator, UISpec, get_ui_generator
from src.ui.renderer import StreamlitRenderer, get_renderer


def create_mock_llm():
    """Create a mock LLM for testing without API keys."""

    def mock_llm(system_prompt: str, user_prompt: str) -> str:
        """Generate UI based on context keywords."""
        import json

        # Parse context to determine what to show
        context_lower = user_prompt.lower()

        # Default components
        components = []

        # Determine layout and theme based on context
        layout = "wide"
        theme = {"primary_color": "#FF6B6B", "background": "#1E1E1E"}

        # Header
        if "garden" in context_lower or "plant" in context_lower:
            components.append({"type": "header", "content": "🌱 Garden Assistant"})
            theme = {"primary_color": "#4CAF50", "background": "#1E1E1E"}
        elif "grant" in context_lower:
            components.append({"type": "header", "content": "📋 Grant Helper"})
            theme = {"primary_color": "#2196F3", "background": "#1E1E1E"}
        elif "virtue" in context_lower or "graph" in context_lower:
            components.append({"type": "header", "content": "🔥 Soul Kiln"})
            components.append({"type": "virtue_display", "props": {"show_activations": True}})
        else:
            components.append({"type": "header", "content": "🔥 Soul Kiln"})

        # Topic indicator if we have topic state
        if "topic_state" in context_lower or "primary_region" in context_lower:
            components.append({
                "type": "topic_indicator",
                "content": {"primary_region": "practical", "confidence": 0.75, "active_concepts": ["conversation"]}
            })

        # Check for artifacts
        if "artifacts" in context_lower and "[]" not in context_lower:
            components.append({
                "type": "subheader",
                "content": "Relevant Resources"
            })
            # Would parse actual artifacts here

        # Main content area
        components.append({
            "type": "divider"
        })

        # Conversation display
        components.append({
            "type": "conversation",
            "content": [],
            "props": {"show_last": 10}
        })

        # Input area
        components.append({
            "type": "text_input",
            "props": {
                "label": "",
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

    return mock_llm


def init_session_state():
    """Initialize Streamlit session state."""
    if "conversation" not in st.session_state:
        st.session_state.conversation = []

    if "topic_state" not in st.session_state:
        st.session_state.topic_state = {
            "primary_region": "unknown",
            "confidence": 0.0,
            "active_concepts": [],
            "active_virtues": []
        }

    if "artifacts" not in st.session_state:
        st.session_state.artifacts = []

    if "ui_generator" not in st.session_state:
        generator = get_ui_generator()
        # Use mock LLM for now - replace with real LLM integration
        generator.set_llm(create_mock_llm())
        st.session_state.ui_generator = generator

    if "renderer" not in st.session_state:
        st.session_state.renderer = get_renderer()


def process_user_input(user_input: str):
    """Process user input and update state."""
    if not user_input.strip():
        return

    # Add to conversation
    st.session_state.conversation.append({
        "role": "user",
        "content": user_input
    })

    # Update topic state based on keywords (mock implementation)
    input_lower = user_input.lower()

    if any(word in input_lower for word in ["garden", "plant", "grow", "seed"]):
        st.session_state.topic_state = {
            "primary_region": "practical",
            "confidence": 0.8,
            "active_concepts": ["garden", "plants", "growth"],
            "active_virtues": ["V19"]  # Service
        }
    elif any(word in input_lower for word in ["grant", "funding", "proposal"]):
        st.session_state.topic_state = {
            "primary_region": "relational",
            "confidence": 0.75,
            "active_concepts": ["grant", "funding", "application"],
            "active_virtues": ["V19", "V02"]  # Service, Truthfulness
        }
    elif any(word in input_lower for word in ["virtue", "trust", "truth", "justice"]):
        st.session_state.topic_state = {
            "primary_region": "foundation",
            "confidence": 0.9,
            "active_concepts": ["virtue", "ethics", "character"],
            "active_virtues": ["V01", "V02", "V03"]
        }

    # Generate mock response
    response = f"I understand you're interested in: {user_input}. How can I help further?"

    st.session_state.conversation.append({
        "role": "assistant",
        "content": response
    })


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

    generator: UIGenerator = st.session_state.ui_generator
    renderer: StreamlitRenderer = st.session_state.renderer

    # Generate UI based on current state
    ui_spec = generator.generate(
        topic_state=st.session_state.topic_state,
        artifacts=st.session_state.artifacts,
        conversation=st.session_state.conversation,
    )

    # Render the generated UI (skip page config since we set it above)
    # Apply theme
    if ui_spec.theme:
        renderer._apply_theme(ui_spec.theme)

    # Render components
    for component in ui_spec.components:
        # Special handling for text_input to capture value
        if component.type.value == "text_input":
            key = component.props.get("key", "user_input")
            placeholder = component.props.get("placeholder", "")
            label = component.props.get("label", "")

            user_input = st.chat_input(placeholder or "What's on your mind?")

            if user_input:
                process_user_input(user_input)
                st.rerun()
        else:
            renderer._render_component(component)


if __name__ == "__main__":
    main()
