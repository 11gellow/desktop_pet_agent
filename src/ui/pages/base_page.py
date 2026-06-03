"""
Base page widget.

All content pages inherit from this class to ensure a consistent interface.
"""

from __future__ import annotations

from PySide6.QtWidgets import QLabel, QVBoxLayout, QWidget


class BasePage(QWidget):
    """Base class for all content pages in the main window."""

    page_title: str = "Page"

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self._build_ui()

    def _build_ui(self) -> None:
        """Create the page UI.  Override in subclasses."""
        layout = QVBoxLayout(self)
        title_label = QLabel(self.page_title)
        title_label.setStyleSheet("font-size: 18px; font-weight: bold; padding: 10px;")
        layout.addWidget(title_label)
        layout.addStretch()
