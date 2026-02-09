# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

kanobot is an ultra-lightweight personal AI assistant framework (~4,000 lines of Python). It provides a tool-using agent loop that connects to multiple LLM providers and chat channels (Telegram, WhatsApp, CLI). Recently renamed from "nanobot" to "kanobot".

## Common Commands

```bash
# Install for development
pip install -e .

# Lint
ruff check kanobot/

# Run tests
pytest tests/

# Run single test
pytest tests/test_tool_validation.py -k "test_name"

# CLI usage
kanobot onboard                    # Initialize config & workspace
kanobot agent -m "message"         # Single message mode
kanobot agent                      # Interactive chat mode
kanobot gateway                    # Start persistent gateway with channels
kanobot status                     # Show configuration status
```

## Architecture

### Core Loop (`kanobot/agent/loop.py`)
`AgentLoop` is the central engine. It consumes `InboundMessage` from the message bus, builds context (system prompt + history + memory + skills), then enters a loop: call LLM → if tool calls, execute them via `ToolRegistry` and feed results back → repeat until LLM responds with text (max 20 iterations). Responses are published as `OutboundMessage`.

### Message Bus (`kanobot/bus/`)
Async event bus decouples channels from the agent. `MessageBus` has inbound/outbound `asyncio.Queue`s. Channels push to inbound; a background dispatch task routes outbound messages to the correct channel subscriber.

### Tool System (`kanobot/agent/tools/`)
Abstract `Tool` base class with JSON Schema parameter validation. `ToolRegistry` dynamically registers tools and formats them in OpenAI function-calling format. Default tools: `read_file`, `write_file`, `edit_file`, `list_dir`, `exec`, `web_search`, `web_fetch`, `message`, `spawn`.

### LLM Providers (`kanobot/providers/`)
Abstract `LLMProvider` interface. `LiteLLMProvider` wraps the litellm library to support OpenRouter, Anthropic, OpenAI, Groq, Gemini, Zhipu, vLLM, and AWS Bedrock. Provider is selected by which API key is configured (priority: OpenRouter > Anthropic > OpenAI > Gemini > Zhipu > Groq > vLLM).

### Context Building (`kanobot/agent/context.py`)
`ContextBuilder` assembles the system prompt from:
1. Core identity (workspace path, current time)
2. Bootstrap markdown files from workspace: `AGENTS.md`, `SOUL.md`, `USER.md`, `TOOLS.md`, `IDENTITY.md`
3. Memory: long-term (`memory/MEMORY.md`) + recent daily notes (last 7 days)
4. Skills: always-loaded skills get full content in prompt; others show summary only (agent uses `read_file` to load on demand)

### Channels (`kanobot/channels/`)
`BaseChannel` abstract class. Telegram uses `python-telegram-bot`. WhatsApp uses a WebSocket bridge to a Node.js service (in `bridge/` directory, powered by Baileys). `ChannelManager` handles lifecycle.

### Sessions (`kanobot/session/manager.py`)
Conversation history persisted as JSONL files in `~/.kanobot/sessions/`. Keyed by `channel:chat_id`. Returns last 50 messages for LLM context.

### Subagents (`kanobot/agent/subagent.py`)
The `spawn` tool creates background `asyncio` tasks that run a separate agent loop. Results are routed back as system messages through the bus to the original channel.

### Scheduled Tasks
- **Cron** (`kanobot/cron/`): Supports `at` (one-time), `every` (interval), `cron` (expression) schedules. Jobs stored in `~/.kanobot/data/cron/jobs.json`.
- **Heartbeat** (`kanobot/heartbeat/`): 30-minute periodic wake-up that reads `HEARTBEAT.md` and executes tasks via the agent.

## Key Conventions

- **Python 3.11+** required. Type hints used throughout.
- **Async/await** pervasively for I/O. `asyncio.Queue` for message passing, `asyncio.create_task()` for background work.
- **Config**: JSON at `~/.kanobot/config.json` with camelCase keys (converted to snake_case internally by `config/loader.py`). Pydantic models in `config/schema.py`. Environment variables prefixed with `NANOBOT_` (legacy prefix, not yet renamed).
- **Workspace**: Default `~/.kanobot/workspace/`. Contains bootstrap `.md` files, `memory/` directory, and `skills/` directory.
- **Ruff config**: line-length 100, target py311, select E/F/I/N/W, ignore E501.
- **pytest config**: `asyncio_mode = "auto"`, testpaths = `["tests"]`.
- **Tools return error strings** instead of raising exceptions, so the agent LLM can see and react to errors.
- **Skills** are markdown files (`SKILL.md`) with YAML frontmatter for metadata (name, description, requirements).
- **Bridge** (`bridge/`): Separate Node.js/TypeScript project for WhatsApp. Has its own `package.json` and `tsconfig.json`. Gets force-included into the wheel at `kanobot/bridge`.

## Development Guidelines

코드 변경 시 아래 원칙을 따른다. 사소한 작업에는 판단에 따라 유연하게 적용.

### Think Before Coding
- 가정을 명시적으로 밝힌다. 불확실하면 먼저 질문한다.
- 해석이 여러 가지일 때, 조용히 하나를 고르지 말고 선택지를 제시한다.
- 더 단순한 접근이 있으면 말한다. 필요하면 반론을 제기한다.

### Simplicity First
- 요청된 것 이상의 기능, 추상화, 유연성을 추가하지 않는다.
- 일어날 수 없는 시나리오에 대한 에러 핸들링을 넣지 않는다.
- 200줄을 50줄로 줄일 수 있다면 다시 작성한다.

### Surgical Changes
- 인접 코드의 개선, 주석 수정, 포맷 변경을 하지 않는다.
- 기존 스타일이 다르더라도 그 스타일에 맞춘다.
- 내 변경으로 인해 생긴 미사용 import/변수/함수만 제거한다. 기존 dead code는 언급만 하고 삭제하지 않는다.
- 모든 변경 라인은 사용자 요청에 직접 연결되어야 한다.

### Goal-Driven Execution
- 작업을 검증 가능한 목표로 변환한다:
  - "검증 추가" → 잘못된 입력 테스트 작성 후 통과시키기
  - "버그 수정" → 재현 테스트 작성 후 통과시키기
  - "리팩터링" → 전후 테스트 통과 확인
- 다단계 작업은 간략한 계획을 먼저 세운다:
  ```
  1. [단계] → 확인: [검증 방법]
  2. [단계] → 확인: [검증 방법]
  ```
