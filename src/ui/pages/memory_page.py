"""
Memory page (placeholder).

TODO: Show:
  - Conversation history viewer (scrollable list)
  - Memory statistics (total turns, token count estimate)
  - Clear memory button
  - Export conversation button
  - Search / filter input
"""

from src.ui.pages.base_page import BasePage


class MemoryPage(BasePage):
    page_title = "Memory"
