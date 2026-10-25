"""
Userbot que transforma um arquivo .html em widget do Telegram.

Usa MTProto (Telethon) com os tipos TL do schema do Telegram (layer 233):
  inputMediaWidget#297da8f8 width:int height:int html:string = InputMedia;
  messageMediaWidget#b7ed7b0d width:int height:int payload:bytes = MessageMedia;
  messages.sendMedia#330e77f ...

Credenciais em config.py: API_ID, API_HASH, PHONE (e FORCE_LAYER opcional).
Envie o .html nas Mensagens Salvas (ou nos chats de config.CHATS).

Uso: pip install telethon && python widget_bot.py
"""
import random
import re
import struct

from telethon import TelegramClient, events
from telethon.tl.tlobject import TLObject
from telethon.tl.functions.messages import SendMediaRequest
from telethon.tl.alltlobjects import tlobjects

import config


# ---------- tipos TL escritos à mão ----------

class InputMediaWidget(TLObject):
    CONSTRUCTOR_ID = 0x297DA8F8
    SUBCLASS_OF_ID = 0xFAF846F4  # InputMedia

    def __init__(self, width: int, height: int, html: str):
        self.width, self.height, self.html = width, height, html

    def _bytes(self) -> bytes:
        return b"".join((
            struct.pack("<I", self.CONSTRUCTOR_ID),
            struct.pack("<ii", self.width, self.height),
            self.serialize_bytes(self.html),
        ))

    @classmethod
    def from_reader(cls, reader):
        width = reader.read_int()
        height = reader.read_int()
        html = reader.tgread_string()
        return cls(width, height, html)


class MessageMediaWidget(TLObject):
    CONSTRUCTOR_ID = 0xB7ED7B0D
    SUBCLASS_OF_ID = 0x60012A32  # MessageMedia

    def __init__(self, width: int = 0, height: int = 0, payload: bytes = b""):
        self.width, self.height, self.payload = width, height, payload

    def _bytes(self) -> bytes:
        return b"".join((
            struct.pack("<I", self.CONSTRUCTOR_ID),
            struct.pack("<ii", self.width, self.height),
            self.serialize_bytes(self.payload),
        ))

    @classmethod
    def from_reader(cls, reader):
        width = reader.read_int()
        height = reader.read_int()
        payload = reader.tgread_bytes()
        return cls(width, height, payload)


# Registra os construtores customizados no registro de tipos do Telethon
tlobjects[InputMediaWidget.CONSTRUCTOR_ID] = InputMediaWidget
tlobjects[MessageMediaWidget.CONSTRUCTOR_ID] = MessageMediaWidget


# Mantém SendWidgetRequest por compatibilidade / conveniência, usando o SendMediaRequest nativo
class SendWidgetRequest(SendMediaRequest):
    """messages.sendMedia#330e77f com mídia do tipo widget."""

    def __init__(self, peer, media, message: str = "", random_id: int = None):
        if random_id is None:
            random_id = random.randint(-2**63, 2**63 - 1)
        super().__init__(
            peer=peer,
            media=media,
            message=message,
            random_id=random_id,
        )


# ---------- userbot ----------

if getattr(config, "FORCE_LAYER", None):
    import telethon.client.telegrambaseclient as _base
    _base.LAYER = int(config.FORCE_LAYER)

client = TelegramClient("widget_user", getattr(config, "API_ID", 0), getattr(config, "API_HASH", ""))

MAX_BYTES = 512 * 1024          # limite de segurança (o do servidor é desconhecido)
DEFAULT_SIZE = (400, 500)       # largura x altura
sizes = {}                      # chat_id -> (w, h)

# Só mensagens SUAS, nos chats de config.CHATS. O filtro é feito dentro do
# handler (mais confiável que chats=[...]); ALLOWED é preenchido após o login.
ALLOWED = set()


def allowed(event):
    ok = event.out and event.chat_id in ALLOWED
    print(f"[log] chat={event.chat_id} out={event.out} permitido={ok} texto={event.raw_text[:40]!r}")
    return ok


@client.on(events.NewMessage(outgoing=True))
async def set_size(event):
    if not allowed(event):
        return
    m = re.match(r"^/size\s+(\d+)\s+(\d+)\s*$", event.raw_text.strip(), re.I)
    if not m:
        return
    w, h = int(m.group(1)), int(m.group(2))
    sizes[event.chat_id] = (w, h)
    await event.reply(f"Tamanho: {w}x{h}")


@client.on(events.NewMessage(outgoing=True, func=lambda e: e.document is not None))
async def on_file(event):
    if not allowed(event):
        return
    doc = event.document
    name = next((a.file_name for a in doc.attributes if hasattr(a, "file_name")), "")
    if not (name.lower().endswith((".html", ".htm")) or doc.mime_type == "text/html"):
        return
    if doc.size > MAX_BYTES:
        return await event.reply(f"Arquivo grande demais (máx. {MAX_BYTES // 1024} KB).")

    html = (await event.download_media(bytes)).decode("utf-8", errors="replace")
    w, h = sizes.get(event.chat_id, DEFAULT_SIZE)
    try:
        await client(SendWidgetRequest(
            peer=await event.get_input_chat(),
            media=InputMediaWidget(w, h, html),
        ))
    except Exception as e:
        await event.reply(f"O servidor recusou o widget:\n{type(e).__name__}: {e}")


if __name__ == "__main__":
    client.start(phone=getattr(config, "PHONE", ""))  # pede código/2FA no primeiro login
    for c in getattr(config, "CHATS", []):
        ALLOWED.add(client.loop.run_until_complete(client.get_peer_id(c)))
    print("Userbot rodando… chats permitidos:", ALLOWED)
    client.run_until_disconnected()
