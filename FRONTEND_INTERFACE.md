# 前后端接口文档

本文档供前端开发者使用。文档描述后端（Agent 引擎 + 各子系统）已提供的全部接口，以及前端（PySide6 页面）与后端交互的约定。

---

## 1. 架构概览

```
main.py                      ← 入口：初始化 Qt + asyncio 事件循环
  └─ Application (app.py)    ← 组装所有子系统，注入 MainWindow
       ├─ AgentEngine         ← 核心管线：消息→记忆→LLM→回复
       │    ├─ BaseLLM        ← LLM 后端（Mock / OpenAI / DeepSeek）
       │    ├─ BaseMemory     ← 对话记忆
       │    └─ CharacterProfile ← 角色设定
       ├─ HardwareSimulator   ← 硬件模拟器（抽象命令→虚拟状态）
       ├─ MockVoice           ← 语音（目前占位）
       └─ MainWindow          ← 主窗口
            ├─ ChatPage       ← 聊天页
            ├─ ModelSettingsPage
            ├─ CharacterSettingsPage
            ├─ HardwareSettingsPage
            ├─ HardwareSimulatorPage
            ├─ MemoryPage
            └─ LogsPage
```

前端只与 `MainWindow` 及其子页面交互。`Application` 负责创建后端实例并通过构造函数注入。前端不直接 import 后端模块（除了数据类型）。

---

## 2. 核心数据类型

所有类型定义在 `src.core.schemas`，基于 **pydantic**。前端需要导入这些类型来获得类型提示和 IDE 自动补全。

### 2.1 AgentResponse — LLM 返回的回复

```python
from src.core.schemas import AgentResponse

class AgentResponse(BaseModel):
    reply: str           # 显示给用户的文本回复，默认 "..."
    emotion: str         # 情绪标签：happy, sad, surprised, neutral, curious, excited
    face: str            # 表情命令：smile, frown, surprised, normal, wink, blink
    action: str          # 动作命令：wave, nod, shake_head, idle, bounce, tilt_head
    led: str             # 灯效命令：warm, cool, breath, rainbow, off
    voice_style: str     # 语音风格：normal, cheerful, whisper, serious
    need_hardware: bool  # 是否需要硬件执行表情/动作/灯效
```

**前端用法**：收到 `AgentResponse` 后：
- `response.reply` → 显示在聊天气泡中
- `response.emotion` / `response.face` / `response.action` / `response.led` → 传给硬件模拟器可视化
- `response.need_hardware` → 控制是否发送硬件命令

### 2.2 ChatMessage — 单条对话消息

```python
from src.core.schemas import ChatMessage

class ChatMessage(BaseModel):
    role: Literal["user", "assistant", "system"]  # 角色
    content: str                                    # 文本内容
    agent_response: AgentResponse | None            # 仅 assistant 消息有此字段
```

**前端用法**：读取记忆（MemoryPage）时遍历此结构。

### 2.3 HardwareCommand — 发送给硬件的命令

```python
from src.core.schemas import HardwareCommand

class HardwareCommand(BaseModel):
    type: Literal["command"] = "command"
    id: str                                      # 命令 ID，如 "cmd_001"
    command: str = "perform"                     # perform, reset, ping, configure
    payload: dict[str, str]                      # {"face": "smile", "action": "wave", ...}
```

**前端不需要手动构造**。调用 `AgentResponse.to_hardware_command(cmd_id)` 即可从回复生成命令。

### 2.4 HardwareEvent — 硬件上报的事件

```python
from src.core.schemas import HardwareEvent

class HardwareEvent(BaseModel):
    type: Literal["event"] = "event"
    id: str                           # 事件 ID 或对应的命令 ID（ack 时）
    event: str                        # ack, touch, shake, button, sensor
    payload: dict[str, str]           # {"sensor": "touch_head", "value": "1"}
```

### 2.5 make_safe_response() — 安全回退

