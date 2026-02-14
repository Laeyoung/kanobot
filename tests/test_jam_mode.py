"""Tests for JustAnswerMe (JAM) mode."""

from pathlib import Path
from unittest.mock import AsyncMock, MagicMock, call, patch

import pytest

from kanobot.agent.context import ContextBuilder
from kanobot.bus.events import InboundMessage
from kanobot.providers.base import LLMResponse

# ---------------------------------------------------------------------------
# Helpers
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


@pytest.fixture
def jam_agent():
    """Create an AgentLoop with mocked provider and session for JAM tests."""
    from kanobot.agent.loop import AgentLoop
    from kanobot.bus.queue import MessageBus

    bus = MessageBus()
    provider = AsyncMock()
    provider.get_default_model.return_value = "test-model"

    with patch("kanobot.agent.loop.SessionManager") as mock_sm:
        mock_session = MagicMock()
        mock_session.get_history.return_value = []
        mock_sm.return_value.get_or_create.return_value = mock_session

        agent = AgentLoop(
            bus=bus, provider=provider, workspace=Path("/tmp/test_ws"),
        )
        # Expose internals for assertions
        agent._mock_session = mock_session
        yield agent


# ===========================================================================
# 1. Prompt building
# ===========================================================================


class TestJamPrompts:
    def test_reason_prompt_structure(self):
        cb = ContextBuilder(Path("/tmp/test_ws"))
        msgs = cb.build_jam_reason_messages("치킨 먹을까? 피자 먹을까?")

        assert len(msgs) == 2
        assert msgs[0]["role"] == "system"
        assert "핵심 고려사항" in msgs[0]["content"]
        assert msgs[1]["role"] == "user"
        assert "치킨" in msgs[1]["content"]

    def test_answer_prompt_structure(self):
        cb = ContextBuilder(Path("/tmp/test_ws"))
        msgs = cb.build_jam_answer_messages("이직할까?", "분석 내용...")

        assert len(msgs) == 2
        assert msgs[0]["role"] == "system"
        assert "10자 이내" in msgs[0]["content"]
        assert "양시론" in msgs[0]["content"]
        assert msgs[1]["role"] == "user"
        assert "질문: 이직할까?" in msgs[1]["content"]
        assert "분석: 분석 내용..." in msgs[1]["content"]

    def test_reason_prompt_has_no_tools_instruction(self):
        """Reasoning prompt should not mention tools or function calling."""
        cb = ContextBuilder(Path("/tmp/test_ws"))
        msgs = cb.build_jam_reason_messages("아무 질문")
        system = msgs[0]["content"]
        assert "tool" not in system.lower()
        assert "function" not in system.lower()

    def test_answer_prompt_enforces_constraints(self):
        """Answer prompt should enforce short answer constraints."""
        cb = ContextBuilder(Path("/tmp/test_ws"))
        msgs = cb.build_jam_answer_messages("q", "r")
        system = msgs[0]["content"]
        assert "반말" in system
        assert "이모지" in system
        assert "한 쪽" in system

    def test_answer_messages_include_reasoning(self):
        """The answer step must receive the reasoning from step 1."""
        cb = ContextBuilder(Path("/tmp/test_ws"))
        reasoning = "치킨은 바삭하고 맥주와 잘 어울린다."
        msgs = cb.build_jam_answer_messages("치킨 vs 피자?", reasoning)
        user_content = msgs[1]["content"]
        assert reasoning in user_content
        assert "치킨 vs 피자?" in user_content


# ===========================================================================
# 2. Metadata detection
# ===========================================================================


class TestJamModeDetection:
    def test_jam_metadata_present(self):
        msg = InboundMessage(
            channel="cli", sender_id="user", chat_id="direct",
            content="치킨 먹을까?", metadata={"mode": "jam"},
        )
        assert msg.metadata.get("mode") == "jam"

    def test_regular_message_has_no_jam(self):
        msg = InboundMessage(
            channel="cli", sender_id="user", chat_id="direct",
            content="Hello",
        )
        assert msg.metadata.get("mode") is None


# ===========================================================================
# 3. Channel prefix detection
# ===========================================================================


