"""
Hardware simulator.

Maintains virtual hardware state (face, action, led, emotion) in memory
so the full pipeline can run without real hardware.  Provides a simple
state-machine that the UI can visualize in the hardware simulator page.

TODO (future):
  - Support configurable event injection (simulate touch, shake, button press)
    for testing the full event loop.
  - Add a timer that produces periodic sensor events.
"""

from __future__ import annotations

from app.agent.schemas import HardwareCommand, HardwareEvent
from src.hardware.base import BaseHardware


class HardwareSimulator(BaseHardware):
    """Simulates hardware by keeping virtual state in memory."""

    def __init__(self) -> None:
        self._connected = False
        self._pending_events: list[HardwareEvent] = []

        # Virtual hardware state — what the "hardware" is currently displaying
        self.current_face: str = "normal"
        self.current_action: str = "idle"
        self.current_led: str = "off"
        self.current_emotion: str = "neutral"

    # ------------------------------------------------------------------
    # BaseHardware interface
    # ------------------------------------------------------------------

    async def connect(self) -> None:
        self._connected = True

    async def disconnect(self) -> None:
        self._connected = False

    async def send_command(self, command: HardwareCommand) -> None:
        """Apply the command payload to the virtual hardware state."""
        if command.command == "perform":
            payload = command.payload
            self.current_face = payload.get("face", self.current_face)
            self.current_action = payload.get("action", self.current_action)
            self.current_led = payload.get("led", self.current_led)
            self.current_emotion = payload.get("emotion", self.current_emotion)

            # Auto-generate an ack event
            ack = HardwareEvent(
                id=command.id,
                event="ack",
                payload={"status": "ok"},
            )
            self._pending_events.append(ack)
        # Other command types (ping, reset, configure) can be added here.
        # For now they are silently acknowledged.
        else:
            self._pending_events.append(
                HardwareEvent(id=command.id, event="ack", payload={"status": "ok"})
            )

    async def receive_event(self) -> HardwareEvent | None:
        """Pop and return the oldest pending event, or None."""
        if self._pending_events:
            return self._pending_events.pop(0)
        return None

    def is_connected(self) -> bool:
        return self._connected

    # ------------------------------------------------------------------
    # Simulator-specific helpers
    # ------------------------------------------------------------------

    def inject_event(self, event: HardwareEvent) -> None:
        """Inject a synthetic event (e.g. touch, shake) for testing."""
        self._pending_events.append(event)

    def get_state(self) -> dict[str, str]:
        """Return a snapshot of the current virtual hardware state."""
        return {
            "face": self.current_face,
            "action": self.current_action,
            "led": self.current_led,
            "emotion": self.current_emotion,
        }

    def reset_state(self) -> None:
        """Reset virtual hardware to defaults."""
        self.current_face = "normal"
        self.current_action = "idle"
        self.current_led = "off"
        self.current_emotion = "neutral"
        self._pending_events.clear()
