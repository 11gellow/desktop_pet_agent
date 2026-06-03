"""
Abstract voice interface.

Supports Text-to-Speech (TTS) and Speech-to-Text (STT).
"""

from __future__ import annotations

from abc import ABC, abstractmethod


class BaseVoice(ABC):
    """Abstract interface for voice input/output."""

    @abstractmethod
    async def speak(self, text: str, *, style: str = "normal") -> None:
        """Convert text to speech and play it.

        Args:
            text: The text to speak.
            style: Voice style hint (normal, cheerful, whisper, etc.).
        """
        ...

    @abstractmethod
    async def listen(self) -> str:
        """Capture microphone input and transcribe to text.

        Returns:
            The transcribed text, or empty string if nothing heard.
        """
        ...

    @abstractmethod
    def is_speaking(self) -> bool:
        """Return True if TTS is currently playing."""
        ...

    @abstractmethod
    def cancel(self) -> None:
        """Cancel current TTS playback."""
        ...
