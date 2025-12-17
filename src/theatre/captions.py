"""
Caption Rendering System.

Movie-subtitle-style captions that appear and fade.
Color-coded by speaker for the theatrical UX.

Design principles:
- Captions appear smoothly
- Captions fade after a duration
- Color indicates speaker
- Position can vary based on scene/speaker
- Multiple captions can be visible during overlap
"""

import logging
import threading
import time
from collections import deque
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any, Callable

from .orchestrator import AgentRole, ConversationTurn

logger = logging.getLogger(__name__)


class CaptionPosition(str, Enum):
    """Screen positions for captions."""

    BOTTOM_CENTER = "bottom_center"  # Default subtitle position
    BOTTOM_LEFT = "bottom_left"
    BOTTOM_RIGHT = "bottom_right"
    TOP_CENTER = "top_center"
    TOP_LEFT = "top_left"
    TOP_RIGHT = "top_right"
    CENTER = "center"


class CaptionAnimation(str, Enum):
    """Animation styles for caption appearance/disappearance."""

    FADE = "fade"  # Simple fade in/out
    SLIDE_UP = "slide_up"  # Slide in from below
    TYPEWRITER = "typewriter"  # Character by character
    DISSOLVE = "dissolve"  # Pixel dissolve effect


@dataclass
class CaptionStyle:
    """Visual style for a caption."""

    color: str = "#FFFFFF"  # Text color (hex)
    background_color: str = "rgba(0,0,0,0.7)"  # Background
    font_size: str = "1.2em"
    font_weight: str = "normal"
    font_style: str = "normal"  # normal, italic
    text_align: str = "center"
    position: CaptionPosition = CaptionPosition.BOTTOM_CENTER
    animation: CaptionAnimation = CaptionAnimation.FADE
    padding: str = "0.5em 1em"
    border_radius: str = "4px"
    max_width: str = "80%"
    opacity: float = 1.0

    def to_css(self) -> dict:
        """Convert to CSS-like properties."""
        return {
            "color": self.color,
            "backgroundColor": self.background_color,
            "fontSize": self.font_size,
            "fontWeight": self.font_weight,
            "fontStyle": self.font_style,
            "textAlign": self.text_align,
            "padding": self.padding,
            "borderRadius": self.border_radius,
            "maxWidth": self.max_width,
            "opacity": self.opacity,
        }

    def to_dict(self) -> dict:
        """Convert to dictionary."""
        return {
            "color": self.color,
            "background_color": self.background_color,
            "font_size": self.font_size,
            "font_weight": self.font_weight,
            "font_style": self.font_style,
            "text_align": self.text_align,
            "position": self.position.value,
            "animation": self.animation.value,
            "padding": self.padding,
            "border_radius": self.border_radius,
            "max_width": self.max_width,
            "opacity": self.opacity,
        }


# Default styles per speaker role
ROLE_STYLES = {
    AgentRole.USER_PROXY: CaptionStyle(
        color="#4CAF50",  # Green
        position=CaptionPosition.BOTTOM_LEFT,
        font_style="italic",
    ),
    AgentRole.BUILDER: CaptionStyle(
        color="#2196F3",  # Blue
        position=CaptionPosition.BOTTOM_CENTER,
    ),
    AgentRole.CURRENT_AGENT: CaptionStyle(
        color="#FF9800",  # Orange
        position=CaptionPosition.BOTTOM_RIGHT,
    ),
    AgentRole.SYSTEM: CaptionStyle(
        color="#9E9E9E",  # Gray
        position=CaptionPosition.TOP_CENTER,
        font_size="0.9em",
        opacity=0.8,
    ),
}


