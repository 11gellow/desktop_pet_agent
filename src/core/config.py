"""
Configuration system.

Loads configuration from environment variables and/or a config file.
API keys MUST NOT be hardcoded.
"""

import os
from dataclasses import dataclass, field
from pathlib import Path


@dataclass
class AppConfig:
    """Application configuration loaded from environment."""

    # LLM settings
    llm_api_key: str = field(default_factory=lambda: os.getenv("LLM_API_KEY", ""))
    llm_base_url: str = field(
        default_factory=lambda: os.getenv("LLM_BASE_URL", "https://api.openai.com/v1")
    )
    llm_model: str = field(default_factory=lambda: os.getenv("LLM_MODEL", "gpt-4o-mini"))

    # Hardware settings
    hardware_port: str = field(default_factory=lambda: os.getenv("HARDWARE_PORT", "COM3"))
    hardware_baudrate: int = field(
        default_factory=lambda: int(os.getenv("HARDWARE_BAUDRATE", "115200"))
    )
    use_hardware_simulator: bool = field(
        default_factory=lambda: os.getenv("USE_HARDWARE_SIMULATOR", "true").lower() == "true"
    )

    # Voice settings
    voice_enabled: bool = field(
        default_factory=lambda: os.getenv("VOICE_ENABLED", "false").lower() == "true"
    )

    # Memory settings
    memory_max_turns: int = field(
        default_factory=lambda: int(os.getenv("MEMORY_MAX_TURNS", "50"))
    )

    # Logging
    log_level: str = field(default_factory=lambda: os.getenv("LOG_LEVEL", "INFO"))

    # Data directory
    data_dir: Path = field(
        default_factory=lambda: Path(
            os.getenv("DESKTOP_PET_DATA_DIR", str(Path.home() / ".desktop_pet_agent"))
        )
    )

    def ensure_data_dir(self) -> None:
        """Create the data directory if it does not exist."""
        self.data_dir.mkdir(parents=True, exist_ok=True)


# Global config instance (created on first import)
_config_instance: AppConfig | None = None


def get_config() -> AppConfig:
    """Get the global AppConfig singleton."""
    global _config_instance
    if _config_instance is None:
        _config_instance = AppConfig()
        _config_instance.ensure_data_dir()
    return _config_instance


def reset_config() -> None:
    """Reset the config singleton (useful for testing)."""
    global _config_instance
    _config_instance = None
