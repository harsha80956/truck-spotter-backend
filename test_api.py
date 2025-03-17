import requests
import json
from pprint import pprint

BASE_URL = 'http://localhost:8001/api'

def test_geocode_api():
    print("\n=== Testing Geocode API with Google Maps ===")
    url = f"{BASE_URL}/locations/geocode/"
    data = {
        "address": "Empire State Building, New York, NY"
    }
    
    response = requests.post(url, json=data)
    print(f"Status Code: {response.status_code}")
    if response.status_code < 400:
        pprint(response.json())
        return response.json()
    else:
        print(f"Error: {response.text}")
        return None

def test_trip_planning_api():
    print("\n=== Testing Trip Planning API with Google Maps ===")
    url = f"{BASE_URL}/trips/plan/"
    data = {
        "current_location": "Chicago, IL",
        "pickup_location": "Indianapolis, IN",
        "dropoff_location": "Columbus, OH",
        "current_cycle_hours": 5.5
    }
    
    response = requests.post(url, json=data)
    print(f"Status Code: {response.status_code}")
    if response.status_code < 400:
        pprint(response.json())
        return response.json()
    else:
        print(f"Error: {response.text}")
        return None

def test_eld_logs_api(trip_id):
    print("\n=== Testing ELD Logs API ===")
    url = f"{BASE_URL}/trips/generate_eld_logs/"
    data = {
        "trip_id": trip_id
    }
    
    response = requests.post(url, json=data)
    print(f"Status Code: {response.status_code}")
    if response.status_code < 400:
        pprint(response.json())
        return response.json()
    else:
        print(f"Error: {response.text}")
        return None

def test_daily_logs_api(trip_id):
    print("\n=== Testing Daily Logs API ===")
    url = f"{BASE_URL}/daily-logs/?trip_id={trip_id}"
    
    response = requests.get(url)
    print(f"Status Code: {response.status_code}")
    if response.status_code < 400:
        pprint(response.json())
        return response.json()
    else:
        print(f"Error: {response.text}")
        return None

if __name__ == "__main__":
    # Test geocode API with Google Maps
    location = test_geocode_api()
    
    # Test trip planning API with Google Maps
    trip = test_trip_planning_api()
    if trip:
        trip_id = trip['id']
        
        # Test ELD logs API
        eld_logs = test_eld_logs_api(trip_id)
        
        # Test daily logs API
        daily_logs = test_daily_logs_api(trip_id)
        
        print("\nAll API tests completed!")
    else:
        print("\nTests failed: Could not create trip.") 