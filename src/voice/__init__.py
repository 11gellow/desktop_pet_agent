# Voice module: abstract interface + mock implementation
from src.voice.base import BaseVoice
from src.voice.mock_voice import MockVoice

__all__ = ["BaseVoice", "MockVoice"]
