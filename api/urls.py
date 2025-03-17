from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import TaskViewSet, TripViewSet, LocationViewSet, DailyLogViewSet, calculate_route

router = DefaultRouter()
router.register(r'tasks', TaskViewSet)
router.register(r'trips', TripViewSet)
router.register(r'locations', LocationViewSet)
router.register(r'daily-logs', DailyLogViewSet)

urlpatterns = [
    path('', include(router.urls)),
    path('route-calculator/', calculate_route, name='calculate-route'),
] 