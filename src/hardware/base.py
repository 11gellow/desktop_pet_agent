"""
Abstract hardware interface.

All hardware backends (real serial, mock, simulator) implement this interface.
"""

from __future__ import annotations

from abc import ABC, abstractmethod

from app.agent.schemas import HardwareCommand, HardwareEvent


class BaseHardware(ABC):
    """Abstract interface for sending commands to and receiving events from hardware."""

    @abstractmethod
    async def connect(self) -> None:
        """Establish connection to hardware."""
        ...

    @abstractmethod
    async def disconnect(self) -> None:
        """Close connection to hardware."""
        ...

    @abstractmethod
    async def send_command(self, command: HardwareCommand) -> None:
        """Send an abstract command to hardware."""
        ...

    @abstractmethod
    async def receive_event(self) -> HardwareEvent | None:
        """Receive one event from hardware (non-blocking, returns None if no event)."""
        ...

    @abstractmethod
    def is_connected(self) -> bool:
        """Return True if the hardware connection is active."""
        ...
