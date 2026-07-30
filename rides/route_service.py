import json
from dataclasses import dataclass
from decimal import Decimal
from urllib.parse import urlencode
from urllib.request import urlopen

from django.conf import settings

from .utils import haversine_distance


@dataclass(frozen=True)
class RouteResult:
    distance_km: Decimal
    duration_minutes: Decimal
    source: str


class RouteService:
    @staticmethod
    def calculate(pickup_lat, pickup_lon, dropoff_lat, dropoff_lon):
        base_url = getattr(settings, "ROUTING_API_URL", "")
        if base_url:
            coordinates = (
                f"{pickup_lon},{pickup_lat};{dropoff_lon},{dropoff_lat}"
            )
            query = urlencode({"overview": "false", "steps": "false"})
            url = f"{base_url.rstrip('/')}/route/v1/driving/{coordinates}?{query}"
            with urlopen(url, timeout=5) as response:  # noqa: S310
                payload = json.load(response)
            route = payload["routes"][0]
            return RouteResult(
                distance_km=(Decimal(str(route["distance"])) / 1000).quantize(
                    Decimal("0.01")
                ),
                duration_minutes=(
                    Decimal(str(route["duration"])) / 60
                ).quantize(Decimal("0.01")),
                source="osrm",
            )

        straight_line = Decimal(
            str(
                haversine_distance(
                    pickup_lat,
                    pickup_lon,
                    dropoff_lat,
                    dropoff_lon,
                )
            )
        )
        estimated_road = straight_line * Decimal("1.25")
        duration = estimated_road / Decimal("30") * Decimal("60")
        return RouteResult(
            distance_km=estimated_road.quantize(Decimal("0.01")),
            duration_minutes=duration.quantize(Decimal("0.01")),
            source="haversine_estimate",
        )
