import os
import django
import random
import datetime
from django.utils import timezone

# Set up Django
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "backend.settings")
django.setup()

# Import models
from api.models import Location, Trip, RouteSegment, DailyLog, LogEntry

def create_locations(num=10):
    """Create random locations"""
    locations = []
    cities = [
        "New York", "Los Angeles", "Chicago", "Houston", "Phoenix", 
        "Philadelphia", "San Antonio", "San Diego", "Dallas", "San Jose",
        "Austin", "Jacksonville", "Fort Worth", "Columbus", "San Francisco"
    ]
    
    for i in range(num):
        city = random.choice(cities)
        location = Location.objects.create(
            address=f"{random.randint(100, 9999)} Main St, {city}, USA",
            latitude=random.uniform(25, 48),
            longitude=random.uniform(-123, -75)
        )
        locations.append(location)
        print(f"Created location: {location}")
    
    return locations

def create_trips(locations, num=5):
    """Create random trips"""
    trips = []
    
    for i in range(num):
        # Select random locations
        loc_set = random.sample(locations, 3)
        current_location = loc_set[0]
        pickup_location = loc_set[1]
        dropoff_location = loc_set[2]
        
        # Generate random distances and durations
        current_to_pickup_distance = random.uniform(50, 200)
        current_to_pickup_duration = int(current_to_pickup_distance * 1.2)  # Assume 50 mph average speed
        pickup_to_dropoff_distance = random.uniform(300, 800)
        pickup_to_dropoff_duration = int(pickup_to_dropoff_distance * 1.2)  # Assume 50 mph average speed
        
        total_distance = current_to_pickup_distance + pickup_to_dropoff_distance
        total_duration = current_to_pickup_duration + pickup_to_dropoff_duration
        
        # Start time is a random time within the past 30 days
        start_time = timezone.now() - datetime.timedelta(days=random.randint(0, 30))
        
        # Calculate end time
        total_driving_hours = (current_to_pickup_duration + pickup_to_dropoff_duration) / 60
        num_breaks = int(total_driving_hours / 8)
        break_time = num_breaks * 0.5  # 30 minutes per break
        loading_time = 1  # 1 hour for loading
        unloading_time = 1  # 1 hour for unloading
        total_trip_time = total_driving_hours + break_time + loading_time + unloading_time
        end_time = start_time + datetime.timedelta(hours=total_trip_time)
        
        # Create the trip
        trip = Trip.objects.create(
            current_location=current_location,
            pickup_location=pickup_location,
            dropoff_location=dropoff_location,
            current_cycle_hours=random.uniform(0, 70),
            total_distance=total_distance,
            total_duration=total_duration,
            start_time=start_time,
            end_time=end_time
        )
        trips.append(trip)
        print(f"Created trip: {trip}")
        
        # Create route segments for the trip
        # 1. Drive from current to pickup
        current_to_pickup_end = start_time + datetime.timedelta(minutes=current_to_pickup_duration)
        drive_segment_1 = RouteSegment.objects.create(
            trip=trip,
            start_location=current_location,
            end_location=pickup_location,
            segment_type='drive',
            distance=current_to_pickup_distance,
            duration=current_to_pickup_duration,
            start_time=start_time,
            end_time=current_to_pickup_end
        )
        print(f"Created segment: {drive_segment_1}")
        
        # 2. Loading at pickup
        loading_end = current_to_pickup_end + datetime.timedelta(hours=1)
        loading_segment = RouteSegment.objects.create(
            trip=trip,
            start_location=pickup_location,
            end_location=pickup_location,
            segment_type='pickup',
            distance=0,
            duration=60,  # 1 hour in minutes
            start_time=current_to_pickup_end,
            end_time=loading_end
        )
        print(f"Created segment: {loading_segment}")
        
        # 3. Drive from pickup to dropoff
        pickup_to_dropoff_end = loading_end + datetime.timedelta(minutes=pickup_to_dropoff_duration)
        drive_segment_2 = RouteSegment.objects.create(
            trip=trip,
            start_location=pickup_location,
            end_location=dropoff_location,
            segment_type='drive',
            distance=pickup_to_dropoff_distance,
            duration=pickup_to_dropoff_duration,
            start_time=loading_end,
            end_time=pickup_to_dropoff_end
        )
        print(f"Created segment: {drive_segment_2}")
        
        # 4. Unloading at dropoff
        unloading_end = pickup_to_dropoff_end + datetime.timedelta(hours=1)
        unloading_segment = RouteSegment.objects.create(
            trip=trip,
            start_location=dropoff_location,
            end_location=dropoff_location,
            segment_type='dropoff',
            distance=0,
            duration=60,  # 1 hour in minutes
            start_time=pickup_to_dropoff_end,
            end_time=unloading_end
        )
        print(f"Created segment: {unloading_segment}")
        
        # Create daily logs for the trip
        start_date = start_time.date()
        end_date = end_time.date()
        day_count = (end_date - start_date).days + 1
        
        for day in range(day_count):
            log_date = start_date + datetime.timedelta(days=day)
            daily_log = DailyLog.objects.create(
                trip=trip,
                date=log_date,
                driver_name="Test Driver",
                carrier_name="Test Carrier",
                truck_number=f"T-{random.randint(1000, 9999)}",
                trailer_number=f"TR-{random.randint(1000, 9999)}",
                start_odometer=random.randint(10000, 100000),
                end_odometer=random.randint(10000, 100000) + random.randint(100, 700),
                total_miles=random.uniform(100, 700)
            )
            print(f"Created daily log: {daily_log}")
            
            # Create log entries for each day
            day_start = datetime.datetime.combine(log_date, datetime.time.min).replace(tzinfo=timezone.get_current_timezone())
            day_end = datetime.datetime.combine(log_date, datetime.time.max).replace(tzinfo=timezone.get_current_timezone())
            
            # Create 4-8 log entries for the day
            entry_count = random.randint(4, 8)
            current_time = day_start
            
            for _ in range(entry_count):
                if current_time >= day_end:
                    break
                    
                # Random duration between 30 minutes and 4 hours
                duration_minutes = random.randint(30, 240)
                entry_end = min(current_time + datetime.timedelta(minutes=duration_minutes), day_end)
                
                # Random status
                status = random.choice(['OFF', 'SB', 'D', 'ON'])
                
                # Create log entry
                log_entry = LogEntry.objects.create(
                    daily_log=daily_log,
                    status=status,
                    start_time=current_time,
                    end_time=entry_end,
                    location=f"{random.randint(100, 9999)} Main St, {random.choice(['New York', 'Los Angeles', 'Chicago'])}, USA",
                    remarks=f"Test remarks for {status} status",
                    odometer=random.randint(10000, 100000),
                    start_location=random.choice(locations),
                    end_location=random.choice(locations)
                )
                print(f"Created log entry: {log_entry}")
                
                current_time = entry_end
    
    return trips

def main():
    """Create all dummy data"""
    print("Creating dummy data...")
    
    # Delete existing data
    print("Deleting existing data...")
    LogEntry.objects.all().delete()
    DailyLog.objects.all().delete()
    RouteSegment.objects.all().delete()
    Trip.objects.all().delete()
    Location.objects.all().delete()
    
    # Create new data
    locations = create_locations(15)
    trips = create_trips(locations, 10)
    
    print("Dummy data creation complete!")

if __name__ == "__main__":
    main() 