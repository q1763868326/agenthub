from __future__ import annotations

import json
import time
from collections.abc import AsyncIterator
from typing import Any

import httpx

from .config import DEFAULT_MODEL, OPENAI_API_KEY, OPENAI_BASE_URL


def _mock_content(messages: list[dict[str, Any]]) -> str:
    last_user = next((m.get("content", "") for m in reversed(messages) if m.get("role") == "user"), "")
    return "我是 AgentHub 的 mock 回复。你已经成功连通了数字人接口。你刚才说：" + str(last_user)


async def chat_completion(messages: list[dict[str, Any]], model: str | None = None) -> dict[str, Any]:
    """Forward a non-streaming request to an OpenAI-compatible provider."""
    resolved_model = model or DEFAULT_MODEL

    if not OPENAI_API_KEY:
        return {
            "id": "chatcmpl-agenthub-mock",
            "object": "chat.completion",
            "created": int(time.time()),
            "model": resolved_model,
            "choices": [
                {
                    "index": 0,
                    "message": {"role": "assistant", "content": _mock_content(messages)},
                    "finish_reason": "stop",
                }
            ],
            "usage": {"prompt_tokens": 0, "completion_tokens": 0, "total_tokens": 0},
        }

    payload = {"model": resolved_model, "messages": messages, "stream": False}
    async with httpx.AsyncClient(timeout=120) as client:
        resp = await client.post(
            f"{OPENAI_BASE_URL.rstrip('/')}/chat/completions",
            headers={"Authorization": f"Bearer {OPENAI_API_KEY}"},
            json=payload,
        )
        resp.raise_for_status()
        return resp.json()


async def chat_completion_stream(messages: list[dict[str, Any]], model: str | None = None) -> AsyncIterator[str]:
    """Yield OpenAI-compatible chat completion chunks as Server-Sent Events."""
    resolved_model = model or DEFAULT_MODEL

    if not OPENAI_API_KEY:
        chunk = {
            "id": "chatcmpl-agenthub-mock",
            "object": "chat.completion.chunk",
            "created": int(time.time()),
            "model": resolved_model,
            "choices": [
                {
                    "index": 0,
                    "delta": {"role": "assistant", "content": _mock_content(messages)},
                    "finish_reason": None,
                }
            ],
        }
        done = {
            "id": "chatcmpl-agenthub-mock",
            "object": "chat.completion.chunk",
            "created": int(time.time()),
            "model": resolved_model,
            "choices": [{"index": 0, "delta": {}, "finish_reason": "stop"}],
        }
        yield f"data: {json.dumps(chunk, ensure_ascii=False)}\n\n"
        yield f"data: {json.dumps(done, ensure_ascii=False)}\n\n"
        yield "data: [DONE]\n\n"
        return

    payload = {"model": resolved_model, "messages": messages, "stream": True}
    async with httpx.AsyncClient(timeout=None) as client:
        async with client.stream(
            "POST",
            f"{OPENAI_BASE_URL.rstrip('/')}/chat/completions",
            headers={"Authorization": f"Bearer {OPENAI_API_KEY}"},
            json=payload,
        ) as resp:
            resp.raise_for_status()
            async for line in resp.aiter_lines():
                if line:
                    yield line + "\n\n"
