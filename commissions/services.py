# commissions/services.py

from decimal import Decimal
from datetime import date
from .models import CommissionRule


class CommissionService:

    @staticmethod
    def get_active_rule(service_type, role):
        today = date.today()

        return CommissionRule.objects.filter(
            service_type=service_type,
            role=role,
            is_active=True,
            effective_from__lte=today
        ).order_by('-effective_from').first()

    @staticmethod
    def calculate_commission(amount, service_type, role):
        amount = Decimal(amount)

        rule = CommissionService.get_active_rule(service_type, role)

        if not rule:
            return Decimal("0.00")

        percentage_amount = (rule.percentage / Decimal("100")) * amount

        return percentage_amount + rule.flat_fee
