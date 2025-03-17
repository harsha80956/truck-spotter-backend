# TruckSpotter Backend - Trip Planning & ELD Logs API

This is the backend API for the TruckSpotter application, designed to help truck drivers plan their trips efficiently while staying compliant with Hours of Service (HOS) regulations. The API provides endpoints for route calculation, ELD log generation, and location geocoding.

## Features

- **Route Calculation**: Calculate optimal routes between current location, pickup, and dropoff points
- **HOS Compliance**: Automatically calculate required rest periods based on current regulations
- **ELD Log Generation**: Generate compliant electronic logging device logs for trips
- **Geocoding**: Convert addresses to coordinates for route planning

## Technology Stack

- Django 4.2.7
- Django REST Framework 3.14.0
- SQLite (for development)
- Python 3.8+

## Getting Started

### Prerequisites

- Python 3.8+
- pip

### Installation

1. Clone the repository and navigate to the backend directory
```bash
git clone https://github.com/yourusername/truckspotter.git
cd truckspotter/backend
```

2. Create and activate a virtual environment
```bash
python -m venv env
source env/bin/activate  # On Windows: env\Scripts\activate
```

3. Install dependencies
```bash
pip install -r requirements.txt
```

4. Set up environment variables
Create a `.env` file in the backend directory with the following variables:
```
DEBUG=True
SECRET_KEY=your-secret-key
ALLOWED_HOSTS=localhost,127.0.0.1
CORS_ALLOW_ALL_ORIGINS=True
GOOGLE_MAPS_API_KEY=your-google-maps-api-key
USE_MOCK_DATA=True
```

5. Run migrations
```bash
python manage.py migrate
```

6. Start the development server
```bash
python manage.py runserver
```

The API will be available at `http://localhost:8000/api/`.

## API Endpoints

### Location API

- `GET /api/locations/`: List all locations
- `POST /api/locations/`: Create a new location
- `GET /api/locations/{id}/`: Retrieve a location
- `PUT /api/locations/{id}/`: Update a location
- `DELETE /api/locations/{id}/`: Delete a location
- `POST /api/locations/geocode/`: Geocode an address to coordinates

### Trip API

- `GET /api/trips/`: List all trips
- `GET /api/trips/{id}/`: Get a single trip by ID
- `POST /api/trips/plan/`: Plan a trip with HOS compliance
- `POST /api/trips/generate_eld_logs/`: Generate ELD logs for a trip

### Daily Logs API

- `GET /api/daily-logs/`: List all daily logs
- `GET /api/daily-logs/{id}/`: Get a single daily log by ID
- `GET /api/daily-logs/?trip_id={trip_id}`: Get daily logs for a specific trip

### Route Calculator API

- `POST /api/route-calculator/`: Calculate a route with HOS compliance

## Data Models

### Location
- `address`: String - The address of the location
- `latitude`: Float - The latitude coordinate
- `longitude`: Float - The longitude coordinate

### Trip
- `current_location`: ForeignKey to Location - The starting point
- `pickup_location`: ForeignKey to Location - The pickup point
- `dropoff_location`: ForeignKey to Location - The delivery point
- `current_cycle_hours`: Float - Current hours in the driver's cycle
- `total_distance`: Float - Total trip distance in miles
- `total_duration`: Integer - Total trip duration in minutes
- `start_time`: DateTime - Trip start time
- `end_time`: DateTime - Trip end time

### RouteSegment
- `trip`: ForeignKey to Trip - The associated trip
- `segment_type`: String - Type of segment (drive, rest, sleep, fuel, pickup, dropoff)
- `start_location`: ForeignKey to Location - Segment start location
- `end_location`: ForeignKey to Location - Segment end location
- `distance`: Float - Segment distance in miles
- `duration`: Integer - Segment duration in minutes
- `start_time`: DateTime - Segment start time
- `end_time`: DateTime - Segment end time

### DailyLog
- `trip`: ForeignKey to Trip - The associated trip
- `date`: Date - The date of the log
- `driver_name`: String - Name of the driver
- `carrier_name`: String - Name of the carrier
- `truck_number`: String - Truck identification number
- `trailer_number`: String - Trailer identification number
- `start_odometer`: Integer - Starting odometer reading
- `end_odometer`: Integer - Ending odometer reading
- `total_miles`: Float - Total miles driven that day

### LogEntry
- `daily_log`: ForeignKey to DailyLog - The associated daily log
- `status`: String - Duty status (OFF, SB, D, ON)
- `start_time`: DateTime - Entry start time
- `end_time`: DateTime - Entry end time
- `location`: String - Location description
- `remarks`: String - Additional remarks

## HOS Regulations

The API implements the following Hours of Service regulations:

- Property-carrying drivers are limited to 11 hours of driving after 10 consecutive hours off duty
- Drivers may not drive beyond the 14th consecutive hour after coming on duty
- Drivers may not drive after 60/70 hours on duty in 7/8 consecutive days
- Drivers must take a 30-minute break when they have driven for a period of 8 cumulative hours without at least a 30-minute interruption

## Development

### Running Tests
```bash
python manage.py test
```

### Creating Test Data
```bash
python create_dummy_data.py
```

## Deployment

The backend can be deployed to various platforms:

- **Heroku**: The backend can be deployed to Heroku with minimal configuration.
- **AWS**: The backend can be deployed to AWS using Elastic Beanstalk or EC2.
- **Docker**: The backend can be containerized and deployed using Docker.

## License

This project is licensed under the MIT License - see the LICENSE file for details. 