```python
from src.core.schemas import make_safe_response

# LLM 失败时的默认回复，前端不需要调用（引擎内部处理）
def make_safe_response() -> AgentResponse:
    return AgentResponse(
        reply="...",
        emotion="neutral", face="normal", action="idle",
        led="off", voice_style="normal", need_hardware=False,
    )
```

---

## 3. AgentEngine — 核心后端入口

**文件**: `src.agent.engine.AgentEngine`

前端**唯一需要调用的后端对象**。所有对话都通过它处理。

### 3.1 构造函数

```python
from src.agent.engine import AgentEngine

agent = AgentEngine(
    llm: BaseLLM,           # LLM 后端（Application 创建）
    memory: BaseMemory,     # 记忆存储
    character: CharacterProfile | None = None,  # 默认用 CharacterProfile.default()
)
```

前端**不需要自己创建** AgentEngine。它在 `Application.__init__` 中构建好，通过 `MainWindow` 构造函数传入。

### 3.2 核心方法

```python
async def process_user_message(self, user_text: str) -> AgentResponse:
```

**这是 ChatPage 唯一需要调用的后端方法。** 完整的处理管线：

```
用户输入文本 (str)
  → 存入 Memory (ChatMessage, role="user")
  → 取出历史 (list[ChatMessage])
  → 调用 LLM.chat(history, character_profile)
  → pydantic 校验 → AgentResponse
    （校验失败自动 fallback 到 make_safe_response()）
  → 存入 Memory (ChatMessage, role="assistant")
  → 返回 AgentResponse
```

**调用方式（ChatPage 中）**：

```python
import asyncio
response = await self._agent.process_user_message("你好")
# response.reply          → 文本回复
# response.emotion        → 情绪
# response.to_hardware_command("cmd_xxx") → 硬件命令
```

错误处理已内置：LLM 调用失败 → 自动记录日志 → 返回安全回退，不会抛异常。

### 3.3 角色设定

```python
agent.character: CharacterProfile
```

```python
@dataclass
class CharacterProfile:
    name: str = "Pebo"                      # 宠物名
    description: str = "A friendly..."      # 描述
    personality: str = "cheerful, ..."      # 性格
    backstory: str = ""                     # 背景故事
    speaking_style: str = "casual and warm" # 说话风格
    temperature: float = 0.8                # LLM 温度
    max_reply_length: int = 200             # 回复最大长度
    preferred_language: str = "zh-CN"       # 首选语言

    def to_system_prompt(self) -> str: ...  # 生成 system prompt
```

**前端用法**：ChatPage 用 `agent.character.name` 显示发送者名称；CharacterSettingsPage 修改 `agent.character` 的字段。

---

## 4. 子系统接口

### 4.1 BaseMemory — 对话记忆

```python
from src.memory.base import BaseMemory

class BaseMemory(ABC):
    def add(self, message: ChatMessage) -> None: ...
    def get_history(self, max_turns: int | None = None) -> list[ChatMessage]: ...
    def clear(self) -> None: ...
    def count(self) -> int: ...
```

`Application` 使用 `SimpleMemory`（内存列表）。接口方法全是同步的。

**前端用法**（MemoryPage）：
- `agent.memory.get_history()` → 获取全部消息列表用于展示
- `agent.memory.count()` → 消息总数
- `agent.memory.clear()` → 清空记忆

### 4.2 HardwareSimulator — 硬件模拟器

```python
from src.hardware.simulator import HardwareSimulator

class HardwareSimulator(BaseHardware):
    # 虚拟硬件状态（实时可读）
    current_face: str        # 当前表情
    current_action: str      # 当前动作
    current_led: str         # 当前灯效
    current_emotion: str     # 当前情绪

    async def connect(self) -> None: ...
    async def disconnect(self) -> None: ...
    async def send_command(self, command: HardwareCommand) -> None: ...
    async def receive_event(self) -> HardwareEvent | None: ...

    # 模拟器特有方法
    def get_state(self) -> dict[str, str]: ...
    def reset_state(self) -> None: ...
    def inject_event(self, event: HardwareEvent) -> None: ...
```

