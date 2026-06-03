#!/usr/bin/env python3
"""Stress-test DeepSeek JSON mode. Run 20 calls, count success/fail/whitespace."""
import asyncio
import os
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

# Load .env
env_path = Path(__file__).resolve().parent.parent / ".env"
if env_path.is_file():
    for line in env_path.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if line and not line.startswith("#") and "=" in line:
            k, _, v = line.partition("=")
            os.environ.setdefault(k.strip(), v.strip())

import httpx

API_KEY = os.getenv("LLM_API_KEY", "")
BASE_URL = os.getenv("LLM_BASE_URL", "https://api.deepseek.com/v1").rstrip("/")
MODEL = os.getenv("LLM_MODEL", "deepseek-chat")

SYSTEM_PROMPT = """JSON output mode. You are a JSON generator.

You are Pebo, A friendly desktop companion pet.
Personality: cheerful, curious, empathetic.
Speaking style: casual and warm, uses emoji occasionally.
Keep replies under 200 characters.

--- OUTPUT FORMAT (STRICT REQUIREMENT) ---
CRITICAL: You MUST output a single JSON object. Do NOT add any text before or after the JSON.
Do NOT wrap the JSON in markdown code fences.

{"reply": "<your reply text in Chinese>","emotion": "happy|sad|surprised|neutral|curious|excited","face": "smile|frown|surprised|normal|wink|blink","action": "wave|nod|shake_head|idle|bounce|tilt_head","led": "warm|cool|breath|rainbow|off","voice_style": "normal|cheerful|whisper|serious","need_hardware": true|false}

Example: {"reply": "哈哈，我也很开心！你今天想聊什么呀？😊", "emotion": "happy", "face": "smile", "action": "bounce", "led": "warm", "voice_style": "cheerful", "need_hardware": true}"""

USER_MESSAGES = [
    "你好呀！今天怎么样？",
    "你心情好吗？",
    "给我讲个笑话吧",
    "你喜欢什么颜色？",
    "你觉得人类怎么样？",
    "我有点难过",
    "今天天气真好",
    "你会跳舞吗？",
    "来抱抱",
    "说个秘密给我听",
]


async def call_deepseek(session: httpx.AsyncClient, msg: str, use_json_mode: bool, temp: float) -> dict:
    body = {
        "model": MODEL,
        "messages": [
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": msg},
        ],
        "temperature": temp,
        "max_tokens": 512,
    }
    if use_json_mode:
        body["response_format"] = {"type": "json_object"}

    resp = await session.post(
        f"{BASE_URL}/chat/completions",
        headers={"Authorization": f"Bearer {API_KEY}", "Content-Type": "application/json"},
        json=body,
    )
    resp.raise_for_status()
    data = resp.json()
    content = data["choices"][0]["message"]["content"]
    finish = data["choices"][0].get("finish_reason", "?")
    return {"content": content, "finish": finish}


async def main():
    if not API_KEY:
        print("No API key. Set LLM_API_KEY in .env")
        return

    configs = [
        ("temp=0 + json_mode", True, 0),
        ("temp=0.8 + json_mode", True, 0.8),
        ("temp=0 + no_json_mode", False, 0),
    ]

    for label, json_mode, temp in configs:
        results = {"success": 0, "whitespace": 0, "text": 0, "errors": 0}
        async with httpx.AsyncClient(timeout=30) as client:
            for i, msg in enumerate(USER_MESSAGES):
                try:
                    r = await call_deepseek(client, msg, json_mode, temp)
                    content = r["content"]
                    if not content.strip():
                        results["whitespace"] += 1
                        status = "WHITESPACE"
                    elif content.strip().startswith("{"):
                        results["success"] += 1
                        status = "JSON"
                    else:
                        results["text"] += 1
                        status = f"TEXT({content[:30]}...)"
                except Exception as e:
                    results["errors"] += 1
                    status = f"ERR({e})"
                print(f"  [{label}] #{i+1}: {status}")
        print(f"  => {label}: {results}")
        print()


if __name__ == "__main__":
    asyncio.run(main())
