from django.contrib import admin
from .models import (
    FleetTruck as Truck, 
    FleetDriver as Driver, 
    FleetMission as Mission, 
    TruckLocation as Location, 
    FleetMissionStop as Checkpoint,
    FleetActivity,
    FleetDriverPerformanceDaily
)

@admin.register(Truck)
class TruckAdmin(admin.ModelAdmin):
    list_display = ('truck_identifier', 'plate', 'status') 
    search_fields = ('truck_identifier', 'plate')
    list_filter = ('status',)

@admin.register(Mission)
class MissionAdmin(admin.ModelAdmin):
    list_display = ('mission_number', 'status', 'priority')
    search_fields = ('mission_number',)
    list_filter = ('status', 'priority')

@admin.register(Checkpoint)
class CheckpointAdmin(admin.ModelAdmin):
    list_display = ('id', 'mission', 'stop_order', 'status')
    search_fields = ('address',)
    list_filter = ('status',)

@admin.register(Driver)
class DriverAdmin(admin.ModelAdmin):
    list_display = ('first_name', 'last_name', 'status', 'on_duty')
    search_fields = ('first_name', 'last_name', 'phone_number')
    list_filter = ('status', 'on_duty')

@admin.register(FleetActivity)
class ActivityAdmin(admin.ModelAdmin):
    list_display = ('truck', 'activity_type', 'timestamp')
    list_filter = ('activity_type', 'is_critical')

@admin.register(FleetDriverPerformanceDaily)
class PerformanceAdmin(admin.ModelAdmin):
    list_display = ('driver', 'date', 'overall_score')
