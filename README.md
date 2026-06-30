# AgentOS

> **面向数字人的操作系统（Operating System for Digital Humans）**

[English](README_EN.md)

AgentOS 不是另一个聊天机器人平台。

它希望成为 **数字人（Digital Human）** 的操作系统，让每一个 Agent 都像一个真正的软件，而不是一段 Prompt。

未来任何人都可以：

- 创建自己的数字人
- 发布自己的数字人
- 安装别人的数字人
- 给数字人安装 Skill
- 给数字人配置 MCP 工具
- 让数字人在工作中持续成长
- 升级、Fork、分享自己的数字人

## 为什么要做 AgentOS？

目前主流 AI 平台（ChatGPT、Coze、Dify、Open WebUI 等）都是围绕 **聊天（Chat）** 构建的。

核心模型通常是：

```text
Workspace
    ↓
Chat
```

或者：

```text
Application
    ↓
Conversation
```

在这种模型里，Agent 更像是一段 Prompt 或一个聊天机器人。

而我们认为，未来 AI 的核心对象应该是 **Agent**。

```text
Workspace
    ↓
Agent
    ↓
Session
    ↓
Experience
```

聊天只是 Agent 的一种能力。

Agent 更应该像一个长期存在、可安装、可升级、可成长的软件实体。

## AgentOS 的核心理念

AgentOS 把 Agent 分成三个核心层级：

```text
Agent Package
        │
        ▼
Agent Instance
        │
        ▼
Experience
```

### Agent Package（数字人安装包）

Package 是数字人的发行版。

例如：

- Java 后端工程师
- 摄影师
- 股票分析师
- 产品经理
- 英语老师

Package 包含：

- Prompt
- Persona
- Skills
- Workflow
- Knowledge
- MCP 声明
- 元数据

Package 是不可变的。

它负责：

- 发布
- 分享
- 升级
- Marketplace

Package 永远不保存用户数据。

### Agent Instance（数字人实例）

Package 安装以后，会生成属于用户自己的 Instance。

例如：

```text
Java Backend Engineer

↓

安装

↓

我的 Java Backend Engineer
```

Instance 保存：

- Memory
- Session
- Experience
- 配置
- 已安装 Skill
- MCP 绑定

不同用户安装同一个 Package，也会拥有完全独立的数字人。

### Session（工作会话）

Session 是数字人的一次工作。

例如：

```text
Java Agent

Session 1
代码 Review

Session 2
Bug 排查

Session 3
架构设计
```

Session 相互隔离。

每个 Session 都可以产生总结。

### Experience（经验）

Experience 不是 Prompt。

也不是 Memory。

它来源于真实工作。

```text
Session

↓

总结

↓

反思

↓

Experience
```

Experience 会不断增强数字人的能力。

数字人真正的成长来源于 Experience，而不是不断修改 Prompt。

## Agent Package 规范

每一个 Agent 都是一个 `.agent` 安装包。

示例：

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

未来任何平台都可以导入：

```text
xxx.agent
```

然后安装成自己的数字人。

### 当前原型格式

当前仓库已经支持最小 `.agent` 包：

```text
packages/zjf.agent/
├── manifest.yaml
├── persona.md
├── prompt.md
└── mcp.json
```

`manifest.yaml` 示例：

```yaml
id: zjf-digital-human
name: 朱健峰数字人
version: 0.1.0
description: 一个 Java/SpringBoot 后端工程师风格的数字人示例。
author: zjf
tags:
  - java
  - springboot
permissions:
  - mcp.call
runtime:
  type: openai-compatible
```

## 整体架构

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

负责：

- UI
- 登录
- Chat
- Workspace

### AgentOS

负责：

- Agent 生命周期
- Package
- Instance
- Session
- Marketplace
- Experience
- Registry

### Agency Orchestrator

负责：

- Workflow
- 多 Agent 协作
- Tool 调用
- DAG 执行

## 命名体系

本项目从 **AgentHub** 升级为 **AgentOS**。

