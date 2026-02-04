"""Message bus module for decoupled channel-agent communication."""

from kanobot.bus.events import InboundMessage, OutboundMessage
from kanobot.bus.queue import MessageBus

__all__ = ["MessageBus", "InboundMessage", "OutboundMessage"]
