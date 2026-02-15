from rest_framework.views import APIView
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework import status

from .models import Rating
from .serializers import RatingSerializer, CreateRatingSerializer
from .services import RatingService


class CreateRatingView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        serializer = CreateRatingSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        rating = RatingService.create_rating(
            rater=request.user,
            rated_account=serializer.validated_data['rated_account'],
            score=serializer.validated_data['score'],
            service=serializer.validated_data['service'],
            reference_id=serializer.validated_data['reference_id'],
            comment=serializer.validated_data.get('comment', "")
        )

        return Response(
            RatingSerializer(rating).data,
            status=status.HTTP_201_CREATED
        )


class MyRatingsView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        ratings = Rating.objects.filter(rated_account=request.user)
        serializer = RatingSerializer(ratings, many=True)
        return Response(serializer.data)
