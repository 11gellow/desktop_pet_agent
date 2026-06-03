"""
Simple in-memory conversation storage.

This is a development implementation.  For production, replace with a
persistent backend (SQLite, JSON file, vector DB, etc.).
"""

from __future__ import annotations

from src.core.config import get_config
from src.core.schemas import ChatMessage
from src.memory.base import BaseMemory


class SimpleMemory(BaseMemory):
    """Stores messages in a plain Python list (volatile)."""

    def __init__(self, max_turns: int | None = None) -> None:
        self._messages: list[ChatMessage] = []
        self._max_turns = max_turns or get_config().memory_max_turns

    def add(self, message: ChatMessage) -> None:
        self._messages.append(message)
        # Trim oldest messages if over limit (2 messages per turn)
        max_messages = self._max_turns * 2
        if len(self._messages) > max_messages:
            self._messages = self._messages[-max_messages:]

    def get_history(self, max_turns: int | None = None) -> list[ChatMessage]:
        if max_turns is None:
            return list(self._messages)
        limit = max_turns * 2
        return self._messages[-limit:]

    def clear(self) -> None:
        self._messages.clear()

    def count(self) -> int:
        return len(self._messages)
