from __future__ import annotations

import json
from collections.abc import AsyncIterator
from typing import Any

from fastapi import APIRouter, HTTPException
from fastapi.responses import StreamingResponse
from pydantic import BaseModel, Field

from .agent_loader import list_agents
from .experience_manager import build_experience_prompt, create_experience_from_session
from .instance_manager import list_instances, resolve_agent
from .openai_client import chat_completion, chat_completion_stream
from .session_manager import append_session_messages, create_session

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
    session_id: str | None = None
    extra: dict[str, Any] = Field(default_factory=dict)


def _latest_user_message(messages: list[ChatMessage]) -> dict[str, Any] | None:
    for message in reversed(messages):
        if message.role == "user":
            return message.model_dump()
    return messages[-1].model_dump() if messages else None


def _refresh_experience(session_id: str) -> None:
    try:
        create_experience_from_session(session_id)
    except ValueError:
        return


async def _recording_stream(messages: list[dict[str, Any]], session_id: str | None) -> AsyncIterator[str]:
    assistant_parts: list[str] = []
    async for event in chat_completion_stream(messages=messages, model=None):
        if event.startswith("data: ") and not event.startswith("data: [DONE]"):
            try:
                payload = json.loads(event.removeprefix("data: ").strip())
            except json.JSONDecodeError:
                payload = {}
            for choice in payload.get("choices", []):
                content = choice.get("delta", {}).get("content")
                if content:
                    assistant_parts.append(str(content))
        yield event

    if session_id and assistant_parts:
        append_session_messages(session_id, [{"role": "assistant", "content": "".join(assistant_parts)}])
        _refresh_experience(session_id)


@router.get("/models")
def models() -> dict[str, Any]:
    data = []
    for instance in list_instances():
        data.append(
            {
                "id": instance.id,
                "object": "model",
                "created": instance.created_at,
                "owned_by": "agentos",
                "permission": [],
                "root": instance.package_id,
                "parent": instance.package_id,
                "description": instance.description,
            }
        )
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
    resolved = resolve_agent(req.model)
    if not resolved:
        raise HTTPException(status_code=404, detail=f"Agent model not found: {req.model}")
    agent, instance = resolved

    messages = [m.model_dump() for m in req.messages]
    system_prompt = agent.system_prompt
    if instance:
        experience_prompt = build_experience_prompt(instance.id)
        if experience_prompt:
            system_prompt = "\n\n".join(part for part in [system_prompt, experience_prompt] if part)
    if system_prompt:
        messages = [{"role": "system", "content": system_prompt}] + messages

    session_id = req.session_id or req.extra.get("session_id")
    if instance and not session_id:
        session_id = create_session(instance_id=instance.id, title="OpenAI Chat").id
    if session_id:
        try:
            latest_user_message = _latest_user_message(req.messages)
            if latest_user_message:
                append_session_messages(session_id, [latest_user_message])
        except ValueError as exc:
            raise HTTPException(status_code=404, detail=str(exc)) from exc

    if req.stream:
        return StreamingResponse(
            _recording_stream(messages=messages, session_id=session_id),
            media_type="text/event-stream",
            headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no"},
        )

    response = await chat_completion(messages=messages, model=None)
    if session_id:
        choice = (response.get("choices") or [{}])[0]
        message = choice.get("message")
        if message:
            append_session_messages(session_id, [message])
            _refresh_experience(session_id)
    return response
