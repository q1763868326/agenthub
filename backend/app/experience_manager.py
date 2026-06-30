from __future__ import annotations

import time
import uuid
from dataclasses import asdict, dataclass
from typing import Any

from .config import AUTO_EXPERIENCE_EVERY_N_MESSAGES, AUTO_EXPERIENCE_MIN_USER_CHARS, DATA_DIR
from .instance_manager import get_instance
from .session_manager import AgentSession, get_session, update_session_summary
from .storage import read_json, write_json

EXPERIENCES_PATH = DATA_DIR / "experiences.json"


@dataclass
class AgentExperience:
    id: str
    instance_id: str
    source_session_id: str
    summary: str
    lessons: list[str]
    created_at: int
    updated_at: int


def _load_experiences() -> list[dict[str, Any]]:
    return read_json(EXPERIENCES_PATH, [])


def _save_experiences(items: list[dict[str, Any]]) -> None:
    write_json(EXPERIENCES_PATH, items)


def _from_dict(item: dict[str, Any]) -> AgentExperience:
    return AgentExperience(
        id=item["id"],
        instance_id=item["instance_id"],
        source_session_id=item["source_session_id"],
        summary=item.get("summary", ""),
        lessons=item.get("lessons") or [],
        created_at=int(item.get("created_at", 0)),
        updated_at=int(item.get("updated_at", item.get("created_at", 0))),
    )


def list_experiences(instance_id: str | None = None, limit: int | None = None) -> list[AgentExperience]:
    experiences = [_from_dict(item) for item in _load_experiences()]
    if instance_id:
        experiences = [experience for experience in experiences if experience.instance_id == instance_id]
    experiences.sort(key=lambda item: item.created_at, reverse=True)
    return experiences[:limit] if limit else experiences


def _message_text(message: dict[str, Any]) -> str:
    content = message.get("content", "")
    if isinstance(content, str):
        return content
    return str(content)


def build_session_summary(session: AgentSession) -> tuple[str, list[str]]:
    user_messages = [_message_text(message) for message in session.messages if message.get("role") == "user"]
    assistant_messages = [_message_text(message) for message in session.messages if message.get("role") == "assistant"]

    last_user = user_messages[-1] if user_messages else "无明确用户输入"
    summary = f"本次会话共 {len(session.messages)} 条消息。用户最后关注：{last_user}"
    lessons = [
        f"用户最近的问题或任务：{last_user}",
        f"本次会话包含 {len(user_messages)} 条用户消息和 {len(assistant_messages)} 条助手消息。",
    ]
    return summary, lessons


def should_refresh_experience(session: AgentSession) -> bool:
    if len(session.messages) < AUTO_EXPERIENCE_EVERY_N_MESSAGES:
        return False
    if len(session.messages) % AUTO_EXPERIENCE_EVERY_N_MESSAGES != 0:
        return False

    latest_user_message = next(
        (_message_text(message).strip() for message in reversed(session.messages) if message.get("role") == "user"),
        "",
    )
    if len(latest_user_message) < AUTO_EXPERIENCE_MIN_USER_CHARS:
        return False

    return True


def refresh_experience_if_needed(session_id: str) -> AgentExperience | None:
    session = get_session(session_id)
    if not session:
        raise ValueError(f"Agent session not found: {session_id}")
    if not should_refresh_experience(session):
        return None
    return create_experience_from_session(session.id)


def create_experience_from_session(session_id: str) -> AgentExperience:
    session = get_session(session_id)
    if not session:
        raise ValueError(f"Agent session not found: {session_id}")
    if not get_instance(session.instance_id):
        raise ValueError(f"Agent instance not found: {session.instance_id}")

    summary, lessons = build_session_summary(session)
    update_session_summary(session.id, summary)

    now = int(time.time())
    items = _load_experiences()
    for item in items:
        if item.get("source_session_id") == session.id:
            item["summary"] = summary
            item["lessons"] = lessons
            item["updated_at"] = now
            _save_experiences(items)
            return _from_dict(item)

    experience = AgentExperience(
        id=f"exp_{uuid.uuid4().hex[:12]}",
        instance_id=session.instance_id,
        source_session_id=session.id,
        summary=summary,
        lessons=lessons,
        created_at=now,
        updated_at=now,
    )
    items.append(asdict(experience))
    _save_experiences(items)
    return experience


def build_experience_prompt(instance_id: str, limit: int = 5) -> str:
    experiences = list_experiences(instance_id=instance_id, limit=limit)
    if not experiences:
        return ""

    lines = ["# Experience", "以下是这个数字人从历史工作中沉淀出的经验，回答时应优先参考："]
    for experience in reversed(experiences):
        lines.append(f"- {experience.summary}")
        for lesson in experience.lessons:
            lines.append(f"  - {lesson}")
    return "\n".join(lines)
