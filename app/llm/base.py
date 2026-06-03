"""
Abstract LLM interface for the app/ layer.

All LLM implementations must subclass LLMClient so they can be swapped
without changing any other code.
"""

from __future__ import annotations

from abc import ABC, abstractmethod

from app.agent.schemas import AgentResponse, ChatMessage


class LLMClient(ABC):
    """Abstract interface for an LLM backend."""

    @abstractmethod
    async def chat(
        self,
        messages: list[ChatMessage],
        *,
        character_profile: str = "",
    ) -> AgentResponse:
        """Send conversation history and receive a structured AgentResponse.

        Args:
            messages: The conversation history (user + assistant turns).
            character_profile: System prompt describing the pet's character.

        Returns:
            A validated AgentResponse.
        """
        ...

    @abstractmethod
    async def is_available(self) -> bool:
        """Check whether the LLM backend is reachable."""
        ...