`Application` 创建 `HardwareSimulator` 实例，存在 `app.hardware`。目前**未注入**到 MainWindow。

需要注入时，改造 `MainWindow.__init__`：

```python
def __init__(self, agent_engine=None, hardware_simulator=None):
    self._hardware = hardware_simulator
```

**前端用法**（HardwareSimulatorPage）：
- `hardware.get_state()` → 轮询获取当前虚拟状态并可视化
- `hardware.inject_event(event)` → 模拟触摸/摇晃等事件

### 4.3 BaseLLM — LLM 后端

前端**不直接使用**。AgentEngine 内部调用。

Application 自动选择：
- 有 `LLM_API_KEY` → `OpenAILLM`（真实调用 DeepSeek/OpenAI）
- 无 `LLM_API_KEY` → `MockLLM`（永远返回 "..."）

### 4.4 MockVoice — 语音

目前是空实现（no-op）。接口：

```python
class BaseVoice(ABC):
    async def speak(self, text: str, style: str = "normal") -> None: ...
    async def listen(self) -> str | None: ...
```

前端不需要处理。

### 4.5 AppConfig — 配置

```python
from src.core.config import get_config

config = get_config()
# config.llm_api_key       → str
# config.llm_base_url      → str (默认 https://api.deepseek.com/v1)
# config.llm_model         → str (默认 deepseek-chat)
# config.hardware_port     → str (默认 COM3)
# config.hardware_baudrate → int
# config.memory_max_turns  → int (默认 50)
# config.log_level         → str (默认 INFO)
# config.voice_enabled     → bool
# config.use_hardware_simulator → bool
```

---

## 5. 页面接口约定

### 5.1 BasePage — 所有页面的基类

```python
from src.ui.pages.base_page import BasePage

class BasePage(QWidget):
    page_title: str = "Page"   # 子类覆盖此属性

    def _build_ui(self) -> None:   # 子类覆盖，创建页面 UI
        """默认创建一个 page_title 标题 Label"""
```

**新建页面**：继承 `BasePage`，设置 `page_title`，覆盖 `_build_ui`。

**页面注册**：在 `MainWindow.__init__` 的 `self._pages` 列表中添加。

```python
self._pages: list[tuple[str, QWidget]] = [
    ("Chat", self._chat_page),
    ("Model Settings", ModelSettingsPage()),
    # 在此添加新页面
]
```

左侧导航栏自动渲染。

### 5.2 ChatPage — 聊天页

**当前状态**: 已接入 AgentEngine，可以正常对话。

```python
class ChatPage(BasePage):
    page_title = "Chat"

    def __init__(self, agent_engine=None, parent=None): ...
    def set_agent_engine(self, agent_engine) -> None: ...  # 后注入
```

**内部调用流程**（已实现）：

```
用户输入 → _on_send()          ← 同步 Qt slot
  → asyncio.ensure_future()
    → _process_message(text)    ← async，在 qasync 事件循环上运行
      → await agent.process_user_message(text)
      → 显示 agent.character.name + response.reply
      → 恢复输入
```

**前端如需扩展**：
- 改变消息气泡样式 → 修改 `_add_message()` 的 `setStyleSheet`
- 发送前预处理 → 在 `_on_send` 的 `asyncio.ensure_future` 之前
- 发送后做硬件动作 → 在 `_process_message` 中收到 `response` 后调用 `response.to_hardware_command()`

### 5.3 占位页面 — 等待实现

以下页面目前只有一个标题 Label:

