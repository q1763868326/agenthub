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
- Package installation: `POST /instances`
- Agent Instance: `GET /instances`
- Session: `POST /instances/{instance_id}/sessions`
- Session summary: `POST /sessions/{session_id}/summarize`
- Experience: `GET /instances/{instance_id}/experiences`
- OpenAI Compatible API: `GET /v1/models`, `POST /v1/chat/completions`
- Open WebUI integration: select digital human instances from the model list

By default, when chatting with an Agent Instance, AgentOS automatically updates the current Session Summary and Experience after each assistant response. `POST /sessions/{session_id}/summarize` is mainly for debugging or manual recomputation.

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
curl http://localhost:8787/instances
curl http://localhost:8787/v1/models
```

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
