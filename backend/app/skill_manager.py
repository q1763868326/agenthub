from __future__ import annotations

import json
import re
import shutil
import subprocess
from pathlib import Path
from typing import Any
from urllib.parse import urlparse

from .config import SKILLS_DIR
from .instance_manager import AgentInstance, get_instance, update_instance

GITHUB_HOSTS = {"github.com", "www.github.com"}


def _slug(value: str) -> str:
    text = re.sub(r"[^a-zA-Z0-9_-]+", "-", value.strip().lower())
    text = re.sub(r"-+", "-", text).strip("-")
    return text or "skill"


def _github_repo_name(url: str) -> str:
    parsed = urlparse(url)
    if parsed.scheme not in {"http", "https"} or parsed.netloc not in GITHUB_HOSTS:
        raise ValueError("Skill URL must be an https GitHub repository URL")
    parts = [part for part in parsed.path.strip("/").split("/") if part]
    if len(parts) < 2:
        raise ValueError("Skill URL must include owner and repository")
    repo = parts[1].removesuffix(".git")
    return repo


def _read_skill_metadata(path: Path, fallback_id: str, source_url: str) -> dict[str, Any]:
    skill_json = path / "skill.json"
    if skill_json.exists():
        data = json.loads(skill_json.read_text(encoding="utf-8"))
    else:
        data = {}

    skill_md = path / "SKILL.md"
    return {
        "id": data.get("id") or fallback_id,
        "name": data.get("name") or data.get("id") or fallback_id,
        "description": data.get("description", ""),
        "source": source_url,
        "path": str(path),
        "entry": "SKILL.md" if skill_md.exists() else data.get("entry", ""),
        "enabled": True,
    }


def install_skill_from_github(instance_id: str, url: str) -> AgentInstance:
    instance = get_instance(instance_id)
    if not instance:
        raise ValueError(f"Agent instance not found: {instance_id}")

    repo_name = _github_repo_name(url)
    skill_id = _slug(repo_name)
    target_dir = SKILLS_DIR / instance_id / skill_id
    target_dir.parent.mkdir(parents=True, exist_ok=True)
    if target_dir.exists():
        shutil.rmtree(target_dir)

    subprocess.run(
        ["git", "clone", "--depth", "1", url, str(target_dir)],
        check=True,
        capture_output=True,
        text=True,
        timeout=120,
    )

    metadata = _read_skill_metadata(target_dir, fallback_id=skill_id, source_url=url)
    skills = [skill for skill in instance.installed_skills if skill.get("id") != metadata["id"]]
    skills.append(metadata)
    return update_instance(instance_id=instance_id, installed_skills=skills)


def update_skill_enabled(instance_id: str, skill_id: str, enabled: bool) -> AgentInstance:
    instance = get_instance(instance_id)
    if not instance:
        raise ValueError(f"Agent instance not found: {instance_id}")

    skills = []
    found = False
    for skill in instance.installed_skills:
        item = dict(skill)
        if item.get("id") == skill_id:
            item["enabled"] = enabled
            found = True
        skills.append(item)
    if not found:
        raise ValueError(f"Agent skill not found: {skill_id}")
    return update_instance(instance_id=instance_id, installed_skills=skills)


def uninstall_skill(instance_id: str, skill_id: str) -> AgentInstance:
    instance = get_instance(instance_id)
    if not instance:
        raise ValueError(f"Agent instance not found: {instance_id}")

    removed = [skill for skill in instance.installed_skills if skill.get("id") == skill_id]
    if not removed:
        raise ValueError(f"Agent skill not found: {skill_id}")

    for skill in removed:
        path = skill.get("path")
        if path:
            shutil.rmtree(path, ignore_errors=True)

    skills = [skill for skill in instance.installed_skills if skill.get("id") != skill_id]
    return update_instance(instance_id=instance_id, installed_skills=skills)


def build_skill_prompt(instance: AgentInstance) -> str:
    enabled_skills = [skill for skill in instance.installed_skills if skill.get("enabled", True)]
    if not enabled_skills:
        return ""

    lines = ["# Installed Skills", "以下是当前数字人已启用的 Skill 声明。它们代表可用能力边界，但当前版本不会直接执行外部代码："]
    for skill in enabled_skills:
        line = f"- {skill.get('name') or skill.get('id')} ({skill.get('id')})"
        if skill.get("description"):
            line += f": {skill['description']}"
        if skill.get("entry"):
            line += f" [entry: {skill['entry']}]"
        lines.append(line)
    return "\n".join(lines)
