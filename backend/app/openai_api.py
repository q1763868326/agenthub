from __future__ import annotations

from typing import Any

from fastapi import APIRouter, HTTPException
from fastapi.responses import StreamingResponse
from pydantic import BaseModel, Field

from .agent_loader import get_agent, list_agents
from .openai_client import chat_completion, chat_completion_stream

router = APIRouter(prefix="/v1", tags=["openai-compatible"])


class ChatMessage(BaseModel):
    role: str
    content: Any


class ChatCompletionRequest(BaseModel):
    model: str
    messages: list[ChatMessage]
    stream: bool = False
    temperature: float | None = None
    max_tokens: int | None = None
    extra: dict[str, Any] = Field(default_factory=dict)


@router.get("/models")
def models() -> dict[str, Any]:
    data = []
    for agent in list_agents():
        data.append(
            {
                "id": agent.id,
                "object": "model",
                "created": 0,
                "owned_by": agent.author or "agenthub",
                "permission": [],
                "root": agent.id,
                "parent": None,
                "description": agent.description,
            }
        )
    return {"object": "list", "data": data}


@router.post("/chat/completions", response_model=None)
async def create_chat_completion(req: ChatCompletionRequest) -> Any:
    agent = get_agent(req.model)
    if not agent:
        raise HTTPException(status_code=404, detail=f"Agent model not found: {req.model}")

    messages = [m.model_dump() for m in req.messages]
    system_prompt = agent.system_prompt
    if system_prompt:
        messages = [{"role": "system", "content": system_prompt}] + messages

    if req.stream:
        return StreamingResponse(
            chat_completion_stream(messages=messages, model=None),
            media_type="text/event-stream",
            headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no"},
        )

    return await chat_completion(messages=messages, model=None)
