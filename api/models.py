from django.db import models

# Create your models here.

class Task(models.Model):
    title = models.CharField(max_length=200)
    description = models.TextField(blank=True)
    completed = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True, db_index=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.title

class Location(models.Model):
    address = models.CharField(max_length=255, db_index=True)
    latitude = models.FloatField()
    longitude = models.FloatField()
    
    class Meta:
        indexes = [
            models.Index(fields=['latitude', 'longitude']),
        ]
    
    def __str__(self):
        return self.address

class Trip(models.Model):
    current_location = models.ForeignKey(Location, on_delete=models.CASCADE, related_name='trips_as_current')
    pickup_location = models.ForeignKey(Location, on_delete=models.CASCADE, related_name='trips_as_pickup')
    dropoff_location = models.ForeignKey(Location, on_delete=models.CASCADE, related_name='trips_as_dropoff')
    current_cycle_hours = models.FloatField(default=0)
    total_distance = models.FloatField(default=0)  # in miles
    total_duration = models.IntegerField(default=0)  # in minutes
    start_time = models.DateTimeField(db_index=True)
    end_time = models.DateTimeField()
    created_at = models.DateTimeField(auto_now_add=True, db_index=True)
    
    class Meta:
        indexes = [
            models.Index(fields=['-created_at']),
            models.Index(fields=['start_time', 'end_time']),
        ]
    
    def __str__(self):
        return f"Trip from {self.current_location} to {self.dropoff_location}"

class RouteSegment(models.Model):
    SEGMENT_TYPES = [
        ('drive', 'Driving'),
        ('rest', 'Rest'),
        ('sleep', 'Sleep'),
        ('fuel', 'Fuel'),
        ('pickup', 'Pickup'),
        ('dropoff', 'Dropoff'),
    ]
    
    trip = models.ForeignKey(Trip, on_delete=models.CASCADE, related_name='segments')
    start_location = models.ForeignKey(Location, on_delete=models.CASCADE, related_name='segments_as_start')
    end_location = models.ForeignKey(Location, on_delete=models.CASCADE, related_name='segments_as_end')
    segment_type = models.CharField(max_length=10, choices=SEGMENT_TYPES, db_index=True)
    distance = models.FloatField(default=0)  # in miles
    duration = models.IntegerField(default=0)  # in minutes
    start_time = models.DateTimeField(db_index=True)
    end_time = models.DateTimeField()
    
    class Meta:
        indexes = [
            models.Index(fields=['trip', 'segment_type']),
            models.Index(fields=['start_time', 'end_time']),
        ]
    
    def __str__(self):
        return f"{self.get_segment_type_display()} from {self.start_location} to {self.end_location}"

class DailyLog(models.Model):
    trip = models.ForeignKey(Trip, on_delete=models.CASCADE, related_name='daily_logs')
    date = models.DateField(db_index=True)
    driver_name = models.CharField(max_length=100)
    carrier_name = models.CharField(max_length=100)
    truck_number = models.CharField(max_length=50)
    trailer_number = models.CharField(max_length=50, blank=True, null=True)
    start_odometer = models.IntegerField(default=0)
    end_odometer = models.IntegerField(default=0)
    total_miles = models.FloatField(default=0)
    
    class Meta:
        indexes = [
            models.Index(fields=['trip', 'date']),
        ]
    
    def __str__(self):
        return f"Log for {self.driver_name} on {self.date}"

class LogEntry(models.Model):
    STATUS_CHOICES = [
        ('OFF', 'Off Duty'),
        ('SB', 'Sleeper Berth'),
        ('D', 'Driving'),
        ('ON', 'On Duty Not Driving'),
    ]
    
    daily_log = models.ForeignKey(DailyLog, on_delete=models.CASCADE, related_name='entries')
    status = models.CharField(max_length=3, choices=STATUS_CHOICES, db_index=True)
    start_time = models.DateTimeField(db_index=True)
    end_time = models.DateTimeField()
    location = models.CharField(max_length=255)
    start_location = models.ForeignKey(Location, on_delete=models.SET_NULL, null=True, blank=True, related_name='entries_as_start')
    end_location = models.ForeignKey(Location, on_delete=models.SET_NULL, null=True, blank=True, related_name='entries_as_end')
    remarks = models.CharField(max_length=255, blank=True)
    
    class Meta:
        indexes = [
            models.Index(fields=['daily_log', 'status']),
            models.Index(fields=['start_time', 'end_time']),
        ]
    
    def __str__(self):
        return f"{self.get_status_display()} from {self.start_time} to {self.end_time}"
