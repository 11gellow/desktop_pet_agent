"""
Chat page.

Pet chat with emoji expressions and bubble-style messages.
"""

from __future__ import annotations

import asyncio

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QPushButton,
    QScrollArea,
    QVBoxLayout,
    QWidget,
)

from app.agent.schemas import AgentResponse
from src.ui.pages.base_page import BasePage


# ---------------------------------------------------------------------------
# Emoji mappings for pet expressions
# ---------------------------------------------------------------------------

EMOTION_EMOJI = {
    "happy": "😊", "sad": "😢", "surprised": "😲",
    "neutral": "😐", "curious": "🤔", "excited": "🥳",
    "angry": "😠", "sleepy": "😴",
}

FACE_EMOJI = {
    "smile": "😊", "frown": "😟", "surprised": "😲",
    "normal": "😐", "wink": "😉", "blink": "😉",
}

ACTION_EMOJI = {
    "wave": "👋", "nod": "👍", "shake_head": "🙂‍↔️",
    "idle": "", "bounce": "🦘", "tilt_head": "🤔",
}

LED_COLORS = {
    "warm": "#F59E0B", "cool": "#3B82F6", "breath": "#8B5CF6",
    "rainbow": "#EC4899", "off": "#64748B",
}


def _pet_emoji(response: AgentResponse) -> str:
    """Pick the best emoji for the pet's current state."""
    return FACE_EMOJI.get(response.face) or EMOTION_EMOJI.get(response.emotion, "😐")


def _action_indicator(response: AgentResponse) -> str:
    """Build a one-line action + led indicator string."""
    parts = []
    a = ACTION_EMOJI.get(response.action, "")
    if a:
        parts.append(a)
    if response.action != "idle":
        parts.append(response.action.replace("_", " "))
    led_emoji = "🔵" if response.led != "off" else "⚫"
    parts.append(f"{led_emoji} {response.led}")
    return "  ".join(parts)


# ---------------------------------------------------------------------------
# Chat page
# ---------------------------------------------------------------------------

