import logging
import json
from urllib.request import Request, urlopen

from django.conf import settings


logger = logging.getLogger(__name__)


class SMSService:
    """Provider boundary for Africa's Talking/Twilio or another SMS gateway."""

    @staticmethod
    def send_code(phone_number, code, purpose):
        if not phone_number:
            raise ValueError("A phone number is required.")
        if settings.SMS_BACKEND == "console":
            logger.info(
                "Development SMS to %s for %s: %s",
                phone_number,
                purpose,
                code,
            )
            return
        if settings.SMS_BACKEND == "http":
            message = f"Your MKE {purpose.replace('_', ' ')} code is {code}."
            request = Request(
                settings.SMS_API_URL,
                data=json.dumps(
                    {
                        "to": phone_number,
                        "message": message,
                        "sender_id": settings.SMS_SENDER_ID,
                    }
                ).encode(),
                headers={
                    "Authorization": f"Bearer {settings.SMS_API_KEY}",
                    "Content-Type": "application/json",
                },
                method="POST",
            )
            with urlopen(request, timeout=10) as response:
                if not 200 <= response.status < 300:
                    raise RuntimeError("The SMS provider rejected the message.")
            return
        raise RuntimeError("A production SMS provider has not been configured.")
