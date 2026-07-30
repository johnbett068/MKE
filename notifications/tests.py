
# Create your tests here.
from unittest.mock import MagicMock, patch

from django.test import SimpleTestCase, override_settings

from .sms import SMSService


class SmsServiceTests(SimpleTestCase):
    @override_settings(
        SMS_BACKEND="http",
        SMS_API_URL="https://sms.example.test/messages",
        SMS_API_KEY="secret",
        SMS_SENDER_ID="MKE",
    )
    @patch("notifications.sms.urlopen")
    def test_http_adapter_sends_authenticated_json(self, mocked_urlopen):
        response = MagicMock(status=202)
        mocked_urlopen.return_value.__enter__.return_value = response

        SMSService.send_code("+254700000001", "123456", "phone_login")

        request = mocked_urlopen.call_args.args[0]
        self.assertEqual(request.get_method(), "POST")
        self.assertEqual(request.headers["Authorization"], "Bearer secret")
        self.assertIn(b"123456", request.data)
