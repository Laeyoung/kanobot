# Changelog

## 2026-02-14 — JustAnswerMe (JAM) Mode

Integrated JustAnswerMe into kanobot. JAM mode lets the agent think deeply about a question, then return only a short, decisive one-line answer.

### Added

- **2-step LLM processing** (`kanobot/agent/loop.py`)
  - `_process_jam()`: Calls the LLM twice — first for deep reasoning (300-500 chars analysis), then for a short decisive answer (10 chars or less, with emoji). Only the short answer is returned to the user.
  - `_process_message()` now detects `metadata["mode"] == "jam"` and delegates to the JAM flow.
  - `process_direct()` accepts an optional `metadata` parameter so the CLI can pass mode info.

- **JAM prompts** (`kanobot/agent/context.py`)
  - `JAM_REASON_PROMPT`: System prompt for deep analysis (key considerations, recommendation, counter-arguments).
  - `JAM_ANSWER_PROMPT`: System prompt for short decisive answers (one side only, casual tone, 10 chars, 1 emoji).
  - `build_jam_reason_messages()` / `build_jam_answer_messages()`: Build message lists for each step.

- **CLI `--jam` flag** (`kanobot/cli/commands.py`)
  - `kanobot agent -m "question" --jam` for single message mode.
  - `kanobot agent --jam` for interactive mode (all messages use JAM).

- **Channel prefix detection** (`kanobot/channels/base.py`)
  - Messages starting with `!jam ` or `/jam ` are routed to JAM mode.
  - Prefix is stripped from content before processing.
  - Works across all channels (Telegram, Discord, Slack, WhatsApp).

- **Telegram `/jam` command** (`kanobot/channels/telegram.py`)
  - Dedicated `CommandHandler` for `/jam` since Telegram's `~filters.COMMAND` filter blocks commands from the general message handler.
  - Usage: `/jam Should I quit my job?`

- **Tests** (`tests/test_jam_mode.py`)
  - 9 tests: prompt content, mode detection, prefix detection (`!jam`, `/jam`), 2-step LLM processing (mock provider), and regression test for regular mode.

### Files Changed

| File | Type |
|------|------|
| `kanobot/agent/context.py` | Modified |
| `kanobot/agent/loop.py` | Modified |
| `kanobot/cli/commands.py` | Modified |
| `kanobot/channels/base.py` | Modified |
| `kanobot/channels/telegram.py` | Modified |
| `tests/test_jam_mode.py` | New |
| `README.md` | Modified |
