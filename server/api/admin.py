from django.contrib import admin
from .models import Truck, Checkpoint, Cargo, Alert, KPI

@admin.register(Truck)
class TruckAdmin(admin.ModelAdmin):
    list_display = ('id', 'plate', 'driver', 'status', 'location', 'speed', 'progress')
    search_fields = ('id', 'plate', 'driver', 'location')
    list_filter = ('status', 'location')

@admin.register(Checkpoint)
class CheckpointAdmin(admin.ModelAdmin):
    list_display = ('id', 'truck', 'name', 'status', 'timestamp')
    search_fields = ('name', 'detail')
    list_filter = ('status',)

@admin.register(Cargo)
class CargoAdmin(admin.ModelAdmin):
    list_display = ('id', 'truck', 'cargo_type', 'weight', 'origin', 'destination')
    search_fields = ('truck__id', 'cargo_type', 'origin', 'destination')
    list_filter = ('cargo_type',)

@admin.register(Alert)
class AlertAdmin(admin.ModelAdmin):
    list_display = ('id', 'truck', 'alert_type', 'message', 'is_resolved', 'timestamp')
    search_fields = ('truck__id', 'message')
    list_filter = ('alert_type', 'is_resolved')

@admin.register(KPI)
class KPIAdmin(admin.ModelAdmin):
    list_display = ('id', 'date', 'active_trucks', 'on_time_rate', 'avg_speed', 'total_deliveries', 'critical_alerts')
    ordering = ('-timestamp',)
