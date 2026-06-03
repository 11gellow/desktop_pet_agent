"""
Agent decision engine.

Orchestrates one turn of conversation:
  user message → memory context → LLM call → AgentResponse → hardware command
"""

from __future__ import annotations

from src.agent.character import CharacterProfile
from src.core.schemas import AgentResponse, ChatMessage, make_safe_response
from src.llm.base import BaseLLM
from src.memory.base import BaseMemory
from src.utils.logger import get_logger

logger = get_logger("agent")


class AgentEngine:
    """The core agent pipeline for processing user input."""

    def __init__(
        self,
        llm: BaseLLM,
        memory: BaseMemory,
        character: CharacterProfile | None = None,
    ) -> None:
        self.llm = llm
        self.memory = memory
        self.character = character or CharacterProfile.default()

    async def process_user_message(self, user_text: str) -> AgentResponse:
        """Process one user message through the full pipeline.

        Args:
            user_text: Raw user input from the chat.

        Returns:
            A validated AgentResponse (always a safe fallback on error).
        """
        # 1. Store user message in memory
        user_msg = ChatMessage(role="user", content=user_text)
        self.memory.add(user_msg)

        # 2. Retrieve conversation history from memory
        history = self.memory.get_history()

        # 3. Call LLM
        try:
            response = await self.llm.chat(
                history,
                character_profile=self.character.to_system_prompt(),
            )
        except Exception:
            logger.exception("LLM call failed, falling back to safe response")
            response = make_safe_response()

        # 4. Store assistant response in memory
        assistant_msg = ChatMessage(
            role="assistant",
            content=response.reply,
            agent_response=response,
        )
        self.memory.add(assistant_msg)

        return response
