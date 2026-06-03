"""
Desktop pet window — frameless, always-on-top, walks around screen.

Drawn blob character with eyes/mouth.  Chat bubbles float as independent
tool windows.  Movement is horizontal-biased; moving up = slow crawl.
"""

from __future__ import annotations

import asyncio
import math
import random
import time

from PySide6.QtCore import Qt, QTimer, QRect, QPoint, QSize
from PySide6.QtGui import QColor, QPainter, QPen, QBrush, QFont
from PySide6.QtWidgets import (
    QApplication,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QPushButton,
    QVBoxLayout,
    QWidget,
)

from app.agent.schemas import AgentResponse
from src.utils.logger import get_logger

logger = get_logger("pet")

# ══════════════════════════════════════════════════════════════════════
# Emotion → colour + mouth shape
# ══════════════════════════════════════════════════════════════════════

EMOTION_COLORS = {
    "happy":     QColor(255, 180, 80),
    "excited":   QColor(255, 140, 60),
    "sad":       QColor(120, 160, 220),
    "angry":     QColor(220, 90, 80),
    "surprised": QColor(255, 210, 100),
    "curious":   QColor(180, 140, 240),
    "neutral":   QColor(180, 200, 180),
    "sleepy":    QColor(160, 180, 200),
}


def _mouth_for_emotion(emotion: str) -> str:
    return {
        "happy": "smile", "excited": "open", "sad": "frown",
        "angry": "zigzag", "surprised": "o",
        "curious": "smirk", "neutral": "flat",
        "sleepy": "yawn",
    }.get(emotion, "flat")


# ══════════════════════════════════════════════════════════════════════
# PetCharacter — drawn blob
# ══════════════════════════════════════════════════════════════════════

