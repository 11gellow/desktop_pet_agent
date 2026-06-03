"""
Character profile management for the app/ agent layer.

Self-contained copy so the app/ module does not depend on src/agent/.
"""

from __future__ import annotations

from dataclasses import dataclass, field


@dataclass
class CharacterProfile:
    """Defines the pet's identity and behavior parameters."""

    name: str = "Pebo"
    description: str = "A friendly desktop companion pet."
    personality: str = "cheerful, curious, empathetic"
    backstory: str = ""
    speaking_style: str = "casual and warm, uses emoji occasionally"
    temperature: float = 0.8

    # Optional constraints
    max_reply_length: int = 200
    preferred_language: str = "zh-CN"

    def to_system_prompt(self) -> str:
        """Build a system-prompt string from this profile for the LLM."""
        # JSON instruction MUST come first — DeepSeek json_object mode
        # requires "json" keyword prominently in the prompt.
        parts = [
            "JSON output mode. You are a JSON generator.",
            "",
            f"You are {self.name}, {self.description}.",
            f"Personality: {self.personality}.",
            f"Speaking style: {self.speaking_style}.",
        ]
        if self.backstory:
            parts.append(f"Backstory: {self.backstory}.")
        parts.append(f"Keep replies under {self.max_reply_length} characters.")
        parts.append(
            "\n"
            "--- OUTPUT FORMAT (STRICT REQUIREMENT) ---\n"
            "CRITICAL: You MUST output a single JSON object. Do NOT add any text before or after the JSON.\n"
            "Do NOT wrap the JSON in markdown code fences.\n"
            "\n"
            '{"reply": "<your reply text in Chinese>",'
            '"emotion": "happy|sad|surprised|neutral|curious|excited",'
            '"face": "smile|frown|surprised|normal|wink|blink",'
            '"action": "wave|nod|shake_head|idle|bounce|tilt_head",'
            '"led": "warm|cool|breath|rainbow|off",'
            '"voice_style": "normal|cheerful|whisper|serious",'
            '"need_hardware": true|false}\n'
            "\n"
            'Example: {"reply": "哈哈，我也很开心！你今天想聊什么呀？😊", "emotion": "happy", "face": "smile", "action": "bounce", "led": "warm", "voice_style": "cheerful", "need_hardware": true}'
        )
        return "\n".join(parts)

    @classmethod
    def default(cls) -> CharacterProfile:
        """Return the default character profile."""
        return cls()
