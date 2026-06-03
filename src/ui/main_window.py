import asyncio
import sys
import uuid

import qasync
from PySide6.QtCore import Qt, QTimer
from PySide6.QtWidgets import (
    QApplication,
    QComboBox,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QListWidget,
    QMainWindow,
    QPushButton,
    QScrollArea,
    QSplitter,
    QStackedWidget,
    QTextEdit,
    QVBoxLayout,
    QWidget,
)

try:
    from src.core.schemas import HardwareEvent
except ImportError:
    HardwareEvent = None  # type: ignore


# ==========================================
# 1. 严格对应文档的 核心数据类型 MOCK (用于独立运行预览)
# ==========================================
class AgentResponse:
    def __init__(
        self,
        reply="...",
        emotion="neutral",
        face="normal",
        action="idle",
        led="off",
        voice_style="normal",
        need_hardware=False,
    ):
        self.reply = reply
        self.emotion = emotion
        self.face = face
        self.action = action
        self.led = led
        self.voice_style = voice_style
        self.need_hardware = need_hardware

    def to_hardware_command(self, cmd_id: str):
        return {
            "id": cmd_id,
            "command": "perform",
            "payload": {
                "face": self.face,
                "action": self.action,
                "led": self.led,
                "emotion": self.emotion,
            },
        }


class CharacterProfile:
    def __init__(self):
        self.name = "Pebo"
        self.personality = "cheerful"
        self.speaking_style = "casual"
        self.temperature = 0.8

    def to_system_prompt(self):
        return f"System Prompt Preview:\nName: {self.name}\nPersonality: {self.personality}"


class SimpleMemory:
    def __init__(self):
        self._history = []

    def get_history(self):
        return self._history

    def count(self):
        return len(self._history)

    def clear(self):
        self._history.clear()

    def add(self, role, text):
        self._history.append({"role": role, "text": text})


class HardwareSimulator:
    def __init__(self):
        self.current_face = "normal"
        self.current_action = "idle"
        self.current_led = "off"
        self.current_emotion = "neutral"

    def get_state(self):
        return {
            "face": self.current_face,
            "action": self.current_action,
            "led": self.current_led,
            "emotion": self.current_emotion,
        }

    async def send_command(self, command):
        """Apply a command dict to virtual state (mock)."""
        payload = command.get("payload", {})
        self.current_face = payload.get("face", self.current_face)
        self.current_action = payload.get("action", self.current_action)
        self.current_led = payload.get("led", self.current_led)
        self.current_emotion = payload.get("emotion", self.current_emotion)

    def inject_event(self, event):
        pass

    async def connect(self):
        await asyncio.sleep(0.5)

    async def disconnect(self):
        await asyncio.sleep(0.1)


class AgentEngine:
    def __init__(self):
        self.character = CharacterProfile()
        self.memory = SimpleMemory()

    async def process_user_message(self, user_text: str) -> AgentResponse:
        await asyncio.sleep(0.8)  # 模拟网络延迟
        self.memory.add("user", user_text)
        reply = f"收到：{user_text}。我是 {self.character.name}！"
        self.memory.add("assistant", reply)
        return AgentResponse(
            reply=reply, emotion="excited", face="smile", action="wave"
        )


