from django.contrib import admin
from .models import (
    FleetTruck, FleetDriver, FleetMission, 
    FleetMissionStop, FleetActivity, FleetDriverPerformanceDaily
)

@admin.register(FleetTruck)
class TruckAdmin(admin.ModelAdmin):
    list_display = ('truck_identifier', 'plate', 'status')
    search_fields = ('truck_identifier', 'plate')
    # Using raw_id_fields stops the 500 error by not loading 
    # a massive dropdown of drivers into the page.
    raw_id_fields = ('assigned_driver',) 

@admin.register(FleetDriver)
class DriverAdmin(admin.ModelAdmin):
    list_display = ('first_name', 'last_name', 'status', 'on_duty')
    search_fields = ('first_name', 'last_name', 'phone_number')
    # This stops the crash when adding a driver
    raw_id_fields = ('truck',)

@admin.register(FleetMission)
class MissionAdmin(admin.ModelAdmin):
    list_display = ('mission_number', 'status', 'priority')
    raw_id_fields = ('truck', 'driver')

@admin.register(FleetMissionStop)
class CheckpointAdmin(admin.ModelAdmin):
    list_display = ('id', 'mission', 'stop_order', 'status')
    raw_id_fields = ('mission',)

@admin.register(FleetActivity)
class ActivityAdmin(admin.ModelAdmin):
    list_display = ('truck', 'activity_type', 'timestamp')
    raw_id_fields = ('truck', 'driver', 'mission')

@admin.register(FleetDriverPerformanceDaily)
class PerformanceAdmin(admin.ModelAdmin):
    list_display = ('driver', 'date', 'overall_score')
    raw_id_fields = ('driver',)
