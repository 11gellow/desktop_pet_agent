"""
Mock hardware backend.

Accepts commands silently and produces no events.  Used when no hardware
or simulator is needed.
"""

from __future__ import annotations

from src.core.schemas import HardwareCommand, HardwareEvent
from src.hardware.base import BaseHardware


class MockHardware(BaseHardware):
    """A no-op hardware backend that always succeeds."""

    def __init__(self) -> None:
        self._connected = False

    async def connect(self) -> None:
        self._connected = True

    async def disconnect(self) -> None:
        self._connected = False

    async def send_command(self, command: HardwareCommand) -> None:
        """Discard the command silently."""
        _ = command

    async def receive_event(self) -> HardwareEvent | None:
        return None

    def is_connected(self) -> bool:
        return self._connected
