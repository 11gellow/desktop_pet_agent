"""
Mock LLM client for the app/ layer.

Returns hardcoded safe/default responses.  Used for development before
a real LLM backend is wired up.
"""

from __future__ import annotations

from app.agent.schemas import AgentResponse, ChatMessage, make_safe_response
from app.llm.base import LLMClient
from src.utils.logger import get_logger

logger = get_logger("llm.mock")


class MockLLMClient(LLMClient):
    """A deterministic mock LLM that always returns a safe default response."""

    async def chat(
        self,
        messages: list[ChatMessage],
        *,
        character_profile: str = "",
    ) -> AgentResponse:
        """Return a safe default AgentResponse.

        TODO: Replace with a configurable mock that can return different
              responses based on the last user message (useful for UI testing).
              For now, always returns the safe fallback.
        """
        logger.debug(
            "MockLLMClient.chat called with %d messages, character_profile length=%d",
            len(messages),
            len(character_profile),
        )
        return make_safe_response()

    async def is_available(self) -> bool:
        logger.debug("MockLLMClient.is_available -> True")
        return True
