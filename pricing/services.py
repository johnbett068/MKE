from decimal import Decimal

from .models import PricingRule, SurgePricing, Zone


class PricingService:
    @staticmethod
    def calculate_fare(
        city,
        service_type,
        distance_km,
        duration_minutes,
        pickup_zone=None,
        dropoff_zone=None,
    ):
        rule = PricingRule.objects.filter(
            city__iexact=city,
            service_type=service_type,
            active=True,
        ).order_by("-created_at").first()
        if not rule:
            raise ValueError(
                f"No active {service_type} pricing rule exists for {city}."
            )

        distance = max(Decimal(str(distance_km)), Decimal("0"))
        duration = max(Decimal(str(duration_minutes)), Decimal("0"))
        fare = (
            rule.base_fare
            + rule.per_km_rate * distance
            + rule.per_minute_rate * duration
        )

        zone_names = {name for name in (pickup_zone, dropoff_zone) if name}
        if zone_names:
            zone_fees = Zone.objects.filter(
                city__iexact=city,
                name__in=zone_names,
                active=True,
            ).values_list("extra_fee", flat=True)
            fare += sum(zone_fees, Decimal("0"))

        surge = next(
            (
                item
                for item in SurgePricing.objects.filter(
                    city__iexact=city, active=True
                ).order_by("-created_at")
                if item.is_active_now()
            ),
            None,
        )
        if surge:
            fare *= surge.multiplier

        return fare.quantize(Decimal("0.01"))
