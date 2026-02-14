"""Discord DM channel implementation using discord.py."""

import discord
from loguru import logger

from kanobot.bus.events import OutboundMessage
from kanobot.bus.queue import MessageBus
from kanobot.channels.base import BaseChannel
from kanobot.config.schema import DiscordConfig

DISCORD_MAX_LENGTH = 2000


def _split_message(text: str, limit: int = DISCORD_MAX_LENGTH) -> list[str]:
    """
    Split a message into chunks that fit within Discord's character limit.

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


def _markdown_for_discord(text: str) -> str:
    """
    Minimal markdown adaptation for Discord.

    Discord natively supports: **bold**, *italic*, ~~strikethrough~~,
    `inline code`, ```code blocks```, > blockquotes, and bullet lists.

    Only [text](url) links need conversion since Discord doesn't render them.
    """
    import re

    # Convert markdown links to "text (url)" since Discord doesn't render them
    text = re.sub(r"\[([^\]]+)\]\(([^)]+)\)", r"\1 (<\2>)", text)

    return text


class DiscordChannel(BaseChannel):
    """
    Discord DM-only channel.

    Listens for direct messages and ignores all guild (server) messages.
    """

    name = "discord"

    def __init__(self, config: DiscordConfig, bus: MessageBus):
        super().__init__(config, bus)
        self.config: DiscordConfig = config
        self._client: discord.Client | None = None

    async def start(self) -> None:
        """Start the Discord bot."""
        if not self.config.token:
            logger.error("Discord bot token not configured")
            return

        self._running = True

        intents = discord.Intents.default()
        intents.message_content = True
        intents.dm_messages = True

        self._client = discord.Client(intents=intents)

        @self._client.event
        async def on_ready():
            logger.info(f"Discord bot {self._client.user} connected")

        @self._client.event
        async def on_message(message: discord.Message):
            await self._on_message(message)

        try:
            await self._client.start(self.config.token)
        except discord.LoginFailure:
            logger.error("Discord login failed — check your bot token")
            self._running = False
        except Exception as e:
            logger.error(f"Discord client error: {e}")
            self._running = False

    async def stop(self) -> None:
        """Stop the Discord bot."""
        self._running = False
        if self._client and not self._client.is_closed():
            await self._client.close()
            self._client = None

    async def send(self, msg: OutboundMessage) -> None:
        """Send a message to a Discord DM channel."""
        if not self._client or self._client.is_closed():
            logger.warning("Discord client not running")
            return

        try:
            channel_id = int(msg.chat_id)
        except ValueError:
            logger.error(f"Invalid Discord chat_id: {msg.chat_id}")
            return

        try:
            channel = self._client.get_channel(channel_id)
            if channel is None:
                channel = await self._client.fetch_channel(channel_id)

            content = _markdown_for_discord(msg.content)
            chunks = _split_message(content)

            for chunk in chunks:
                await channel.send(chunk)
        except discord.NotFound:
            logger.error(f"Discord channel {channel_id} not found")
        except discord.Forbidden:
            logger.error(f"Cannot send to Discord channel {channel_id} (forbidden)")
        except Exception as e:
            logger.error(f"Error sending Discord message: {e}")

    async def _on_message(self, message: discord.Message) -> None:
        """Handle an incoming Discord message."""
        # Ignore bot's own messages
        if message.author == self._client.user:
            return

        # DM only — ignore guild messages
        if not isinstance(message.channel, discord.DMChannel):
            return

        user = message.author
        sender_id = f"{user.id}|{user.name}"
        chat_id = str(message.channel.id)

        # Build content
        content_parts: list[str] = []
        media: list[str] = []

        if message.content:
            content_parts.append(message.content)

        for attachment in message.attachments:
            media.append(attachment.url)
            content_parts.append(f"[attachment: {attachment.filename}]")

        content = "\n".join(content_parts) if content_parts else "[empty message]"

        logger.debug(f"Discord DM from {sender_id}: {content[:50]}...")

        await self._handle_message(
            sender_id=sender_id,
            chat_id=chat_id,
            content=content,
            media=media,
            metadata={
                "message_id": message.id,
                "user_id": user.id,
                "username": user.name,
                "display_name": user.display_name,
            },
        )
