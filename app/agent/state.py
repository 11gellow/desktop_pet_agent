"""
Agent internal state machine.

Tracks the pet's emotional dimensions, activity level, and interaction
history.  Emotions decay over time and are boosted by user interaction.
The LLM's AgentResponse can also nudge the state.
"""

from __future__ import annotations

import time
from dataclasses import dataclass, field

from src.utils.logger import get_logger

logger = get_logger("agent.state")


@dataclass
class AgentState:
    """Persistent emotional and behavioral state of the desktop pet.

    All emotional values are in [0.0, 1.0].  Higher = more intense.

    The state is designed to be:
      - Tick-driven: call tick(dt) periodically (e.g. every 1-5 seconds).
      - LLM-influenced: call apply_response(resp) after each AgentResponse.
      - Observable: fields can be bound to UI widgets or sent to hardware.
    """

    # ------------------------------------------------------------------
    # Emotional dimensions [0.0, 1.0]
    # ------------------------------------------------------------------
    happiness: float = 0.5
    energy: float = 0.5
    affection: float = 0.3
    curiosity: float = 0.5

    # ------------------------------------------------------------------
    # Display state (what hardware is currently showing)
    # ------------------------------------------------------------------
    current_emotion: str = "neutral"
    current_face: str = "normal"
    current_action: str = "idle"
    current_led: str = "off"

    # ------------------------------------------------------------------
    # Timing & counters
    # ------------------------------------------------------------------
    last_interaction_at: float = 0.0
    interaction_count: int = 0
    total_active_seconds: float = 0.0

    # ------------------------------------------------------------------
    # Configuration (tweakable per character)
    # ------------------------------------------------------------------
    happiness_decay: float = 0.001   # lost per second of idle
    energy_decay: float = 0.0008
    affection_decay: float = 0.0003
    curiosity_decay: float = 0.0005

    # ------------------------------------------------------------------
    # Core tick
    # ------------------------------------------------------------------

    def tick(self, delta_seconds: float) -> None:
        """Advance the state by *delta_seconds* of idle time.

        Call this periodically from a QTimer.  Emotions drift toward
        neutral (0.5) — positive emotions decay, negative ones recover.
        """
        if delta_seconds <= 0:
            return

        self.total_active_seconds += delta_seconds

        # Drift each dimension toward neutral (0.5)
        for attr, decay_rate in [
            ("happiness", self.happiness_decay),
            ("energy", self.energy_decay),
            ("affection", self.affection_decay),
            ("curiosity", self.curiosity_decay),
        ]:
            current = getattr(self, attr)
            drift = (0.5 - current) * min(decay_rate * delta_seconds, 1.0)
            setattr(self, attr, self._clamp(current + drift))

        # Energy decays faster when happiness is low
        if self.happiness < 0.3:
            self.energy = self._clamp(self.energy - 0.002 * delta_seconds)

        # Derive display emotion from internal dimensions
        self._update_display_emotion()

    # ------------------------------------------------------------------
    # Event handlers
    # ------------------------------------------------------------------

    def on_user_interaction(self) -> None:
        """Called when the user sends a message or touches the pet."""
        self.last_interaction_at = time.time()
        self.interaction_count += 1

        # Interaction boosts emotional dimensions
        self.happiness = self._clamp(self.happiness + 0.08)
        self.energy = self._clamp(self.energy + 0.06)
        self.affection = self._clamp(self.affection + 0.05)
        self.curiosity = self._clamp(self.curiosity + 0.07)

        logger.debug(
            "State after interaction — happiness=%.2f energy=%.2f affection=%.2f curiosity=%.2f",
            self.happiness, self.energy, self.affection, self.curiosity,
        )

    def apply_response(self, emotion: str, face: str, action: str, led: str) -> None:
        """Apply the LLM's output to the display state.

        Also nudges the internal emotional dimensions based on the
        emotion label.
        """
        old_emotion = self.current_emotion
        self.current_emotion = emotion
        self.current_face = face
        self.current_action = action
        self.current_led = led

        # Nudge internal state based on the LLM's emotion
        emotion_boost: dict[str, tuple[float, float, float, float]] = {
            "happy":     (+0.05, +0.03, +0.02, +0.02),
            "excited":   (+0.08, +0.10, +0.03, +0.05),
            "surprised": (+0.02, +0.05, +0.01, +0.08),
            "sad":       (-0.08, -0.10, +0.02, -0.03),
            "angry":     (-0.05, +0.05, -0.05,  0.00),
            "neutral":   ( 0.00,  0.00,  0.00,  0.00),
            "curious":   (+0.02, +0.02, +0.01, +0.10),
        }
        boosts = emotion_boost.get(emotion, (0, 0, 0, 0))
        self.happiness = self._clamp(self.happiness + boosts[0])
        self.energy = self._clamp(self.energy + boosts[1])
        self.affection = self._clamp(self.affection + boosts[2])
        self.curiosity = self._clamp(self.curiosity + boosts[3])

        if old_emotion != emotion:
            logger.debug("Display emotion: %s → %s", old_emotion, emotion)

    # ------------------------------------------------------------------
    # Derived state
    # ------------------------------------------------------------------

    @property
    def idle_seconds(self) -> float:
        """Seconds since the last user interaction."""
        if self.last_interaction_at == 0.0:
            return 0.0
        return time.time() - self.last_interaction_at

    @property
    def is_bored(self) -> bool:
        """Pet is bored: low energy + idle for a while."""
        return self.energy < 0.35 and self.idle_seconds > 30

    @property
    def is_sleepy(self) -> bool:
        """Pet is sleepy: very low energy."""
        return self.energy < 0.2

    @property
    def wants_attention(self) -> bool:
        """Pet actively wants the user to interact."""
        return self.affection > 0.6 and self.idle_seconds > 20

    @property
    def dominant_emotion(self) -> str:
        """Map internal dimensions to a single emotion label."""
        if self.happiness > 0.7 and self.energy > 0.6:
            return "happy"
        if self.energy > 0.8:
            return "excited"
        if self.happiness < 0.25:
            return "sad"
        if self.curiosity > 0.75:
            return "curious"
        if self.energy < 0.3:
            return "sleepy"
        return "neutral"

    # ------------------------------------------------------------------
    # Serialization
    # ------------------------------------------------------------------

    def to_dict(self) -> dict:
        """Serialize state to a plain dict (for saving to file)."""
        return {
            "happiness": self.happiness,
            "energy": self.energy,
            "affection": self.affection,
            "curiosity": self.curiosity,
            "current_emotion": self.current_emotion,
            "current_face": self.current_face,
            "current_action": self.current_action,
            "current_led": self.current_led,
            "last_interaction_at": self.last_interaction_at,
            "interaction_count": self.interaction_count,
            "total_active_seconds": self.total_active_seconds,
        }

    @classmethod
    def from_dict(cls, data: dict) -> AgentState:
        """Restore state from a plain dict."""
        return cls(**{k: v for k, v in data.items() if k in cls.__dataclass_fields__})

    def reset(self) -> None:
        """Reset all values to defaults."""
        defaults = AgentState()
        for field_name in self.__dataclass_fields__:
            setattr(self, field_name, getattr(defaults, field_name))

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------

    @staticmethod
    def _clamp(value: float, lo: float = 0.0, hi: float = 1.0) -> float:
        return max(lo, min(hi, value))

    def _update_display_emotion(self) -> None:
        """Derive emotion/face from internal dimensions.

        Only updates if no explicit LLM-driven emotion was recently set
        (we don't want tick() to immediately override the LLM).
        """
        # If interaction happened recently (< 3s ago), keep current display
        if self.idle_seconds < 3.0:
            return

        # Map internal state to display
        emo = self.dominant_emotion
        face_map = {
            "happy": "smile", "excited": "smile", "curious": "blink",
            "sad": "frown", "sleepy": "normal", "neutral": "normal",
        }
        action_map = {
            "happy": "bounce", "excited": "wave", "curious": "tilt_head",
            "sad": "idle", "sleepy": "idle", "neutral": "idle",
        }

        if emo != self.current_emotion:
            self.current_emotion = emo
            self.current_face = face_map.get(emo, "normal")
            self.current_action = action_map.get(emo, "idle")
