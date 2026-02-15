from django.db import transaction
from .models import Rating


class RatingService:

    @staticmethod
    @transaction.atomic
    def create_rating(
        rater,
        rated_account,
        score,
        service,
        reference_id,
        comment=""
    ):
        return Rating.objects.create(
            rater=rater,
            rated_account=rated_account,
            score=score,
            service=service,
            reference_id=reference_id,
            comment=comment
        )
