# TODO_HANDOFF.md -- Desktop Pet Agent

## Project Status: Skeleton Complete / Minimum Runnable

The project can be started with `python main.py` and shows the main window with
7 navigable pages. All subsystems use mock implementations.

---

## Completed

### Directory Structure
```
desktop_pet_agent/
├── main.py                    # Entry point
├── requirements.txt           # PySide6, pydantic
├── CLAUDE.md                  # Project spec (existing, preserved)
├── TODO_HANDOFF.md            # This file
└── src/
    ├── __init__.py
    ├── app.py                 # Application bootstrap (wires subsystems)
    ├── core/
    │   ├── __init__.py
    │   ├── config.py          # Env-based configuration (dataclass)
    │   ├── schemas.py         # AgentResponse, HardwareCommand, HardwareEvent, ChatMessage
    │   └── exceptions.py      # DesktopPetError hierarchy
    ├── llm/
    │   ├── __init__.py
    │   ├── base.py            # Abstract BaseLLM (async chat + is_available)
    │   └── mock_llm.py        # MockLLM (returns safe default AgentResponse)
    ├── agent/
    │   ├── __init__.py
    │   ├── engine.py          # AgentEngine (user msg -> memory -> LLM -> response)
    │   └── character.py       # CharacterProfile (name, personality, system prompt builder)
    ├── memory/
    │   ├── __init__.py
    │   ├── base.py            # Abstract BaseMemory (add, get_history, clear, count)
    │   └── simple_memory.py   # SimpleMemory (in-memory list, with max_turns trim)
    ├── hardware/
    │   ├── __init__.py
    │   ├── protocol.py        # HardwareProtocol (make_command, parse_event)
    │   ├── base.py            # Abstract BaseHardware (connect, disconnect, send_command, receive_event)
    │   ├── mock_hardware.py   # MockHardware (no-op)
    │   └── simulator.py       # HardwareSimulator (virtual state machine + ack events)
    ├── voice/
    │   ├── __init__.py
    │   ├── base.py            # Abstract BaseVoice (speak, listen, is_speaking, cancel)
    │   └── mock_voice.py      # MockVoice (no-op)
    ├── ui/
    │   ├── __init__.py
    │   ├── main_window.py     # MainWindow (QSplitter: left nav + right QStackedWidget)
    │   └── pages/
    │       ├── __init__.py
    │       ├── base_page.py           # BasePage (common page skeleton)
    │       ├── chat_page.py           # Chat page (message area + input + send button, NOT wired to engine yet)
    │       ├── model_settings_page.py # Placeholder
    │       ├── character_settings_page.py # Placeholder
    │       ├── hardware_settings_page.py  # Placeholder
    │       ├── hardware_simulator_page.py # Placeholder
    │       ├── memory_page.py         # Placeholder
    │       └── logs_page.py           # Placeholder
    └── utils/
        ├── __init__.py
        └── logger.py          # setup_logging, get_logger (console + rotating file)
```

### Implemented Core Flow
1. `main.py` creates QApplication and Application instance
2. `Application.__init__` loads config, sets up logging, creates mock subsystems
3. `MainWindow` shows 7-page navigation
4. `AgentEngine.process_user_message` implements the full pipeline:
   user text -> store in memory -> call LLM -> parse AgentResponse -> store reply in memory -> return
5. `HardwareSimulator` maintains virtual state and auto-generates ack events

---

## Not Yet Implemented (TODO)

### Priority 1: Wire Chat Page to Agent Engine
- **File**: `src/ui/pages/chat_page.py` line ~72 (`_on_send`)
- **What**: Replace the placeholder "Agent: This is a placeholder..." with a call to `Application.agent.process_user_message(text)`
- **Challenge**: The ChatPage currently has no reference to the Application or AgentEngine. You need to either:
  - Pass the engine through MainWindow -> ChatPage constructor, OR
  - Use a signal/slot pattern, OR
  - Use a simple service locator.
- **Note**: `process_user_message` is async, so you need to handle this correctly in the Qt event loop (use `asyncio.ensure_future` or a `QThread` helper).

### Priority 2: Real LLM Backend (OpenAI-compatible)
- **File**: New file `src/llm/openai_llm.py`
- **What**: Implement `BaseLLM` using `openai` package (or `httpx` directly).
- **Signature**: Same as `BaseLLM.chat()`.
- **Key concerns**:
  - Parse LLM JSON output into `AgentResponse` via pydantic.
  - On parse failure, fall back to `make_safe_response()`.
  - Never log the full API key.
  - Respect `character_profile` as the system prompt.

### Priority 3: Real Hardware Backend (Serial)
- **File**: New file `src/hardware/serial_hardware.py`
- **What**: Implement `BaseHardware` using `pyserial` (or `pySerial`).
- **Signature**: Same as `BaseHardware`.
- **Key concerns**:
  - Send/receive JSON lines (or a binary protocol) over the serial port.
  - Handle disconnection gracefully (auto-reconnect? notify UI?).
  - Run serial I/O in a background thread to avoid blocking the UI.

### Priority 4: Settings Pages (5 pages)
- **Files**: `src/ui/pages/model_settings_page.py`, `character_settings_page.py`, `hardware_settings_page.py`
- **What**: Replace the placeholder labels with actual form widgets.
- **Each page should**:
  - Load current values from `AppConfig` / `CharacterProfile`.
  - Allow editing.
  - Save changes back.
  - (Model settings) Include a "Test Connection" button.