class TestPrefixDetection:
    async def test_bang_prefix(self, mock_channel):
        """!jam prefix should set mode and strip prefix."""
        mock_channel.bus.publish_inbound = AsyncMock()
        await mock_channel._handle_message(
            sender_id="u1", chat_id="c1", content="!jam 치킨 vs 피자",
        )
        msg = mock_channel.bus.publish_inbound.call_args[0][0]
        assert msg.content == "치킨 vs 피자"
        assert msg.metadata["mode"] == "jam"

    async def test_slash_prefix(self, mock_channel):
        """/jam prefix should set mode and strip prefix."""
        mock_channel.bus.publish_inbound = AsyncMock()
        await mock_channel._handle_message(
            sender_id="u1", chat_id="c1", content="/jam 이직할까?",
        )
        msg = mock_channel.bus.publish_inbound.call_args[0][0]
        assert msg.content == "이직할까?"
        assert msg.metadata["mode"] == "jam"

    async def test_no_prefix(self, mock_channel):
        """Regular messages should not have JAM mode."""
        mock_channel.bus.publish_inbound = AsyncMock()
        await mock_channel._handle_message(
            sender_id="u1", chat_id="c1", content="그냥 질문",
        )
        msg = mock_channel.bus.publish_inbound.call_args[0][0]
        assert msg.content == "그냥 질문"
        assert msg.metadata.get("mode") is None

    async def test_jamming_no_false_positive(self, mock_channel):
        """'!jamming' should NOT trigger JAM mode (requires '!jam ')."""
        mock_channel.bus.publish_inbound = AsyncMock()
        await mock_channel._handle_message(
            sender_id="u1", chat_id="c1", content="!jamming to music",
        )
        msg = mock_channel.bus.publish_inbound.call_args[0][0]
        assert msg.content == "!jamming to music"
        assert msg.metadata.get("mode") is None

    async def test_slash_jam_no_space_no_trigger(self, mock_channel):
        """'/jamtest' should NOT trigger JAM mode."""
        mock_channel.bus.publish_inbound = AsyncMock()
        await mock_channel._handle_message(
            sender_id="u1", chat_id="c1", content="/jamtest",
        )
        msg = mock_channel.bus.publish_inbound.call_args[0][0]
        assert msg.content == "/jamtest"
        assert msg.metadata.get("mode") is None

    async def test_uppercase_bang_prefix(self, mock_channel):
        """!JAM (uppercase) should also trigger JAM mode."""
        mock_channel.bus.publish_inbound = AsyncMock()
        await mock_channel._handle_message(
            sender_id="u1", chat_id="c1", content="!JAM 치킨 먹을까?",
        )
        msg = mock_channel.bus.publish_inbound.call_args[0][0]
        assert msg.content == "치킨 먹을까?"
        assert msg.metadata["mode"] == "jam"

    async def test_mixed_case_slash_prefix(self, mock_channel):
        """/Jam (mixed case) should also trigger JAM mode."""
        mock_channel.bus.publish_inbound = AsyncMock()
        await mock_channel._handle_message(
            sender_id="u1", chat_id="c1", content="/Jam 이직할까?",
        )
        msg = mock_channel.bus.publish_inbound.call_args[0][0]
        assert msg.content == "이직할까?"
        assert msg.metadata["mode"] == "jam"

    async def test_bang_prefix_only_no_question(self, mock_channel):
        """'!jam ' with no question should NOT activate JAM mode."""
        mock_channel.bus.publish_inbound = AsyncMock()
        await mock_channel._handle_message(
            sender_id="u1", chat_id="c1", content="!jam ",
        )
        msg = mock_channel.bus.publish_inbound.call_args[0][0]
        assert msg.content == "!jam "
        assert msg.metadata.get("mode") is None

    async def test_prefix_preserves_existing_metadata(self, mock_channel):
        """!jam prefix should merge mode into existing metadata, not replace."""
        mock_channel.bus.publish_inbound = AsyncMock()
        await mock_channel._handle_message(
            sender_id="u1", chat_id="c1", content="!jam 질문",
            metadata={"user_id": 42, "is_group": False},
        )
        msg = mock_channel.bus.publish_inbound.call_args[0][0]
        assert msg.metadata["mode"] == "jam"
        assert msg.metadata["user_id"] == 42
        assert msg.metadata["is_group"] is False


# ===========================================================================
# 4. Two-step LLM processing
# ===========================================================================


