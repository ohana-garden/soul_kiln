"""
Hume.ai Integration.

Provides emotional intelligence signals from audio/video input.
These signals augment topic detection and influence scene generation.

Hume.ai provides:
- Voice prosody analysis (tone, pitch, rhythm)
- Facial expression recognition
- Language sentiment analysis
- Emotional classification

This integration abstracts Hume's API for use in the theatre module.
"""

import logging
import os
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any, Callable

logger = logging.getLogger(__name__)


class EmotionCategory(str, Enum):
    """High-level emotion categories (Hume's taxonomy)."""

    # Primary emotions
    JOY = "joy"
    SADNESS = "sadness"
    ANGER = "anger"
    FEAR = "fear"
    SURPRISE = "surprise"
    DISGUST = "disgust"

    # Secondary emotions
    INTEREST = "interest"
    CONFUSION = "confusion"
    CONTEMPT = "contempt"
    CONCENTRATION = "concentration"
    BOREDOM = "boredom"
    ANXIETY = "anxiety"
    EXCITEMENT = "excitement"
    CONTENTMENT = "contentment"
    DETERMINATION = "determination"
    EMPATHY = "empathy"

    # Neutral
    NEUTRAL = "neutral"


# Emotion to arousal/valence mapping (circumplex model)
EMOTION_CIRCUMPLEX = {
    EmotionCategory.JOY: (0.8, 0.9),  # High arousal, high valence
    EmotionCategory.SADNESS: (0.3, 0.2),  # Low arousal, low valence
    EmotionCategory.ANGER: (0.9, 0.2),  # High arousal, low valence
    EmotionCategory.FEAR: (0.8, 0.3),  # High arousal, low valence
    EmotionCategory.SURPRISE: (0.7, 0.6),  # High arousal, mid valence
    EmotionCategory.DISGUST: (0.5, 0.2),  # Mid arousal, low valence
    EmotionCategory.INTEREST: (0.6, 0.7),  # Mid-high arousal, high valence
    EmotionCategory.CONFUSION: (0.5, 0.4),  # Mid arousal, mid-low valence
    EmotionCategory.CONTEMPT: (0.4, 0.3),  # Mid-low arousal, low valence
    EmotionCategory.CONCENTRATION: (0.6, 0.5),  # Mid arousal, mid valence
    EmotionCategory.BOREDOM: (0.2, 0.4),  # Low arousal, mid valence
    EmotionCategory.ANXIETY: (0.7, 0.3),  # High arousal, low valence
    EmotionCategory.EXCITEMENT: (0.9, 0.8),  # High arousal, high valence
    EmotionCategory.CONTENTMENT: (0.3, 0.8),  # Low arousal, high valence
    EmotionCategory.DETERMINATION: (0.7, 0.6),  # High arousal, mid-high valence
    EmotionCategory.EMPATHY: (0.4, 0.7),  # Mid-low arousal, high valence
    EmotionCategory.NEUTRAL: (0.5, 0.5),  # Mid arousal, mid valence
}


@dataclass
class EmotionScore:
    """Score for a single emotion."""

    emotion: EmotionCategory
    score: float  # 0-1 confidence
    raw_name: str = ""  # Original name from Hume

    def to_dict(self) -> dict:
        """Convert to dictionary."""
        return {
            "emotion": self.emotion.value,
            "score": self.score,
            "raw_name": self.raw_name,
        }


