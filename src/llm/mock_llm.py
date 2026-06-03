"""
Mock LLM implementation.

Returns hardcoded safe/default responses.  Used for development before
a real LLM backend is wired up.  This allows the full UI + agent pipeline
to be tested end-to-end without network calls.
"""

from __future__ import annotations

from typing import Iterable

from src.core.schemas import AgentResponse, ChatMessage, make_safe_response
from src.llm.base import BaseLLM


class MockLLM(BaseLLM):
    """A deterministic mock LLM that always returns a safe default response."""

    async def chat(
        self,
        messages: Iterable[ChatMessage],
        *,
        character_profile: str = "",
    ) -> AgentResponse:
        """Return a safe default AgentResponse.

        TODO: Replace with a configurable mock that can return different
              responses based on the last user message (useful for UI testing).
              For now, always returns the safe fallback.
        """
        return make_safe_response()

    async def is_available(self) -> bool:
        return True
