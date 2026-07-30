import hashlib
import hmac

from django.conf import settings


def start_pin_for_trip(trip_id):
    digest = hmac.new(
        settings.SECRET_KEY.encode(),
        f"trip-start:{trip_id}".encode(),
        hashlib.sha256,
    ).hexdigest()
    return f"{int(digest[:8], 16) % 10000:04d}"


def hash_start_pin(trip_id, pin):
    return hmac.new(
        settings.SECRET_KEY.encode(),
        f"{trip_id}:{pin}".encode(),
        hashlib.sha256,
    ).hexdigest()


def verify_start_pin(trip, pin):
    supplied = hash_start_pin(trip.id, pin)
    return hmac.compare_digest(trip.ride_details.start_pin_hash, supplied)
