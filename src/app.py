"""
Application bootstrap.

Creates all subsystems, wires them together, and starts the Qt event loop.
"""

from __future__ import annotations

import logging
import os

from src.agent.engine import AgentEngine
from src.core.config import get_config
from src.hardware.simulator import HardwareSimulator
from src.llm.mock_llm import MockLLM
from src.llm.openai_llm import OpenAILLM
from src.memory.simple_memory import SimpleMemory
from src.ui.main_window import MainWindow
from src.utils.logger import setup_logging, get_logger
from src.voice.mock_voice import MockVoice


class Application:
    """Bootstraps and owns the lifetime of all subsystems."""

    def __init__(self) -> None:
        self.config = get_config()

        # Logging
        self.logger: logging.Logger = setup_logging(
            log_level=self.config.log_level,
            log_file=self.config.data_dir / "app.log",
        )

        # LLM: use real backend when API key is set, otherwise mock
        if self.config.llm_api_key:
            get_logger("app").info(
                "Using OpenAI-compatible LLM: %s @ %s",
                self.config.llm_model,
                self.config.llm_base_url,
            )
            self.llm = OpenAILLM(
                api_key=self.config.llm_api_key,
                base_url=self.config.llm_base_url,
                model=self.config.llm_model,
            )
        else:
            get_logger("app").info("No LLM_API_KEY set, using MockLLM")
            self.llm = MockLLM()

        # Agent backend selection
        agent_backend = os.getenv("AGENT_BACKEND", "engine")
        if agent_backend == "pet_brain":
            # Use app/ PetAgentBrain (lazy import to avoid httpx dependency in engine mode)
            from app.agent.brain import PetAgentBrain
            from app.llm.openai_compatible import OpenAICompatibleClient as AppOpenAICompatibleClient

            if self.config.llm_api_key:
                app_llm = AppOpenAICompatibleClient(
                    api_key=self.config.llm_api_key,
                    base_url=self.config.llm_base_url,
                    model=self.config.llm_model,
                )
            else:
                from app.llm.mock import MockLLMClient
                app_llm = MockLLMClient()
            self.agent = PetAgentBrain(llm=app_llm)
            get_logger("app").info("Using PetAgentBrain with %s", type(app_llm).__name__)
        else:
            # Existing AgentEngine path (default)
            self.memory = SimpleMemory(max_turns=self.config.memory_max_turns)
            self.agent = AgentEngine(llm=self.llm, memory=self.memory)

        # Shared subsystems
        self.hardware = HardwareSimulator()
        self.voice = MockVoice()

        # UI
        self.main_window = MainWindow(agent_engine=self.agent, hardware=self.hardware, voice=self.voice)

        get_logger("app").info("Application initialized")

    def run(self) -> None:
        """Show the main window and start the Qt event loop."""
        self.main_window.show()
        get_logger("app").info("Main window shown, entering event loop")
