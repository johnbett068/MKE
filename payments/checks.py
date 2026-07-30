from django.conf import settings
from django.core.checks import Error, register


@register()
def payment_configuration_check(app_configs, **kwargs):
    errors = []
    credentials_present = any(
        [
            settings.MPESA_CONSUMER_KEY,
            settings.MPESA_CONSUMER_SECRET,
            settings.MPESA_SHORTCODE,
            settings.MPESA_PASSKEY,
        ]
    )
    if credentials_present and not settings.MPESA_CALLBACK_TOKEN:
        errors.append(
            Error(
                "MPESA_CALLBACK_TOKEN is required when M-Pesa is configured.",
                id="payments.E001",
            )
        )
    if (
        not settings.DEBUG
        and settings.MPESA_STK_CALLBACK_URL
        and not settings.MPESA_STK_CALLBACK_URL.startswith("https://")
    ):
        errors.append(
            Error(
                "Production M-Pesa callback URL must use HTTPS.",
                id="payments.E002",
            )
        )
    return errors
