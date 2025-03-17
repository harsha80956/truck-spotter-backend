from rest_framework import serializers
from .models import Task, Location, Trip, RouteSegment, DailyLog, LogEntry


class TaskSerializer(serializers.ModelSerializer):
    class Meta:
        model = Task
        fields = ['id', 'title', 'description', 'completed', 'created_at', 'updated_at']


class LocationSerializer(serializers.ModelSerializer):
    class Meta:
        model = Location
        fields = ['id', 'address', 'latitude', 'longitude']


class RouteSegmentSerializer(serializers.ModelSerializer):
    start_location = LocationSerializer()
    end_location = LocationSerializer()
    
    class Meta:
        model = RouteSegment
        fields = ['id', 'segment_type', 'distance', 'duration', 'start_time', 'end_time', 'start_location', 'end_location']


# Simplified serializer for location data in list views
class LocationLightSerializer(serializers.ModelSerializer):
    class Meta:
        model = Location
        fields = ['id', 'address']


# Simplified serializer for route segments in list views
class RouteSegmentLightSerializer(serializers.ModelSerializer):
    class Meta:
        model = RouteSegment
        fields = ['id', 'segment_type', 'distance', 'duration', 'start_time', 'end_time']


# Optimized serializer for trip list view
class TripListSerializer(serializers.ModelSerializer):
    current_location_address = serializers.CharField(source='current_location.address')
    pickup_location_address = serializers.CharField(source='pickup_location.address')
    dropoff_location_address = serializers.CharField(source='dropoff_location.address')
    segment_count = serializers.SerializerMethodField()
    
    class Meta:
        model = Trip
        fields = ['id', 'current_location_address', 'pickup_location_address', 'dropoff_location_address', 
                 'total_distance', 'total_duration', 'start_time', 'end_time', 'created_at', 'segment_count']
    
    def get_segment_count(self, obj):
        return obj.segments.count()


class TripSerializer(serializers.ModelSerializer):
    current_location = LocationSerializer()
    pickup_location = LocationSerializer()
    dropoff_location = LocationSerializer()
    segments = RouteSegmentSerializer(many=True, read_only=True)
    
    class Meta:
        model = Trip
        fields = ['id', 'current_location', 'pickup_location', 'dropoff_location', 'current_cycle_hours',
                 'total_distance', 'total_duration', 'start_time', 'end_time', 'created_at', 'segments']
    
    def create(self, validated_data):
        current_location_data = validated_data.pop('current_location')
        pickup_location_data = validated_data.pop('pickup_location')
        dropoff_location_data = validated_data.pop('dropoff_location')
        
        current_location = Location.objects.create(**current_location_data)
        pickup_location = Location.objects.create(**pickup_location_data)
        dropoff_location = Location.objects.create(**dropoff_location_data)
        
        trip = Trip.objects.create(
            current_location=current_location,
            pickup_location=pickup_location,
            dropoff_location=dropoff_location,
            **validated_data
        )
        
        return trip


class LogEntrySerializer(serializers.ModelSerializer):
    start_location = LocationSerializer()
    end_location = LocationSerializer()
    
    class Meta:
        model = LogEntry
        fields = ['id', 'status', 'start_time', 'end_time', 'location', 'start_location', 'end_location', 'remarks']


class DailyLogSerializer(serializers.ModelSerializer):
    entries = LogEntrySerializer(many=True, read_only=True)
    
    class Meta:
        model = DailyLog
        fields = ['id', 'date', 'driver_name', 'carrier_name', 'truck_number', 'trailer_number',
                 'start_odometer', 'end_odometer', 'total_miles', 'entries']


class TripPlanRequestSerializer(serializers.Serializer):
    current_location = serializers.CharField()
    pickup_location = serializers.CharField()
    dropoff_location = serializers.CharField()
    current_cycle_hours = serializers.FloatField(min_value=0, max_value=70)


class EldLogsRequestSerializer(serializers.Serializer):
    trip_id = serializers.IntegerField() 