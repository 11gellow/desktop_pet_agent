"""
PetAgentBrain — the core agent pipeline for processing user input.

Orchestrates one turn of conversation:
  user message -> memory -> LLM call -> AgentResponse

This is a standalone implementation in the app/ layer that does not
depend on src/agent/engine.py.
"""

from __future__ import annotations

from app.agent.character import CharacterProfile
from app.agent.schemas import AgentResponse, ChatMessage, make_safe_response
from app.llm.base import LLMClient
from app.llm.mock import MockLLMClient
from src.utils.logger import get_logger

logger = get_logger("agent.brain")


class PetAgentBrain:
    """The core agent pipeline for processing user input.

    Owns the LLM client, character profile, and conversation memory.
    """

    def __init__(
        self,
        llm: LLMClient | None = None,
        character: CharacterProfile | None = None,
        memory_max_turns: int = 50,
    ) -> None:
        # LLM: default to MockLLMClient when none is provided (requirement #7)
        self.llm: LLMClient = llm or MockLLMClient()
        logger.info(
            "PetAgentBrain initialized with LLM: %s", type(self.llm).__name__
        )

        # Character
        self.character: CharacterProfile = character or CharacterProfile.default()

        # Memory
        self._memory_max_turns = memory_max_turns
        self._messages: list[ChatMessage] = []

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    async def process_user_message(self, user_text: str) -> AgentResponse:
        """Process one user message through the full pipeline.

        Args:
            user_text: Raw user input from the chat.

        Returns:
            A validated AgentResponse (always a safe fallback on error).
        """
        # 1. Log and store user message
        logger.info("User message: %s", user_text)
        user_msg = ChatMessage(role="user", content=user_text)
        self._messages.append(user_msg)

        # 2. Trim memory before building history
        self._trim_memory()

        # 3. Build conversation history (a snapshot for the LLM call)
        history = list(self._messages)

        # 4. Call LLM
        logger.debug(
            "Calling LLM (%s) with %d history messages",
            type(self.llm).__name__,
            len(history),
        )
        try:
            response = await self.llm.chat(
                history,
                character_profile=self.character.to_system_prompt(),
            )
        except Exception:
            logger.exception("LLM call failed, falling back to safe response")
            response = make_safe_response()

        # 5. Log the response fields
        logger.info(
            "Agent response - reply=%s, emotion=%s, face=%s, action=%s, led=%s, voice_style=%s, need_hardware=%s",
            response.reply,
            response.emotion,
            response.face,
            response.action,
            response.led,
            response.voice_style,
            response.need_hardware,
        )

        # 6. Store assistant response in memory
        assistant_msg = ChatMessage(
            role="assistant",
            content=response.reply,
            agent_response=response,
        )
        self._messages.append(assistant_msg)

        return response

    # ------------------------------------------------------------------
    # Memory management
    # ------------------------------------------------------------------

    @property
    def memory_count(self) -> int:
        """Number of messages currently stored in memory."""
        return len(self._messages)

    def clear_memory(self) -> None:
        """Clear all conversation history."""
        self._messages.clear()
        logger.debug("Memory cleared")

    def _trim_memory(self) -> None:
        """Trim the message list so it does not exceed max_turns * 2 messages.

        Each turn consists of a user message and an assistant message (2 messages).
        We keep the most recent turns and discard older ones.
        """
        max_messages = self._memory_max_turns * 2
        if len(self._messages) > max_messages:
            removed = self._messages[:-max_messages]
            self._messages = self._messages[-max_messages:]
            logger.debug("Memory trimmed: removed %d old messages", len(removed))
