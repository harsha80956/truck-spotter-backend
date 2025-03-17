from django.shortcuts import render
from rest_framework import viewsets, status, pagination
from rest_framework.decorators import action, api_view, permission_classes
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated, AllowAny
from datetime import datetime, timedelta
from django.utils import timezone
import json
import math
import random
import requests
import os
from dotenv import load_dotenv

from .models import Task, Location, Trip, RouteSegment, DailyLog, LogEntry
from .serializers import (
    TaskSerializer, LocationSerializer, TripSerializer, RouteSegmentSerializer,
    DailyLogSerializer, LogEntrySerializer, TripPlanRequestSerializer, EldLogsRequestSerializer,
    TripListSerializer
)

# Load environment variables from .env file
load_dotenv()

# Google Maps API Key from environment variable
GOOGLE_MAPS_API_KEY = os.getenv('GOOGLE_MAPS_API_KEY')

# Flag to use mock data instead of Google Maps API
USE_MOCK_DATA = os.getenv('USE_MOCK_DATA', 'True').lower() in ('true', 'yes', '1')

# Custom pagination class with smaller page size for better performance
class OptimizedPagination(pagination.PageNumberPagination):
    page_size = 10
    page_size_query_param = 'page_size'
    max_page_size = 50

# Create your views here.

class TaskViewSet(viewsets.ModelViewSet):
    queryset = Task.objects.all().order_by('-created_at')
    serializer_class = TaskSerializer
    permission_classes = [AllowAny]  # For development, change to IsAuthenticated for production


class LocationViewSet(viewsets.ModelViewSet):
    queryset = Location.objects.all()
    serializer_class = LocationSerializer
    permission_classes = [AllowAny]
    
    @action(detail=False, methods=['post'])
    def geocode(self, request):
        """
        Geocode an address to get latitude and longitude.
        Uses Google Maps API if available, otherwise falls back to mock data.
        """
        address = request.data.get('address')
        if not address:
            return Response({"error": "Address is required"}, status=status.HTTP_400_BAD_REQUEST)
        
        if not USE_MOCK_DATA and GOOGLE_MAPS_API_KEY:
            # Try to use Google Maps Geocoding API
            try:
                url = f"https://maps.googleapis.com/maps/api/geocode/json?address={address}&key={GOOGLE_MAPS_API_KEY}"
                response = requests.get(url)
                data = response.json()
                
                if data['status'] == 'OK':
                    # Extract coordinates from the API response
                    location_data = data['results'][0]['geometry']['location']
                    latitude = location_data['lat']
                    longitude = location_data['lng']
                    formatted_address = data['results'][0]['formatted_address']
                    
                    location = Location.objects.create(
                        address=formatted_address,
                        latitude=latitude,
                        longitude=longitude
                    )
                    
                    serializer = LocationSerializer(location)
                    return Response(serializer.data, status=status.HTTP_201_CREATED)
                else:
                    # If geocoding failed, log the error and fall back to mock data
                    print(f"Geocoding failed: {data.get('status')} - {data.get('error_message', 'No error message')}")
            except Exception as e:
                # If API call fails, log the error and fall back to mock data
                print(f"Geocoding API error: {str(e)}")
        
        # Use mock data
        latitude = random.uniform(30, 45)
        longitude = random.uniform(-120, -70)
        
        location = Location.objects.create(
            address=address,
            latitude=latitude,
            longitude=longitude
        )
        
        serializer = LocationSerializer(location)
        return Response(serializer.data, status=status.HTTP_201_CREATED)


