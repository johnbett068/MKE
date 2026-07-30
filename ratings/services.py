from django.db import transaction
from .models import Rating
from rides.models import Trip


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
        try:
            trip = Trip.objects.get(pk=reference_id, trip_type=service)
        except (Trip.DoesNotExist, ValueError) as exc:
            raise ValueError("The referenced completed service does not exist.") from exc
        if trip.status != "completed":
            raise ValueError("Ratings are allowed only after completion.")
        participants = {trip.customer_id, trip.driver_id}
        if rater.id not in participants or rated_account.id not in participants:
            raise PermissionError("Only service participants may rate each other.")
        if rater.id == rated_account.id:
            raise ValueError("An account cannot rate itself.")
        return Rating.objects.create(
            rater=rater,
            rated_account=rated_account,
            score=score,
            service=service,
            reference_id=reference_id,
            comment=comment
        )