class TestProcessJam:
    async def test_two_step_calls(self, jam_agent):
        """_process_jam should call provider.chat exactly twice with no tools."""
        jam_agent.provider.chat = AsyncMock(side_effect=[
            LLMResponse(content="치킨이 더 맛있는 이유는..."),
            LLMResponse(content="치킨 먹어 🍗"),
        ])

        msg = InboundMessage(
            channel="cli", sender_id="user", chat_id="direct",
            content="치킨 먹을까? 피자 먹을까?", metadata={"mode": "jam"},
        )
        result = await jam_agent._process_jam(msg)

        assert result.content == "치킨 먹어 🍗"
        assert jam_agent.provider.chat.call_count == 2
        for c in jam_agent.provider.chat.call_args_list:
            assert c.kwargs.get("tools") is None

    async def test_reasoning_passed_to_answer_step(self, jam_agent):
        """Step 2 messages must contain the reasoning from step 1."""
        reasoning_text = "치킨은 바삭하고 맥주와 잘 어울리기 때문에..."
        jam_agent.provider.chat = AsyncMock(side_effect=[
            LLMResponse(content=reasoning_text),
            LLMResponse(content="치킨 ㄱㄱ 🍗"),
        ])

        msg = InboundMessage(
            channel="cli", sender_id="user", chat_id="direct",
            content="치킨 vs 피자?", metadata={"mode": "jam"},
        )
        await jam_agent._process_jam(msg)

        # Check the messages sent to the second LLM call
        second_call_messages = jam_agent.provider.chat.call_args_list[1].kwargs["messages"]
        user_msg = second_call_messages[1]["content"]
        assert reasoning_text in user_msg
        assert "치킨 vs 피자?" in user_msg

    async def test_session_saves_question_and_short_answer(self, jam_agent):
        """Session should store the original question and short answer only."""
        jam_agent.provider.chat = AsyncMock(side_effect=[
            LLMResponse(content="장문의 분석 내용..."),
            LLMResponse(content="이직해 🚀"),
        ])

        msg = InboundMessage(
            channel="cli", sender_id="user", chat_id="direct",
            content="이직할까?", metadata={"mode": "jam"},
        )
        await jam_agent._process_jam(msg)

        session = jam_agent._mock_session
        assert session.add_message.call_count == 2
        session.add_message.assert_has_calls([
            call("user", "이직할까?"),
            call("assistant", "이직해 🚀"),
        ])

    async def test_empty_reasoning_still_produces_answer(self, jam_agent):
        """Even if reasoning returns empty, answer step should still run."""
        jam_agent.provider.chat = AsyncMock(side_effect=[
            LLMResponse(content=None),
            LLMResponse(content="치킨 🍗"),
        ])

        msg = InboundMessage(
            channel="cli", sender_id="user", chat_id="direct",
            content="치킨 vs 피자?", metadata={"mode": "jam"},
        )
        result = await jam_agent._process_jam(msg)

        assert result.content == "치킨 🍗"
        assert jam_agent.provider.chat.call_count == 2

    async def test_empty_answer_returns_empty_string(self, jam_agent):
        """If the answer LLM returns None, result should be empty string."""
        jam_agent.provider.chat = AsyncMock(side_effect=[
            LLMResponse(content="분석..."),
            LLMResponse(content=None),
        ])

        msg = InboundMessage(
            channel="cli", sender_id="user", chat_id="direct",
            content="질문?", metadata={"mode": "jam"},
        )
        result = await jam_agent._process_jam(msg)
        assert result.content == ""

    async def test_answer_step_failure_returns_reasoning(self, jam_agent):
        """If the answer LLM call fails, reasoning should be returned as fallback."""
        reasoning_text = "치킨이 맛있는 이유는 바삭하기 때문..."
        jam_agent.provider.chat = AsyncMock(side_effect=[
            LLMResponse(content=reasoning_text),
            RuntimeError("LLM unavailable"),
        ])

        msg = InboundMessage(
            channel="cli", sender_id="user", chat_id="direct",
            content="치킨 vs 피자?", metadata={"mode": "jam"},
        )
        result = await jam_agent._process_jam(msg)

        assert result.content == reasoning_text

    async def test_outbound_has_correct_channel_and_chat_id(self, jam_agent):
        """OutboundMessage should route back to the originating channel."""
        jam_agent.provider.chat = AsyncMock(side_effect=[
            LLMResponse(content="분석"),
            LLMResponse(content="답 🎯"),
        ])

        msg = InboundMessage(
            channel="telegram", sender_id="user", chat_id="12345",
            content="질문?", metadata={"mode": "jam"},
        )
        result = await jam_agent._process_jam(msg)

        assert result.channel == "telegram"
        assert result.chat_id == "12345"


# ===========================================================================
# 5. Routing: _process_message dispatches to _process_jam
# ===========================================================================


