# Desktop Pet Agent

虚拟桌宠应用。接 DeepSeek 大模型，宠物有性格、情绪、表情和动作。

> 🚧 半成品，持续开发中。

## 功能

- AI 对话 —— DeepSeek 驱动的个性宠物聊天
- 情绪系统 —— 宠物有 happiness/energy/affection/curiosity 四个情感维度，随时间衰减，互动提升
- 表情动作 —— 每次回复附带 emotion/face/action/led 状态，emoji 可视化
- 硬件模拟 —— 虚拟状态机，无需真实硬件即可运行
- 7 页界面 —— 聊天、模型设置、角色设置、硬件设置、硬件模拟器、记忆、日志

## 快速开始

```bash
# 1. 安装依赖
pip install -r requirements.txt

# 2. 配置 API Key
cp .env.example .env
# 编辑 .env，填入 DeepSeek API Key

# 3. 运行
python main.py
```

没有 API Key 也能跑，聊天会返回占位回复。

## 项目结构

```
src/         主代码
├── agent/   Agent 引擎 + 状态机
├── llm/     LLM 后端（DeepSeek / Mock）
├── memory/  对话记忆
├── hardware/ 硬件模拟器
├── voice/   语音接口（占位）
├── ui/      PySide6 界面
└── utils/   日志

app/         新模块（开发中）
└── agent/   PetAgentBrain + schemas + state + character
```

## 技术栈

Python 3.10+ / PySide6 / pydantic v2 / httpx / qasync / DeepSeek API

## 开发计划

- [x] 项目骨架 + 主窗口
- [x] DeepSeek 对话
- [x] 聊天气泡 + emoji 表情
- [x] AgentState 情感状态机
- [ ] 空闲主动行为（定时器触发）
- [ ] 情绪状态持久化
- [ ] 语音输入/输出
- [ ] 真实硬件通信

## License

MIT