- **AgentOS**：整个项目，数字人的操作系统
- **AgentHub**：AgentOS 的子模块，负责 Marketplace / Registry
- **Agent Package**：数字人安装包
- **Agent Instance**：用户安装后的数字人实例
- **Agent Runtime**：执行引擎，可对接 Agency Orchestrator、LangGraph 等

## 当前状态

当前仓库是一个最小可运行的 **OpenAI-compatible 数字人 / Agent Registry** 原型。

它可以让 Open WebUI 像选择模型一样选择不同数字人：

- `my-zjf-digital-human`
- `my-photographer-agent`
- `zjf-digital-human`
- `photographer-agent`

启动时，AgentOS 会把 `packages/` 下的默认 Package 自动安装成用户 Instance。

没有配置真实 LLM Key 时，系统会返回 mock 回复，方便先验证 Open WebUI 是否接通。

当前已经具备第一阶段的最小闭环：

- Package Registry：扫描 `packages/*.agent`
- Package 校验：检查 manifest 必填字段、runtime、权限类型和必需文件
- Package 创建：`POST /packages`，支持 Persona、Prompt、Skills 声明和 MCP 声明
- Package 安装：`POST /instances`
- Agent Instance：`GET /instances`、`PATCH /instances/{instance_id}`
- Skill 安装：`POST /instances/{instance_id}/skills`，支持从 GitHub 仓库下载到实例
- Skill 生命周期：`PATCH /instances/{instance_id}/skills/{skill_id}`、`DELETE /instances/{instance_id}/skills/{skill_id}`
- Session：`POST /instances/{instance_id}/sessions`
- Session 总结：`POST /sessions/{session_id}/summarize`
- Experience：`GET /instances/{instance_id}/experiences`
- Experience 管理：`GET /experiences/{experience_id}`、`PATCH /experiences/{experience_id}`、`DELETE /experiences/{experience_id}`
- OpenAI Compatible API：`GET /v1/models`、`POST /v1/chat/completions`
- Open WebUI 接入：通过模型列表选择数字人实例
- AgentOS Admin：`GET /admin`

默认情况下，使用 Agent Instance 聊天时，AgentOS 会记录原始消息，并按阈值自动更新当前 Session 的 Summary 和 Experience。默认策略是每累计 6 条消息触发一次，并跳过过短的用户输入。`POST /sessions/{session_id}/summarize` 主要用于调试或手动重算。

Experience 默认启用，会被注入到后续对话的 system prompt。可以禁用或删除不想继续影响数字人的经验：

```bash
curl -X PATCH http://localhost:8787/experiences/{experience_id} \
  -H "Content-Type: application/json" \
  -d '{"enabled": false}'

curl -X DELETE http://localhost:8787/experiences/{experience_id}
```

Instance 可以独立编辑名称、描述、配置和 MCP 绑定：

```bash
curl -X PATCH http://localhost:8787/instances/my-zjf-digital-human \
  -H "Content-Type: application/json" \
  -d '{"name": "我的 Java 后端工程师", "config": {"tone": "pragmatic"}, "mcp_bindings": {}}'
```

给 Instance 安装 GitHub Skill：

```bash
curl -X POST http://localhost:8787/instances/my-zjf-digital-human/skills \
  -H "Content-Type: application/json" \
  -d '{"url": "https://github.com/owner/skill-repo"}'
```

启用或卸载 Skill：

```bash
curl -X PATCH http://localhost:8787/instances/my-zjf-digital-human/skills/code-review \
  -H "Content-Type: application/json" \
  -d '{"enabled": false}'

curl -X DELETE http://localhost:8787/instances/my-zjf-digital-human/skills/code-review
```

当前版本会下载并登记 Skill 元数据，并把启用的 Skill 声明注入数字人的 system prompt，但不会执行 Skill 代码；Runtime 执行和权限沙箱会在后续阶段接入。

## 本地运行