@dataclass
class EmotionalState:
    """Complete emotional state from analysis."""

    # Top emotions detected
    emotions: list[EmotionScore] = field(default_factory=list)

    # Dimensional model (circumplex)
    arousal: float = 0.5  # 0 = calm, 1 = activated
    valence: float = 0.5  # 0 = negative, 1 = positive

    # Prosody features (if available)
    speech_rate: float | None = None  # Words per minute estimate
    pitch_variability: float | None = None  # 0-1
    volume_level: float | None = None  # 0-1

    # Confidence in the analysis
    confidence: float = 0.5

    # Source of analysis
    source: str = "unknown"  # "audio", "video", "text", "multimodal"

    timestamp: datetime = field(default_factory=datetime.utcnow)

    @property
    def dominant_emotion(self) -> str | None:
        """Get the dominant emotion name."""
        if self.emotions:
            return self.emotions[0].emotion.value
        return None

    @property
    def is_positive(self) -> bool:
        """Check if overall state is positive."""
        return self.valence > 0.5

    @property
    def is_activated(self) -> bool:
        """Check if arousal is high."""
        return self.arousal > 0.6

    def to_dict(self) -> dict:
        """Convert to dictionary."""
        return {
            "emotions": [e.to_dict() for e in self.emotions],
            "arousal": self.arousal,
            "valence": self.valence,
            "speech_rate": self.speech_rate,
            "pitch_variability": self.pitch_variability,
            "volume_level": self.volume_level,
            "confidence": self.confidence,
            "source": self.source,
            "dominant_emotion": self.dominant_emotion,
            "timestamp": self.timestamp.isoformat(),
        }


