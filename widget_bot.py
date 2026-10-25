"""
Userbot que transforma um arquivo .html em widget do Telegram.

Usa MTProto (Telethon) com os tipos TL do schema do Telegram (layer 233):
  inputMediaWidget#297da8f8 width:int height:int html:string = InputMedia;
  messageMediaWidget#b7ed7b0d width:int height:int payload:bytes = MessageMedia;
  messageReplyHeader#ddb5ab75 ... = MessageReplyHeader;
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


class MessageReplyHeader233(TLObject):
    """messageReplyHeader#ddb5ab75 do layer 233."""
    CONSTRUCTOR_ID = 0xDDB5AB75
    SUBCLASS_OF_ID = 0xAF8E50E0  # MessageReplyHeader

    def __init__(
        self,
        reply_to_scheduled: bool = False,
        forum_topic: bool = False,
        quote: bool = False,
        reply_to_ephemeral: bool = False,
        reply_to_msg_id: int = None,
        reply_to_peer_id = None,
        reply_from = None,
        reply_media = None,
        reply_to_top_id: int = None,
        quote_text: str = None,
        quote_entities = None,
        quote_offset: int = None,
        todo_item_id: int = None,
        poll_option: bytes = None,
        quote_rich = None,
    ):
        self.reply_to_scheduled = reply_to_scheduled
        self.forum_topic = forum_topic
        self.quote = quote
        self.reply_to_ephemeral = reply_to_ephemeral
        self.reply_to_msg_id = reply_to_msg_id
        self.reply_to_peer_id = reply_to_peer_id
        self.reply_from = reply_from
        self.reply_media = reply_media
        self.reply_to_top_id = reply_to_top_id
        self.quote_text = quote_text
        self.quote_entities = quote_entities
        self.quote_offset = quote_offset
        self.todo_item_id = todo_item_id
        self.poll_option = poll_option
        self.quote_rich = quote_rich

    def _bytes(self) -> bytes:
        flags = 0
        if self.reply_to_scheduled:
            flags |= 1 << 2
        if self.forum_topic:
            flags |= 1 << 3
        if self.quote:
            flags |= 1 << 9
        if self.reply_to_ephemeral:
            flags |= 1 << 13

        if self.reply_to_msg_id is not None:
            flags |= 1 << 4
        if self.reply_to_peer_id is not None:
            flags |= 1 << 0
        if self.reply_from is not None:
            flags |= 1 << 5
        if self.reply_media is not None:
            flags |= 1 << 8
        if self.reply_to_top_id is not None:
            flags |= 1 << 1
        if self.quote_text is not None:
            flags |= 1 << 6
        if self.quote_entities is not None:
            flags |= 1 << 7
        if self.quote_offset is not None:
            flags |= 1 << 10
        if self.todo_item_id is not None:
            flags |= 1 << 11
        if self.poll_option is not None:
            flags |= 1 << 12
        if self.quote_rich is not None:
            flags |= 1 << 14

        return b"".join((
            struct.pack("<I", self.CONSTRUCTOR_ID),
            struct.pack("<i", flags),
            struct.pack("<i", self.reply_to_msg_id) if self.reply_to_msg_id is not None else b"",
            self.reply_to_peer_id._bytes() if self.reply_to_peer_id is not None else b"",
            self.reply_from._bytes() if self.reply_from is not None else b"",
            self.reply_media._bytes() if self.reply_media is not None else b"",
            struct.pack("<i", self.reply_to_top_id) if self.reply_to_top_id is not None else b"",
            self.serialize_bytes(self.quote_text) if self.quote_text is not None else b"",
            b"".join((b"\x15\xc4\xb5\x1c", struct.pack("<i", len(self.quote_entities)), b"".join(x._bytes() for x in self.quote_entities))) if self.quote_entities is not None else b"",
            struct.pack("<i", self.quote_offset) if self.quote_offset is not None else b"",
            struct.pack("<i", self.todo_item_id) if self.todo_item_id is not None else b"",
            self.serialize_bytes(self.poll_option) if self.poll_option is not None else b"",
            b"".join((b"\x15\xc4\xb5\x1c", struct.pack("<i", len(self.quote_rich)), b"".join(x._bytes() for x in self.quote_rich))) if self.quote_rich is not None else b"",
        ))

    @classmethod
    def from_reader(cls, reader):
        flags = reader.read_int()
        reply_to_scheduled = bool(flags & (1 << 2))
        forum_topic = bool(flags & (1 << 3))
        quote = bool(flags & (1 << 9))
        reply_to_ephemeral = bool(flags & (1 << 13))

        reply_to_msg_id = reader.read_int() if (flags & (1 << 4)) else None
        reply_to_peer_id = reader.tgread_object() if (flags & (1 << 0)) else None
        reply_from = reader.tgread_object() if (flags & (1 << 5)) else None
        reply_media = reader.tgread_object() if (flags & (1 << 8)) else None
        reply_to_top_id = reader.read_int() if (flags & (1 << 1)) else None
        quote_text = reader.tgread_string() if (flags & (1 << 6)) else None

        if flags & (1 << 7):
            reader.read_int()
            count = reader.read_int()
            quote_entities = [reader.tgread_object() for _ in range(count)]
        else:
            quote_entities = None

        quote_offset = reader.read_int() if (flags & (1 << 10)) else None
        todo_item_id = reader.read_int() if (flags & (1 << 11)) else None
        poll_option = reader.tgread_bytes() if (flags & (1 << 12)) else None

        if flags & (1 << 14):
            reader.read_int()
            count = reader.read_int()
            quote_rich = [reader.tgread_object() for _ in range(count)]
        else:
            quote_rich = None

        return cls(
            reply_to_scheduled=reply_to_scheduled,
            forum_topic=forum_topic,
            quote=quote,
            reply_to_ephemeral=reply_to_ephemeral,
            reply_to_msg_id=reply_to_msg_id,
            reply_to_peer_id=reply_to_peer_id,
            reply_from=reply_from,
            reply_media=reply_media,
            reply_to_top_id=reply_to_top_id,
            quote_text=quote_text,
            quote_entities=quote_entities,
            quote_offset=quote_offset,
            todo_item_id=todo_item_id,
            poll_option=poll_option,
            quote_rich=quote_rich,
        )


# Registra os construtores customizados no registro de tipos do Telethon
tlobjects[InputMediaWidget.CONSTRUCTOR_ID] = InputMediaWidget
tlobjects[MessageMediaWidget.CONSTRUCTOR_ID] = MessageMediaWidget
tlobjects[MessageReplyHeader233.CONSTRUCTOR_ID] = MessageReplyHeader233


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
