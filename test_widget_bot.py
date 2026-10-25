import unittest
import struct
from telethon.extensions import BinaryReader
from telethon.tl.alltlobjects import tlobjects
from telethon.tl.types import InputPeerSelf

from widget_bot import InputMediaWidget, MessageMediaWidget, MessageReplyHeader233, SendWidgetRequest


class TestWidgetTL(unittest.TestCase):

    def test_tlobjects_registration(self):
        """Verifica se os tipos TL customizados estão registrados no Telethon."""
        self.assertIn(InputMediaWidget.CONSTRUCTOR_ID, tlobjects)
        self.assertEqual(tlobjects[InputMediaWidget.CONSTRUCTOR_ID], InputMediaWidget)
        self.assertIn(MessageMediaWidget.CONSTRUCTOR_ID, tlobjects)
        self.assertEqual(tlobjects[MessageMediaWidget.CONSTRUCTOR_ID], MessageMediaWidget)
        self.assertIn(MessageReplyHeader233.CONSTRUCTOR_ID, tlobjects)
        self.assertEqual(tlobjects[MessageReplyHeader233.CONSTRUCTOR_ID], MessageReplyHeader233)

    def test_input_media_widget_serialization(self):
        """Testa serialização e desserialização de InputMediaWidget."""
        widget = InputMediaWidget(width=400, height=500, html="<div>Hello World</div>")
        raw_bytes = widget._bytes()

        # Construtor (4 bytes) + width (4 bytes) + height (4 bytes)
        self.assertEqual(raw_bytes[:4], struct.pack("<I", 0x297DA8F8))
        self.assertEqual(raw_bytes[4:8], struct.pack("<i", 400))
        self.assertEqual(raw_bytes[8:12], struct.pack("<i", 500))

        # Desserialização usando BinaryReader
        reader = BinaryReader(raw_bytes)
        parsed = reader.tgread_object()

        self.assertIsInstance(parsed, InputMediaWidget)
        self.assertEqual(parsed.width, 400)
        self.assertEqual(parsed.height, 500)
        self.assertEqual(parsed.html, "<div>Hello World</div>")

    def test_message_media_widget_serialization(self):
        """Testa serialização e desserialização de MessageMediaWidget."""
        payload = b"test payload"
        widget = MessageMediaWidget(width=300, height=450, payload=payload)
        raw_bytes = widget._bytes()

        # Construtor (4 bytes) + width (4 bytes) + height (4 bytes)
        self.assertEqual(raw_bytes[:4], struct.pack("<I", 0xB7ED7B0D))
        self.assertEqual(raw_bytes[4:8], struct.pack("<i", 300))
        self.assertEqual(raw_bytes[8:12], struct.pack("<i", 450))

        # Desserialização usando BinaryReader
        reader = BinaryReader(raw_bytes)
        parsed = reader.tgread_object()

        self.assertIsInstance(parsed, MessageMediaWidget)
        self.assertEqual(parsed.width, 300)
        self.assertEqual(parsed.height, 450)
        self.assertEqual(parsed.payload, payload)

    def test_message_reply_header_233_deserialization(self):
        """Testa a desserialização de MessageReplyHeader233 (0xDDB5AB75)."""
        raw = b"u\xab\xb5\xdd\x10\x00\x00\x00\xcc4\x00\x00"
        reader = BinaryReader(raw)
        header = reader.tgread_object()

        self.assertIsInstance(header, MessageReplyHeader233)
        self.assertEqual(header.reply_to_msg_id, 13516)

        # Testa round-trip de bytes
        roundtrip = header._bytes()
        self.assertEqual(roundtrip, raw)

    def test_send_widget_request_bytes(self):
        """Testa a construção de SendWidgetRequest com e sem random_id explícito."""
        peer = InputPeerSelf()
        media = InputMediaWidget(width=400, height=500, html="<p>Test</p>")

        # Teste com random_id explícito
        req1 = SendWidgetRequest(peer=peer, media=media, message="", random_id=12345)
        data1 = req1._bytes()
        self.assertEqual(data1[:4], b'\x7f\xe70\x03')
        self.assertIn(struct.pack("<I", 0x297DA8F8), data1)

        # Teste sem random_id (gerado automaticamente)
        req2 = SendWidgetRequest(peer=peer, media=media, message="")
        self.assertIsNotNone(req2.random_id)
        self.assertIsInstance(req2.random_id, int)
        data2 = req2._bytes()
        self.assertEqual(data2[:4], b'\x7f\xe70\x03')


if __name__ == "__main__":
    unittest.main()
