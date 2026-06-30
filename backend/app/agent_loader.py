from __future__ import annotations

import json
import re
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import yaml

from .config import PACKAGES_DIR

REQUIRED_MANIFEST_FIELDS = ["id", "name", "version", "description", "runtime"]
REQUIRED_PACKAGE_FILES = ["manifest.yaml", "prompt.md", "persona.md"]
SUPPORTED_RUNTIME_TYPES = {"openai-compatible"}
PACKAGE_ID_PATTERN = re.compile(r"^[a-zA-Z0-9_-]+$")


@dataclass
class PackageValidation:
    valid: bool
    errors: list[str]
    warnings: list[str]


@dataclass
class AgentPackage:
    id: str
    name: str
    version: str
    description: str
    author: str
    tags: list[str]
    permissions: list[str]
    skills: list[dict[str, Any]]
    runtime: dict[str, Any]
    package_path: str
    files: list[str]
    prompt: str
    persona: str
    mcp: dict[str, Any]
    raw_manifest: dict[str, Any]
    validation: PackageValidation

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


def _read_yaml(path: Path) -> dict[str, Any]:
    if not path.exists():
        return {}
    return yaml.safe_load(path.read_text(encoding="utf-8")) or {}


def _read_json(path: Path) -> dict[str, Any]:
    if not path.exists():
        return {}
    return json.loads(path.read_text(encoding="utf-8"))


def _list_package_files(agent_dir: Path) -> list[str]:
    return sorted(path.relative_to(agent_dir).as_posix() for path in agent_dir.rglob("*") if path.is_file())


def _write_text(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content.rstrip() + "\n", encoding="utf-8")


def validate_agent_package(agent_dir: Path, manifest: dict[str, Any] | None = None) -> PackageValidation:
    errors: list[str] = []
    warnings: list[str] = []
    manifest = manifest if manifest is not None else _read_yaml(agent_dir / "manifest.yaml")

    for filename in REQUIRED_PACKAGE_FILES:
        if not (agent_dir / filename).exists():
            errors.append(f"Missing required file: {filename}")

    for field in REQUIRED_MANIFEST_FIELDS:
        if manifest.get(field) in (None, ""):
            errors.append(f"Missing required manifest field: {field}")

    agent_id = manifest.get("id")
    if agent_id and not isinstance(agent_id, str):
        errors.append("manifest.id must be a string")
    elif isinstance(agent_id, str) and not PACKAGE_ID_PATTERN.fullmatch(agent_id):
        errors.append("manifest.id may contain only letters, numbers, hyphen, and underscore")

    if "tags" in manifest and not isinstance(manifest.get("tags"), list):
        errors.append("manifest.tags must be a list")
    for list_field in ["tags", "permissions", "skills"]:
        if list_field in manifest and not isinstance(manifest.get(list_field), list):
            errors.append(f"manifest.{list_field} must be a list")

    runtime = manifest.get("runtime")
    if runtime is not None and not isinstance(runtime, dict):
        errors.append("manifest.runtime must be an object")
    elif isinstance(runtime, dict):
        runtime_type = runtime.get("type")
        if runtime_type not in SUPPORTED_RUNTIME_TYPES:
            errors.append(f"Unsupported runtime.type: {runtime_type}")

    if not (agent_dir / "mcp.json").exists():
        warnings.append("Optional file not found: mcp.json")

    return PackageValidation(valid=not errors, errors=errors, warnings=warnings)


def load_agent_package(agent_dir: Path) -> AgentPackage | None:
    manifest_path = agent_dir / "manifest.yaml"
    if not manifest_path.exists():
        return None

    manifest = _read_yaml(manifest_path)
    agent_id = manifest.get("id") or agent_dir.name.replace(".agent", "")
    validation = validate_agent_package(agent_dir, manifest)

    return AgentPackage(
        id=agent_id,
        name=manifest.get("name", agent_id),
        version=str(manifest.get("version", "0.1.0")),
        description=manifest.get("description", ""),
        author=manifest.get("author", ""),
        tags=manifest.get("tags", []) or [],
        permissions=manifest.get("permissions", []) or [],
        skills=manifest.get("skills", []) or [],
        runtime=manifest.get("runtime", {}) or {},
        package_path=str(agent_dir),
        files=_list_package_files(agent_dir),
        prompt=_read_text(agent_dir / "prompt.md"),
        persona=_read_text(agent_dir / "persona.md"),
        mcp=_read_json(agent_dir / "mcp.json"),
        raw_manifest=manifest,
        validation=validation,
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


def create_agent_package(
    agent_id: str,
    name: str,
    description: str,
    author: str,
    persona: str,
    prompt: str,
    tags: list[str] | None = None,
    permissions: list[str] | None = None,
    skills: list[dict[str, Any]] | None = None,
    runtime: dict[str, Any] | None = None,
    mcp: dict[str, Any] | None = None,
) -> AgentPackage:
    if not PACKAGE_ID_PATTERN.fullmatch(agent_id):
        raise ValueError("Package id may contain only letters, numbers, hyphen, and underscore")

    agent_dir = PACKAGES_DIR / f"{agent_id}.agent"
    if agent_dir.exists():
        raise ValueError(f"Agent package already exists: {agent_id}")

    manifest = {
        "id": agent_id,
        "name": name,
        "version": "0.1.0",
        "description": description,
        "author": author,
        "tags": tags or [],
        "permissions": permissions or [],
        "skills": skills or [],
        "runtime": runtime or {"type": "openai-compatible"},
    }

    agent_dir.mkdir(parents=True, exist_ok=False)
    _write_text(agent_dir / "manifest.yaml", yaml.safe_dump(manifest, allow_unicode=True, sort_keys=False))
    _write_text(agent_dir / "persona.md", persona)
    _write_text(agent_dir / "prompt.md", prompt)
    _write_text(agent_dir / "mcp.json", json.dumps(mcp or {"servers": []}, ensure_ascii=False, indent=2))

    package = load_agent_package(agent_dir)
    if not package:
        raise ValueError(f"Failed to load created agent package: {agent_id}")
    if not package.validation.valid:
        raise ValueError("; ".join(package.validation.errors))
    return package


def package_summary(agent: AgentPackage) -> dict[str, Any]:
    return {
        "id": agent.id,
        "name": agent.name,
        "version": agent.version,
        "description": agent.description,
        "author": agent.author,
        "tags": agent.tags,
        "permissions": agent.permissions,
        "skills": agent.skills,
        "runtime": agent.runtime,
        "valid": agent.validation.valid,
        "validation": agent.validation.__dict__,
    }


def package_detail(agent: AgentPackage) -> dict[str, Any]:
    data = package_summary(agent)
    data.update(
        {
            "package_path": agent.package_path,
            "files": agent.files,
            "manifest": agent.raw_manifest,
            "mcp": agent.mcp,
            "prompt": agent.prompt,
            "persona": agent.persona,
        }
    )
    return data
