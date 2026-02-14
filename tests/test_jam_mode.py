"""Tests for JustAnswerMe (JAM) mode."""

from pathlib import Path
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from kanobot.agent.context import ContextBuilder
from kanobot.bus.events import InboundMessage
from kanobot.providers.base import LLMResponse

# ---------------------------------------------------------------------------
# Prompt tests
# ---------------------------------------------------------------------------


def test_jam_reason_prompt():
    cb = ContextBuilder(Path("/tmp/test_ws"))
    msgs = cb.build_jam_reason_messages("치킨 먹을까? 피자 먹을까?")

    assert len(msgs) == 2
    assert msgs[0]["role"] == "system"
    assert "핵심 고려사항" in msgs[0]["content"]
    assert msgs[1]["role"] == "user"
    assert "치킨" in msgs[1]["content"]


def test_jam_answer_prompt():
    cb = ContextBuilder(Path("/tmp/test_ws"))
    msgs = cb.build_jam_answer_messages("이직할까?", "분석 내용...")

    assert len(msgs) == 2
    assert msgs[0]["role"] == "system"
    assert "10자 이내" in msgs[0]["content"]
    assert "양시론" in msgs[0]["content"]
    assert msgs[1]["role"] == "user"
    assert "질문: 이직할까?" in msgs[1]["content"]
    assert "분석: 분석 내용..." in msgs[1]["content"]


# ---------------------------------------------------------------------------
# JAM mode detection (metadata)
# ---------------------------------------------------------------------------


def test_jam_mode_detection():
    msg = InboundMessage(
        channel="cli",
        sender_id="user",
        chat_id="direct",
        content="치킨 먹을까?",
        metadata={"mode": "jam"},
    )
    assert msg.metadata.get("mode") == "jam"


def test_regular_message_has_no_jam():
    msg = InboundMessage(
        channel="cli",
        sender_id="user",
        chat_id="direct",
        content="Hello",
    )
    assert msg.metadata.get("mode") is None


# ---------------------------------------------------------------------------
# Prefix detection in BaseChannel._handle_message
# ---------------------------------------------------------------------------


@pytest.fixture
def mock_channel():
    """Create a minimal concrete channel for testing prefix detection."""
    from kanobot.bus.queue import MessageBus
    from kanobot.channels.base import BaseChannel

    class _TestChannel(BaseChannel):
        name = "test"

        async def start(self):
            pass

        async def stop(self):
            pass

        async def send(self, msg):
            pass

    bus = MessageBus()
    config = MagicMock()
    config.allow_from = []
    return _TestChannel(config, bus)


async def test_jam_prefix_bang(mock_channel):
    """!jam prefix should set mode and strip prefix."""
    mock_channel.bus.publish_inbound = AsyncMock()

    await mock_channel._handle_message(
        sender_id="u1", chat_id="c1", content="!jam 치킨 vs 피자"
    )

    mock_channel.bus.publish_inbound.assert_called_once()
    msg = mock_channel.bus.publish_inbound.call_args[0][0]
    assert msg.content == "치킨 vs 피자"
    assert msg.metadata["mode"] == "jam"


async def test_jam_prefix_slash(mock_channel):
    """/jam prefix should set mode and strip prefix."""
    mock_channel.bus.publish_inbound = AsyncMock()

    await mock_channel._handle_message(
        sender_id="u1", chat_id="c1", content="/jam 이직할까?"
    )

    msg = mock_channel.bus.publish_inbound.call_args[0][0]
    assert msg.content == "이직할까?"
    assert msg.metadata["mode"] == "jam"


async def test_no_prefix_no_jam(mock_channel):
    """Regular messages should not have JAM mode."""
    mock_channel.bus.publish_inbound = AsyncMock()

    await mock_channel._handle_message(
        sender_id="u1", chat_id="c1", content="그냥 질문"
    )

    msg = mock_channel.bus.publish_inbound.call_args[0][0]
    assert msg.content == "그냥 질문"
    assert msg.metadata.get("mode") is None


# ---------------------------------------------------------------------------
# 2-step LLM processing
# ---------------------------------------------------------------------------


async def test_process_jam_two_step():
    """_process_jam should call provider.chat exactly twice."""
    from kanobot.agent.loop import AgentLoop
    from kanobot.bus.queue import MessageBus

    bus = MessageBus()
    provider = AsyncMock()
    provider.get_default_model.return_value = "test-model"

    # First call returns reasoning, second returns short answer
    provider.chat = AsyncMock(
        side_effect=[
            LLMResponse(content="치킨이 더 맛있는 이유는..."),
            LLMResponse(content="치킨 먹어 🍗"),
        ]
    )

    with patch("kanobot.agent.loop.SessionManager") as mock_sm:
        mock_session = MagicMock()
        mock_session.get_history.return_value = []
        mock_sm.return_value.get_or_create.return_value = mock_session

        agent = AgentLoop(
            bus=bus,
            provider=provider,
            workspace=Path("/tmp/test_ws"),
        )

        msg = InboundMessage(
            channel="cli",
            sender_id="user",
            chat_id="direct",
            content="치킨 먹을까? 피자 먹을까?",
            metadata={"mode": "jam"},
        )

        result = await agent._process_jam(msg)

    assert result.content == "치킨 먹어 🍗"
    assert provider.chat.call_count == 2

    # First call: reasoning (no tools)
    first_call = provider.chat.call_args_list[0]
    assert first_call.kwargs.get("tools") is None

    # Second call: answer (no tools)
    second_call = provider.chat.call_args_list[1]
    assert second_call.kwargs.get("tools") is None

    # Session should have user + assistant messages saved
    assert mock_session.add_message.call_count == 2


# ---------------------------------------------------------------------------
# Regression: regular mode unaffected
# ---------------------------------------------------------------------------


async def test_regular_mode_unaffected():
    """Normal messages should go through the standard agent loop."""
    from kanobot.agent.loop import AgentLoop
    from kanobot.bus.queue import MessageBus

    bus = MessageBus()
    provider = AsyncMock()
    provider.get_default_model.return_value = "test-model"
    provider.chat = AsyncMock(
        return_value=LLMResponse(content="Hello! How can I help?")
    )

    with patch("kanobot.agent.loop.SessionManager") as mock_sm:
        mock_session = MagicMock()
        mock_session.get_history.return_value = []
        mock_sm.return_value.get_or_create.return_value = mock_session

        agent = AgentLoop(
            bus=bus,
            provider=provider,
            workspace=Path("/tmp/test_ws"),
        )

        result = await agent.process_direct("Hello")

    assert result == "Hello! How can I help?"
    # Standard mode: only 1 LLM call (no tool calls in response)
    assert provider.chat.call_count == 1
    # Standard mode passes tools
    first_call = provider.chat.call_args_list[0]
    assert first_call.kwargs.get("tools") is not None