class TestJamRouting:
    async def test_process_message_routes_jam(self, jam_agent):
        """_process_message should delegate to _process_jam when mode is jam."""
        jam_agent.provider.chat = AsyncMock(side_effect=[
            LLMResponse(content="분석"),
            LLMResponse(content="답 🎯"),
        ])

        msg = InboundMessage(
            channel="cli", sender_id="user", chat_id="direct",
            content="질문?", metadata={"mode": "jam"},
        )
        result = await jam_agent._process_message(msg)

        assert result.content == "답 🎯"
        # JAM: exactly 2 calls, no tools
        assert jam_agent.provider.chat.call_count == 2
        for c in jam_agent.provider.chat.call_args_list:
            assert c.kwargs.get("tools") is None

    async def test_process_direct_with_jam_metadata(self, jam_agent):
        """process_direct(metadata={"mode":"jam"}) should use JAM flow."""
        jam_agent.provider.chat = AsyncMock(side_effect=[
            LLMResponse(content="분석"),
            LLMResponse(content="해 🔥"),
        ])

        result = await jam_agent.process_direct(
            "할까 말까?", metadata={"mode": "jam"},
        )

        assert result == "해 🔥"
        assert jam_agent.provider.chat.call_count == 2


# ===========================================================================
# 6. Regression: regular mode unaffected
# ===========================================================================


class TestRegression:
    async def test_regular_mode_uses_tools(self, jam_agent):
        """Normal messages should go through the standard agent loop with tools."""
        jam_agent.provider.chat = AsyncMock(
            return_value=LLMResponse(content="Hello! How can I help?"),
        )
        result = await jam_agent.process_direct("Hello")

        assert result == "Hello! How can I help?"
        assert jam_agent.provider.chat.call_count == 1
        first_call = jam_agent.provider.chat.call_args_list[0]
        assert first_call.kwargs.get("tools") is not None

    async def test_process_direct_default_metadata_is_none(self, jam_agent):
        """process_direct without metadata should use normal flow."""
        jam_agent.provider.chat = AsyncMock(
            return_value=LLMResponse(content="Normal response"),
        )
        result = await jam_agent.process_direct("Hi")

        assert result == "Normal response"
        # Normal path: 1 call with tools
        assert jam_agent.provider.chat.call_count == 1
        assert jam_agent.provider.chat.call_args_list[0].kwargs.get("tools") is not None


# ===========================================================================
# 7. Telegram /jam command handler
# ===========================================================================


class TestTelegramJam:
    @pytest.fixture
    def tg_channel(self):
        """Create a TelegramChannel with mocked internals."""
        from kanobot.bus.queue import MessageBus
        from kanobot.channels.telegram import TelegramChannel
        from kanobot.config.schema import TelegramConfig

        config = TelegramConfig(token="fake-token", enabled=True)
        bus = MessageBus()
        ch = TelegramChannel(config, bus)
        ch._handle_message = AsyncMock()
        return ch

    def _make_update(self, text, user_id=111, username="testuser", chat_id=999):
        """Build a mock Telegram Update with message and user."""
        update = MagicMock()
        update.message.text = text
        update.message.chat_id = chat_id
        update.effective_user.id = user_id
        update.effective_user.username = username
        return update

    async def test_on_jam_forwards_with_metadata(self, tg_channel):
        update = self._make_update("/jam 피자 먹을까?")
        await tg_channel._on_jam(update, None)

        tg_channel._handle_message.assert_called_once()
        kwargs = tg_channel._handle_message.call_args.kwargs
        assert kwargs["content"] == "피자 먹을까?"
        assert kwargs["metadata"] == {"mode": "jam"}

    async def test_on_jam_strips_command_prefix(self, tg_channel):
        update = self._make_update("/jam   여러 공백 포함 질문")
        await tg_channel._on_jam(update, None)

        kwargs = tg_channel._handle_message.call_args.kwargs
        assert kwargs["content"] == "여러 공백 포함 질문"

    async def test_on_jam_empty_text_replies_usage(self, tg_channel):
        """If /jam has no question text, should reply with usage."""
        update = self._make_update("/jam")
        update.message.reply_text = AsyncMock()
        await tg_channel._on_jam(update, None)

        tg_channel._handle_message.assert_not_called()
        update.message.reply_text.assert_called_once()
        usage_text = update.message.reply_text.call_args[0][0]
        assert "사용법" in usage_text

    async def test_on_jam_no_message_noop(self, tg_channel):
        """If update has no message, handler should do nothing."""
        update = MagicMock()
        update.message = None
        update.effective_user = None
        await tg_channel._on_jam(update, None)
        tg_channel._handle_message.assert_not_called()

    async def test_on_jam_sender_id_format(self, tg_channel):
        """Sender ID should include user_id|username."""
        update = self._make_update("/jam 질문", user_id=42, username="foo")
        await tg_channel._on_jam(update, None)

        kwargs = tg_channel._handle_message.call_args.kwargs
        assert kwargs["sender_id"] == "42|foo"