# ==========================================
# 2. 全局炫酷现代感 QSS 样式表
# ==========================================
MODERN_STYLE = """
QMainWindow {
    background-color: #121418;
}
QWidget {
    color: #E2E8F0;
    font-family: 'Segoe UI', 'Microsoft YaHei', sans-serif;
    font-size: 13px;
}
/* 左侧导航栏 */
QListWidget {
    background-color: #1A1D24;
    border: none;
    border-right: 1px solid #2D3139;
    padding-top: 10px;
    outline: none;
    show-decoration-selected: 1;
}
QListWidget::item {
    height: 45px;
    padding-left: 15px;
    border-radius: 8px;
    margin: 4px 8px;
    color: #94A3B8;
}
QListWidget::item:hover {
    background-color: #242933;
    color: #F8FAFC;
}
QListWidget::item:selected {
    background-color: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 #3B82F6, stop:1 #1D4ED8);
    color: white;
    font-weight: bold;
}
QListWidget::item:focus, QListWidget::item:selected:focus {
    border: none;
    outline: none;
}
/* 右侧页面容器 */
QStackedWidget {
    background-color: #121418;
}
/* 标题样式 */
QLabel#PageTitle {
    font-size: 24px;
    font-weight: bold;
    color: #F8FAFC;
    padding-bottom: 5px;
}
/* 输入组件 */
QLineEdit, QTextEdit, QComboBox {
    background-color: #1A1D24;
    border: 1px solid #2D3139;
    border-radius: 6px;
    padding: 8px;
    color: #F8FAFC;
}
QLineEdit:focus, QTextEdit:focus, QComboBox:focus {
    border: 1px solid #3B82F6;
}
/* 按钮基础样式 */
QPushButton {
    background-color: #242933;
    border: 1px solid #3B82F6;
    border-radius: 6px;
    padding: 8px 16px;
    color: #3B82F6;
    font-weight: bold;
}
QPushButton:hover {
    background-color: #3B82F6;
    color: white;
}
QPushButton:pressed {
    background-color: #1D4ED8;
}
/* 强调主按钮 */
QPushButton#PrimaryBtn {
    background-color: #3B82F6;
    color: white;
    border: none;
}
QPushButton#PrimaryBtn:hover {
    background-color: #2563EB;
}
QPushButton#PrimaryBtn:disabled {
    background-color: #1E293B;
    color: #64748B;
}
/* 危险动作按钮 */
QPushButton#DangerBtn {
    background-color: #EF4444;
    color: white;
    border: none;
}
QPushButton#DangerBtn:hover {
    background-color: #DC2626;
}
/* 滑块样式 */
QSlider::groove:horizontal {
    height: 4px;
    background: #2D3139;
    border-radius: 2px;
}
QSlider::handle:horizontal {
    background: #3B82F6;
    width: 14px;
    margin-top: -5px;
    margin-bottom: -5px;
    border-radius: 7px;
}
/* 聊天气泡 */
QTextEdit#ChatDisplay {
    background-color: #16191E;
    border: none;
}
"""


# ==========================================
# 3. 基础页面类
# ==========================================
class BasePage(QWidget):
    page_title: str = "Page"

    def __init__(self, parent=None):
        super().__init__(parent)
        self.layout = QVBoxLayout(self)
        self.layout.setContentsMargins(24, 24, 24, 24)
        self.layout.setSpacing(20)

        # 极简大标题
        self.title_label = QLabel(self.page_title)
        self.title_label.setObjectName("PageTitle")
        self.layout.addWidget(self.title_label)

        self._build_ui()

    def _build_ui(self):
        pass


# ==========================================
# 4. 各子页面前端实现 (极简 UI 交互)
# ==========================================


# ---------------------------------------------------------------------------
# Chat emoji mappings
# ---------------------------------------------------------------------------

CHAT_EMOTION_EMOJI = {
    "happy": "😊", "sad": "😢", "surprised": "😲",
    "neutral": "😐", "curious": "🤔", "excited": "🥳",
    "angry": "😠", "sleepy": "😴",
}
CHAT_ACTION_EMOJI = {
    "wave": "👋", "nod": "👍", "shake_head": "🙂‍↔️",
    "idle": "", "bounce": "🦘", "tilt_head": "🤔",
}


def _pick_pet_emoji(response) -> str:
    return CHAT_EMOTION_EMOJI.get(response.emotion, "😐")


def _action_bar(response) -> str:
    parts = []
    a = CHAT_ACTION_EMOJI.get(response.action, "")
    if a:
        parts.append(a)
    if response.action != "idle":
        parts.append(response.action.replace("_", " "))
    led = "🔵" if response.led != "off" else "⚫"
    parts.append(f"{led} {response.led}")
    return "  ".join(parts)


