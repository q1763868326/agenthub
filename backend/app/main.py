from contextlib import asynccontextmanager
from collections.abc import AsyncIterator
from pathlib import Path
import tempfile

from fastapi import Body, FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, Field

from .agent_loader import (
    create_agent_package,
    delete_agent_package,
    export_agent_package,
    get_agent,
    import_agent_package,
    list_agents,
    package_detail,
    package_summary,
)
from .experience_manager import (
    create_experience_from_session,
    delete_experience,
    delete_experiences_for_instance,
    get_experience,
    list_experiences,
    update_experience_enabled,
)
from .instance_manager import delete_instance, ensure_default_instances, install_package, list_instances, update_instance
from .openai_api import router as openai_router
from .session_manager import create_session, delete_sessions_for_instance, get_session, list_sessions
from .skill_manager import delete_skill_files_for_instance, install_skill_from_github, uninstall_skill, update_skill_enabled


@asynccontextmanager
async def lifespan(_: FastAPI) -> AsyncIterator[None]:
    ensure_default_instances()
    yield


app = FastAPI(title="AgentOS", version="0.1.0", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(openai_router)

STATIC_DIR = Path(__file__).resolve().parent / "static"
if STATIC_DIR.exists():
    app.mount("/static", StaticFiles(directory=STATIC_DIR), name="static")


class InstallPackageRequest(BaseModel):
    package_id: str
    name: str | None = None
    config: dict = Field(default_factory=dict)


class CreatePackageRequest(BaseModel):
    id: str
    name: str
    description: str = ""
    author: str = ""
    persona: str
    prompt: str
    tags: list[str] = Field(default_factory=list)
    permissions: list[str] = Field(default_factory=list)
    skills: list[dict] = Field(default_factory=list)
    runtime: dict = Field(default_factory=lambda: {"type": "openai-compatible"})
    mcp: dict = Field(default_factory=lambda: {"servers": []})


class CreateSessionRequest(BaseModel):
    title: str | None = None


class UpdateInstanceRequest(BaseModel):
    name: str | None = None
    description: str | None = None
    config: dict | None = None
    mcp_bindings: dict | None = None


class InstallSkillRequest(BaseModel):
    url: str


class UpdateSkillRequest(BaseModel):
    enabled: bool


class UpdateExperienceRequest(BaseModel):
    enabled: bool


@app.get("/admin", include_in_schema=False)
def admin() -> FileResponse:
    return FileResponse(STATIC_DIR / "admin.html")


@app.get("/health")
def health() -> dict:
    return {"status": "ok", "packages": len(list_agents()), "instances": len(list_instances())}


@app.get("/packages")
def packages() -> list[dict]:
    return [package_summary(agent) for agent in list_agents()]


@app.post("/packages")
def create_package(req: CreatePackageRequest) -> dict:
    try:
        agent = create_agent_package(
            agent_id=req.id,
            name=req.name,
            description=req.description,
            author=req.author,
            persona=req.persona,
            prompt=req.prompt,
            tags=req.tags,
            permissions=req.permissions,
            skills=req.skills,
            runtime=req.runtime,
            mcp=req.mcp,
        )
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    return package_detail(agent)


@app.get("/packages/{package_id}")
def package(package_id: str) -> dict:
    agent = get_agent(package_id)
    if not agent:
        raise HTTPException(status_code=404, detail=f"Agent package not found: {package_id}")
    return package_detail(agent)


@app.get("/packages/{package_id}/export")
def export_package(package_id: str) -> FileResponse:
    try:
        archive_path = export_agent_package(package_id)
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    return FileResponse(
        archive_path,
        media_type="application/zip",
        filename=archive_path.name,
    )


@app.delete("/packages/{package_id}")
def delete_package(package_id: str) -> dict:
    used_by = [instance.id for instance in list_instances() if instance.package_id == package_id]
    if used_by:
        raise HTTPException(status_code=409, detail={"message": "Package is installed by instances", "instances": used_by})
    try:
        delete_agent_package(package_id)
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    return {"deleted": True, "id": package_id}


@app.post("/packages/import")
async def import_package(body: bytes = Body(..., media_type="application/zip")) -> dict:
    with tempfile.NamedTemporaryFile(suffix=".zip", delete=False) as tmp:
        tmp.write(body)
        tmp_path = Path(tmp.name)

    try:
        agent = import_agent_package(tmp_path)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    finally:
        tmp_path.unlink(missing_ok=True)
    return package_detail(agent)


@app.get("/agents")
def agents() -> list[dict]:
    return packages()


@app.post("/instances")
def create_instance(req: InstallPackageRequest) -> dict:
    try:
        instance = install_package(package_id=req.package_id, name=req.name, config=req.config)
    except ValueError as exc:
        message = str(exc)
        status_code = 400 if "invalid" in message else 404
        raise HTTPException(status_code=status_code, detail=message) from exc
    return instance.__dict__


@app.get("/instances")
def instances() -> list[dict]:
    return [instance.__dict__ for instance in list_instances()]


@app.patch("/instances/{instance_id}")
def patch_instance(instance_id: str, req: UpdateInstanceRequest) -> dict:
    try:
        instance = update_instance(
            instance_id=instance_id,
            name=req.name,
            description=req.description,
            config=req.config,
            mcp_bindings=req.mcp_bindings,
        )
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    return instance.__dict__


@app.delete("/instances/{instance_id}")
def uninstall_instance(instance_id: str) -> dict:
    try:
        instance = delete_instance(instance_id)
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc

    deleted_sessions = delete_sessions_for_instance(instance_id)
    deleted_experiences = delete_experiences_for_instance(instance_id)
    deleted_skills = delete_skill_files_for_instance(instance)
    return {
        "deleted": True,
        "id": instance_id,
        "sessions": deleted_sessions,
        "experiences": deleted_experiences,
        "skill_files": deleted_skills,
    }


@app.post("/instances/{instance_id}/skills")
def install_skill(instance_id: str, req: InstallSkillRequest) -> dict:
    try:
        instance = install_skill_from_github(instance_id=instance_id, url=req.url)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except Exception as exc:
        raise HTTPException(status_code=502, detail=f"Failed to install skill: {exc}") from exc
    return instance.__dict__


@app.patch("/instances/{instance_id}/skills/{skill_id}")
def update_skill(instance_id: str, skill_id: str, req: UpdateSkillRequest) -> dict:
    try:
        instance = update_skill_enabled(instance_id=instance_id, skill_id=skill_id, enabled=req.enabled)
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    return instance.__dict__


@app.delete("/instances/{instance_id}/skills/{skill_id}")
def remove_skill(instance_id: str, skill_id: str) -> dict:
    try:
        instance = uninstall_skill(instance_id=instance_id, skill_id=skill_id)
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    return instance.__dict__


@app.post("/instances/{instance_id}/sessions")
def new_session(instance_id: str, req: CreateSessionRequest) -> dict:
    try:
        session = create_session(instance_id=instance_id, title=req.title)
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    return session.__dict__


@app.get("/instances/{instance_id}/sessions")
def sessions(instance_id: str) -> list[dict]:
    return [session.__dict__ for session in list_sessions(instance_id=instance_id)]


@app.get("/sessions/{session_id}")
def session_detail(session_id: str) -> dict:
    session = get_session(session_id)
    if not session:
        raise HTTPException(status_code=404, detail=f"Agent session not found: {session_id}")
    return session.__dict__


@app.post("/sessions/{session_id}/summarize")
def summarize_session(session_id: str) -> dict:
    try:
        experience = create_experience_from_session(session_id)
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    session = get_session(session_id)
    return {"session": session.__dict__ if session else None, "experience": experience.__dict__}


@app.get("/instances/{instance_id}/experiences")
def experiences(instance_id: str) -> list[dict]:
    return [experience.__dict__ for experience in list_experiences(instance_id=instance_id)]


@app.get("/experiences/{experience_id}")
def experience_detail(experience_id: str) -> dict:
    experience = get_experience(experience_id)
    if not experience:
        raise HTTPException(status_code=404, detail=f"Agent experience not found: {experience_id}")
    return experience.__dict__


@app.patch("/experiences/{experience_id}")
def update_experience(experience_id: str, req: UpdateExperienceRequest) -> dict:
    try:
        experience = update_experience_enabled(experience_id, req.enabled)
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    return experience.__dict__


@app.delete("/experiences/{experience_id}")
def remove_experience(experience_id: str) -> dict:
    try:
        delete_experience(experience_id)
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    return {"deleted": True, "id": experience_id}
