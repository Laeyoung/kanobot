"""Tests for Discord DM channel implementation."""

from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from kanobot.config.schema import DiscordConfig


# ---------------------------------------------------------------------------
# Config defaults
# ---------------------------------------------------------------------------

def test_discord_config_defaults():
    cfg = DiscordConfig()
    assert cfg.enabled is False
    assert cfg.token == ""
    assert cfg.allow_from == []


def test_discord_config_custom():
    cfg = DiscordConfig(enabled=True, token="abc123", allow_from=["111", "222"])
    assert cfg.enabled is True
    assert cfg.token == "abc123"
    assert cfg.allow_from == ["111", "222"]


# ---------------------------------------------------------------------------
# _split_message
# ---------------------------------------------------------------------------

from kanobot.channels.discord import _split_message


def test_split_message_short():
    assert _split_message("hello") == ["hello"]


def test_split_message_at_newline():
    text = "a" * 1990 + "\n" + "b" * 50
    chunks = _split_message(text, limit=2000)
    assert len(chunks) == 2
    assert chunks[0] == "a" * 1990
    assert chunks[1] == "b" * 50


def test_split_message_at_space():
    # No newlines, but has a space before the limit
    text = "word " * 500  # 2500 chars
    chunks = _split_message(text, limit=2000)
    assert all(len(c) <= 2000 for c in chunks)
    assert len(chunks) >= 2


def test_split_message_hard_cut():
    # No newlines or spaces — must hard-cut
    text = "x" * 5000
    chunks = _split_message(text, limit=2000)
    assert chunks[0] == "x" * 2000
    assert chunks[1] == "x" * 2000
    assert chunks[2] == "x" * 1000


# ---------------------------------------------------------------------------
# _markdown_for_discord
# ---------------------------------------------------------------------------

from kanobot.channels.discord import _markdown_for_discord


def test_markdown_links_converted():
    text = "Check [docs](https://example.com) now"
    result = _markdown_for_discord(text)
    assert result == "Check docs (<https://example.com>) now"


def test_markdown_native_passes_through():
    text = "**bold** *italic* ~~strike~~ `code`"
    assert _markdown_for_discord(text) == text


# ---------------------------------------------------------------------------
# Channel behaviour (mocked discord.py)
# ---------------------------------------------------------------------------


def _make_channel():
    """Create a DiscordChannel with a mocked client."""
    from kanobot.channels.discord import DiscordChannel

    bus = MagicMock()
    bus.publish_inbound = AsyncMock()
    cfg = DiscordConfig(enabled=True, token="fake-token")
    channel = DiscordChannel(cfg, bus)

    # Mock discord client & its user
    client = MagicMock()
    client.user = MagicMock()
    client.user.id = 999
    client.user.name = "TestBot"
    client.is_closed.return_value = False
    channel._client = client

    return channel, bus


def _make_dm_message(author_id=123, author_name="alice", content="hi", attachments=None):
    """Create a mock Discord DM message."""
    import discord as _discord

    msg = MagicMock()
    msg.author = MagicMock()
    msg.author.id = author_id
    msg.author.name = author_name
    msg.author.display_name = author_name
    msg.content = content
    msg.id = 42
    msg.attachments = attachments or []

    # DM channel
    dm_channel = MagicMock(spec=_discord.DMChannel)
    dm_channel.id = 7777
    msg.channel = dm_channel

    return msg


@pytest.mark.asyncio
async def test_ignores_own_message():
    channel, bus = _make_channel()
    msg = _make_dm_message()
    msg.author = channel._client.user  # Bot's own message

    await channel._on_message(msg)
    bus.publish_inbound.assert_not_awaited()


@pytest.mark.asyncio
async def test_ignores_guild_message():
    channel, bus = _make_channel()
    msg = _make_dm_message()
    # Make channel a guild text channel (not DMChannel)
    msg.channel = MagicMock()  # generic mock, not DMChannel spec
    msg.channel.__class__ = type("TextChannel", (), {})

    await channel._on_message(msg)
    bus.publish_inbound.assert_not_awaited()


@pytest.mark.asyncio
async def test_handles_dm():
    channel, bus = _make_channel()
    msg = _make_dm_message(author_id=123, author_name="alice", content="hello bot")

    await channel._on_message(msg)
    bus.publish_inbound.assert_awaited_once()

    inbound = bus.publish_inbound.call_args[0][0]
    assert inbound.channel == "discord"
    assert inbound.sender_id == "123|alice"
    assert inbound.chat_id == "7777"
    assert inbound.content == "hello bot"


@pytest.mark.asyncio
async def test_handles_attachments():
    channel, bus = _make_channel()
    att = MagicMock()
    att.url = "https://cdn.discord.com/file.png"
    att.filename = "file.png"
    msg = _make_dm_message(content="see this", attachments=[att])

    await channel._on_message(msg)
    bus.publish_inbound.assert_awaited_once()

    inbound = bus.publish_inbound.call_args[0][0]
    assert "https://cdn.discord.com/file.png" in inbound.media
    assert "[attachment: file.png]" in inbound.content


@pytest.mark.asyncio
async def test_send_splits_long_message():
    channel, _ = _make_channel()

    dm_channel_mock = AsyncMock()
    channel._client.get_channel = MagicMock(return_value=dm_channel_mock)

    from kanobot.bus.events import OutboundMessage

    long_text = "x" * 3000
    msg = OutboundMessage(channel="discord", chat_id="7777", content=long_text)
    await channel.send(msg)

    # Should have been split into 2 chunks
    assert dm_channel_mock.send.await_count == 2
