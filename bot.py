"""
Telegram Bot for rendering Layer 233 HTML Widgets.

This bot accepts HTML files sent by users and renders them using
Telegram Layer 233 InputMediaWidget.
"""

import logging
from telethon import TelegramClient, events
from telethon.errors import RPCError

import config
from widget_tl import InputMediaWidget

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def process_html_content(raw_bytes: bytes) -> str:
    """Decode raw bytes into HTML string."""
    try:
        return raw_bytes.decode('utf-8')
    except UnicodeDecodeError:
        return raw_bytes.decode('latin-1')


async def handle_start(event):
    """Handle /start command."""
    welcome_text = (
        "Olá! Envie-me um arquivo HTML (.html) e eu tentarei renderizá-lo "
        "como um widget da Layer 233 do Telegram."
    )
    await event.respond(welcome_text)


async def handle_document(event):
    """Handle document uploads and render HTML widgets."""
    message = event.message
    if not message.document:
        return

    # Check file extension / mime type
    filename = message.file.name or ""
    mime_type = message.file.mime_type or ""

    is_html = filename.lower().endswith('.html') or filename.lower().endswith('.htm') or mime_type == 'text/html'

    if not is_html:
        await event.respond("Por favor, envie um arquivo com extensão .html para renderizar o widget.")
        return

    status_msg = await event.respond("Baixando e processando arquivo HTML...")

    try:
        file_bytes = await message.download_media(file=bytes)
        if not file_bytes:
            await status_msg.edit("Falha ao baixar o arquivo.")
            return

        html_content = process_html_content(file_bytes)
        if not html_content.strip():
            await status_msg.edit("O arquivo HTML enviado está vazio.")
            return

        widget_media = InputMediaWidget(
            width=config.WIDGET_WIDTH,
            height=config.WIDGET_HEIGHT,
            html=html_content
        )

        await message.client.send_file(
            event.chat_id,
            file=widget_media,
            reply_to=message.id
        )
        await status_msg.delete()

    except RPCError as e:
        logger.exception("RPCError ao renderizar widget HTML")
        if "INPUT_MEDIA_WIDGET_NOT_ALLOWED" in str(e):
            await status_msg.edit(
                "O servidor do Telegram retornou `INPUT_MEDIA_WIDGET_NOT_ALLOWED`.\n"
                "A renderização de widgets da Layer 233 (`inputMediaWidget`) não é permitida para esta conta ou servidor no momento."
            )
        else:
            await status_msg.edit(f"Erro de RPC do Telegram ao tentar renderizar o widget: {e.message or e}")
    except Exception as e:
        logger.exception("Erro inesperado ao renderizar widget HTML")
        await status_msg.edit(f"Erro ao tentar renderizar o widget HTML: {e}")


def create_bot_client(api_id: int = config.API_ID, api_hash: str = config.API_HASH, bot_token: str = config.BOT_TOKEN) -> TelegramClient:
    """Create and configure TelegramClient for the bot."""
    client = TelegramClient('widget_bot_session', api_id, api_hash)
    client.add_event_handler(handle_start, events.NewMessage(pattern=r'^/start'))
    client.add_event_handler(handle_document, events.NewMessage(func=lambda e: bool(e.document)))
    return client


def main():
    if not (config.API_ID and config.API_HASH and config.BOT_TOKEN):
        print("Erro: API_ID, API_HASH e BOT_TOKEN devem ser fornecidos em config.py ou via variáveis de ambiente.")
        return

    client = create_bot_client()
    client.start(bot_token=config.BOT_TOKEN)
    logger.info("Bot de renderização de Widget HTML rodando...")
    client.run_until_disconnected()


if __name__ == '__main__':
    main()
