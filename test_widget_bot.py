"""
Tests for Layer 233 Widget TL Objects and Bot logic.
"""

from unittest.mock import AsyncMock, MagicMock
import pytest
from telethon import utils
from telethon.errors import RPCError
from telethon.extensions import BinaryReader
from widget_tl import InputMediaWidget, MessageMediaWidget
from bot import process_html_content, handle_document


def test_input_media_widget_serialization():
    html = "<div><h1>Widget Test</h1></div>"
    widget = InputMediaWidget(width=400, height=300, html=html)

    assert widget.CONSTRUCTOR_ID == 0x297da8f8
    assert widget.SUBCLASS_OF_ID == 0xfaf846f4

    # Check casting via telethon utils.get_input_media
    casted = utils.get_input_media(widget)
    assert casted is widget

    # Check serialization & deserialization
    data = widget._bytes()
    reader = BinaryReader(data)
    cid = reader.read_int(signed=False)
    assert cid == InputMediaWidget.CONSTRUCTOR_ID

    deserialized = InputMediaWidget.from_reader(reader)
    assert deserialized.width == 400
    assert deserialized.height == 300
    assert deserialized.html == html

    # Check to_dict representation
    d = widget.to_dict()
    assert d['_'] == 'InputMediaWidget'
    assert d['width'] == 400
    assert d['height'] == 300
    assert d['html'] == html


def test_message_media_widget_serialization():
    payload = b"\x00\x01\x02\x03\x04"
    widget = MessageMediaWidget(width=500, height=250, payload=payload)

    assert widget.CONSTRUCTOR_ID == 0xb7ed7b0d
    assert widget.SUBCLASS_OF_ID == 0x476cbe32

    # Check serialization & deserialization
    data = widget._bytes()
    reader = BinaryReader(data)
    cid = reader.read_int(signed=False)
    assert cid == MessageMediaWidget.CONSTRUCTOR_ID

    deserialized = MessageMediaWidget.from_reader(reader)
    assert deserialized.width == 500
    assert deserialized.height == 250
    assert deserialized.payload == payload

    # Check to_dict representation
    d = widget.to_dict()
    assert d['_'] == 'MessageMediaWidget'
    assert d['width'] == 500
    assert d['height'] == 250
    assert d['payload'] == payload


def test_process_html_content():
    utf8_bytes = "<h1>Olá Mundo</h1>".encode('utf-8')
    assert process_html_content(utf8_bytes) == "<h1>Olá Mundo</h1>"

    latin1_bytes = "<h1>Olá Mundo</h1>".encode('latin-1')
    assert process_html_content(latin1_bytes) == "<h1>Olá Mundo</h1>"


@pytest.mark.asyncio
async def test_handle_document_rpc_error_not_allowed():
    event = MagicMock()
    message = MagicMock()
    event.message = message
    event.chat_id = 123456
    message.id = 1
    message.document = MagicMock()
    message.file.name = "widget.html"
    message.file.mime_type = "text/html"
    message.download_media = AsyncMock(return_value=b"<h1>Test</h1>")

    status_msg = MagicMock()
    status_msg.edit = AsyncMock()
    event.respond = AsyncMock(return_value=status_msg)

    rpc_err = RPCError(request=None, message="INPUT_MEDIA_WIDGET_NOT_ALLOWED", code=400)
    message.client.send_file = AsyncMock(side_effect=rpc_err)

    await handle_document(event)

    status_msg.edit.assert_called_once()
    args, _ = status_msg.edit.call_args
    assert "INPUT_MEDIA_WIDGET_NOT_ALLOWED" in args[0]
