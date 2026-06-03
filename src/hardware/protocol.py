"""
Hardware communication protocol helpers.

Defines the abstract command/event format used between PC and hardware.
No low-level hardware control logic lives here.
"""

from __future__ import annotations

from src.core.schemas import HardwareCommand, HardwareEvent


class HardwareProtocol:
    """Factory and validation helpers for the hardware protocol."""

    @staticmethod
    def make_command(
        cmd_id: str,
        command: str = "perform",
        payload: dict[str, str] | None = None,
    ) -> HardwareCommand:
        """Create a HardwareCommand with a unique id."""
        return HardwareCommand(
            id=cmd_id,
            command=command,
            payload=payload or {},
        )

    @staticmethod
    def parse_event(raw: dict[str, object]) -> HardwareEvent:
        """Parse and validate an incoming event from hardware."""
        return HardwareEvent.model_validate(raw)
