from django.core.management.base import BaseCommand
from django.db import connection
from api.models import Task, Location, Trip, RouteSegment, DailyLog, LogEntry

class Command(BaseCommand):
    help = 'Clears all data from all tables while maintaining the database structure'

    def handle(self, *args, **options):
        # Delete all data from tables in reverse order of dependencies
        LogEntry.objects.all().delete()
        DailyLog.objects.all().delete()
        RouteSegment.objects.all().delete()
        Trip.objects.all().delete()
        Location.objects.all().delete()
        Task.objects.all().delete()

        # Reset SQLite auto-increment counters
        with connection.cursor() as cursor:
            cursor.execute("DELETE FROM sqlite_sequence")
            cursor.execute("INSERT INTO sqlite_sequence (name, seq) VALUES ('api_task', 0)")
            cursor.execute("INSERT INTO sqlite_sequence (name, seq) VALUES ('api_location', 0)")
            cursor.execute("INSERT INTO sqlite_sequence (name, seq) VALUES ('api_trip', 0)")
            cursor.execute("INSERT INTO sqlite_sequence (name, seq) VALUES ('api_routesegment', 0)")
            cursor.execute("INSERT INTO sqlite_sequence (name, seq) VALUES ('api_dailylog', 0)")
            cursor.execute("INSERT INTO sqlite_sequence (name, seq) VALUES ('api_logentry', 0)")

        self.stdout.write(self.style.SUCCESS('Successfully cleared all tables')) 