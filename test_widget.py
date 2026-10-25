import io
import unittest
from telethon.extensions import BinaryReader
from telethon.tl.alltlobjects import tlobjects
from widget_bot import InputMediaWidget, MessageMediaWidget, parse_dimensions_and_html


class TestWidgetBot(unittest.TestCase):

    def test_tl_registration(self):
        self.assertIn(InputMediaWidget.CONSTRUCTOR_ID, tlobjects)
        self.assertIn(MessageMediaWidget.CONSTRUCTOR_ID, tlobjects)
        self.assertEqual(tlobjects[InputMediaWidget.CONSTRUCTOR_ID], InputMediaWidget)
        self.assertEqual(tlobjects[MessageMediaWidget.CONSTRUCTOR_ID], MessageMediaWidget)

    def test_input_media_widget_serialization(self):
        widget = InputMediaWidget(width=360, height=500, html="<h1>Test</h1>")
        encoded = bytes(widget)
        self.assertTrue(len(encoded) > 0)

        reader = BinaryReader(encoded[4:])  # Skip constructor id header for from_reader
        decoded = InputMediaWidget.from_reader(reader)

        self.assertEqual(decoded.width, 360)
        self.assertEqual(decoded.height, 500)
        self.assertEqual(decoded.html, "<h1>Test</h1>")

    def test_message_media_widget_serialization(self):
        widget = MessageMediaWidget(width=400, height=300, payload=b"payload_bytes")
        encoded = bytes(widget)
        self.assertTrue(len(encoded) > 0)

        reader = BinaryReader(encoded[4:])
        decoded = MessageMediaWidget.from_reader(reader)

        self.assertEqual(decoded.width, 400)
        self.assertEqual(decoded.height, 300)
        self.assertEqual(decoded.payload, b"payload_bytes")

    def test_parse_dimensions_and_html(self):
        sample_html = "<!-- dimensions: width=450 height=600 -->\n<html><body>Content</body></html>"
        width, height, html = parse_dimensions_and_html(sample_html)
        self.assertEqual(width, 450)
        self.assertEqual(height, 600)
        self.assertEqual(html, sample_html)

        # Default fallback
        no_dim_html = "<html><body>No dims</body></html>"
        w_def, h_def, _ = parse_dimensions_and_html(no_dim_html)
        self.assertEqual(w_def, 360)
        self.assertEqual(h_def, 500)


if __name__ == '__main__':
    unittest.main()
