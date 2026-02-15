from django.db import models
from accounts.models import Account


class Rating(models.Model):
    rater = models.ForeignKey(
        Account,
        on_delete=models.CASCADE,
        related_name='ratings_given'
    )
    rated_account = models.ForeignKey(
        Account,
        on_delete=models.CASCADE,
        related_name='ratings_received'
    )

    score = models.PositiveSmallIntegerField()
    comment = models.TextField(blank=True)

    service = models.CharField(
        max_length=50
    )
    reference_id = models.CharField(
        max_length=100
    )

    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = (
            'rater',
            'rated_account',
            'service',
            'reference_id'
        )

    def __str__(self):
        return f"{self.score} ⭐ from {self.rater}"
