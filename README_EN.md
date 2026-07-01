# AgentOS

> **Operating System for Digital Humans**

[中文](README.md)

AgentOS is not another chatbot platform.

It aims to become an operating system for **Digital Humans**, where every Agent behaves like real software instead of a single prompt.

In the future, anyone should be able to:

- Create their own digital humans
- Publish their own digital humans
- Install digital humans created by others
- Install Skills for digital humans
- Configure MCP tools for digital humans
- Let digital humans continuously grow through work
- Upgrade, fork, and share digital humans

## Why AgentOS?

Most mainstream AI platforms, including ChatGPT, Coze, Dify, and Open WebUI, are built around **Chat**.

Their core model is usually:

```text
Workspace
    ↓
Chat
```

or:

```text
Application
    ↓
Conversation
```

In this model, an Agent is closer to a prompt or chatbot.

AgentOS takes a different position: the core object of future AI software should be the **Agent**.

```text
Workspace
    ↓
Agent
    ↓
Session
    ↓
Experience
```

Chat is only one capability of an Agent.

An Agent should be a long-lived, installable, upgradeable, and continuously improving software entity.

## Core Concepts

AgentOS organizes Agents into three core layers:

```text
Agent Package
        │
        ▼
Agent Instance
        │
        ▼
Experience
```

### Agent Package

A Package is the distributable version of a digital human.

Examples:

- Java backend engineer
- Photographer
- Stock analyst
- Product manager
- English teacher

A Package contains:

- Prompt
- Persona
- Skills
- Workflow
- Knowledge
- MCP declarations
- Metadata

Packages are immutable.

They are responsible for:

- Publishing
- Sharing
- Upgrading
- Marketplace distribution

Packages never store user data.

### Agent Instance

After a Package is installed, it becomes a user-owned Instance.

```text
Java Backend Engineer

↓

Install

↓

My Java Backend Engineer
```

An Instance stores:

- Memory
- Sessions
- Experiences
- Configuration
- Installed Skills
- MCP bindings

Different users can install the same Package while owning completely independent digital humans.

### Session

A Session is one unit of work performed by a digital human.

```text
Java Agent

Session 1
Code Review

Session 2
Bug Investigation

Session 3
Architecture Design
```

Sessions are isolated from each other.

Each Session can produce a summary.

### Experience

Experience is not Prompt.

Experience is not Memory.

It comes from real work.

```text
Session

↓

Summary

↓

Reflection

↓

Experience
```

Experience continuously improves the capability of a digital human.

Real growth should come from Experience, not from repeatedly editing prompts.

## Agent Package Specification

Every Agent is a `.agent` package.

Example:

```text
backend-engineer.agent/
├── manifest.yaml
├── prompt.md
├── persona.md
├── knowledge/
├── skills/
├── workflow/
├── examples/
├── mcp.json
└── avatar.png
```

Any platform should eventually be able to import:

```text
xxx.agent
```

and install it as a user-owned digital human.

### Current Prototype Format

The current repository supports a minimal `.agent` package:

```text
packages/zjf.agent/
├── manifest.yaml
├── persona.md
├── prompt.md
└── mcp.json
```

Example `manifest.yaml`:

```yaml
id: zjf-digital-human
name: Zhu Jianfeng Digital Human
version: 0.1.0
description: A Java/Spring Boot backend engineer style digital human example.
author: zjf
tags:
  - java
  - springboot
permissions:
  - mcp.call
runtime:
  type: openai-compatible
```

## Architecture

```text
                Open WebUI
                     │
                     ▼
                AgentOS
────────────────────────────────

 Agent Registry

 Package Manager

 Session Manager

 Experience Engine

 AgentHub / Marketplace

 Runtime Adapter

 OpenAI Compatible API

────────────────────────────────
                     │
                     ▼

          Agency Orchestrator

────────────────────────────────

 Workflow

 DAG

 Multi-Agent

 Tool Calling

────────────────────────────────
                     │
                     ▼

             LLM / MCP / Tools
```

### Open WebUI

Responsible for:

- UI
- Authentication
- Chat
- Workspace

### AgentOS

Responsible for:

- Agent lifecycle
- Packages
- Instances
- Sessions
- Marketplace
- Experience
- Registry

### Agency Orchestrator

Responsible for:

- Workflow
- Multi-agent collaboration
- Tool calling
- DAG execution

## Naming

