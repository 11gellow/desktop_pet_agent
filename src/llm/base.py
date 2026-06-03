"""
Abstract LLM interface.

All LLM implementations must subclass BaseLLM so they can be swapped
without changing any other code.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Iterable

from src.core.schemas import AgentResponse, ChatMessage


class BaseLLM(ABC):
    """Abstract interface for an LLM backend."""

    @abstractmethod
    async def chat(
        self,
        messages: Iterable[ChatMessage],
        *,
        character_profile: str = "",
    ) -> AgentResponse:
        """Send conversation history and receive a structured AgentResponse.

        Args:
            messages: The conversation history (user + assistant turns).
            character_profile: System prompt describing the pet's character.

        Returns:
            A validated AgentResponse.

        Raises:
            LLMError: On any failure (network, API error, invalid response).
        """
        ...

    @abstractmethod
    async def is_available(self) -> bool:
        """Check whether the LLM backend is reachable."""
        ...