@dataclass
class Caption:
    """A single caption to be displayed."""

    id: str
    text: str
    speaker_name: str
    role: AgentRole
    style: CaptionStyle
    duration: float  # Seconds to display
    created_at: datetime = field(default_factory=datetime.utcnow)

    # Animation state
    state: str = "entering"  # entering, visible, exiting, gone
    progress: float = 0.0  # Animation progress 0-1
    actual_opacity: float = 0.0  # Current opacity after animation

    # Timing
    enter_duration: float = 0.3
    exit_duration: float = 0.5

    def to_dict(self) -> dict:
        """Convert to dictionary for rendering."""
        return {
            "id": self.id,
            "text": self.text,
            "speaker_name": self.speaker_name,
            "role": self.role.value,
            "style": self.style.to_dict(),
            "duration": self.duration,
            "state": self.state,
            "progress": self.progress,
            "actual_opacity": self.actual_opacity,
            "created_at": self.created_at.isoformat(),
        }

    def to_render_dict(self) -> dict:
        """Convert to dictionary optimized for rendering."""
        css = self.style.to_css()
        css["opacity"] = self.actual_opacity

        return {
            "id": self.id,
            "text": self.text,
            "speakerName": self.speaker_name,
            "position": self.style.position.value,
            "animation": self.style.animation.value,
            "css": css,
            "state": self.state,
        }


