"""
Abstract memory interface.

All memory backends must implement BaseMemory.
"""

from __future__ import annotations

from abc import ABC, abstractmethod

from src.core.schemas import ChatMessage


class BaseMemory(ABC):
    """Abstract interface for conversation memory storage."""

    @abstractmethod
    def add(self, message: ChatMessage) -> None:
        """Store a chat message."""
        ...

    @abstractmethod
    def get_history(self, max_turns: int | None = None) -> list[ChatMessage]:
        """Retrieve conversation history.

        Args:
            max_turns: Maximum number of recent turns to return.
                       A turn = one user message + one assistant response.
                       If None, return all stored messages.
        """
        ...

    @abstractmethod
    def clear(self) -> None:
        """Clear all stored messages."""
        ...

    @abstractmethod
    def count(self) -> int:
        """Return the number of stored messages."""
        ...
