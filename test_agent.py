import unittest
from unittest.mock import patch, MagicMock, mock_open
import os
import json

from connectors.gmail_client import GmailClient
from skills.rfq_parser import RFQSkill

class TestGmailClient(unittest.TestCase):
    def setUp(self):
        self.client = GmailClient("test@gmail.com", "password")

    @patch('connectors.gmail_client.MailBox')
    @patch('os.makedirs')
    def test_fetch_unprocessed_rfqs(self, mock_makedirs, mock_mailbox_class):
        # Setup mock mailbox
        mock_mailbox = MagicMock()
        mock_mailbox_class.return_value.login.return_value.__enter__.return_value = mock_mailbox

        # Setup mock message
        mock_msg = MagicMock()
        mock_msg.uid = "123"
        mock_msg.subject = "New RFQ"
        mock_msg.from_ = "client@example.com"
        mock_msg.text = "Please quote these items."
        mock_msg.date = "2023-10-01"

        # Setup mock attachment
        mock_att = MagicMock()
        mock_att.filename = "spec.pdf"
        mock_att.payload = b"pdf_data"
        mock_msg.attachments = [mock_att]

        mock_mailbox.fetch.return_value = [mock_msg]

        with patch('builtins.open', mock_open()) as m:
            rfqs = self.client.fetch_unprocessed_rfqs("/tmp/test_rfq")

            # Assertions
            mock_makedirs.assert_called_with("/tmp/test_rfq", exist_ok=True)
            self.assertEqual(len(rfqs), 1)
            self.assertEqual(rfqs[0]['uid'], "123")
            self.assertEqual(rfqs[0]['subject'], "New RFQ")
            self.assertEqual(rfqs[0]['attachments'], ["/tmp/test_rfq/123_spec.pdf"])
            m.assert_called_with("/tmp/test_rfq/123_spec.pdf", "wb")
            m().write.assert_called_with(b"pdf_data")

    @patch('connectors.gmail_client.smtplib.SMTP_SSL')
    def test_send_mail(self, mock_smtp):
        mock_server = MagicMock()
        mock_smtp.return_value.__enter__.return_value = mock_server

        self.client.send_mail("vendor@example.com", "Test Subject", "Test Body")

        mock_server.login.assert_called_with("test@gmail.com", "password")
        self.assertTrue(mock_server.send_message.called)


class TestRFQSkill(unittest.TestCase):
    def setUp(self):
        # We don't want to actually hit the Gemini API in tests unless specified.
        # But we initialize to test the __init__ logic
        with patch('skills.rfq_parser.genai') as mock_genai:
            self.skill = RFQSkill("fake_api_key")

    @patch('skills.rfq_parser.genai')
    def test_parse_and_draft_text_only(self, mock_genai):
        # Mocking the Gemini response
        mock_response = MagicMock()
        mock_response.text = '{"items": [{"material_type": "Aluminum"}], "draft": "Hello"}'

        # In our implementation self.model is used, we mock its generate_content
        self.skill.model.generate_content.return_value = mock_response

        result = self.skill.parse_and_draft("Need 10 pcs of Aluminum 6061 Bar")

        self.assertIn("items", result)
        self.assertIn("draft", result)
        self.assertEqual(result["items"][0]["material_type"], "Aluminum")

if __name__ == "__main__":
    unittest.main()