class CaptionRenderer:
    """
    Manages caption display with timing and animation.

    Handles:
    - Converting conversation turns to captions
    - Caption timing (duration based on text length)
    - Animation states (entering, visible, exiting)
    - Multiple simultaneous captions
    - Cleanup of expired captions
    """

    # Reading speed assumptions
    CHARS_PER_SECOND = 15  # Average reading speed
    MIN_DURATION = 2.0  # Minimum seconds to show
    MAX_DURATION = 10.0  # Maximum seconds to show

    def __init__(
        self,
        default_duration: float = 4.0,
        overlap_enabled: bool = True,
        max_visible: int = 3,
    ):
        """
        Initialize the caption renderer.

        Args:
            default_duration: Default display duration in seconds
            overlap_enabled: Allow multiple captions visible at once
            max_visible: Maximum simultaneous captions
        """
        self._default_duration = default_duration
        self._overlap_enabled = overlap_enabled
        self._max_visible = max_visible

        self._active_captions: deque[Caption] = deque(maxlen=20)
        self._caption_counter = 0
        self._running = False
        self._update_thread: threading.Thread | None = None
        self._lock = threading.RLock()

        # Callbacks
        self._update_callbacks: list[Callable[[list[Caption]], None]] = []

    def start(self) -> None:
        """Start the caption update loop."""
        if self._running:
            return

        self._running = True
        self._update_thread = threading.Thread(
            target=self._update_loop, daemon=True
        )
        self._update_thread.start()
        logger.info("Caption renderer started")

    def stop(self) -> None:
        """Stop the caption update loop."""
        self._running = False
        if self._update_thread:
            self._update_thread.join(timeout=1.0)
        logger.info("Caption renderer stopped")

    def add_turn(self, turn: ConversationTurn) -> Caption:
        """
        Create and add a caption from a conversation turn.

        Args:
            turn: The conversation turn to display

        Returns:
            The created Caption
        """
        with self._lock:
            self._caption_counter += 1

            # Get style for this role
            style = ROLE_STYLES.get(turn.role, CaptionStyle())

            # Override with speaker's color if available
            if turn.metadata.get("color"):
                style.color = turn.metadata["color"]

            # Calculate duration based on text length
            duration = self._calculate_duration(turn.content)

            caption = Caption(
                id=f"caption_{self._caption_counter}",
                text=turn.content,
                speaker_name=turn.speaker_name,
                role=turn.role,
                style=style,
                duration=duration,
            )

            self._active_captions.append(caption)

            # Remove oldest if over max
            visible_count = sum(
                1 for c in self._active_captions if c.state != "gone"
            )
            if visible_count > self._max_visible and not self._overlap_enabled:
                # Force oldest to exit
                for c in self._active_captions:
                    if c.state == "visible":
                        c.state = "exiting"
                        c.progress = 0.0
                        break

            return caption

    def add_text(
        self,
        text: str,
        speaker_name: str = "System",
        role: AgentRole = AgentRole.SYSTEM,
        style: CaptionStyle | None = None,
        duration: float | None = None,
    ) -> Caption:
        """
        Add a raw text caption.

        Args:
            text: Text to display
            speaker_name: Name of speaker
            role: Speaker role
            style: Optional custom style
            duration: Optional custom duration

        Returns:
            The created Caption
        """
        with self._lock:
            self._caption_counter += 1

            if style is None:
                style = ROLE_STYLES.get(role, CaptionStyle())

            if duration is None:
                duration = self._calculate_duration(text)

            caption = Caption(
                id=f"caption_{self._caption_counter}",
                text=text,
                speaker_name=speaker_name,
                role=role,
                style=style,
                duration=duration,
            )

            self._active_captions.append(caption)
            return caption

    def _calculate_duration(self, text: str) -> float:
        """Calculate display duration based on text length."""
        # Base duration on character count
        char_count = len(text)
        duration = char_count / self.CHARS_PER_SECOND

        # Add time for any punctuation pauses
        punctuation_count = text.count(".") + text.count("!") + text.count("?")
        duration += punctuation_count * 0.3

        # Clamp to min/max
        return max(self.MIN_DURATION, min(self.MAX_DURATION, duration))

    def _update_loop(self) -> None:
        """Main update loop for caption animations."""
        last_time = time.time()

        while self._running:
            current_time = time.time()
            delta = current_time - last_time
            last_time = current_time

            with self._lock:
                # Update all active captions
                visible_captions = []

                for caption in list(self._active_captions):
                    if caption.state == "gone":
                        continue

                    self._update_caption(caption, delta)

                    if caption.state != "gone":
                        visible_captions.append(caption)

                # Notify callbacks
                self._notify_update(visible_captions)

                # Cleanup gone captions
                self._active_captions = deque(
                    (c for c in self._active_captions if c.state != "gone"),
                    maxlen=20,
                )

            # ~60 updates per second
            time.sleep(1 / 60)

    def _update_caption(self, caption: Caption, delta: float) -> None:
        """Update a single caption's animation state."""
        if caption.state == "entering":
            # Fade in
            caption.progress += delta / caption.enter_duration
            caption.actual_opacity = min(1.0, caption.progress) * caption.style.opacity

            if caption.progress >= 1.0:
                caption.state = "visible"
                caption.progress = 0.0
                caption.actual_opacity = caption.style.opacity

        elif caption.state == "visible":
            # Count down duration
            caption.progress += delta / caption.duration

            if caption.progress >= 1.0:
                caption.state = "exiting"
                caption.progress = 0.0

        elif caption.state == "exiting":
            # Fade out
            caption.progress += delta / caption.exit_duration
            caption.actual_opacity = max(0.0, 1.0 - caption.progress) * caption.style.opacity

            if caption.progress >= 1.0:
                caption.state = "gone"
                caption.actual_opacity = 0.0

    def get_visible_captions(self) -> list[Caption]:
        """Get all currently visible captions."""
        with self._lock:
            return [
                c for c in self._active_captions
                if c.state != "gone" and c.actual_opacity > 0
            ]

    def get_render_data(self) -> list[dict]:
        """Get render-ready data for all visible captions."""
        return [c.to_render_dict() for c in self.get_visible_captions()]

    def clear(self) -> None:
        """Clear all captions immediately."""
        with self._lock:
            for caption in self._active_captions:
                caption.state = "gone"
                caption.actual_opacity = 0.0
            self._active_captions.clear()

    def force_exit(self, caption_id: str) -> bool:
        """Force a specific caption to start exiting."""
        with self._lock:
            for caption in self._active_captions:
                if caption.id == caption_id:
                    if caption.state in ("entering", "visible"):
                        caption.state = "exiting"
                        caption.progress = 0.0
                    return True
            return False

    def on_update(self, callback: Callable[[list[Caption]], None]) -> None:
        """Register callback for caption updates."""
        self._update_callbacks.append(callback)

    def _notify_update(self, captions: list[Caption]) -> None:
        """Notify callbacks of caption update."""
        for callback in self._update_callbacks:
            try:
                callback(captions)
            except Exception as e:
                logger.error(f"Caption update callback error: {e}")

    def set_style_for_role(self, role: AgentRole, style: CaptionStyle) -> None:
        """Set custom style for a role."""
        ROLE_STYLES[role] = style

    def get_stats(self) -> dict:
        """Get caption renderer statistics."""
        with self._lock:
            return {
                "total_created": self._caption_counter,
                "active_count": len(self._active_captions),
                "visible_count": len(self.get_visible_captions()),
                "running": self._running,
            }


# Singleton instance
_renderer: CaptionRenderer | None = None


def get_caption_renderer() -> CaptionRenderer:
    """Get the singleton caption renderer."""
    global _renderer
    if _renderer is None:
        _renderer = CaptionRenderer()
    return _renderer
