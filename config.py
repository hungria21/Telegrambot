"""
Configuration module for Telegram Widget Bot/Userbot credentials and settings.
"""

import os

API_ID = int(os.environ.get("API_ID", "0"))
API_HASH = os.environ.get("API_HASH", "")
BOT_TOKEN = os.environ.get("BOT_TOKEN", "")

# Userbot configuration
USE_USERBOT = os.environ.get("USE_USERBOT", "false").lower() in ("true", "1", "yes")
SESSION_STRING = os.environ.get("SESSION_STRING", "")
PHONE_NUMBER = os.environ.get("PHONE_NUMBER", "")

# Default widget dimensions
WIDGET_WIDTH = int(os.environ.get("WIDGET_WIDTH", "300"))
WIDGET_HEIGHT = int(os.environ.get("WIDGET_HEIGHT", "200"))
