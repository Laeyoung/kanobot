"""Slack DM channel implementation using slack-bolt Socket Mode."""

import re

from loguru import logger

from kanobot.bus.events import OutboundMessage
from kanobot.bus.queue import MessageBus
from kanobot.channels.base import BaseChannel
from kanobot.config.schema import SlackConfig

SLACK_MAX_LENGTH = 4000


def _split_message(text: str, limit: int = SLACK_MAX_LENGTH) -> list[str]:
    """
    Split a message into chunks that fit within Slack's character limit.

    Split priority: newline > space > hard cut.
    """
    if len(text) <= limit:
        return [text]

    chunks: list[str] = []
    while text:
        if len(text) <= limit:
            chunks.append(text)
            break

        # Try to split at a newline
        split_pos = text.rfind("\n", 0, limit)
        if split_pos == -1:
            # Try to split at a space
            split_pos = text.rfind(" ", 0, limit)
        if split_pos == -1:
            # Hard cut
            split_pos = limit

        chunks.append(text[:split_pos])
        text = text[split_pos:].lstrip("\n")

    return chunks


def _markdown_for_slack(text: str) -> str:
    """
    Convert standard markdown to Slack mrkdwn format.

    Conversions:
    - **bold** → *bold*
    - ~~strikethrough~~ → ~strikethrough~
    - Code blocks and inline code are left untouched.
    - Links [text](url) are left as-is (Slack renders them).
    """
    # Protect code blocks from conversion
    code_blocks: list[str] = []

    def _save_code_block(match: re.Match) -> str:
        code_blocks.append(match.group(0))
        return f"\x00CODEBLOCK{len(code_blocks) - 1}\x00"

    # Save fenced code blocks and inline code
    text = re.sub(r"```[\s\S]*?```", _save_code_block, text)
    text = re.sub(r"`[^`]+`", _save_code_block, text)

    # **bold** → *bold*
    text = re.sub(r"\*\*(.+?)\*\*", r"*\1*", text)

    # ~~strike~~ → ~strike~
    text = re.sub(r"~~(.+?)~~", r"~\1~", text)

    # Restore code blocks
    for i, block in enumerate(code_blocks):
        text = text.replace(f"\x00CODEBLOCK{i}\x00", block)

    return text


class SlackChannel(BaseChannel):
    """
    Slack DM-only channel using Socket Mode.

    Connects via WebSocket (no public URL needed) and listens for
    direct messages only — channel/group messages are ignored.
    """

    name = "slack"

    def __init__(self, config: SlackConfig, bus: MessageBus):
        super().__init__(config, bus)
        self.config: SlackConfig = config
        self._app = None  # AsyncApp
        self._handler = None  # AsyncSocketModeHandler
        self._user_cache: dict[str, str] = {}  # user_id → username

    async def start(self) -> None:
        """Start the Slack bot via Socket Mode."""
        if not self.config.bot_token:
            logger.error("Slack bot token not configured")
            return
        if not self.config.app_token:
            logger.error("Slack app token not configured (required for Socket Mode)")
            return

        self._running = True

        from slack_bolt.adapter.socket_mode.async_handler import AsyncSocketModeHandler
        from slack_bolt.async_app import AsyncApp

        self._app = AsyncApp(token=self.config.bot_token)

        @self._app.event("message")
        async def handle_message(event, say):
            await self._on_message(event)

        self._handler = AsyncSocketModeHandler(self._app, self.config.app_token)

        try:
            logger.info("Starting Slack Socket Mode connection...")
            await self._handler.start_async()
        except Exception as e:
            logger.error(f"Slack connection error: {e}")
            self._running = False

    async def stop(self) -> None:
        """Stop the Slack bot."""
        self._running = False
        if self._handler:
            await self._handler.close_async()
            self._handler = None
        self._app = None

    async def send(self, msg: OutboundMessage) -> None:
        """Send a message to a Slack DM channel."""
        if not self._app:
            logger.warning("Slack app not running")
            return

        try:
            content = _markdown_for_slack(msg.content)
            chunks = _split_message(content)

            for chunk in chunks:
                await self._app.client.chat_postMessage(
                    channel=msg.chat_id,
                    text=chunk,
                )
        except Exception as e:
            logger.error(f"Error sending Slack message: {e}")

    async def _on_message(self, event: dict) -> None:
        """Handle an incoming Slack message event."""
        # Ignore bot messages
        if "bot_id" in event or event.get("subtype"):
            return

        # DM only — ignore channel/group messages
        if event.get("channel_type") != "im":
            return

        user_id = event.get("user", "")
        channel_id = event.get("channel", "")
        text = event.get("text", "")

        # Resolve username (with cache)
        username = await self._resolve_username(user_id)
        sender_id = f"{user_id}|{username}"

        # Build content
        content_parts: list[str] = []
        media: list[str] = []

        if text:
            content_parts.append(text)

        for file_info in event.get("files", []):
            url = file_info.get("url_private", "")
            name = file_info.get("name", "file")
            if url:
                media.append(url)
                content_parts.append(f"[attachment: {name}]")

        content = "\n".join(content_parts) if content_parts else "[empty message]"

        logger.debug(f"Slack DM from {sender_id}: {content[:50]}...")

        await self._handle_message(
            sender_id=sender_id,
            chat_id=channel_id,
            content=content,
            media=media,
            metadata={
                "user_id": user_id,
                "username": username,
                "channel_id": channel_id,
            },
        )

    async def _resolve_username(self, user_id: str) -> str:
        """Resolve a Slack user ID to a username, with caching."""
        if user_id in self._user_cache:
            return self._user_cache[user_id]

        username = user_id  # fallback
        if self._app:
            try:
                result = await self._app.client.users_info(user=user_id)
                if result and result.get("ok"):
                    user_data = result["user"]
                    username = (
                        user_data.get("name")
                        or user_data.get("real_name")
                        or user_id
                    )
            except Exception as e:
                logger.debug(f"Could not resolve Slack user {user_id}: {e}")

        self._user_cache[user_id] = username
        return username
