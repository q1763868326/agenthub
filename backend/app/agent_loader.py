from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any

import yaml

from .config import PACKAGES_DIR


@dataclass
class AgentPackage:
    id: str
    name: str
    version: str
    description: str
    author: str
    tags: list[str]
    prompt: str
    persona: str
    raw_manifest: dict[str, Any]

    @property
    def system_prompt(self) -> str:
        parts = []
        if self.persona.strip():
            parts.append("# Persona\n" + self.persona.strip())
        if self.prompt.strip():
            parts.append("# Instructions\n" + self.prompt.strip())
        return "\n\n".join(parts).strip()


def _read_text(path: Path) -> str:
    return path.read_text(encoding="utf-8") if path.exists() else ""


def load_agent_package(agent_dir: Path) -> AgentPackage | None:
    manifest_path = agent_dir / "manifest.yaml"
    if not manifest_path.exists():
        return None

    manifest = yaml.safe_load(manifest_path.read_text(encoding="utf-8")) or {}
    agent_id = manifest.get("id") or agent_dir.name.replace(".agent", "")

    return AgentPackage(
        id=agent_id,
        name=manifest.get("name", agent_id),
        version=str(manifest.get("version", "0.1.0")),
        description=manifest.get("description", ""),
        author=manifest.get("author", ""),
        tags=manifest.get("tags", []) or [],
        prompt=_read_text(agent_dir / "prompt.md"),
        persona=_read_text(agent_dir / "persona.md"),
        raw_manifest=manifest,
    )


def list_agents() -> list[AgentPackage]:
    if not PACKAGES_DIR.exists():
        return []
    agents: list[AgentPackage] = []
    for child in sorted(PACKAGES_DIR.iterdir()):
        if child.is_dir() and child.name.endswith(".agent"):
            pkg = load_agent_package(child)
            if pkg:
                agents.append(pkg)
    return agents


def get_agent(agent_id: str) -> AgentPackage | None:
    for agent in list_agents():
        if agent.id == agent_id:
            return agent
    return None
