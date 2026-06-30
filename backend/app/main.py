from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from .agent_loader import list_agents
from .openai_api import router as openai_router

app = FastAPI(title="AgentHub", version="0.1.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(openai_router)


@app.get("/health")
def health() -> dict:
    return {"status": "ok", "agents": len(list_agents())}


@app.get("/agents")
def agents() -> list[dict]:
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