class TripViewSet(viewsets.ModelViewSet):
    queryset = Trip.objects.all().order_by('-created_at')
    serializer_class = TripSerializer
    permission_classes = [AllowAny]  # For development, change to IsAuthenticated for production
    pagination_class = OptimizedPagination
    
    def get_serializer_class(self):
        """
        Use different serializers for different actions to optimize performance
        """
        if self.action == 'list':
            return TripListSerializer
        return TripSerializer
    
    def get_queryset(self):
        """
        Optimize queryset by prefetching related objects to avoid N+1 query problem
        """
        queryset = Trip.objects.all().order_by('-created_at')
        
        # Only prefetch related objects when needed
        if self.action == 'list':
            return queryset.select_related(
                'current_location',
                'pickup_location',
                'dropoff_location'
            )
        elif self.action in ['retrieve', 'update', 'partial_update']:
            return queryset.select_related(
                'current_location',
                'pickup_location',
                'dropoff_location'
            ).prefetch_related(
                'segments',
                'segments__start_location',
                'segments__end_location'
            )
        
        return queryset
    
    def list(self, request, *args, **kwargs):
        """
        Optimized list method with pagination and caching
        """
        queryset = self.filter_queryset(self.get_queryset())
        
        # Apply pagination
        page = self.paginate_queryset(queryset)
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return self.get_paginated_response(serializer.data)
        
        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data)
        
    @action(detail=False, methods=['post'])
    def generate_eld_logs(self, request):
        """
        Generate ELD logs for a trip
        """
        try:
            serializer = EldLogsRequestSerializer(data=request.data)
            if not serializer.is_valid():
                return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
            
            trip_id = serializer.validated_data['trip_id']
            print(f"Generating ELD logs for trip_id={trip_id}")
            
            try:
                trip = Trip.objects.get(id=trip_id)
            except Trip.DoesNotExist:
                return Response(
                    {"error": f"Trip with ID {trip_id} not found"}, 
                    status=status.HTTP_404_NOT_FOUND
                )
                
            # Delete existing logs for this trip
            DailyLog.objects.filter(trip=trip).delete()
            
            # Generate daily logs based on trip segments
            daily_logs = []
            
            # Get all segments for the trip
            segments = RouteSegment.objects.filter(trip=trip).order_by('start_time')
            print(f"Found {segments.count()} segments for trip_id={trip_id}")
            
            if not segments:
                return Response(
                    {"error": "No segments found for this trip"}, 
                    status=status.HTTP_400_BAD_REQUEST
                )
                
            # Get the start and end dates of the trip
            trip_start_date = trip.start_time.date()
            trip_end_date = trip.end_time.date()
            print(f"Trip date range: {trip_start_date} to {trip_end_date}")
            
            # Generate a log for each day of the trip
            current_date = trip_start_date
            day_counter = 1
            
            while current_date <= trip_end_date:
                print(f"Processing day {day_counter}: {current_date}")
                # Create a daily log
                daily_log = DailyLog.objects.create(
                    trip=trip,
                    date=current_date,
                    driver_name="Test Driver",
                    carrier_name="Test Carrier",
                    truck_number=f"TRUCK-{trip_id}",
                    trailer_number=f"TRAILER-{trip_id}",
                    start_odometer=100000 + (day_counter - 1) * 500,
                    end_odometer=100000 + day_counter * 500,
                    total_miles=500
                )
                
                # Get segments for this day
                day_start = datetime.combine(current_date, datetime.min.time()).replace(tzinfo=timezone.utc)
                day_end = datetime.combine(current_date, datetime.max.time()).replace(tzinfo=timezone.utc)
                
                # Find segments that overlap with this day
                day_segments = []
                for segment in segments:
                    # Check if segment overlaps with current day
                    if (segment.start_time <= day_end and segment.end_time >= day_start):
                        day_segments.append(segment)
                
                print(f"Found {len(day_segments)} segments for day {current_date}")
                
                # Create log entries based on segments
                for segment in day_segments:
                    print(f"Processing segment: {segment.segment_type} from {segment.start_time} to {segment.end_time}")
                    # Determine status based on segment type (case-insensitive)
                    segment_type_lower = segment.segment_type.lower()
                    
                    if 'drive' in segment_type_lower:
                        status = 'D'  # Driving
                    elif 'rest' in segment_type_lower or 'sleep' in segment_type_lower:
                        status = 'SB'  # Sleeper Berth
                    elif 'pickup' in segment_type_lower or 'dropoff' in segment_type_lower or 'loading' in segment_type_lower or 'unloading' in segment_type_lower:
                        status = 'ON'  # On Duty Not Driving
                    else:
                        status = 'OFF'  # Off Duty
                    
                    print(f"Creating log entry with status: {status}")
                    
                    # Calculate start and end times that fall within this day
                    entry_start = max(segment.start_time, day_start)
                    entry_end = min(segment.end_time, day_end)
                    
                    # Create log entry
                    log_entry = LogEntry.objects.create(
                        daily_log=daily_log,
                        status=status,
                        start_time=entry_start,
                        end_time=entry_end,
                        location=segment.start_location.address,
                        remarks=f"{segment.segment_type.capitalize()} segment"
                    )
                    print(f"Created log entry: {log_entry.id}")
                
                # If no segments were found for this day, create a default "Off Duty" entry
                if not day_segments:
                    print(f"No segments found for day {current_date}, creating default OFF entry")
                    LogEntry.objects.create(
                        daily_log=daily_log,
                        status='OFF',
                        start_time=day_start,
                        end_time=day_end,
                        location=trip.current_location.address,
                        remarks="Off duty (default)"
                    )
                
                daily_logs.append(daily_log)
                current_date += timedelta(days=1)
                day_counter += 1
            
            # Serialize the daily logs
            serializer = DailyLogSerializer(daily_logs, many=True)
            
            return Response({"logs": serializer.data}, status=status.HTTP_201_CREATED)
            
        except Exception as e:
            print(f"Error generating ELD logs: {str(e)}")
            import traceback
            traceback.print_exc()
            return Response(
                {"error": f"Failed to generate ELD logs: {str(e)}"}, 
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


class DailyLogViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = DailyLog.objects.all()
    serializer_class = DailyLogSerializer
    permission_classes = [AllowAny]
    
    def get_queryset(self):
        queryset = DailyLog.objects.all()
        trip_id = self.request.query_params.get('trip_id')
        
        if trip_id:
            queryset = queryset.filter(trip_id=trip_id)
        
        return queryset
    
    @action(detail=True, methods=['get'])
    def entries(self, request, pk=None):
        """
        Retrieve all log entries for a specific daily log.
        """
        daily_log = self.get_object()
        entries = daily_log.entries.all()
        serializer = LogEntrySerializer(entries, many=True)
        return Response(serializer.data)

@api_view(['POST'])
@permission_classes([AllowAny])
def calculate_route(request):
    """
    Calculate a route based on current location, pickup, and dropoff points.
    Applies HOS (Hours of Service) rules to the route.
    """
    try:
        # Validate input data
        if not request.data:
            return Response(
                {"error": "No data provided"}, 
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Extract location data from request
        current_location = request.data.get('currentLocation')
        pickup_location = request.data.get('pickupLocation')
        dropoff_location = request.data.get('dropoffLocation')
        
        # Validate required location data
        if not current_location or not pickup_location or not dropoff_location:
            return Response(
                {"error": "Missing location data. Current, pickup, and dropoff locations are required."}, 
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Extract additional parameters
        current_cycle_hours = request.data.get('currentCycleHours', 0)
        current_status = request.data.get('currentStatus', 'OFF')
        start_datetime = request.data.get('startDateTime')
        vehicle_details = request.data.get('vehicleDetails', {})
        
        # Calculate route using Google Maps API or mock data
        if not USE_MOCK_DATA and GOOGLE_MAPS_API_KEY:
            # Use Google Maps API for real route calculation
            try:
                # Calculate distance and duration from current to pickup
                current_to_pickup_url = f"https://maps.googleapis.com/maps/api/directions/json?origin={current_location['latitude']},{current_location['longitude']}&destination={pickup_location['latitude']},{pickup_location['longitude']}&key={GOOGLE_MAPS_API_KEY}"
                current_to_pickup_response = requests.get(current_to_pickup_url)
                current_to_pickup_data = current_to_pickup_response.json()
                
                if current_to_pickup_data['status'] != 'OK':
                    raise Exception(f"Google Maps API error: {current_to_pickup_data.get('status')} - {current_to_pickup_data.get('error_message', 'No error message')}")
                
                current_to_pickup_distance = current_to_pickup_data['routes'][0]['legs'][0]['distance']['value'] / 1609.34  # Convert meters to miles
                current_to_pickup_duration = current_to_pickup_data['routes'][0]['legs'][0]['duration']['value'] / 60  # Convert seconds to minutes
                
                # Calculate distance and duration from pickup to dropoff
                pickup_to_dropoff_url = f"https://maps.googleapis.com/maps/api/directions/json?origin={pickup_location['latitude']},{pickup_location['longitude']}&destination={dropoff_location['latitude']},{dropoff_location['longitude']}&key={GOOGLE_MAPS_API_KEY}"
                pickup_to_dropoff_response = requests.get(pickup_to_dropoff_url)
                pickup_to_dropoff_data = pickup_to_dropoff_response.json()
                
                if pickup_to_dropoff_data['status'] != 'OK':
                    raise Exception(f"Google Maps API error: {pickup_to_dropoff_data.get('status')} - {pickup_to_dropoff_data.get('error_message', 'No error message')}")
                
                pickup_to_dropoff_distance = pickup_to_dropoff_data['routes'][0]['legs'][0]['distance']['value'] / 1609.34  # Convert meters to miles
                pickup_to_dropoff_duration = pickup_to_dropoff_data['routes'][0]['legs'][0]['duration']['value'] / 60  # Convert seconds to minutes
                
            except Exception as e:
                print(f"Error using Google Maps API: {str(e)}")
                # Fall back to mock data
                current_to_pickup_distance = random.uniform(50, 200)
                current_to_pickup_duration = current_to_pickup_distance * 1.2  # Assume 50 mph average speed
                pickup_to_dropoff_distance = random.uniform(300, 800)
                pickup_to_dropoff_duration = pickup_to_dropoff_distance * 1.2  # Assume 50 mph average speed
        else:
            # Use mock data for route calculation
            current_to_pickup_distance = random.uniform(50, 200)
            current_to_pickup_duration = current_to_pickup_distance * 1.2  # Assume 50 mph average speed
            pickup_to_dropoff_distance = random.uniform(300, 800)
            pickup_to_dropoff_duration = pickup_to_dropoff_distance * 1.2  # Assume 50 mph average speed
        
        # Calculate end time based on HOS rules
        total_driving_hours = (current_to_pickup_duration + pickup_to_dropoff_duration) / 60
        
        # Add mandatory breaks
        num_breaks = math.floor(total_driving_hours / 8)
        break_time = num_breaks * 0.5  # 30 minutes per break
        
        # Add loading/unloading time
        loading_time = 1  # 1 hour for loading
        unloading_time = 1  # 1 hour for unloading
        
        # Calculate total trip time including breaks and loading/unloading
        total_trip_time = total_driving_hours + break_time + loading_time + unloading_time
        
        # Check if we need to add a rest period
        if total_trip_time > 14 - current_cycle_hours:
            # Add a 10-hour rest period
            total_trip_time += 10
        
        # Calculate start and end time
        start_time = timezone.now() if not start_datetime else datetime.fromisoformat(start_datetime.replace('Z', '+00:00'))
        end_time = start_time + timedelta(hours=total_trip_time)
        
        # Create a new Trip object
        trip = Trip.objects.create(
            current_location=Location.objects.create(
                address=current_location.get('address', ''),
                latitude=current_location.get('latitude', 0),
                longitude=current_location.get('longitude', 0)
            ),
            pickup_location=Location.objects.create(
                address=pickup_location.get('address', ''),
                latitude=pickup_location.get('latitude', 0),
                longitude=pickup_location.get('longitude', 0)
            ),
            dropoff_location=Location.objects.create(
                address=dropoff_location.get('address', ''),
                latitude=dropoff_location.get('latitude', 0),
                longitude=dropoff_location.get('longitude', 0)
            ),
            total_distance=current_to_pickup_distance + pickup_to_dropoff_distance,
            total_duration=current_to_pickup_duration + pickup_to_dropoff_duration,
            start_time=start_time,
            end_time=end_time
        )
        
        # Create route segments
        segments = []
        
        # Current location to pickup
        current_time = trip.start_time
        
        # Add driving segment from current location to pickup
        drive_to_pickup = RouteSegment.objects.create(
            trip=trip,
            segment_type='DRIVE',
            start_location=trip.current_location,
            end_location=trip.pickup_location,
            distance=current_to_pickup_distance,
            duration=current_to_pickup_duration,
            start_time=current_time,
            end_time=current_time + timedelta(minutes=current_to_pickup_duration)
        )
        segments.append(drive_to_pickup)
        current_time = drive_to_pickup.end_time
        
        # Add loading segment at pickup
        loading = RouteSegment.objects.create(
            trip=trip,
            segment_type='LOADING',
            start_location=trip.pickup_location,
            end_location=trip.pickup_location,
            distance=0,
            duration=loading_time * 60,  # Convert hours to minutes
            start_time=current_time,
            end_time=current_time + timedelta(hours=loading_time)
        )
        segments.append(loading)
        current_time = loading.end_time
        
        # Check if we need a break before continuing
        driving_time_so_far = current_to_pickup_duration / 60  # Convert to hours
        if driving_time_so_far >= 8:
            # Add a break
            break_segment = RouteSegment.objects.create(
                trip=trip,
                segment_type='BREAK',
                start_location=trip.pickup_location,
                end_location=trip.pickup_location,
                distance=0,
                duration=30,  # 30 minutes
                start_time=current_time,
                end_time=current_time + timedelta(minutes=30)
            )
            segments.append(break_segment)
            current_time = break_segment.end_time
            driving_time_so_far = 0  # Reset driving time
        
        # Add driving segment from pickup to dropoff
        drive_to_dropoff = RouteSegment.objects.create(
            trip=trip,
            segment_type='DRIVE',
            start_location=trip.pickup_location,
            end_location=trip.dropoff_location,
            distance=pickup_to_dropoff_distance,
            duration=pickup_to_dropoff_duration,
            start_time=current_time,
            end_time=current_time + timedelta(minutes=pickup_to_dropoff_duration)
        )
        segments.append(drive_to_dropoff)
        current_time = drive_to_dropoff.end_time
        
        # Add unloading segment at dropoff
        unloading = RouteSegment.objects.create(
            trip=trip,
            segment_type='UNLOADING',
            start_location=trip.dropoff_location,
            end_location=trip.dropoff_location,
            distance=0,
            duration=unloading_time * 60,  # Convert hours to minutes
            start_time=current_time,
            end_time=current_time + timedelta(hours=unloading_time)
        )
        segments.append(unloading)
        
        # Serialize the trip with segments
        serializer = TripSerializer(trip)
        
        return Response(serializer.data, status=status.HTTP_201_CREATED)
        
    except Exception as e:
        print(f"Error calculating route: {str(e)}")
        return Response(
            {"error": f"Failed to calculate route: {str(e)}"}, 
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )
