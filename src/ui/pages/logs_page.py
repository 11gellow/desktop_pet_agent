"""
Logs page (placeholder).

TODO: Show:
  - Scrollable log viewer (read from log file or in-memory buffer)
  - Log level filter (DEBUG, INFO, WARNING, ERROR)
  - Auto-scroll toggle
  - Clear log button
  - Export log button
"""

from src.ui.pages.base_page import BasePage


class LogsPage(BasePage):
    page_title = "Logs"
