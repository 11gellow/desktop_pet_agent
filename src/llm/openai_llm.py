"""
OpenAI-compatible LLM backend.

Supports DeepSeek, OpenAI, and any other provider that exposes
an OpenAI-compatible /chat/completions endpoint.
"""

from __future__ import annotations

import json
import re
from typing import Iterable

import httpx

from src.core.exceptions import LLMError
from src.core.schemas import AgentResponse, ChatMessage, make_safe_response
from src.llm.base import BaseLLM
from src.utils.logger import get_logger

logger = get_logger("llm")


class OpenAILLM(BaseLLM):
    """LLM backend for any OpenAI-compatible API (DeepSeek, OpenAI, etc.)."""

    def __init__(
        self,
        api_key: str,
        base_url: str = "https://api.deepseek.com/v1",
        model: str = "deepseek-chat",
        temperature: float = 0.8,
        max_tokens: int = 512,
        timeout: float = 30.0,
    ) -> None:
        self.api_key = api_key
        self.base_url = base_url.rstrip("/")
        self.model = model
        self.temperature = temperature
        self.max_tokens = max_tokens
        self.timeout = timeout

    async def chat(
        self,
        messages: Iterable[ChatMessage],
        *,
        character_profile: str = "",
    ) -> AgentResponse:
        """Send conversation to the LLM and parse an AgentResponse."""
        api_messages: list[dict[str, str]] = []
        if character_profile:
            api_messages.append({"role": "system", "content": character_profile})

        for msg in messages:
            api_messages.append({"role": msg.role, "content": msg.content})

        logger.debug("Calling %s with %d messages", self.model, len(api_messages))

        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                http_resp = await client.post(
                    f"{self.base_url}/chat/completions",
                    headers={
                        "Authorization": f"Bearer {self.api_key}",
                        "Content-Type": "application/json",
                    },
                    json={
                        "model": self.model,
                        "messages": api_messages,
                        "temperature": self.temperature,
                        "max_tokens": self.max_tokens,
                        "response_format": {"type": "json_object"},
                    },
                )
                http_resp.raise_for_status()
        except httpx.HTTPStatusError as e:
            logger.error("HTTP %d from LLM API: %s", e.response.status_code, e.response.text[:500])
            return make_safe_response()
        except httpx.RequestError as e:
            logger.error("LLM request failed: %s", e)
            return make_safe_response()

        data = http_resp.json()
        content: str = data["choices"][0]["message"]["content"]
        finish_reason = data["choices"][0].get("finish_reason", "?")
        logger.info(
            "API response: finish_reason=%s content_len=%d content_preview=%s",
            finish_reason, len(content), repr(content[:150]),
        )

        # If response_format json_object produced empty output, retry without it.
        # Some providers / edge cases cause the model to return empty content
        # when forced into JSON mode.
        if not content.strip():
            logger.warning(
                "LLM returned empty content with response_format=json_object. "
                "Retrying without response_format."
            )
            try:
                async with httpx.AsyncClient(timeout=self.timeout) as client:
                    http_resp = await client.post(
                        f"{self.base_url}/chat/completions",
                        headers={
                            "Authorization": f"Bearer {self.api_key}",
                            "Content-Type": "application/json",
                        },
                        json={
                            "model": self.model,
                            "messages": api_messages,
                            "temperature": self.temperature,
                            "max_tokens": self.max_tokens,
                        },
                    )
                    http_resp.raise_for_status()
                data = http_resp.json()
                content = data["choices"][0]["message"]["content"]
                logger.debug("Retry raw response: %s", content[:300])
            except Exception as e:
                logger.error("Retry also failed: %s", e)
                return make_safe_response()

        return self._parse_response(content)

    async def is_available(self) -> bool:
        """Quick connectivity check."""
        try:
            async with httpx.AsyncClient(timeout=5.0) as client:
                resp = await client.get(
                    f"{self.base_url}/models",
                    headers={"Authorization": f"Bearer {self.api_key}"},
                )
            return resp.is_success
        except Exception:
            return False

    def _parse_response(self, raw: str) -> AgentResponse:
        """Extract JSON from LLM output and validate as AgentResponse.

        Tries multiple extraction strategies in order:
          1. Direct JSON parse of the full text.
          2. Extract from markdown code fence (```json ... ```).
          3. Extract the first {...} object via regex (handles JSON-in-text).
          4. Fall back: wrap the raw text as reply, with safe defaults for other fields.
        """
        candidates: list[str] = []

        # Strategy 1: full text as-is
        candidates.append(raw.strip())

        # Strategy 2: markdown code fence extraction
        md_match = re.search(r"```(?:json)?\s*([\s\S]*?)```", raw)
        if md_match:
            candidates.append(md_match.group(1).strip())

        # Strategy 3: find the first outermost {...} using brace matching
        brace_match = self._extract_first_json_object(raw)
        if brace_match:
            candidates.append(brace_match)

        # Try each candidate
        for json_str in candidates:
            try:
                return AgentResponse.model_validate_json(json_str)
            except Exception:
                continue

        # Strategy 4: all JSON parsing failed — wrap raw text as a conversational reply
        logger.warning(
            "All JSON extraction strategies failed. Using raw text as reply. "
            "Raw (first 200 chars): %s", raw[:200]
        )
        cleaned = raw.strip()
        if not cleaned:
            return make_safe_response()
        if len(cleaned) > 500:
            cleaned = cleaned[:497] + "..."
        return AgentResponse(
            reply=cleaned,
            emotion="neutral",
            face="normal",
            action="idle",
            led="off",
            voice_style="normal",
            need_hardware=False,
        )

    @staticmethod
    def _extract_first_json_object(text: str) -> str | None:
        """Extract the first balanced {...} JSON object from arbitrary text.

        Uses brace counting to handle nested objects/strings correctly.
        Returns None if no valid brace pair is found.
        """
        start = text.find("{")
        if start == -1:
            return None

        depth = 0
        in_string = False
        escape = False
        for i in range(start, len(text)):
            ch = text[i]
            if escape:
                escape = False
                continue
            if ch == "\\" and in_string:
                escape = True
                continue
            if ch == '"':
                in_string = not in_string
                continue
            if in_string:
                continue
            if ch == "{":
                depth += 1
            elif ch == "}":
                depth -= 1
                if depth == 0:
                    return text[start : i + 1]
        return None
