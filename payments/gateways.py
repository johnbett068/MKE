import base64
import json
from abc import ABC, abstractmethod
from datetime import datetime
from urllib.request import Request, urlopen

from django.conf import settings


class PaymentProviderError(RuntimeError):
    pass


class PaymentGateway(ABC):
    @abstractmethod
    def initiate_stk_push(self, intent):
        raise NotImplementedError

    @abstractmethod
    def initiate_b2c(self, *, phone_number, amount, reference, remarks):
        raise NotImplementedError


class MpesaGateway(PaymentGateway):
    def __init__(self):
        self.base_url = settings.MPESA_BASE_URL.rstrip("/")
        self.consumer_key = settings.MPESA_CONSUMER_KEY
        self.consumer_secret = settings.MPESA_CONSUMER_SECRET
        self.shortcode = settings.MPESA_SHORTCODE
        self.passkey = settings.MPESA_PASSKEY
        self.callback_url = settings.MPESA_STK_CALLBACK_URL

    def _configured(self):
        return all(
            [
                self.consumer_key,
                self.consumer_secret,
                self.shortcode,
                self.passkey,
                self.callback_url,
            ]
        )

    def _request(self, path, payload=None, headers=None):
        request = Request(  # noqa: S310
            f"{self.base_url}/{path.lstrip('/')}",
            data=json.dumps(payload).encode() if payload is not None else None,
            headers=headers or {},
            method="POST" if payload is not None else "GET",
        )
        with urlopen(request, timeout=10) as response:  # noqa: S310
            return json.load(response)

    def _access_token(self):
        credentials = base64.b64encode(
            f"{self.consumer_key}:{self.consumer_secret}".encode()
        ).decode()
        response = self._request(
            "/oauth/v1/generate?grant_type=client_credentials",
            headers={"Authorization": f"Basic {credentials}"},
        )
        return response["access_token"]

    def initiate_stk_push(self, intent):
        if not self._configured():
            raise PaymentProviderError("M-Pesa STK Push is not configured.")
        timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
        password = base64.b64encode(
            f"{self.shortcode}{self.passkey}{timestamp}".encode()
        ).decode()
        phone_number = intent.phone_number.lstrip("+")
        payload = {
            "BusinessShortCode": self.shortcode,
            "Password": password,
            "Timestamp": timestamp,
            "TransactionType": "CustomerPayBillOnline",
            "Amount": int(intent.amount),
            "PartyA": phone_number,
            "PartyB": self.shortcode,
            "PhoneNumber": phone_number,
            "CallBackURL": self.callback_url,
            "AccountReference": str(intent.public_id),
            "TransactionDesc": intent.get_purpose_display(),
        }
        return self._request(
            "/mpesa/stkpush/v1/processrequest",
            payload,
            headers={
                "Authorization": f"Bearer {self._access_token()}",
                "Content-Type": "application/json",
            },
        )

    def initiate_b2c(self, *, phone_number, amount, reference, remarks):
        raise PaymentProviderError(
            "B2C requires certificate-backed credential configuration."
        )
