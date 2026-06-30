from contextlib import asynccontextmanager
from collections.abc import AsyncIterator

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field

from .agent_loader import list_agents
from .experience_manager import create_experience_from_session, list_experiences
from .instance_manager import ensure_default_instances, install_package, list_instances
from .openai_api import router as openai_router
from .session_manager import create_session, get_session, list_sessions


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


class InstallPackageRequest(BaseModel):
    package_id: str
    name: str | None = None
    config: dict = Field(default_factory=dict)


class CreateSessionRequest(BaseModel):
    title: str | None = None


@app.get("/health")
def health() -> dict:
    return {"status": "ok", "packages": len(list_agents()), "instances": len(list_instances())}


@app.get("/packages")
def packages() -> list[dict]:
    return [
        {
            "id": agent.id,
            "name": agent.name,
            "version": agent.version,
            "description": agent.description,
            "author": agent.author,
            "tags": agent.tags,
        }
        for agent in list_agents()
    ]


@app.get("/agents")
def agents() -> list[dict]:
    return packages()


@app.post("/instances")
def create_instance(req: InstallPackageRequest) -> dict:
    try:
        instance = install_package(package_id=req.package_id, name=req.name, config=req.config)
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    return instance.__dict__


@app.get("/instances")
def instances() -> list[dict]:
    return [instance.__dict__ for instance in list_instances()]


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
