"""
Mock voice backend.

Does nothing — speak() is silent, listen() returns empty string.
"""

from __future__ import annotations

from src.voice.base import BaseVoice


class MockVoice(BaseVoice):
    """A no-op voice backend."""

    def __init__(self) -> None:
        self._speaking = False

    async def speak(self, text: str, *, style: str = "normal") -> None:
        _ = (text, style)
        self._speaking = True
        # In a real implementation we would play audio here.
        # For the mock, just mark as done immediately.
        self._speaking = False

    async def listen(self) -> str:
        return ""

    def is_speaking(self) -> bool:
        return self._speaking

    def cancel(self) -> None:
        self._speaking = False