| 页面 | 类名 | 需要获取的后端数据 |
|------|------|-------------------|
| ModelSettingsPage | 模型设置 | `AppConfig` 读写 |
| CharacterSettingsPage | 角色设置 | `AgentEngine.character` (CharacterProfile) |
| HardwareSettingsPage | 硬件设置 | `AppConfig` (端口/波特率) + `HardwareSimulator` 连接状态 |
| HardwareSimulatorPage | 硬件模拟器 | `HardwareSimulator.get_state()` |
| MemoryPage | 记忆 | `AgentEngine.memory` (BaseMemory) |
| LogsPage | 日志 | 日志文件读取 |

### 5.4 如何让页面获取后端数据

**方案 A（推荐）— 通过 MainWindow 注入**：

1. `Application.__init__` 将后端实例传给 `MainWindow`
2. `MainWindow` 创建页面时通过构造函数注入

示例：

```python
# app.py 中
self.main_window = MainWindow(
    agent_engine=self.agent,
    hardware=self.hardware,    # 新增
)

# main_window.py 中
class MainWindow:
    def __init__(self, agent_engine=None, hardware=None):
        self._hardware = hardware
        self._simulator_page = HardwareSimulatorPage(hardware=hardware)
        # ... 注册到 self._pages
```

**方案 B — 通过 AgentEngine 间接访问**：

```python
# 在 MemoryPage 中
agent = ...  # 从 MainWindow 获取
history = agent.memory.get_history()
```

两种方案都可行，需要先改造 `MainWindow.__init__` 以传递更多后端引用。

---

## 6. 异步通信模式

### 6.1 事件循环

项目使用 **qasync** 将 Qt 事件循环与 asyncio 融合：

```python
# main.py
loop = qasync.QEventLoop(app)
asyncio.set_event_loop(loop)
# ...
with loop:
    loop.run_forever()
```

### 6.2 前端调用异步后端的方式

**模式：同步 slot → asyncio.ensure_future → async handler**

```python
def _on_send(self) -> None:                    # 同步 Qt slot
    asyncio.ensure_future(self._process())      # 调度到事件循环

async def _process(self) -> None:              # 异步 handler
    result = await self._agent.process_user_message(text)
    # 更新 UI（在主线程安全）
```

**关键约束**：
- Qt slot（如 `_on_send`）必须保持同步 — 不能 `async def`
- 所有 `await` 调用必须在 `async def` 函数中
- `asyncio.ensure_future()` 把协程调度到正在运行的 qasync 事件循环
- UI 更新在 async handler 中直接做是安全的（qasync 保证在 Qt 主线程执行）

### 6.3 需要 `await` 的后端方法

| 方法 | 用途 |
|------|------|
| `agent.process_user_message(text)` | 对话 |
| `hardware.send_command(cmd)` | 发送硬件命令 |
| `hardware.connect()` / `disconnect()` | 硬件连接 |
| `llm.chat(messages)`, `llm.is_available()` | LLM（一般不直接调） |
| `voice.speak(text)`, `voice.listen()` | 语音 |

**不需要 `await` 的后端方法**（同步）：

| 方法 | 用途 |
|------|------|
| `agent.memory.add(msg)` / `.get_history()` / `.clear()` / `.count()` | 记忆操作 |
| `hardware.get_state()` / `.reset_state()` | 硬件模拟器状态 |
| `hardware.inject_event(event)` | 注入模拟事件 |
| `get_config()` | 读取配置 |
| `agent.character` (属性读写) | 角色设定 |

---

## 7. MainWindow 结构

### 7.1 布局

```
┌────────────────┬───────────────────────────┐
│                │                           │
│  QListWidget   │    QStackedWidget         │
│  固定宽度 180px │    (自动拉伸)             │
│                │                           │
│  · Chat        │    当前显示的页面          │
│  · Model Set.  │                           │
│  · Char. Set.  │                           │
│  · HW Set.     │                           │
│  · HW Sim.     │                           │
│  · Memory      │                           │
│  · Logs        │                           │
│                │                           │
└────────────────┴───────────────────────────┘
```

使用 `QSplitter` 分割，导航栏不可拉伸（stretchFactor=0），内容区可拉伸（stretchFactor=1）。

