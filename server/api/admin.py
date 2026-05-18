from django.contrib import admin
from .models import (
    FleetTruck, FleetDriver, FleetMission, 
    FleetActivity, FleetDriverPerformanceDaily, Alert
)

@admin.register(FleetTruck)
class TruckAdmin(admin.ModelAdmin):
    list_display = ('truck_identifier', 'plate', 'status')
    search_fields = ('truck_identifier', 'plate')

@admin.register(FleetDriver)
class DriverAdmin(admin.ModelAdmin):
    list_display = ('first_name', 'last_name', 'status', 'on_duty')
    search_fields = ('first_name', 'last_name', 'phone_number')
    raw_id_fields = ('truck',)

@admin.register(FleetMission)
class MissionAdmin(admin.ModelAdmin):
    list_display = ('mission_number', 'status', 'priority')
    raw_id_fields = ('truck', 'driver')

@admin.register(FleetActivity)
class ActivityAdmin(admin.ModelAdmin):
    list_display = ('truck', 'activity_type', 'timestamp')
    raw_id_fields = ('truck', 'driver', 'mission')

@admin.register(FleetDriverPerformanceDaily)
class PerformanceAdmin(admin.ModelAdmin):
    list_display = ('driver', 'date', 'rating')
    raw_id_fields = ('driver',)

@admin.register(Alert)
class AlertAdmin(admin.ModelAdmin):
    list_display = ('alert_type', 'severity', 'is_resolved', 'created_at')
    search_fields = ('message',)