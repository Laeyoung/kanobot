"""Tests for Slack DM channel implementation."""

from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from kanobot.config.schema import SlackConfig


# ---------------------------------------------------------------------------
# Config defaults
# ---------------------------------------------------------------------------

def test_slack_config_defaults():
    cfg = SlackConfig()
    assert cfg.enabled is False
    assert cfg.bot_token == ""
    assert cfg.app_token == ""
    assert cfg.allow_from == []


def test_slack_config_custom():
    cfg = SlackConfig(
        enabled=True,
        bot_token="xoxb-test",
        app_token="xapp-test",
        allow_from=["U111", "U222"],
    )
    assert cfg.enabled is True
    assert cfg.bot_token == "xoxb-test"
    assert cfg.app_token == "xapp-test"
    assert cfg.allow_from == ["U111", "U222"]


# ---------------------------------------------------------------------------
# _split_message
# ---------------------------------------------------------------------------

from kanobot.channels.slack import _split_message


def test_split_message_short():
    assert _split_message("hello") == ["hello"]


def test_split_message_at_newline():
    text = "a" * 3990 + "\n" + "b" * 50
    chunks = _split_message(text, limit=4000)
    assert len(chunks) == 2
    assert chunks[0] == "a" * 3990
    assert chunks[1] == "b" * 50


def test_split_message_at_space():
    # No newlines, but has spaces before the limit
    text = "word " * 1000  # 5000 chars
    chunks = _split_message(text, limit=4000)
    assert all(len(c) <= 4000 for c in chunks)
    assert len(chunks) >= 2


def test_split_message_hard_cut():
    # No newlines or spaces — must hard-cut
    text = "x" * 10000
    chunks = _split_message(text, limit=4000)
    assert chunks[0] == "x" * 4000
    assert chunks[1] == "x" * 4000
    assert chunks[2] == "x" * 2000


# ---------------------------------------------------------------------------
# _markdown_for_slack
# ---------------------------------------------------------------------------

from kanobot.channels.slack import _markdown_for_slack


def test_markdown_bold_converted():
    assert _markdown_for_slack("**bold**") == "*bold*"


def test_markdown_strikethrough_converted():
    assert _markdown_for_slack("~~strike~~") == "~strike~"


def test_markdown_bold_and_strike():
    text = "**bold** and ~~strike~~"
    assert _markdown_for_slack(text) == "*bold* and ~strike~"


def test_markdown_links_pass_through():
    text = "Check [docs](https://example.com) now"
    assert _markdown_for_slack(text) == "Check [docs](https://example.com) now"


def test_markdown_inline_code_untouched():
    text = "use `**not bold**` here"
    assert _markdown_for_slack(text) == "use `**not bold**` here"


def test_markdown_code_block_untouched():
    text = "before\n```\n**not bold**\n~~not strike~~\n```\nafter **bold**"
    result = _markdown_for_slack(text)
    assert "```\n**not bold**\n~~not strike~~\n```" in result
    assert result.endswith("after *bold*")


# ---------------------------------------------------------------------------
# Channel behaviour (mocked slack-bolt)
# ---------------------------------------------------------------------------


def _make_channel():
    """Create a SlackChannel with mocked internals."""
    from kanobot.channels.slack import SlackChannel

    bus = MagicMock()
    bus.publish_inbound = AsyncMock()
    cfg = SlackConfig(enabled=True, bot_token="xoxb-fake", app_token="xapp-fake")
    channel = SlackChannel(cfg, bus)

    # Mock the Slack app client
    app = MagicMock()
    app.client = MagicMock()
    app.client.chat_postMessage = AsyncMock()
    app.client.users_info = AsyncMock(return_value={
        "ok": True,
        "user": {"name": "alice", "real_name": "Alice Smith"},
    })
    channel._app = app

    return channel, bus


def _make_dm_event(
    user="U123",
    channel="D456",
    text="hello",
    channel_type="im",
    files=None,
    bot_id=None,
    subtype=None,
):
    """Create a mock Slack message event dict."""
    event = {
        "user": user,
        "channel": channel,
        "text": text,
        "channel_type": channel_type,
    }
    if files:
        event["files"] = files
    if bot_id:
        event["bot_id"] = bot_id
    if subtype:
        event["subtype"] = subtype
    return event


@pytest.mark.asyncio
async def test_ignores_bot_message():
    channel, bus = _make_channel()
    event = _make_dm_event(bot_id="B999")

    await channel._on_message(event)
    bus.publish_inbound.assert_not_awaited()


@pytest.mark.asyncio
async def test_ignores_subtype_message():
    channel, bus = _make_channel()
    event = _make_dm_event(subtype="message_changed")

    await channel._on_message(event)
    bus.publish_inbound.assert_not_awaited()


@pytest.mark.asyncio
async def test_ignores_non_dm():
    channel, bus = _make_channel()
    event = _make_dm_event(channel_type="channel")

    await channel._on_message(event)
    bus.publish_inbound.assert_not_awaited()


@pytest.mark.asyncio
async def test_handles_dm():
    channel, bus = _make_channel()
    event = _make_dm_event(user="U123", text="hello bot")

    await channel._on_message(event)
    bus.publish_inbound.assert_awaited_once()

    inbound = bus.publish_inbound.call_args[0][0]
    assert inbound.channel == "slack"
    assert inbound.sender_id == "U123|alice"
    assert inbound.chat_id == "D456"
    assert inbound.content == "hello bot"


@pytest.mark.asyncio
async def test_handles_files():
    channel, bus = _make_channel()
    files = [{"url_private": "https://files.slack.com/file.png", "name": "file.png"}]
    event = _make_dm_event(text="see this", files=files)

    await channel._on_message(event)
    bus.publish_inbound.assert_awaited_once()

    inbound = bus.publish_inbound.call_args[0][0]
    assert "https://files.slack.com/file.png" in inbound.media
    assert "[attachment: file.png]" in inbound.content


@pytest.mark.asyncio
async def test_send_splits_long_message():
    channel, _ = _make_channel()

    from kanobot.bus.events import OutboundMessage

    long_text = "x" * 6000
    msg = OutboundMessage(channel="slack", chat_id="D456", content=long_text)
    await channel.send(msg)

    # Should have been split into 2 chunks (4000 + 2000)
    assert channel._app.client.chat_postMessage.await_count == 2


@pytest.mark.asyncio
async def test_send_converts_markdown():
    channel, _ = _make_channel()

    from kanobot.bus.events import OutboundMessage

    msg = OutboundMessage(channel="slack", chat_id="D456", content="**bold** ~~strike~~")
    await channel.send(msg)

    call_kwargs = channel._app.client.chat_postMessage.call_args
    assert call_kwargs.kwargs["text"] == "*bold* ~strike~"


@pytest.mark.asyncio
async def test_username_caching():
    channel, bus = _make_channel()

    # First call — API should be called
    event1 = _make_dm_event(user="U123", text="msg1")
    await channel._on_message(event1)
    assert channel._app.client.users_info.await_count == 1

    # Second call — should use cache
    event2 = _make_dm_event(user="U123", text="msg2")
    await channel._on_message(event2)
    assert channel._app.client.users_info.await_count == 1  # still 1
