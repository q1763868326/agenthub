from __future__ import annotations

import time
import uuid
from dataclasses import asdict, dataclass
from typing import Any

from .config import DATA_DIR
from .instance_manager import get_instance
from .storage import read_json, write_json

SESSIONS_PATH = DATA_DIR / "sessions.json"


@dataclass
class AgentSession:
    id: str
    instance_id: str
    title: str
    created_at: int
    updated_at: int
    summary: str
    messages: list[dict[str, Any]]


def _load_sessions() -> list[dict[str, Any]]:
    return read_json(SESSIONS_PATH, [])


def _save_sessions(items: list[dict[str, Any]]) -> None:
    write_json(SESSIONS_PATH, items)


def _from_dict(item: dict[str, Any]) -> AgentSession:
    return AgentSession(
        id=item["id"],
        instance_id=item["instance_id"],
        title=item.get("title") or "Untitled Session",
        created_at=int(item.get("created_at", 0)),
        updated_at=int(item.get("updated_at", item.get("created_at", 0))),
        summary=item.get("summary", ""),
        messages=item.get("messages") or [],
    )


def list_sessions(instance_id: str | None = None) -> list[AgentSession]:
    sessions = [_from_dict(item) for item in _load_sessions()]
    if instance_id:
        sessions = [session for session in sessions if session.instance_id == instance_id]
    return sessions


def get_session(session_id: str) -> AgentSession | None:
    for session in list_sessions():
        if session.id == session_id:
            return session
    return None


def create_session(instance_id: str, title: str | None = None) -> AgentSession:
    if not get_instance(instance_id):
        raise ValueError(f"Agent instance not found: {instance_id}")

    now = int(time.time())
    session = AgentSession(
        id=f"sess_{uuid.uuid4().hex[:12]}",
        instance_id=instance_id,
        title=title or "Untitled Session",
        created_at=now,
        updated_at=now,
        summary="",
        messages=[],
    )
    items = _load_sessions()
    items.append(asdict(session))
    _save_sessions(items)
    return session


def append_session_messages(session_id: str, messages: list[dict[str, Any]]) -> AgentSession:
    items = _load_sessions()
    now = int(time.time())
    for item in items:
        if item["id"] == session_id:
            item.setdefault("messages", []).extend(messages)
            item["updated_at"] = now
            _save_sessions(items)
            return _from_dict(item)
    raise ValueError(f"Agent session not found: {session_id}")