# ---------------------------------------------------------------------------
# Chat page with emoji + bubbles
# ---------------------------------------------------------------------------

class ChatPage(BasePage):
    page_title = "Chat"

    def __init__(
        self, agent_engine: AgentEngine, hardware: HardwareSimulator, parent=None
    ):
        self._agent = agent_engine
        self._hardware = hardware
        self._message_layout: QVBoxLayout | None = None
        super().__init__(parent)

    def _build_ui(self):
        # Scrollable message area (wrapper-widget style, not QTextEdit)
        self._scroll = QScrollArea()
        self._scroll.setWidgetResizable(True)
        self._scroll.setStyleSheet(
            "QScrollArea { border: none; background: #121418; }"
        )

        container = QWidget()
        container.setStyleSheet("background: #121418;")
        self._message_layout = QVBoxLayout(container)
        self._message_layout.setAlignment(Qt.AlignmentFlag.AlignTop)
        self._message_layout.setSpacing(8)
        self._message_layout.addStretch()
        self._scroll.setWidget(container)

        self.layout.addWidget(self._scroll, stretch=1)

        # Input row
        input_layout = QHBoxLayout()
        self.input_field = QLineEdit()
        self.input_field.setPlaceholderText("和 Pebo 说点什么...")
        self.input_field.returnPressed.connect(self._on_send)

        self.send_btn = QPushButton("发送")
        self.send_btn.setObjectName("PrimaryBtn")
        self.send_btn.clicked.connect(self._on_send)

        input_layout.addWidget(self.input_field)
        input_layout.addWidget(self.send_btn)
        self.layout.addLayout(input_layout)

    def _on_send(self):
        if not hasattr(self, "send_btn") or self.send_btn is None:
            return
        text = self.input_field.text().strip()
        if text:
            self.input_field.clear()
            self._add_user_bubble(text)
            self.send_btn.setEnabled(False)
            self.send_btn.setText("...")
            asyncio.ensure_future(self._process_message(text))

    async def _process_message(self, text: str):
        try:
            response = await self._agent.process_user_message(text)
            name = self._agent.character.name
            self._add_pet_bubble(name, response)

            cmd = response.to_hardware_command(f"chat_{uuid.uuid4().hex[:8]}")
            await self._hardware.send_command(cmd)
        except Exception:
            self._add_system_note("出了点问题，请重试")
        finally:
            self.send_btn.setEnabled(True)
            self.send_btn.setText("发送")

    def _add_user_bubble(self, text: str):
        if self._message_layout is None:
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
        self._message_layout.insertWidget(self._message_layout.count() - 1, wrapper)
        self._scroll_to_bottom()

    def _add_pet_bubble(self, name: str, response):
        if self._message_layout is None:
            return
        emoji = _pick_pet_emoji(response)
        action_text = _action_bar(response)

        wrapper = QWidget()
        row = QHBoxLayout(wrapper)
        row.setContentsMargins(8, 4, 40, 4)

        # Emoji avatar
        avatar = QLabel(emoji)
        avatar.setFixedWidth(36)
        avatar.setAlignment(Qt.AlignmentFlag.AlignTop)
        avatar.setStyleSheet("font-size: 26px; background: transparent;")
        row.addWidget(avatar)

        # Bubble
        bubble = QWidget()
        bubble.setMaximumWidth(420)
        bl = QVBoxLayout(bubble)
        bl.setContentsMargins(0, 0, 0, 0)
        bl.setSpacing(4)

        name_lbl = QLabel(f"<b style='color:#F8FAFC;'>{name}</b>")
        name_lbl.setStyleSheet("font-size: 12px; background: transparent;")
        bl.addWidget(name_lbl)

        reply_lbl = QLabel(response.reply)
        reply_lbl.setWordWrap(True)
        reply_lbl.setStyleSheet("color: #E2E8F0; font-size: 14px; background: transparent;")
        bl.addWidget(reply_lbl)

        if action_text:
            bar = QLabel(action_text)
            bar.setStyleSheet(
                "color: #94A3B8; font-size: 11px; background: transparent; padding-top: 2px;"
            )
            bl.addWidget(bar)

        bubble.setStyleSheet(
            "background: #1A1D24; border-radius: 12px;"
            "padding: 10px 14px; border: 1px solid #2D3139;"
        )
        row.addWidget(bubble)
        row.addStretch()
        self._message_layout.insertWidget(self._message_layout.count() - 1, wrapper)
        self._scroll_to_bottom()

    def _add_system_note(self, text: str):
        if self._message_layout is None:
            return
        label = QLabel(f"<span style='color:#64748B;font-size:12px;'>{text}</span>")
        label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self._message_layout.insertWidget(self._message_layout.count() - 1, label)
        self._scroll_to_bottom()

    def _scroll_to_bottom(self):
        """Auto-scroll the chat to the latest message.

        Uses QTimer.singleShot(0) to defer until after Qt finishes layout.
        Otherwise bar.maximum() may return the old value.
        """
        if hasattr(self, '_scroll') and self._scroll:
            QTimer.singleShot(0, self._do_scroll)

    def _do_scroll(self):
        """Execute the actual scroll (called deferred)."""
        if hasattr(self, '_scroll') and self._scroll:
            bar = self._scroll.verticalScrollBar()
            if bar:
                bar.setValue(bar.maximum())


