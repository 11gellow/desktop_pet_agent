"""
Pydantic schemas for data validation.

All LLM output must be validated against AgentResponse.
All hardware communication uses HardwareCommand / HardwareEvent.

Note: field_validator removed from this module's imports.
Consumer code should import it from pydantic directly.
"""

from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, Field

# Re-export core types from app/ (single source of truth)
from app.agent.schemas import AgentResponse, ChatMessage, HardwareCommand, make_safe_response


# ---------------------------------------------------------------------------
# Hardware communication protocol
# ---------------------------------------------------------------------------

# Hardware protocol command/event type constants.
# Available for use by HardwareCommand.type and HardwareEvent.type fields.
CommandType = Literal["command", "event"]


class HardwareEvent(BaseModel):
    """Event reported from hardware back to PC."""

    type: Literal["event"] = "event"
    id: str = Field(default="", description="Event id, or cmd id if this is an ack.")
    event: str = Field(..., description="Event type: ack, touch, shake, button, sensor.")
    payload: dict[str, str] = Field(
        default_factory=dict,
        description="Event payload, e.g. {sensor: touch_head, value: 1}.",
    )
