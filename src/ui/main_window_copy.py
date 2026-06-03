"""
Main application window.

Layout:
┌──────────┬──────────────────────────────┐
│          │                              │
│  Nav     │  Content Area                │
│  (list)  │  (QStackedWidget)            │
│          │                              │
│          │                              │
└──────────┴──────────────────────────────┘

The navigation bar on the left switches pages in the content area on the right.
"""

from __future__ import annotations

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QHBoxLayout,
    QListWidget,
    QListWidgetItem,
    QMainWindow,
    QSplitter,
    QStackedWidget,
    QWidget,
)

from src.ui.pages.chat_page import ChatPage
from src.ui.pages.character_settings_page import CharacterSettingsPage
from src.ui.pages.hardware_settings_page import HardwareSettingsPage
from src.ui.pages.hardware_simulator_page import HardwareSimulatorPage
from src.ui.pages.logs_page import LogsPage
from src.ui.pages.memory_page import MemoryPage
from src.ui.pages.model_settings_page import ModelSettingsPage


class MainWindow(QMainWindow):
    """Main application window with sidebar navigation."""

    WINDOW_TITLE = "Desktop Pet Agent"
    DEFAULT_WIDTH = 1000
    DEFAULT_HEIGHT = 680

    def __init__(self, agent_engine: object | None = None) -> None:
        super().__init__()

        self.setWindowTitle(self.WINDOW_TITLE)
        self.resize(self.DEFAULT_WIDTH, self.DEFAULT_HEIGHT)

        # Central widget with horizontal splitter
        central = QWidget()
        self.setCentralWidget(central)

        splitter = QSplitter(Qt.Orientation.Horizontal)
        layout = QHBoxLayout(central)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.addWidget(splitter)

        # -- Left sidebar: navigation list --
        self._nav_list = QListWidget()
        self._nav_list.setFixedWidth(180)
        self._nav_list.setStyleSheet(
            "QListWidget { background: #2c2c2c; color: #e0e0e0; border: none; }"
            "QListWidget::item { padding: 10px; font-size: 14px; }"
            "QListWidget::item:selected { background: #3a6ea5; }"
        )

        # -- Right side: stacked pages --
        self._stack = QStackedWidget()

        self._chat_page = ChatPage(agent_engine=agent_engine)

        self._pages: list[tuple[str, QWidget]] = [
            ("Chat", self._chat_page),
            ("Model Settings", ModelSettingsPage()),
            ("Character Settings", CharacterSettingsPage()),
            ("Hardware Settings", HardwareSettingsPage()),
            ("Hardware Simulator", HardwareSimulatorPage()),
            ("Memory", MemoryPage()),
            ("Logs", LogsPage()),
        ]

        for label, page in self._pages:
            item = QListWidgetItem(label)
            self._nav_list.addItem(item)
            self._stack.addWidget(page)

        splitter.addWidget(self._nav_list)
        splitter.addWidget(self._stack)
        splitter.setStretchFactor(0, 0)  # nav doesn't stretch
        splitter.setStretchFactor(1, 1)  # content stretches

        # Connect navigation
        self._nav_list.currentRowChanged.connect(self._stack.setCurrentIndex)

        # Default to first page
        self._nav_list.setCurrentRow(0)
