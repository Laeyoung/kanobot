"""Configuration module for kanobot."""

from kanobot.config.loader import load_config, get_config_path
from kanobot.config.schema import Config

__all__ = ["Config", "load_config", "get_config_path"]
