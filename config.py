import os

# Telegram Bot Token (Read from environment variable)
BOT_TOKEN = os.environ.get('BOT_TOKEN', '')

# Telegram API ID and API Hash (defaulting to standard Telegram client credentials)
API_ID = int(os.environ.get('TELEGRAM_API_ID', 6))
API_HASH = os.environ.get('TELEGRAM_API_HASH', 'eb06630f012e128d16156365b2b00d90')
