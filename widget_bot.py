import os
import sys
import struct
import logging
import asyncio
from typing import Optional, Tuple

from telethon import TelegramClient, events
from telethon.tl.alltlobjects import tlobjects
from telethon.tl.tlobject import TLObject
from telethon.tl.functions.messages import SendMediaRequest

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger('WidgetBot')

# Schema definitions from TGScheme (main_api.tl):
# inputMediaWidget#297da8f8 width:int height:int html:string = InputMedia;
# messageMediaWidget#b7ed7b0d width:int height:int payload:bytes = MessageMedia;

class InputMediaWidget(TLObject):
    CONSTRUCTOR_ID = 0x297da8f8
    SUBCLASS_OF_ID = 0xf33f885  # InputMedia

    def __init__(self, width: int, height: int, html: str):
        self.width = int(width)
        self.height = int(height)
        self.html = str(html)

    def _bytes(self):
        return b''.join((
            struct.pack('<I', self.CONSTRUCTOR_ID),
            struct.pack('<i', self.width),
            struct.pack('<i', self.height),
            self.serialize_bytes(self.html),
        ))

    @classmethod
    def from_reader(cls, reader):
        width = reader.read_int()
        height = reader.read_int()
        html = reader.tgread_string()
        return cls(width, height, html)


class MessageMediaWidget(TLObject):
    CONSTRUCTOR_ID = 0xb7ed7b0d
    SUBCLASS_OF_ID = 0xa8fd52f5  # MessageMedia

    def __init__(self, width: int, height: int, payload: bytes):
        self.width = int(width)
        self.height = int(height)
        self.payload = payload

    def _bytes(self):
        return b''.join((
            struct.pack('<I', self.CONSTRUCTOR_ID),
            struct.pack('<i', self.width),
            struct.pack('<i', self.height),
            self.serialize_bytes(self.payload),
        ))

    @classmethod
    def from_reader(cls, reader):
        width = reader.read_int()
        height = reader.read_int()
        payload = reader.tgread_bytes()
        return cls(width, height, payload)


# Register custom TL objects in Telethon
tlobjects[InputMediaWidget.CONSTRUCTOR_ID] = InputMediaWidget
tlobjects[MessageMediaWidget.CONSTRUCTOR_ID] = MessageMediaWidget


def parse_dimensions_and_html(html_text: str, default_width: int = 360, default_height: int = 500) -> Tuple[int, int, str]:
    """
    Parses optional width and height specified in comments like:
    <!-- dimensions: width=400 height=600 -->
    or returns defaults.
    """
    width = default_width
    height = default_height
    lines = html_text.splitlines()
    for line in lines[:10]:
        if "dimensions:" in line.lower() or "widget:" in line.lower():
            parts = line.replace(":", " ").replace("=", " ").split()
            for i in range(len(parts) - 1):
                if parts[i].lower() == "width" and parts[i+1].isdigit():
                    width = int(parts[i+1])
                elif parts[i].lower() == "height" and parts[i+1].isdigit():
                    height = int(parts[i+1])
    return width, height, html_text


async def create_widget_bot(bot_token: str, api_id: int = 6, api_hash: str = 'eb06630f012e128d16156365b2b00d90') -> TelegramClient:
    client = TelegramClient('widget_bot_session', api_id, api_hash)

    @client.on(events.NewMessage(pattern='/start'))
    async def start_handler(event):
        await event.reply(
            "👋 Welcome to the HTML Widget Bot!\n\n"
            "Send me an `.html` file (e.g., Dinosaur Game) or raw HTML text, "
            "and I will transform it into an interactive Chat Widget Bubble!\n\n"
            "You can specify dimensions in the first lines of HTML using comment:\n"
            "`<!-- dimensions: width=360 height=500 -->`"
        )

    @client.on(events.NewMessage)
    async def message_handler(event):
        if event.text and event.text.startswith('/start'):
            return

        html_content = None
        filename = "widget.html"

        # Check if user sent an HTML file
        if event.message.file and (event.message.file.name or "").endswith(".html"):
            filename = event.message.file.name
            file_bytes = await event.message.download_media(bytes)
            html_content = file_bytes.decode('utf-8', errors='ignore')
        elif event.text and ("<html" in event.text.lower() or "<div" in event.text.lower() or "<script" in event.text.lower()):
            html_content = event.text

        if not html_content:
            return

        await event.reply(f"🔄 Processing HTML file `{filename}` into widget bubble...")

        width, height, html_text = parse_dimensions_and_html(html_content)

        input_widget = InputMediaWidget(width=width, height=height, html=html_text)

        try:
            # Send widget media via MTProto SendMediaRequest
            peer = await client.get_input_entity(event.chat_id)
            req = SendMediaRequest(
                peer=peer,
                media=input_widget,
                message="",
                random_id=int.from_bytes(os.urandom(8), 'big', signed=True)
            )
            result = await client(req)
            logger.info(f"Widget successfully sent to chat {event.chat_id}: {result}")
            await event.reply("✅ Widget bubble sent successfully!")
        except Exception as e:
            logger.error(f"Error sending InputMediaWidget: {e}", exc_info=True)
            await event.reply(f"❌ Failed to render widget media: `{type(e).__name__}: {e}`")

    return client


if __name__ == '__main__':
    bot_token = os.environ.get('BOT_TOKEN')
    if not bot_token:
        print("Error: BOT_TOKEN environment variable is required.")
        sys.exit(1)

    api_id = int(os.environ.get('TELEGRAM_API_ID', 6))
    api_hash = os.environ.get('TELEGRAM_API_HASH', 'eb06630f012e128d16156365b2b00d90')

    print("Starting Widget Bot...")
    client = TelegramClient('widget_bot_session', api_id, api_hash)

    async def run():
        bot = await create_widget_bot(bot_token, api_id=api_id, api_hash=api_hash)
        await bot.start(bot_token=bot_token)
        me = await bot.get_me()
        print(f"Bot running as @{me.username} (ID: {me.id})")
        await bot.run_until_disconnected()

    try:
        asyncio.run(run())
    except KeyboardInterrupt:
        print("Bot stopped.")