### Priority 5: Hardware Simulator Page
- **File**: `src/ui/pages/hardware_simulator_page.py`
- **What**: Show the virtual hardware state from `HardwareSimulator.get_state()` in real-time.
- **Visual ideas**:
  - A simple pet icon/avatar that changes expression.
  - Color indicator for LED.
  - Action label.
  - Buttons to inject synthetic events (touch, shake).

### Priority 6: Memory Page
- **File**: `src/ui/pages/memory_page.py`
- **What**: Show conversation history from `SimpleMemory.get_history()`.
- **Features**: Scrollable list, clear button, message count.

### Priority 7: Logs Page
- **File**: `src/ui/pages/logs_page.py`
- **What**: Show live log output in a scrollable text area.
- **Approach**: Add a custom `logging.Handler` that emits Qt signals, or poll the log file.

### Priority 8: Voice Module (TTS + STT)
- **Files**: New files `src/voice/tts_engine.py`, `src/voice/stt_engine.py`
- **What**: Real TTS (e.g., edge-tts, pyttsx3) and STT (e.g., whisper, SpeechRecognition).
- **Key concerns**:
  - TTS should play without blocking UI.
  - STT should show a "listening..." indicator.
  - `voice_style` from AgentResponse should affect TTS parameters.

### Priority 9: Persistent Memory
- **File**: New file `src/memory/sqlite_memory.py` or `src/memory/json_memory.py`
- **What**: Store conversation history across restarts.

### Priority 10: Event Loop (Hardware -> Agent)
- **What**: Poll `hardware.receive_event()` periodically and feed sensor events (touch, shake) to the AgentEngine so the pet can react proactively.

---

## Interface Reference

### AgentResponse (pydantic)
```python
class AgentResponse(BaseModel):
    reply: str = "..."
    emotion: str = "neutral"       # happy, sad, angry, surprised, neutral
    face: str = "normal"           # smile, frown, blink, normal
    action: str = "idle"           # wave, nod, shake_head, idle
    led: str = "off"               # warm, cool, breath, rainbow, off
    voice_style: str = "normal"    # normal, cheerful, whisper, serious
    need_hardware: bool = True
```

### HardwareCommand (pydantic)
```python
class HardwareCommand(BaseModel):
    type: Literal["command"] = "command"
    id: str                        # Unique, e.g. "cmd_001"
    command: str = "perform"       # perform, reset, ping, configure
    payload: dict[str, str] = {}   # {face: smile, action: wave, led: warm, emotion: happy}
```

### HardwareEvent (pydantic)
```python
class HardwareEvent(BaseModel):
    type: Literal["event"] = "event"
    id: str = ""
    event: str                     # ack, touch, shake, button, sensor
    payload: dict[str, str] = {}
```

### BaseLLM (abstract)
```python
class BaseLLM(ABC):
    async def chat(self, messages: Iterable[ChatMessage], *, character_profile: str = "") -> AgentResponse: ...
    async def is_available(self) -> bool: ...
```

### BaseHardware (abstract)
```python
class BaseHardware(ABC):
    async def connect(self) -> None: ...
    async def disconnect(self) -> None: ...
    async def send_command(self, command: HardwareCommand) -> None: ...
    async def receive_event(self) -> HardwareEvent | None: ...
    def is_connected(self) -> bool: ...
```

### BaseMemory (abstract)
```python
class BaseMemory(ABC):
    def add(self, message: ChatMessage) -> None: ...
    def get_history(self, max_turns: int | None = None) -> list[ChatMessage]: ...
    def clear(self) -> None: ...
    def count(self) -> int: ...
```

### BaseVoice (abstract)
```python
class BaseVoice(ABC):
    async def speak(self, text: str, *, style: str = "normal") -> None: ...
    async def listen(self) -> str: ...
    def is_speaking(self) -> bool: ...
    def cancel(self) -> None: ...
```

---

## How to Run

```bash
# 1. Create and activate a virtual environment (recommended)
python -m venv .venv
.venv\Scripts\activate   # Windows
# source .venv/bin/activate  # Linux/macOS

# 2. Install dependencies
pip install -r requirements.txt

# 3. Run
python main.py
```

The main window should appear with a left sidebar (7 navigation items) and a content area.
Clicking "Chat" shows a simple chat interface. Other pages show a title label.

---

## How to Test

Manual testing (for now):
1. Run the app, verify all 7 pages are navigable.
2. Type a message in Chat and click Send -- a placeholder reply appears.
3. Close the app cleanly.

Automated testing (not yet set up):
- A `tests/` directory should be added at the project root.
- Unit tests for `AgentResponse` validation, `make_safe_response()`, `SimpleMemory`, `HardwareSimulator`.
- Integration test: `AgentEngine.process_user_message("hello")` with MockLLM.
- UI tests: launch MainWindow, verify page count and titles.

---

## How to Continue

Recommended next step: **Wire the Chat page to the AgentEngine** (Priority 1).
This gives instant visible progress and tests the pipeline end-to-end.

After that, implement a real OpenAI-compatible LLM backend (Priority 2) so the pet
actually talks. Then fill in the settings pages.

### Suitable for:
- **implementation-coder**: Most TODO items are straightforward "implement this interface, add this UI".
- **code-reviewer**: After each batch of changes, review for architectural consistency.
- **debugger**: If anything breaks during wiring (async in Qt, pydantic validation, etc.).

### Agent handoff recommendation:
Pass this TODO_HANDOFF.md to the next agent along with the instruction:
"Pick one priority from the TODO list and implement it. Do not change the module boundaries."