class ModelSettingsPage(BasePage):
    page_title = "模型"

    def _build_ui(self):
        # 极简并排或堆叠表单
        self.layout.addWidget(QLabel("接口地址"))
        self.url_input = QLineEdit("https://api.deepseek.com/v1")
        self.layout.addWidget(self.url_input)

        self.layout.addWidget(QLabel("密钥"))
        self.key_input = QLineEdit()
        self.key_input.setEchoMode(QLineEdit.EchoMode.Password)
        self.layout.addWidget(self.key_input)

        self.layout.addWidget(QLabel("模型"))
        self.model_box = QComboBox()
        self.model_box.addItems(["deepseek-chat", "gpt-4o"])
        self.layout.addWidget(self.model_box)

        self.test_btn = QPushButton("测试连接")
        self.test_btn.clicked.connect(self._on_test)
        self.layout.addWidget(self.test_btn)
        self.layout.addStretch()

    def _on_test(self):
        self.test_btn.setText("成功")


class CharacterSettingsPage(BasePage):
    """Character profile editor.

    Requires agent_engine.character with:
      - name: str
      - personality: str
      - to_system_prompt() -> str
    """

    page_title = "角色"

    def __init__(self, agent_engine: AgentEngine, parent=None):
        self._agent = agent_engine
        super().__init__(parent)

    def _build_ui(self):
        self.layout.addWidget(QLabel("名字"))
        self.name_input = QLineEdit(self._agent.character.name)
        self.name_input.textChanged.connect(self._update_profile)
        self.layout.addWidget(self.name_input)

        self.layout.addWidget(QLabel("性格"))
        self.personality_input = QLineEdit(self._agent.character.personality)
        self.personality_input.textChanged.connect(self._update_profile)
        self.layout.addWidget(self.personality_input)

        self.layout.addWidget(QLabel("提示词预览"))
        self.preview = QTextEdit()
        self.preview.setReadOnly(True)
        self.layout.addWidget(self.preview)
        self.layout.addStretch()

        self._update_profile()

    def _update_profile(self):
        self._agent.character.name = self.name_input.text()
        self._agent.character.personality = self.personality_input.text()
        self.preview.setPlainText(self._agent.character.to_system_prompt())


