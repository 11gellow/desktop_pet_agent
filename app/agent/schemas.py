"""
Pydantic schemas for the app/ agent layer.

Self-contained copy of the core data structures so the app/ module
does not depend on src/core/.
"""

from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, Field, field_validator


# ---------------------------------------------------------------------------
# Agent response (output from LLM → parsed by pydantic)
# ---------------------------------------------------------------------------


class AgentResponse(BaseModel):
    """The structured output every LLM call must produce.

    If the LLM output fails validation, the system must fall back to a safe
    default response.
    """

    reply: str = Field(
        default="...",
        description="Text reply shown to the user in the chat.",
    )
    emotion: str = Field(
        default="neutral",
        description="Emotion label, e.g. happy, sad, angry, surprised, neutral.",
    )
    face: str = Field(
        default="normal",
        description="Facial expression command sent to hardware, e.g. smile, frown, blink.",
    )
    action: str = Field(
        default="idle",
        description="Physical action command, e.g. wave, nod, shake_head, idle.",
    )
    led: str = Field(
        default="off",
        description="LED effect command, e.g. warm, cool, breath, rainbow, off.",
    )
    voice_style: str = Field(
        default="normal",
        description="Voice style hint, e.g. normal, cheerful, whisper, serious.",
    )
    need_hardware: bool = Field(
        default=True,
        description="Whether this response requires hardware execution.",
    )

    @field_validator("reply", "emotion", "face", "action", "led", "voice_style", mode="before")
    @classmethod
    def ensure_str(cls, v: object) -> str:
        if v is None:
            return ""
        return str(v)

    def to_hardware_command(self, cmd_id: str) -> HardwareCommand:
        """Convert agent response fields into a hardware perform command."""
        return HardwareCommand(
            id=cmd_id,
            command="perform",
            payload={
                "face": self.face,
                "action": self.action,
                "led": self.led,
                "emotion": self.emotion,
            },
        )


def make_safe_response() -> AgentResponse:
    """Return a safe default AgentResponse used as fallback."""
    return AgentResponse(
        reply="...",
        emotion="neutral",
        face="normal",
        action="idle",
        led="off",
        voice_style="normal",
        need_hardware=False,
    )


# ---------------------------------------------------------------------------
# Hardware communication protocol
# ---------------------------------------------------------------------------


class HardwareCommand(BaseModel):
    """Abstract command sent from PC to hardware.

    Software MUST NOT include low-level hardware details (GPIO, servo angles, etc.).
    Hardware interprets abstract commands on its own.
    """

    type: Literal["command"] = "command"
    id: str = Field(..., description="Unique command id, e.g. cmd_001.")
    command: str = Field(
        default="perform",
        description="Command type: perform, reset, ping, configure.",
    )
    payload: dict[str, str] = Field(
        default_factory=dict,
        description="Abstract payload, e.g. {face: smile, action: wave, led: warm}.",
    )


# ---------------------------------------------------------------------------
# Chat message
# ---------------------------------------------------------------------------


class ChatMessage(BaseModel):
    """A single message in the chat history."""

    role: Literal["user", "assistant", "system"] = "user"
    content: str = ""
    agent_response: AgentResponse | None = Field(
        default=None,
        description="Parsed AgentResponse when role is assistant.",
    )