class HumeIntegration:
    """
    Integration layer for Hume.ai emotional intelligence.

    Provides:
    - Audio analysis (voice prosody)
    - Video analysis (facial expressions)
    - Text analysis (sentiment)
    - Multimodal fusion

    When Hume.ai is not available, falls back to simple heuristics.
    """

    # Hume.ai API endpoints (when available)
    AUDIO_ENDPOINT = "https://api.hume.ai/v0/batch/jobs"
    STREAMING_ENDPOINT = "wss://api.hume.ai/v0/stream/evi"

    def __init__(
        self,
        api_key: str | None = None,
        enable_streaming: bool = False,
    ):
        """
        Initialize Hume.ai integration.

        Args:
            api_key: Hume.ai API key (or from HUME_API_KEY env)
            enable_streaming: Enable real-time streaming analysis
        """
        self._api_key = api_key or os.environ.get("HUME_API_KEY")
        self._enable_streaming = enable_streaming
        self._connected = False

        # Callbacks for emotional state changes
        self._state_callbacks: list[Callable[[EmotionalState], None]] = []

        # State tracking
        self._current_state: EmotionalState | None = None
        self._state_history: list[EmotionalState] = []

        if not self._api_key:
            logger.warning("No Hume.ai API key - using fallback analysis")

    @property
    def is_available(self) -> bool:
        """Check if Hume.ai integration is available."""
        return bool(self._api_key)

    @property
    def current_state(self) -> EmotionalState | None:
        """Get current emotional state."""
        return self._current_state

    def analyze_audio(self, audio_data: bytes) -> EmotionalState:
        """
        Analyze audio for emotional content.

        Args:
            audio_data: Raw audio bytes (WAV or similar)

        Returns:
            EmotionalState with analysis results
        """
        if self._api_key:
            try:
                return self._analyze_audio_hume(audio_data)
            except Exception as e:
                logger.error(f"Hume audio analysis failed: {e}")

        # Fallback to simple analysis
        return self._analyze_audio_fallback(audio_data)

    def analyze_text(self, text: str) -> EmotionalState:
        """
        Analyze text for emotional content.

        Args:
            text: Text to analyze

        Returns:
            EmotionalState with analysis results
        """
        if self._api_key:
            try:
                return self._analyze_text_hume(text)
            except Exception as e:
                logger.error(f"Hume text analysis failed: {e}")

        # Fallback to keyword-based analysis
        return self._analyze_text_fallback(text)

    def analyze_video(self, frame_data: bytes) -> EmotionalState:
        """
        Analyze video frame for emotional content.

        Args:
            frame_data: Image frame bytes

        Returns:
            EmotionalState with analysis results
        """
        if self._api_key:
            try:
                return self._analyze_video_hume(frame_data)
            except Exception as e:
                logger.error(f"Hume video analysis failed: {e}")

        # Fallback - no video analysis without Hume
        return EmotionalState(source="video_fallback", confidence=0.1)

    def fuse_modalities(
        self,
        audio_state: EmotionalState | None = None,
        text_state: EmotionalState | None = None,
        video_state: EmotionalState | None = None,
    ) -> EmotionalState:
        """
        Fuse emotional states from multiple modalities.

        Weighted fusion based on confidence scores.

        Args:
            audio_state: State from audio analysis
            text_state: State from text analysis
            video_state: State from video analysis

        Returns:
            Fused EmotionalState
        """
        states = [s for s in [audio_state, text_state, video_state] if s]

        if not states:
            return EmotionalState(source="none", confidence=0.0)

        if len(states) == 1:
            return states[0]

        # Weighted average based on confidence
        total_confidence = sum(s.confidence for s in states)
        if total_confidence == 0:
            total_confidence = len(states)

        fused_arousal = sum(
            s.arousal * s.confidence for s in states
        ) / total_confidence

        fused_valence = sum(
            s.valence * s.confidence for s in states
        ) / total_confidence

        # Combine emotion lists (weighted by confidence)
        emotion_scores: dict[EmotionCategory, float] = {}
        for state in states:
            weight = state.confidence / total_confidence
            for emotion in state.emotions:
                current = emotion_scores.get(emotion.emotion, 0)
                emotion_scores[emotion.emotion] = current + emotion.score * weight

        # Sort and take top emotions
        sorted_emotions = sorted(
            emotion_scores.items(), key=lambda x: x[1], reverse=True
        )
        top_emotions = [
            EmotionScore(emotion=e, score=s) for e, s in sorted_emotions[:5]
        ]

        fused_state = EmotionalState(
            emotions=top_emotions,
            arousal=fused_arousal,
            valence=fused_valence,
            confidence=max(s.confidence for s in states),
            source="multimodal",
        )

        self._update_state(fused_state)
        return fused_state

    def _analyze_audio_hume(self, audio_data: bytes) -> EmotionalState:
        """Analyze audio using Hume.ai API."""
        # Note: This is a placeholder for actual Hume.ai API integration
        # In production, this would:
        # 1. Upload audio to Hume.ai batch API or send via streaming
        # 2. Parse the response for emotion predictions
        # 3. Map Hume's emotion taxonomy to our EmotionCategory

        # For now, return a neutral state indicating Hume analysis pending
        logger.info("Hume.ai audio analysis requested (API integration pending)")
        return EmotionalState(
            source="audio_hume_pending",
            confidence=0.3,
        )

    def _analyze_text_hume(self, text: str) -> EmotionalState:
        """Analyze text using Hume.ai API."""
        # Placeholder for Hume.ai text analysis
        logger.info("Hume.ai text analysis requested (API integration pending)")
        return EmotionalState(
            source="text_hume_pending",
            confidence=0.3,
        )

    def _analyze_video_hume(self, frame_data: bytes) -> EmotionalState:
        """Analyze video frame using Hume.ai API."""
        # Placeholder for Hume.ai video analysis
        logger.info("Hume.ai video analysis requested (API integration pending)")
        return EmotionalState(
            source="video_hume_pending",
            confidence=0.3,
        )

    def _analyze_audio_fallback(self, audio_data: bytes) -> EmotionalState:
        """Simple audio analysis without Hume.ai."""
        # Very basic analysis based on audio properties
        # In practice, could use simple volume/pitch detection

        # Return neutral-ish state with low confidence
        return EmotionalState(
            emotions=[EmotionScore(emotion=EmotionCategory.NEUTRAL, score=0.5)],
            arousal=0.5,
            valence=0.5,
            confidence=0.2,
            source="audio_fallback",
        )

    def _analyze_text_fallback(self, text: str) -> EmotionalState:
        """Keyword-based text analysis without Hume.ai."""
        text_lower = text.lower()

        # Simple keyword matching for emotions
        emotion_keywords = {
            EmotionCategory.JOY: [
                "happy", "joy", "excited", "great", "wonderful", "love",
                "amazing", "fantastic", "delighted", "thrilled"
            ],
            EmotionCategory.SADNESS: [
                "sad", "unhappy", "depressed", "disappointed", "sorry",
                "regret", "miss", "lost", "grief"
            ],
            EmotionCategory.ANGER: [
                "angry", "frustrated", "annoyed", "furious", "mad",
                "irritated", "upset"
            ],
            EmotionCategory.FEAR: [
                "afraid", "scared", "worried", "anxious", "nervous",
                "terrified", "concerned"
            ],
            EmotionCategory.SURPRISE: [
                "surprised", "shocked", "amazed", "unexpected", "wow",
                "astonished"
            ],
            EmotionCategory.INTEREST: [
                "interesting", "curious", "intrigued", "fascinated",
                "wondering", "want to know"
            ],
            EmotionCategory.CONFUSION: [
                "confused", "unclear", "don't understand", "what",
                "puzzled", "lost"
            ],
            EmotionCategory.DETERMINATION: [
                "determined", "committed", "will", "going to", "must",
                "need to", "have to"
            ],
        }

        # Score each emotion
        scores: dict[EmotionCategory, float] = {}
        for emotion, keywords in emotion_keywords.items():
            score = sum(1 for kw in keywords if kw in text_lower)
            if score > 0:
                scores[emotion] = min(1.0, score * 0.2)

        # If no emotions detected, return neutral
        if not scores:
            return EmotionalState(
                emotions=[EmotionScore(emotion=EmotionCategory.NEUTRAL, score=0.6)],
                arousal=0.5,
                valence=0.5,
                confidence=0.4,
                source="text_fallback",
            )

        # Sort by score
        sorted_emotions = sorted(scores.items(), key=lambda x: x[1], reverse=True)
        top_emotions = [
            EmotionScore(emotion=e, score=s) for e, s in sorted_emotions[:3]
        ]

        # Calculate arousal/valence from top emotion
        top_emotion = sorted_emotions[0][0]
        arousal, valence = EMOTION_CIRCUMPLEX.get(
            top_emotion, (0.5, 0.5)
        )

        return EmotionalState(
            emotions=top_emotions,
            arousal=arousal,
            valence=valence,
            confidence=0.5,
            source="text_fallback",
        )

    def _update_state(self, state: EmotionalState) -> None:
        """Update current state and notify callbacks."""
        self._current_state = state
        self._state_history.append(state)

        # Keep history bounded
        if len(self._state_history) > 100:
            self._state_history = self._state_history[-50:]

        # Notify callbacks
        for callback in self._state_callbacks:
            try:
                callback(state)
            except Exception as e:
                logger.error(f"Emotional state callback error: {e}")

    def on_state_change(
        self, callback: Callable[[EmotionalState], None]
    ) -> None:
        """Register callback for emotional state changes."""
        self._state_callbacks.append(callback)

    def get_trend(self, window: int = 10) -> dict:
        """
        Get emotional trend over recent history.

        Args:
            window: Number of recent states to analyze

        Returns:
            Trend information
        """
        if not self._state_history:
            return {"trend": "stable", "direction": 0}

        recent = self._state_history[-window:]
        if len(recent) < 2:
            return {"trend": "stable", "direction": 0}

        # Calculate arousal/valence trends
        arousal_trend = recent[-1].arousal - recent[0].arousal
        valence_trend = recent[-1].valence - recent[0].valence

        # Determine overall trend
        if abs(arousal_trend) < 0.1 and abs(valence_trend) < 0.1:
            trend = "stable"
        elif valence_trend > 0.1:
            trend = "improving" if arousal_trend > 0 else "calming"
        elif valence_trend < -0.1:
            trend = "declining" if arousal_trend < 0 else "agitating"
        elif arousal_trend > 0.1:
            trend = "activating"
        else:
            trend = "deactivating"

        return {
            "trend": trend,
            "arousal_change": arousal_trend,
            "valence_change": valence_trend,
            "window_size": len(recent),
        }


# Singleton instance
_hume: HumeIntegration | None = None


def get_hume_integration() -> HumeIntegration:
    """Get the singleton Hume.ai integration."""
    global _hume
    if _hume is None:
        _hume = HumeIntegration()
    return _hume