class HardwareSettingsPage(BasePage):
    page_title = "硬件"

    def __init__(self, hardware: HardwareSimulator, parent=None):
        self._hardware = hardware
        super().__init__(parent)

    def _build_ui(self):
        self.layout.addWidget(QLabel("端口"))
        self.port_box = QComboBox()
        self.port_box.addItems(["COM3", "COM4", "/dev/ttyUSB0"])
        self.layout.addWidget(self.port_box)

        # 连按状态切换
        self.conn_btn = QPushButton("连接")
        self.conn_btn.setObjectName("PrimaryBtn")
        self.conn_btn.clicked.connect(self._toggle_connect)
        self.layout.addWidget(self.conn_btn)
        self.layout.addStretch()

    def _toggle_connect(self):
        self.conn_btn.setEnabled(False)
        if self.conn_btn.text() == "连接":
            asyncio.ensure_future(self._connect())
        else:
            asyncio.ensure_future(self._disconnect())

    async def _connect(self):
        try:
            await self._hardware.connect()
            self.conn_btn.setText("断开")
            self.conn_btn.setObjectName("DangerBtn")
            self.conn_btn.style().unpolish(self.conn_btn)
            self.conn_btn.style().polish(self.conn_btn)
        finally:
            self.conn_btn.setEnabled(True)

    async def _disconnect(self):
        try:
            await self._hardware.disconnect()
            self.conn_btn.setText("连接")
            self.conn_btn.setObjectName("PrimaryBtn")
            self.conn_btn.style().unpolish(self.conn_btn)
            self.conn_btn.style().polish(self.conn_btn)
        finally:
            self.conn_btn.setEnabled(True)


class HardwareSimulatorPage(BasePage):
    page_title = "模拟器"

    def __init__(self, hardware: HardwareSimulator, parent=None):
        self._hardware = hardware
        super().__init__(parent)
        # 开启轮询器监听状态
        self.start_timer()

    def _build_ui(self):
        # 炫酷看板：展示当前状态矩阵
        self.state_label = QLabel()
        self.state_label.setStyleSheet(
            "font-size: 16px; background-color: #1A1D24; padding: 15px; border-radius: 8px;"
        )
        self.layout.addWidget(self.state_label)

        # 快捷模拟事件触发
        self.layout.addWidget(QLabel("触发事件"))
        h_box = QHBoxLayout()
        touch_btn = QPushButton("触摸头部")
        touch_btn.clicked.connect(lambda: self._inject("touch", "head"))
        shake_btn = QPushButton("摇晃宠物")
        shake_btn.clicked.connect(lambda: self._inject("shake", "true"))

        h_box.addWidget(touch_btn)
        h_box.addWidget(shake_btn)
        self.layout.addLayout(h_box)
        self.layout.addStretch()

    def start_timer(self):
        self.timer = QTimer(self)
        self.timer.timeout.connect(self._update_state_display)
        self.timer.start(300)  # 300ms 刷新

    def _update_state_display(self):
        s = self._hardware.get_state()
        text = f"表情: {s['face']}\n动作: {s['action']}\n灯效: {s['led']}\n情绪: {s['emotion']}"
        self.state_label.setText(text)

    def _inject(self, event_type, val):
        if HardwareEvent is not None:
            event = HardwareEvent(event=event_type, payload={"value": val})
        else:
            event = {"event": event_type, "payload": {"value": val}}
        self._hardware.inject_event(event)


class MemoryPage(BasePage):
    page_title = "记忆"

    def __init__(self, agent_engine: AgentEngine, parent=None):
        self._agent = agent_engine
        super().__init__(parent)

    def _build_ui(self):
        self.counter = QLabel("条目数: 0")
        self.layout.addWidget(self.counter)

        self.clear_btn = QPushButton("清空")
        self.clear_btn.setObjectName("DangerBtn")
        self.clear_btn.clicked.connect(self._clear_memory)
        self.layout.addWidget(self.clear_btn)
        self.layout.addStretch()

    def _get_memory_count(self) -> int:
        """Return memory item count.

        Compatible with both AgentEngine (memory.count()) and
        PetAgentBrain (memory_count property).
        """
        if hasattr(self._agent, "memory"):
            return self._agent.memory.count()
        if hasattr(self._agent, "memory_count"):
            return self._agent.memory_count
        return 0

    def _do_clear_memory(self) -> None:
        """Clear memory, works with AgentEngine and PetAgentBrain."""
        if hasattr(self._agent, "memory"):
            self._agent.memory.clear()
        elif hasattr(self._agent, "clear_memory"):
            self._agent.clear_memory()

    def showEvent(self, event):
        super().showEvent(event)
        self.counter.setText(f"条目数: {self._get_memory_count()}")

    def _clear_memory(self):
        self._do_clear_memory()
        self.counter.setText("条目数: 0")


