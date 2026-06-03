"""
Custom exception hierarchy for the Desktop Pet Agent.

All application-specific errors inherit from DesktopPetError so they can be
caught at a single point in the UI layer.
"""


class DesktopPetError(Exception):
    """Base exception for all application errors."""

    def __init__(self, message: str = "", *, detail: str | None = None) -> None:
        super().__init__(message)
        self.detail = detail or message


class ConfigError(DesktopPetError):
    """Configuration-related errors (missing key, invalid format, etc.)."""


class LLMError(DesktopPetError):
    """LLM call failures (network, API error, invalid response)."""


class HardwareError(DesktopPetError):
    """Hardware communication errors (serial timeout, disconnect)."""


class MemoryError(DesktopPetError):
    """Memory system errors (storage failure, corruption)."""


class VoiceError(DesktopPetError):
    """Voice module errors (TTS/STT failure)."""