```bash
cd agenthub/backend
pip install -r requirements.txt
uvicorn app.main:app --host 0.0.0.0 --port 8787
```

然后访问：

```bash
curl http://localhost:8787/health
curl http://localhost:8787/packages
curl http://localhost:8787/packages/zjf-digital-human
curl http://localhost:8787/instances
curl http://localhost:8787/v1/models
```

创建一个数字人 Package：

```bash
curl -X POST http://localhost:8787/packages \
  -H "Content-Type: application/json" \
  -d '{
    "id": "my-agent",
    "name": "我的数字人",
    "description": "一个自定义数字人",
    "author": "me",
    "tags": ["custom"],
    "persona": "你是我的数字人分身。",
    "prompt": "使用中文，回答务实、具体、可执行。",
    "skills": [{"id": "code-review", "name": "代码 Review"}],
    "mcp": {"servers": []}
  }'
```

也可以打开管理台：

```text
http://localhost:8787/admin
```

管理台支持创建数字人 Package、填写 Persona/Prompt/Skills/MCP 声明、查看 Package 校验结果、安装 Package、编辑 Instance 配置、从 GitHub 安装/启用/禁用/卸载 Skill、查看 Session、启用/禁用/删除 Experience。

手动重算一次 Experience：

```bash
curl -X POST http://localhost:8787/sessions/{session_id}/summarize
curl http://localhost:8787/instances/my-zjf-digital-human/experiences
```

## Docker 运行

```bash
cd agenthub
export OPENAI_API_KEY=你的key
# 可选：export OPENAI_BASE_URL=https://api.openai.com/v1
docker compose up --build
```

Compose 会同时启动：

- AgentOS API：`http://localhost:8787`
- Open WebUI：`http://localhost:3000`

Open WebUI 已通过环境变量预置连接到 AgentOS：

```text
OPENAI_API_BASE_URL=http://agenthub:8787/v1
OPENAI_API_KEY=agenthub
```

默认设置了 `WEBUI_AUTH=False`，本地打开即可使用。如果需要登录系统，可以启动前设置：

```bash
export WEBUI_AUTH=True
```

可以通过环境变量调整 Experience 自动刷新策略：

```bash
export AGENTHUB_AUTO_EXPERIENCE_EVERY_N_MESSAGES=6
export AGENTHUB_AUTO_EXPERIENCE_MIN_USER_CHARS=8
```

## 接入 Open WebUI

在 Open WebUI 里添加一个 OpenAI-compatible Provider：

```text
Base URL: http://localhost:8787/v1
API Key: 随便填一个，例如 agenthub
```

然后模型列表里应该能看到：

```text
my-zjf-digital-human
my-photographer-agent
zjf-digital-human
photographer-agent
```

选择后聊天，请求会进入 AgentOS。

## 项目路线图

### 第一阶段：数字人能够运行

完成：

- Agent Registry
- Package 导入
- Package 安装
- Agent Instance
- Session
- OpenAI Compatible API
- Open WebUI 接入

目标：

上传一个数字人，并能够开始工作。

### 第二阶段：数字人拥有能力

完成：

- Skills
- MCP
- Knowledge
- 权限管理

目标：

数字人真正能够完成任务。

### 第三阶段：数字人成长

完成：

- Session 总结
- Reflection
- Experience Engine
- Memory 管理

目标：

数字人能够随着工作不断成长。

### 第四阶段：数字人生态

完成：

- Marketplace
- Package 发布
- Package 升级
- Package 回滚
- Fork
- 分享

目标：

最终形成开放的数字人生态。

## 长期愿景

Docker 让软件可以打包和分发。

GitHub 让代码可以协作和共享。

VS Code Marketplace 让插件可以安装和升级。

AgentOS 希望让 **数字人** 也拥有同样完整的生命周期：

> 创建 → 打包 → 发布 → 安装 → 工作 → 成长 → 升级 → 分享

我们并不是在做另一个聊天机器人。

我们希望构建的是：

**数字人的操作系统（Operating System for Digital Humans）。**
