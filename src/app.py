"""
Application bootstrap.

Creates all subsystems, wires them together, starts the Qt event loop.
"""

from __future__ import annotations

import logging

from PySide6.QtCore import QTimer

from app.agent.brain import PetAgentBrain
from app.agent.state import AgentState
from app.llm.mock import MockLLMClient
from app.llm.openai_compatible import OpenAICompatibleClient
from src.core.config import get_config
from src.hardware.simulator import HardwareSimulator
from src.ui.main_window import MainWindow
from src.ui.pet_window import PetWindow
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

        # LLM
        if self.config.llm_api_key:
            get_logger("app").info(
                "Using OpenAI-compatible LLM: %s @ %s",
                self.config.llm_model, self.config.llm_base_url,
            )
            llm = OpenAICompatibleClient(
                api_key=self.config.llm_api_key,
                base_url=self.config.llm_base_url,
                model=self.config.llm_model,
            )
        else:
            get_logger("app").info("No LLM_API_KEY set, using MockLLM")
            llm = MockLLMClient()

        # Agent brain
        self.agent = PetAgentBrain(llm=llm)

        # Shared subsystems
        self.hardware = HardwareSimulator()
        self.voice = MockVoice()

        # Agent state
        self.state = AgentState()

        # Desktop pet window
        self.pet_window = PetWindow(agent_engine=self.agent, state=self.state)
        self.pet_window.show()

        # State tick timer — 1 Hz
        self._state_timer = QTimer()
        self._state_timer.timeout.connect(lambda: self.pet_window.tick_state(1.0))
        self._state_timer.start(1000)

        # Control panel
        self.main_window = MainWindow(
            agent_engine=self.agent, hardware=self.hardware, voice=self.voice,
        )

        get_logger("app").info("Application initialized")

    def run(self) -> None:
        self.main_window.show()
        get_logger("app").info("Control panel shown, pet active, entering event loop")
