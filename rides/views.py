from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework import status
from .models import Trip, Vehicle, TripEvent
from .serializers import TripSerializer, VehicleSerializer, TripEventSerializer

# Customer creates a trip
@api_view(['POST'])
@permission_classes([IsAuthenticated])
def request_trip(request):
    serializer = TripSerializer(data=request.data)
    if serializer.is_valid():
        serializer.save(customer=request.user)
        return Response(serializer.data, status=status.HTTP_201_CREATED)
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


# Driver lists available trips
@api_view(['GET'])
@permission_classes([IsAuthenticated])
def available_trips(request):
    trips = Trip.objects.filter(status='requested').exclude(customer=request.user)
    serializer = TripSerializer(trips, many=True)
    return Response(serializer.data)


# Driver accepts a trip
@api_view(['PATCH'])
@permission_classes([IsAuthenticated])
def accept_trip(request, trip_id):
    try:
        trip = Trip.objects.get(id=trip_id)
    except Trip.DoesNotExist:
        return Response({'error': 'Trip not found'}, status=status.HTTP_404_NOT_FOUND)

    if trip.status != 'requested':
        return Response({'error': 'Trip already accepted'}, status=status.HTTP_400_BAD_REQUEST)

    trip.driver = request.user
    trip.status = 'accepted'
    trip.save()
    return Response(TripSerializer(trip).data)


# Update trip status
@api_view(['PATCH'])
@permission_classes([IsAuthenticated])
def update_trip_status(request, trip_id):
    try:
        trip = Trip.objects.get(id=trip_id)
    except Trip.DoesNotExist:
        return Response({'error': 'Trip not found'}, status=status.HTTP_404_NOT_FOUND)

    new_status = request.data.get('status')
    if new_status not in dict(Trip.STATUS_CHOICES):
        return Response({'error': 'Invalid status'}, status=status.HTTP_400_BAD_REQUEST)

    trip.status = new_status
    trip.save()
    # Optional: create a TripEvent
    TripEvent.objects.create(trip=trip, status=new_status)
    return Response(TripSerializer(trip).data)


# Trip details
@api_view(['GET'])
@permission_classes([IsAuthenticated])
def trip_details(request, trip_id):
    try:
        trip = Trip.objects.get(id=trip_id)
    except Trip.DoesNotExist:
        return Response({'error': 'Trip not found'}, status=status.HTTP_404_NOT_FOUND)

    serializer = TripSerializer(trip)
    return Response(serializer.data)