class LogsPage(BasePage):
    page_title = "日志"

    def _build_ui(self):
        self.log_area = QTextEdit(
            "INFO - [System] Initialized OK.\nINFO - [Agent] Waiting for prompt..."
        )
        self.log_area.setReadOnly(True)
        self.layout.addWidget(self.log_area, stretch=1)


# ==========================================
# 5. 主窗口 MainWindow 骨架及布局组织
# ==========================================
class MainWindow(QMainWindow):
    """Main application window.

    Parameters
    ----------
    agent_engine:
        Agent object that implements:
          - process_user_message(text: str) -> AgentResponse (async)
          - character attribute with name: str, personality: str, to_system_prompt()
          - memory.count() + memory.clear() or memory_count + clear_memory()
    hardware:
        HardwareSimulator instance for sending/receiving hardware commands.
    voice:
        Optional voice module (e.g. MockVoice) for speech synthesis/recognition.
    """

    def __init__(
        self, agent_engine: AgentEngine, hardware: HardwareSimulator, voice=None
    ):
        super().__init__()
        self.voice = voice
        self.setWindowTitle("Pet Agent")
        self.resize(900, 600)
        self.setStyleSheet(MODERN_STYLE)

        # 核心分割布局
        splitter = QSplitter(Qt.Horizontal)
        splitter.setHandleWidth(1)

        # 左导航
        self._nav_list = QListWidget()
        self._nav_list.setFixedWidth(160)

        # 右多页容器
        self._stack = QStackedWidget()

        # 实例化子页面
        self._chat_page = ChatPage(agent_engine, hardware)
        self._model_page = ModelSettingsPage()
        self._char_page = CharacterSettingsPage(agent_engine)
        self._hw_page = HardwareSettingsPage(hardware)
        self._sim_page = HardwareSimulatorPage(hardware)
        self._mem_page = MemoryPage(agent_engine)
        self._log_page = LogsPage()

        # 注册映射关系 (极简名称)
        self._pages = [
            ("Chat", self._chat_page),
            ("模型", self._model_page),
            ("角色", self._char_page),
            ("硬件", self._hw_page),
            ("模拟器", self._sim_page),
            ("记忆", self._mem_page),
            ("日志", self._log_page),
        ]

        # 装载进 Qt 布局
        for name, page_widget in self._pages:
            self._nav_list.addItem(name)
            self._stack.addWidget(page_widget)

        # 连接导航控制信号
        self._nav_list.currentRowChanged.connect(self._stack.setCurrentIndex)
        self._nav_list.setCurrentRow(0)

        splitter.addWidget(self._nav_list)
        splitter.addWidget(self._stack)
        splitter.setStretchFactor(0, 0)
        splitter.setStretchFactor(1, 1)

        self.setCentralWidget(splitter)


# ==========================================
# 6. 系统入口初始化 (含事件循环合并)
# ==========================================
def main():
    app = QApplication(sys.argv)

    # 结合 Qt 和 asyncio 核心机制
    loop = qasync.QEventLoop(app)
    asyncio.set_event_loop(loop)

    # 模拟 Application 组装后端组件并注入
    mock_hardware = HardwareSimulator()
    mock_agent = AgentEngine()

    main_win = MainWindow(agent_engine=mock_agent, hardware=mock_hardware)
    main_win.show()

    with loop:
        loop.run_forever()


if __name__ == "__main__":
    main()
