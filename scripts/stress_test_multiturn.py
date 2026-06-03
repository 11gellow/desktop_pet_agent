#!/usr/bin/env python3
"""Multi-turn stress test: 5-turn conversation, 5 rounds. No response_format."""
import asyncio, os, sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

env_path = Path(__file__).resolve().parent.parent / ".env"
for line in env_path.read_text(encoding="utf-8").splitlines():
    line = line.strip()
    if line and not line.startswith("#") and "=" in line:
        k, _, v = line.partition("=")
        os.environ.setdefault(k.strip(), v.strip())

import httpx, json

API_KEY = os.getenv("LLM_API_KEY", "")
BASE_URL = os.getenv("LLM_BASE_URL", "https://api.deepseek.com/v1").rstrip("/")
MODEL = os.getenv("LLM_MODEL", "deepseek-chat")

SYSTEM = """JSON output mode. You are a JSON generator.

You are Pebo, A friendly desktop companion pet.
Personality: cheerful, curious, empathetic.
Keep replies under 200 characters.

--- OUTPUT FORMAT (STRICT REQUIREMENT) ---
CRITICAL: You MUST output a single JSON object. Do NOT add any text before or after the JSON.
Do NOT wrap the JSON in markdown code fences.

{"reply": "<your reply text in Chinese>","emotion": "happy|sad|surprised|neutral|curious|excited","face": "smile|frown|surprised|normal|wink|blink","action": "wave|nod|shake_head|idle|bounce|tilt_head","led": "warm|cool|breath|rainbow|off","voice_style": "normal|cheerful|whisper|serious","need_hardware": true|false}

Example: {"reply": "哈哈，我也很开心！你今天想聊什么呀？😊", "emotion": "happy", "face": "smile", "action": "bounce", "led": "warm", "voice_style": "cheerful", "need_hardware": true}"""

USER_TURNS = [
    "你好呀！", "打你！", "摸摸头", "今天天气真好",
    "你最喜欢什么？", "我有点难过", "讲个笑话",
]


async def run_round(label: str):
    history = [{"role": "system", "content": SYSTEM}]
    results = {"json": 0, "text": 0, "empty": 0}
    async with httpx.AsyncClient(timeout=30) as c:
        for i, msg in enumerate(USER_TURNS):
            history.append({"role": "user", "content": msg})
            resp = await c.post(
                f"{BASE_URL}/chat/completions",
                headers={"Authorization": f"Bearer {API_KEY}", "Content-Type": "application/json"},
                json={"model": MODEL, "messages": history, "temperature": 0, "max_tokens": 512},
            )
            resp.raise_for_status()
            data = resp.json()
            content = data["choices"][0]["message"]["content"]
            if not content.strip():
                results["empty"] += 1
                status = "EMPTY"
            elif content.strip().startswith("{"):
                results["json"] += 1
                parsed = json.loads(content)
                emo = parsed.get("emotion", "?")
                fac = parsed.get("face", "?")
                status = f"JSON(emoji={emo},face={fac})"
                history.append({"role": "assistant", "content": content})
            else:
                results["text"] += 1
                status = f"TEXT({content[:40]}...)"
            print(f"  [{label}] #{i+1}: {status}")
    print(f"  => {label}: {results}")


async def main():
    for r in range(3):
        print(f"\n=== Round {r+1} ===")
        await run_round(f"R{r+1}")


if __name__ == "__main__":
    asyncio.run(main())