This project is evolving from **AgentHub** to **AgentOS**.

- **AgentOS**: the whole project, an operating system for digital humans
- **AgentHub**: a submodule of AgentOS for Marketplace / Registry
- **Agent Package**: the installable digital human package
- **Agent Instance**: the user-owned installed digital human
- **Agent Runtime**: the execution engine, such as Agency Orchestrator or LangGraph

## Current Status

This repository is currently a minimal runnable **OpenAI-compatible digital human / Agent Registry** prototype.

It lets Open WebUI select digital humans like models:

- `my-zjf-digital-human`
- `my-photographer-agent`
- `zjf-digital-human`
- `photographer-agent`

On startup, AgentOS automatically installs default Packages from `packages/` as user Instances.

Without a real LLM key, the system returns mock responses so the Open WebUI integration can be verified first.

The current prototype already has the minimal Phase 1 loop:

- Package Registry: scans `packages/*.agent`
- Package validation: checks required manifest fields, runtime, permission types, and required files
- Package creation: `POST /packages`, with Persona, Prompt, Skills declarations, and MCP declarations
- Package import/export/delete: `POST /packages/import`, `GET /packages/{package_id}/export`, `DELETE /packages/{package_id}`
- Package installation: `POST /instances`
- Agent Instance: `GET /instances`, `PATCH /instances/{instance_id}`, `POST /instances/{instance_id}/upgrade`, `DELETE /instances/{instance_id}`
- Skill installation: `POST /instances/{instance_id}/skills`, downloads a GitHub repository into an Instance
- Skill lifecycle: `PATCH /instances/{instance_id}/skills/{skill_id}`, `DELETE /instances/{instance_id}/skills/{skill_id}`
- Session: `POST /instances/{instance_id}/sessions`
- Session summary: `POST /sessions/{session_id}/summarize`
- Experience: `GET /instances/{instance_id}/experiences`
- Experience management: `GET /experiences/{experience_id}`, `PATCH /experiences/{experience_id}`, `DELETE /experiences/{experience_id}`
- OpenAI Compatible API: `GET /v1/models`, `POST /v1/chat/completions`
- Open WebUI integration: select digital human instances from the model list
- AgentOS Admin: `GET /admin`

By default, when chatting with an Agent Instance, AgentOS records raw messages and updates the current Session Summary and Experience only when a threshold is reached. The default policy refreshes every 6 messages and skips very short user inputs. `POST /sessions/{session_id}/summarize` is mainly for debugging or manual recomputation.

Experiences are enabled by default and injected into future conversations through the system prompt. Unwanted Experiences can be disabled or deleted:

```bash
curl -X PATCH http://localhost:8787/experiences/{experience_id} \
  -H "Content-Type: application/json" \
  -d '{"enabled": false}'

curl -X DELETE http://localhost:8787/experiences/{experience_id}
```

Instances can independently edit name, description, config, and MCP bindings:

```bash
curl -X PATCH http://localhost:8787/instances/my-zjf-digital-human \
  -H "Content-Type: application/json" \
  -d '{"name": "My Java Backend Engineer", "config": {"tone": "pragmatic"}, "mcp_bindings": {}}'
```

Instances expose their installed `package_version`, the current Package `current_package_version`, and `upgrade_available`. Upgrading only updates the bound Package version and does not delete user config, Sessions, Experiences, or Skills:

```bash
curl -X POST http://localhost:8787/instances/my-zjf-digital-human/upgrade \
  -H "Content-Type: application/json" \
  -d '{"sync_description": false}'
```

Uninstalling an Instance deletes its Sessions, Experiences, and Skill files:

```bash
curl -X DELETE http://localhost:8787/instances/my-zjf-digital-human
```

Install a GitHub Skill into an Instance:

```bash
curl -X POST http://localhost:8787/instances/my-zjf-digital-human/skills \
  -H "Content-Type: application/json" \
  -d '{"url": "https://github.com/owner/skill-repo"}'
```

Enable, disable, or uninstall a Skill:

```bash
curl -X PATCH http://localhost:8787/instances/my-zjf-digital-human/skills/code-review \
  -H "Content-Type: application/json" \
  -d '{"enabled": false}'

curl -X DELETE http://localhost:8787/instances/my-zjf-digital-human/skills/code-review
```

The current version downloads and registers Skill metadata, and injects enabled Skill declarations into the digital human's system prompt, but does not execute Skill code yet. Runtime execution and permission sandboxing will be connected in a later phase.