class PetCharacter(QWidget):
    """QPainter-drawn blob pet with eyes and emotion-driven mouth."""

    SIZE = 80

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self._emotion = "neutral"
        self._facing_right = True
        self.setFixedSize(self.SIZE, self.SIZE)

    def set_emotion(self, emotion: str) -> None:
        self._emotion = emotion
        self.update()

    def set_facing(self, right: bool) -> None:
        self._facing_right = right
        self.update()

    def paintEvent(self, event) -> None:
        p = QPainter(self)
        p.setRenderHint(QPainter.RenderHint.Antialiasing)

        color = EMOTION_COLORS.get(self._emotion, EMOTION_COLORS["neutral"])
        w, h = self.width(), self.height()
        cx, cy = w / 2, h / 2
        r = min(w, h) / 2 - 4

        # ── body (circle with slight squash) ──
        body_color = QColor(color)
        p.setBrush(QBrush(body_color))
        p.setPen(QPen(body_color.darker(130), 2))
        p.drawEllipse(QPoint(int(cx), int(cy)), int(r), int(r * 0.92))

        # ── cheeks (lighter blush) ──
        blush = QColor(color.lighter(130))
        blush.setAlpha(120)
        p.setBrush(QBrush(blush))
        p.setPen(Qt.PenStyle.NoPen)
        p.drawEllipse(QPoint(int(cx - r * 0.55), int(cy + r * 0.2)), int(r * 0.22), int(r * 0.15))
        p.drawEllipse(QPoint(int(cx + r * 0.55), int(cy + r * 0.2)), int(r * 0.22), int(r * 0.15))

        # ── eyes (white + pupil) ──
        eye_y = int(cy - r * 0.18)
        eye_offset = int(r * 0.32)
        eye_r = int(r * 0.2)
        pupil_r = int(eye_r * 0.5)
        pupil_dir = 1 if self._facing_right else -1

        for side in [-1, 1]:
            ex = int(cx + side * eye_offset)
            p.setBrush(QBrush(Qt.GlobalColor.white))
            p.setPen(QPen(Qt.GlobalColor.black, 1))
            p.drawEllipse(QPoint(ex, eye_y), eye_r, eye_r)
            # pupil (looks in movement direction)
            px = int(ex + pupil_dir * eye_r * 0.25)
            p.setBrush(QBrush(Qt.GlobalColor.black))
            p.drawEllipse(QPoint(px, eye_y), pupil_r, pupil_r)

        # ── mouth ──
        mouth_shape = _mouth_for_emotion(self._emotion)
        p.setPen(QPen(Qt.GlobalColor.black, 2))
        my = int(cy + r * 0.35)
        mw = int(r * 0.5)

        if mouth_shape == "smile":
            p.drawArc(int(cx - mw), int(my - mw), mw * 2, mw * 2, 0, -180 * 16)
        elif mouth_shape == "frown":
            p.drawArc(int(cx - mw), int(my), mw * 2, mw * 2, 0, 180 * 16)
        elif mouth_shape == "open":
            p.drawChord(int(cx - mw // 2), int(my - mw // 3), mw, mw // 2, 0, 180 * 16)
        elif mouth_shape == "o":
            p.drawEllipse(QPoint(int(cx), int(my + mw // 4)), mw // 3, mw // 3)
        elif mouth_shape == "flat":
            p.drawLine(int(cx - mw), int(my + mw // 4), int(cx + mw), int(my + mw // 4))
        elif mouth_shape == "smirk":
            p.drawArc(int(cx), int(my - mw // 2), mw, mw, 0, -180 * 16)
        elif mouth_shape == "yawn":
            p.drawChord(int(cx - mw), int(my - mw // 2), mw * 2, mw, 0, 180 * 16)
        elif mouth_shape == "zigzag":
            zx = int(cx - mw)
            zy = int(my)
            path = [QPoint(zx, zy), QPoint(zx + mw // 3, zy + 6), QPoint(zx + 2 * mw // 3, zy - 2), QPoint(zx + mw, zy + 4)]
            for i in range(len(path) - 1):
                p.drawLine(path[i], path[i + 1])

        p.end()


# ══════════════════════════════════════════════════════════════════════
# PetBubble — floating chat bubble (independent tool window)
# ══════════════════════════════════════════════════════════════════════

class PetBubble(QWidget):
    """Independent frameless bubble that floats above the pet."""

    def __init__(self, text: str, is_user: bool = False) -> None:
        super().__init__(None)
        self.setWindowFlags(
            Qt.WindowType.FramelessWindowHint
            | Qt.WindowType.Tool
            | Qt.WindowType.WindowStaysOnTopHint
        )
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        self.setAttribute(Qt.WidgetAttribute.WA_ShowWithoutActivating)

        label = QLabel(text, self)
        label.setWordWrap(True)
        label.setMaximumWidth(220)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.addWidget(label)

        if is_user:
            label.setStyleSheet(
                "background: #3B82F6; color: white; border-radius: 10px;"
                "padding: 8px 12px; font-size: 13px;"
            )
        else:
            label.setStyleSheet(
                "background: #1A1D24; color: #E2E8F0; border-radius: 10px;"
                "padding: 8px 12px; font-size: 13px; border: 1px solid #3B82F6;"
            )

        label.adjustSize()
        self.adjustSize()
        self._created = time.time()

    def age(self) -> float:
        return time.time() - self._created


# ══════════════════════════════════════════════════════════════════════
# PetWindow
# ══════════════════════════════════════════════════════════════════════

class PetWindow(QWidget):
    """Frameless desktop pet — drawn blob + chat bubbles + movement."""

    MOVE_INTERVAL = 80    # ms
    IDLE_INTERVAL = 4000  # ms
    BUBBLE_LIFETIME = 6.0  # seconds

    def __init__(self, agent_engine, state, parent=None) -> None:
        super().__init__(parent)
        self._agent = agent_engine
        self._state = state

        # ── window ──
        self.setWindowFlags(
            Qt.WindowType.FramelessWindowHint
            | Qt.WindowType.Tool
            | Qt.WindowType.WindowStaysOnTopHint
        )
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        self.setAttribute(Qt.WidgetAttribute.WA_ShowWithoutActivating)
        self.setFixedSize(120, 140)

        screen = QApplication.primaryScreen()
        self._move_bounds = (
            screen.availableGeometry()
            if screen
            else QRect(0, 0, 1920, 1080)
        )

        # Start center-bottom
        self.move(self._move_bounds.center().x(), self._move_bounds.bottom() - 250)

        # ── pet character widget ──
        self._pet = PetCharacter(self)
        self._pet.move(20, 10)

        # ── chat input (hidden) ──
        self._input_widget = QWidget(self)
        self._input_widget.setVisible(False)
        self._input_widget.move(20, -35)
        row = QHBoxLayout(self._input_widget)
        row.setContentsMargins(0, 0, 0, 0)

        self._input_field = QLineEdit()
        self._input_field.setPlaceholderText("说点什么...")
        self._input_field.setFixedWidth(150)
        self._input_field.setStyleSheet(
            "background: #1A1D24; color: #F8FAFC; border: 1px solid #3B82F6;"
            "border-radius: 8px; padding: 5px 8px; font-size: 12px;"
        )
        self._input_field.returnPressed.connect(self._on_chat_send)

        btn = QPushButton("→")
        btn.setFixedWidth(28)
        btn.setStyleSheet(
            "background: #3B82F6; color: white; border: none; border-radius: 6px;"
            "padding: 4px; font-size: 12px;"
        )
        btn.clicked.connect(self._on_chat_send)
        row.addWidget(self._input_field)
        row.addWidget(btn)

        # ── bubbles (independent windows) ──
        self._bubbles: list[PetBubble] = []

        # ── timers ──
        self._move_timer = QTimer(self)
        self._move_timer.timeout.connect(self._tick_move)
        self._move_timer.start(self.MOVE_INTERVAL)

        self._idle_timer = QTimer(self)
        self._idle_timer.timeout.connect(self._tick_idle)
        self._idle_timer.start(self.IDLE_INTERVAL)

        self._bubble_timer = QTimer(self)
        self._bubble_timer.timeout.connect(self._tick_bubbles)
        self._bubble_timer.start(400)

        # ── movement state ──
        self._dx = random.uniform(1.5, 3.0) * random.choice([-1, 1])
        self._dy = 0.0
        self._chatting = False

    # ════════════════════════════════════════════════════════════════
    # Movement — horizontal-biased, up = crawl
    # ════════════════════════════════════════════════════════════════

    def _tick_move(self) -> None:
        if self._chatting:
            return

        energy = self._state.energy
        speed = 0.8 + energy * 1.8  # 0.8 ~ 2.6

        # ── horizontal: random drift, dominant ──
        self._dx += random.uniform(-0.25, 0.25)
        self._dx = max(-4.0, min(4.0, self._dx))

        # ── vertical: occasional, slow ──
        if random.random() < 0.08:
            self._dy += random.choice([-1, 1]) * random.uniform(0.3, 1.0)
        self._dy += random.uniform(-0.05, 0.05)
        self._dy = max(-2.0, min(2.0, self._dy))

        # Crawl upward = slow, slide down = faster
        vy = self._dy
        if vy < 0:
            vy *= 0.25  # crawl up
        else:
            vy *= 1.4   # slide down faster

        x = self.x() + int(self._dx * speed)
        y = self.y() + int(vy * speed)

        # Facing direction
        if self._dx > 0.15:
            self._pet.set_facing(True)
        elif self._dx < -0.15:
            self._pet.set_facing(False)

        # Bounce edges
        w, h = self.width(), self.height()
        b = self._move_bounds
        if x <= b.x():
            x = b.x()
            self._dx = abs(self._dx)
        elif x + w >= b.right():
            x = b.right() - w
            self._dx = -abs(self._dx)
        if y <= b.y():
            y = b.y()
            self._dy = abs(self._dy)
        elif y + h >= b.bottom():
            y = b.bottom() - h
            self._dy = -abs(self._dy)

        self.move(x, y)

    # ════════════════════════════════════════════════════════════════
    # Idle
    # ════════════════════════════════════════════════════════════════

    def _tick_idle(self) -> None:
        emo = self._state.current_emotion
        self._pet.set_emotion(emo)

    # ════════════════════════════════════════════════════════════════
    # Bubbles
    # ════════════════════════════════════════════════════════════════

    def _show_bubble(self, text: str, is_user: bool = False) -> None:
        bubble = PetBubble(text, is_user)
        # Position above pet window
        px = self.x() + (self.width() - bubble.width()) // 2
        py = self.y() - bubble.height() - 6
        bubble.move(px, py)
        bubble.show()
        self._bubbles.append(bubble)

    def _tick_bubbles(self) -> None:
        survived: list[PetBubble] = []
        for b in self._bubbles:
            if b.age() > self.BUBBLE_LIFETIME:
                b.hide()
                b.deleteLater()
            else:
                # Float upward
                b.move(b.x(), b.y() - 1)
                # Track pet horizontal position
                px = self.x() + (self.width() - b.width()) // 2
                b.move(px, b.y())
                survived.append(b)
        self._bubbles = survived

    # ════════════════════════════════════════════════════════════════
    # Chat
    # ════════════════════════════════════════════════════════════════

    def mousePressEvent(self, event) -> None:
        self._input_widget.setVisible(not self._input_widget.isVisible())
        self._chatting = self._input_widget.isVisible()
        if self._chatting:
            self._input_field.setFocus()

    def _on_chat_send(self) -> None:
        text = self._input_field.text().strip()
        if not text:
            return
        self._input_field.clear()
        self._input_widget.setVisible(False)
        self._chatting = False
        self._show_bubble(text, is_user=True)
        asyncio.ensure_future(self._process_chat(text))

    async def _process_chat(self, text: str) -> None:
        try:
            self._state.on_user_interaction()
            response = await self._agent.process_user_message(text)
            self._state.apply_response(
                response.emotion, response.face, response.action, response.led,
            )
            self._show_bubble(response.reply)
        except Exception:
            self._show_bubble("…")

    # ════════════════════════════════════════════════════════════════
    # External tick
    # ════════════════════════════════════════════════════════════════

    def tick_state(self, dt: float) -> None:
        self._state.tick(dt)