class ChatPage(BasePage):
    """Chat page with emoji pet expressions and bubble messages."""

    page_title = "Chat"

    def __init__(
        self,
        agent_engine: object | None = None,
        parent: QWidget | None = None,
    ) -> None:
        self._agent = agent_engine
        self._message_area: QVBoxLayout | None = None
        self._scroll: QScrollArea | None = None
        self._input_field: QLineEdit | None = None
        self._send_btn: QPushButton | None = None
        super().__init__(parent)

    def set_agent_engine(self, agent_engine: object) -> None:
        """Inject the agent engine after construction."""
        self._agent = agent_engine

    def _build_ui(self) -> None:
        super()._build_ui()

        layout = self.layout()
        if layout is None:
            return

        # Scrollable message area
        self._scroll = QScrollArea()
        self._scroll.setWidgetResizable(True)
        self._scroll.setStyleSheet(
            "QScrollArea { border: none; background: #121418; }"
        )

        message_container = QWidget()
        message_container.setStyleSheet("background: #121418;")
        self._message_area = QVBoxLayout(message_container)
        self._message_area.setAlignment(Qt.AlignmentFlag.AlignTop)
        self._message_area.setSpacing(8)
        self._message_area.addStretch()
        self._scroll.setWidget(message_container)

        # Input row
        input_row = QHBoxLayout()
        self._input_field = QLineEdit()
        self._input_field.setPlaceholderText("和 Pebo 说点什么...")
        self._input_field.returnPressed.connect(self._on_send)

        self._send_btn = QPushButton("发送")
        self._send_btn.clicked.connect(self._on_send)

        input_row.addWidget(self._input_field, 1)
        input_row.addWidget(self._send_btn)

        layout.addWidget(self._scroll, 1)
        layout.addLayout(input_row)

    # ------------------------------------------------------------------
    # Send flow
    # ------------------------------------------------------------------

    def _on_send(self) -> None:
        text = self._input_field.text().strip() if self._input_field else ""
        if not text:
            return

        self._add_user_bubble(text)
        self._input_field.clear()
        self._set_input_enabled(False)

        if self._agent is None:
            self._add_system_note("Agent 未连接")
            self._set_input_enabled(True)
            return

        asyncio.ensure_future(self._process_message(text))

    async def _process_message(self, text: str) -> None:
        try:
            response = await self._agent.process_user_message(text)
            self._add_pet_bubble(self._agent.character.name, response)
        except Exception:
            self._add_system_note("出了点问题，请重试")
        finally:
            self._set_input_enabled(True)

    # ------------------------------------------------------------------
    # Bubble rendering
    # ------------------------------------------------------------------

    def _add_user_bubble(self, text: str) -> None:
        """User message — right-aligned, blue bubble."""
        if self._message_area is None:
            return

        wrapper = QWidget()
        row = QHBoxLayout(wrapper)
        row.setContentsMargins(40, 4, 8, 4)
        row.addStretch()

        bubble = QLabel(text)
        bubble.setWordWrap(True)
        bubble.setMaximumWidth(420)
        bubble.setStyleSheet(
            "background: #3B82F6; color: white; border-radius: 12px;"
            "padding: 10px 14px; font-size: 14px;"
        )
        row.addWidget(bubble)

        self._message_area.insertWidget(self._message_area.count() - 1, wrapper)
        self._defer_scroll()

    def _add_pet_bubble(self, name: str, response: AgentResponse) -> None:
        """Pet message — left-aligned with emoji avatar, dark bubble."""
        if self._message_area is None:
            return

        emoji = _pet_emoji(response)
        action_text = _action_indicator(response)

        wrapper = QWidget()
        row = QHBoxLayout(wrapper)
        row.setContentsMargins(8, 4, 40, 4)

        # Emoji avatar
        avatar = QLabel(emoji)
        avatar.setFixedWidth(36)
        avatar.setAlignment(Qt.AlignmentFlag.AlignTop)
        avatar.setStyleSheet("font-size: 26px; background: transparent;")
        row.addWidget(avatar)

        # Bubble content
        bubble = QWidget()
        bubble.setMaximumWidth(420)
        bubble_layout = QVBoxLayout(bubble)
        bubble_layout.setContentsMargins(0, 0, 0, 0)
        bubble_layout.setSpacing(4)

        # Name + reply
        body = QLabel(f"<b style='color:#F8FAFC;'>{name}</b>")
        body.setStyleSheet("font-size: 12px; background: transparent;")
        bubble_layout.addWidget(body)

        reply = QLabel(response.reply)
        reply.setWordWrap(True)
        reply.setStyleSheet("color: #E2E8F0; font-size: 14px; background: transparent;")
        bubble_layout.addWidget(reply)

        # Action / LED indicator bar
        if action_text:
            bar = QLabel(action_text)
            bar.setStyleSheet(
                "color: #94A3B8; font-size: 11px; background: transparent;"
                "padding-top: 2px;"
            )
            bubble_layout.addWidget(bar)

        # Bubble background
        bubble.setStyleSheet(
            "background: #1A1D24; border-radius: 12px;"
            "padding: 10px 14px; border: 1px solid #2D3139;"
        )
        row.addWidget(bubble)
        row.addStretch()

        self._message_area.insertWidget(self._message_area.count() - 1, wrapper)
        self._defer_scroll()

    def _defer_scroll(self):
        """Scroll to bottom after Qt finishes layout."""
        from PySide6.QtCore import QTimer
        if self._scroll:
            QTimer.singleShot(0, lambda: self._scroll.verticalScrollBar().setValue(
                self._scroll.verticalScrollBar().maximum()))

    def _add_system_note(self, text: str) -> None:
        """Centered grey system note."""
        if self._message_area is None:
            return

        label = QLabel(f"<span style='color:#64748B;font-size:12px;'>{text}</span>")
        label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self._message_area.insertWidget(self._message_area.count() - 1, label)
        self._defer_scroll()

    # ------------------------------------------------------------------
    # Input state
    # ------------------------------------------------------------------

    def _set_input_enabled(self, enabled: bool) -> None:
        if self._input_field:
            self._input_field.setEnabled(enabled)
        if self._send_btn:
            self._send_btn.setEnabled(enabled)
        if enabled and self._input_field:
            self._input_field.setFocus()