## Local Development

```bash
cd agenthub/backend
pip install -r requirements.txt
uvicorn app.main:app --host 0.0.0.0 --port 8787
```

Then visit:

```bash
curl http://localhost:8787/health
curl http://localhost:8787/packages
curl http://localhost:8787/packages/zjf-digital-human
curl http://localhost:8787/instances
curl http://localhost:8787/v1/models
```

Create a digital human Package:

```bash
curl -X POST http://localhost:8787/packages \
  -H "Content-Type: application/json" \
  -d '{
    "id": "my-agent",
    "name": "My Digital Human",
    "description": "A custom digital human",
    "author": "me",
    "tags": ["custom"],
    "persona": "You are my digital human twin.",
    "prompt": "Answer concretely and pragmatically.",
    "skills": [{"id": "code-review", "name": "Code Review"}],
    "mcp": {"servers": []}
  }'
```

Export and import `.agent.zip`:

```bash
curl -L http://localhost:8787/packages/my-agent/export -o my-agent.agent.zip

curl -X POST http://localhost:8787/packages/import \
  -H "Content-Type: application/zip" \
  --data-binary "@my-agent.agent.zip"
```

Delete a Package that is not installed by any Instance:

```bash
curl -X DELETE http://localhost:8787/packages/my-agent
```

You can also open the admin console:

```text
http://localhost:8787/admin
```

The admin console supports digital human Package creation, Persona/Prompt/Skills/MCP declarations, `.agent` Package import/export/delete, package validation results, Instance installation, upgrade, and uninstallation, instance config editing, GitHub Skill installation, enabling, disabling, and uninstalling Skills, sessions, and enabling, disabling, or deleting Experiences.

Manually recompute an Experience:

```bash
curl -X POST http://localhost:8787/sessions/{session_id}/summarize
curl http://localhost:8787/instances/my-zjf-digital-human/experiences
```

## Docker

```bash
cd agenthub
export OPENAI_API_KEY=your_key
# Optional: export OPENAI_BASE_URL=https://api.openai.com/v1
docker compose up --build
```

Compose starts:

- AgentOS API: `http://localhost:8787`
- Open WebUI: `http://localhost:3000`

Open WebUI is preconfigured to connect to AgentOS:

```text
OPENAI_API_BASE_URL=http://agenthub:8787/v1
OPENAI_API_KEY=agenthub
```

`WEBUI_AUTH=False` is enabled by default for local use. To require login:

```bash
export WEBUI_AUTH=True
```

The automatic Experience refresh policy can be adjusted with environment variables:

```bash
export AGENTHUB_AUTO_EXPERIENCE_EVERY_N_MESSAGES=6
export AGENTHUB_AUTO_EXPERIENCE_MIN_USER_CHARS=8
```

## Open WebUI Integration

Add an OpenAI-compatible Provider in Open WebUI:

```text
Base URL: http://localhost:8787/v1
API Key: any value, for example agenthub
```

The model list should show:

```text
my-zjf-digital-human
my-photographer-agent
zjf-digital-human
photographer-agent
```

After selecting one, chat requests will be routed into AgentOS.

## Roadmap

### Phase 1: Digital Humans Can Run

Scope:

- Agent Registry
- Package import
- Package installation
- Agent Instance
- Session
- OpenAI Compatible API
- Open WebUI integration

Goal:

Upload a digital human and start working with it.

### Phase 2: Digital Humans Have Capabilities

Scope:

- Skills
- MCP
- Knowledge
- Permission management

Goal:

Digital humans can perform real tasks.

### Phase 3: Digital Humans Grow

Scope:

- Session summaries
- Reflection
- Experience Engine
- Memory management

Goal:

Digital humans continuously improve through work.

### Phase 4: Digital Human Ecosystem

Scope:

- Marketplace
- Package publishing
- Package upgrades
- Package rollback
- Fork
- Sharing

Goal:

Build an open ecosystem for digital humans.

## Long-Term Vision

Docker made software packageable and distributable.

GitHub made code collaborative and shareable.

VS Code Marketplace made plugins installable and upgradeable.

AgentOS wants to give **Digital Humans** the same complete lifecycle:

> Create → Package → Publish → Install → Work → Grow → Upgrade → Share

We are not building another chatbot.

We are building:

**An Operating System for Digital Humans.**
