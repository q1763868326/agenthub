from __future__ import annotations

import re
import time
from dataclasses import asdict, dataclass
from typing import Any

from .agent_loader import AgentPackage, get_agent, list_agents
from .config import DATA_DIR
from .storage import read_json, write_json

INSTANCES_PATH = DATA_DIR / "instances.json"


@dataclass
class AgentInstance:
    id: str
    package_id: str
    package_version: str
    name: str
    description: str
    created_at: int
    updated_at: int
    config: dict[str, Any]
    installed_skills: list[dict[str, Any]]
    mcp_bindings: dict[str, Any]


def _slug(value: str) -> str:
    text = re.sub(r"[^a-zA-Z0-9_-]+", "-", value.strip().lower())
    text = re.sub(r"-+", "-", text).strip("-")
    return text or "agent"


def _load_instances() -> list[dict[str, Any]]:
    return read_json(INSTANCES_PATH, [])


def _save_instances(items: list[dict[str, Any]]) -> None:
    write_json(INSTANCES_PATH, items)


def _from_dict(item: dict[str, Any]) -> AgentInstance:
    return AgentInstance(
        id=item["id"],
        package_id=item["package_id"],
        package_version=str(item.get("package_version", "")),
        name=item.get("name") or item["id"],
        description=item.get("description", ""),
        created_at=int(item.get("created_at", 0)),
        updated_at=int(item.get("updated_at", item.get("created_at", 0))),
        config=item.get("config") or {},
        installed_skills=item.get("installed_skills") or [],
        mcp_bindings=item.get("mcp_bindings") or {},
    )


def list_instances() -> list[AgentInstance]:
    return [_from_dict(item) for item in _load_instances()]


def get_instance(instance_id: str) -> AgentInstance | None:
    for instance in list_instances():
        if instance.id == instance_id:
            return instance
    return None


def update_instance(
    instance_id: str,
    name: str | None = None,
    description: str | None = None,
    config: dict[str, Any] | None = None,
    mcp_bindings: dict[str, Any] | None = None,
    installed_skills: list[dict[str, Any]] | None = None,
) -> AgentInstance:
    items = _load_instances()
    now = int(time.time())
    for item in items:
        if item["id"] == instance_id:
            if name is not None:
                item["name"] = name
            if description is not None:
                item["description"] = description
            if config is not None:
                item["config"] = config
            if mcp_bindings is not None:
                item["mcp_bindings"] = mcp_bindings
            if installed_skills is not None:
                item["installed_skills"] = installed_skills
            item["updated_at"] = now
            _save_instances(items)
            return _from_dict(item)
    raise ValueError(f"Agent instance not found: {instance_id}")


def install_package(package_id: str, name: str | None = None, config: dict[str, Any] | None = None) -> AgentInstance:
    package = get_agent(package_id)
    if not package:
        raise ValueError(f"Agent package not found: {package_id}")
    if not package.validation.valid:
        errors = "; ".join(package.validation.errors)
        raise ValueError(f"Agent package is invalid: {errors}")

    now = int(time.time())
    base_id = _slug(name or f"my-{package.id}")
    instance_id = base_id
    existing_ids = {item["id"] for item in _load_instances()}
    index = 2
    while instance_id in existing_ids:
        instance_id = f"{base_id}-{index}"
        index += 1

    instance = AgentInstance(
        id=instance_id,
        package_id=package.id,
        package_version=package.version,
        name=name or f"我的 {package.name}",
        description=package.description,
        created_at=now,
        updated_at=now,
        config=config or {},
        installed_skills=[],
        mcp_bindings={},
    )

    items = _load_instances()
    items.append(asdict(instance))
    _save_instances(items)
    return instance

def delete_instance(instance_id: str) -> AgentInstance:
    items = _load_instances()
    for item in items:
        if item["id"] == instance_id:
            remaining = [candidate for candidate in items if candidate["id"] != instance_id]
            _save_instances(remaining)
            return _from_dict(item)
    raise ValueError(f"Agent instance not found: {instance_id}")


def resolve_agent(model_id: str) -> tuple[AgentPackage, AgentInstance | None] | None:
    instance = get_instance(model_id)
    if instance:
        package = get_agent(instance.package_id)
        return (package, instance) if package else None

    package = get_agent(model_id)
    return (package, None) if package else None


def ensure_default_instances() -> None:
    if _load_instances():
        return
    for package in list_agents():
        install_package(package.id)
