# CLAUDE.md

本项目是一个实体桌宠 Agent 的电脑端软件。

## 项目边界

本项目只负责软件端，不负责嵌入式固件、硬件驱动、电路设计、外壳结构、舵机控制细节。

软件端负责：
- 用户 UI
- 大模型调用
- Agent 对话与行为决策
- 角色设定
- 记忆系统
- 语音模块接口
- 硬件通信协议
- 硬件模拟器
- 日志与调试

硬件端负责：
- 接收软件命令
- 执行表情、动作、灯效、声音等表现
- 上报传感器事件

## 开发原则

1. 不要让 Agent 直接控制具体硬件参数，例如舵机角度、GPIO 引脚。
2. Agent 只能输出抽象行为，例如 wave、nod、smile、blue_breath。
3. 具体硬件如何执行动作由嵌入式端实现。
4. 所有软件和硬件交互必须经过统一协议。
5. 所有大模型输出必须经过 pydantic 校验。
6. 如果大模型输出格式错误，必须 fallback 到安全默认响应。
7. UI 不得因为模型请求或硬件通信阻塞。
8. API Key 不得硬编码，不得完整写入日志。
9. 每个核心模块都要可替换。
10. 在真实硬件完成前，软件必须可以通过硬件模拟器完整运行。

## 推荐开发顺序

1. 项目骨架
2. PySide6 主窗口
3. AgentResponse schema
4. MockLLM
5. 聊天页面
6. 硬件模拟器
7. 配置系统
8. OpenAI-compatible LLM
9. 串口通信
10. 日志调试
11. 记忆系统
12. 语音输入输出

## AgentResponse 格式

Agent 每次输出必须符合：

```json
{
  "reply": "...",
  "emotion": "...",
  "face": "...",
  "action": "...",
  "led": "...",
  "voice_style": "...",
  "need_hardware": true
}
```

## 硬件通信原则

电脑端发送抽象命令：

```json
{
  "type": "command",
  "id": "cmd_001",
  "command": "perform",
  "payload": {
    "face": "smile",
    "action": "wave",
    "led": "warm",
    "emotion": "happy"
  }
}
```

硬件端返回事件或 ack。

不要在软件中写任何硬件底层控制逻辑。
