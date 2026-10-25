"""
Layer 233 Widget TL Objects for Telethon.

This module defines custom TL objects introduced in Telegram Layer 233 for rendering HTML widgets:
- InputMediaWidget (CONSTRUCTOR_ID = 0x297da8f8)
- MessageMediaWidget (CONSTRUCTOR_ID = 0xb7ed7b0d)
"""

import telethon.tl.alltlobjects
from telethon.tl.tlobject import TLObject


class InputMediaWidget(TLObject):
    CONSTRUCTOR_ID = 0x297da8f8
    SUBCLASS_OF_ID = 0xfaf846f4  # InputMedia CRC32

    def __init__(self, width: int, height: int, html: str):
        self.width = width
        self.height = height
        self.html = html

    def _bytes(self):
        return b''.join((
            InputMediaWidget.CONSTRUCTOR_ID.to_bytes(4, 'little'),
            self.width.to_bytes(4, 'little', signed=True),
            self.height.to_bytes(4, 'little', signed=True),
            TLObject.serialize_bytes(self.html)
        ))

    @classmethod
    def from_reader(cls, reader):
        width = reader.read_int()
        height = reader.read_int()
        html = reader.tgread_string()
        return cls(width, height, html)

    def to_dict(self):
        return {
            '_': 'InputMediaWidget',
            'width': self.width,
            'height': self.height,
            'html': self.html
        }


class MessageMediaWidget(TLObject):
    CONSTRUCTOR_ID = 0xb7ed7b0d
    SUBCLASS_OF_ID = 0x476cbe32  # MessageMedia CRC32

    def __init__(self, width: int, height: int, payload: bytes):
        self.width = width
        self.height = height
        self.payload = payload

    def _bytes(self):
        return b''.join((
            MessageMediaWidget.CONSTRUCTOR_ID.to_bytes(4, 'little'),
            self.width.to_bytes(4, 'little', signed=True),
            self.height.to_bytes(4, 'little', signed=True),
            TLObject.serialize_bytes(self.payload)
        ))

    @classmethod
    def from_reader(cls, reader):
        width = reader.read_int()
        height = reader.read_int()
        payload = reader.tgread_bytes()
        return cls(width, height, payload)

    def to_dict(self):
        return {
            '_': 'MessageMediaWidget',
            'width': self.width,
            'height': self.height,
            'payload': self.payload
        }


# Register constructors with Telethon's TLObject registry
telethon.tl.alltlobjects.tlobjects[InputMediaWidget.CONSTRUCTOR_ID] = InputMediaWidget
telethon.tl.alltlobjects.tlobjects[MessageMediaWidget.CONSTRUCTOR_ID] = MessageMediaWidget