### 7.2 导航切换

```python
self._nav_list.currentRowChanged.connect(self._stack.setCurrentIndex)
```

`QListWidget` 当前行变化 → `QStackedWidget` 切换到对应索引的页面。两者索引一一对应（导航项顺序 = 页面添加顺序）。

### 7.3 如何添加页面

```python
# 在 MainWindow.__init__ 中，self._pages 列表追加
("New Page", NewPage(...)),

# 如果有特殊构造（如 ChatPage 需要 agent_engine），
# 在 self._pages 外面先创建：
self._new_page = NewPage(backend=some_backend)
# 然后加入列表：
("New Page", self._new_page),
```

---

## 8. 页面前端可实现的功能清单

### 已实现
- 聊天：输入文本 → 异步调用 AgentEngine → 显示回复

### 待实现（按页面）

**ChatPage 可增强**：
- 发送中显示 typing 动画
- 根据 `response.emotion` 切换气泡颜色
- 消息时间戳
- 图片/GIF 展示

**ModelSettingsPage**：
- API Base URL 输入框 → 写入 config
- API Key 密码输入框 → 写入 config / .env
- Model 名称下拉/输入
- Temperature 滑块
- 「测试连接」按钮 → 调用 `await llm.is_available()`

**CharacterSettingsPage**：
- 宠物名、性格、说话风格等输入框 → 读写 `agent.character` 字段
- 实时预览 system prompt

**HardwareSettingsPage**：
- 端口列表下拉 → 写入 config
- 连接/断开按钮 → `await hardware.connect()/disconnect()`
- 连接状态指示灯

**HardwareSimulatorPage**：
- 实时显示 `hardware.current_face` / `current_action` / `current_led` / `current_emotion`
- 事件注入按钮 → `hardware.inject_event(...)`

**MemoryPage**：
- 对话历史列表 → `agent.memory.get_history()`
- 清空按钮 → `agent.memory.clear()`
- 统计信息 → `agent.memory.count()`

**LogsPage**：
- 读取 `~/.desktop_pet_agent/app.log`
- 按级别过滤
- 自动刷新

---

## 9. 环境变量 / 配置

项目根目录 `.env` 文件（在 `main.py` 启动时自动加载）：

```env
LLM_API_KEY=sk-xxx           # DeepSeek API Key
LLM_BASE_URL=https://api.deepseek.com/v1
LLM_MODEL=deepseek-chat
```

前端不需要处理这些。如需在设置页中修改，可以写入 `.env` 文件或修改 `os.environ`。

---

## 10. 快速参考卡片

```python
# === 前端需要的 import ===
from src.core.schemas import AgentResponse, ChatMessage, HardwareCommand, HardwareEvent, make_safe_response
from src.agent.character import CharacterProfile
from src.memory.base import BaseMemory
from src.hardware.simulator import HardwareSimulator

# === ChatPage 调用后端 ===
response = await agent.process_user_message(user_text)   # 发送消息，得到回复
sender_name = agent.character.name                        # 宠物名
cmd = response.to_hardware_command("cmd_xxx")              # AgentResponse → 硬件命令

# === MemoryPage ===
history = agent.memory.get_history()   # 获取全部历史
agent.memory.clear()                   # 清空
count = agent.memory.count()           # 消息数

# === HardwareSimulatorPage ===
state = hardware.get_state()           # {"face": "...", "action": "...", "led": "...", "emotion": "..."}
hardware.inject_event(event)           # 模拟事件

# === CharacterSettingsPage ===
agent.character.name = "新名字"        # 直接修改属性
agent.character.personality = "..."
agent.character.to_system_prompt()     # 预览生成的 system prompt

# === 配置 ===
from src.core.config import get_config
cfg = get_config()
cfg.llm_base_url             # 读
os.environ["LLM_BASE_URL"] = "..."  # 写（运行时）
```
