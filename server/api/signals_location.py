from django.db.models.signals import post_save
from django.dispatch import receiver
from .models import TruckLocation, FleetMission, FleetActivity
from django.db import transaction
from django.db.models import Avg, Max

@receiver(post_save, sender=TruckLocation)
def update_mission_speed_and_trail(sender, instance, created, **kwargs):
    """
    When a TruckLocation is created during mission tracking, record activity audit trail
    with avg_speed and compressed_trail for the mission.
    """
    if not created:
        return

    # Find the mission for this truck/driver at this time
    mission = None
    if instance.driver and instance.truck:
        mission = FleetMission.objects.filter(
            driver=instance.driver, truck=instance.truck, status__in=["enroute", "assigned"]
        ).order_by('-started_at').first()
    if not mission:
        return

    # Calculate stats from all locations during this mission
    locations = TruckLocation.objects.filter(truck=instance.truck, driver=instance.driver, timestamp__gte=mission.started_at)
    max_speed = locations.aggregate(Max('speed'))['speed__max'] or 0
    avg_speed = locations.aggregate(Avg('speed'))['speed__avg'] or 0

    # Compress trail: store only every Nth point or last 100 points
    N = 10
    points = list(locations.order_by('timestamp').values_list('latitude', 'longitude', 'timestamp'))
    compressed = [[float(lat), float(lon), ts.isoformat() if hasattr(ts, 'isoformat') else str(ts)] for i, (lat, lon, ts) in enumerate(points) if i % N == 0 or i == len(points)-1]
    if len(compressed) > 100:
        compressed = compressed[-100:]

    # Save to activity audit trail
    # Only create one activity record per mission (or update if exists)
    activity, created_activity = FleetActivity.objects.get_or_create(
        mission=mission,
        driver=instance.driver,
        truck=instance.truck,
        activity_type='start',  # Location updates belong to 'start' activity
        defaults={
            'activity_category': 'tracking',
            'description': f'GPS tracking: {len(locations)} location points recorded',
            'avg_speed': avg_speed,
            'compressed_trail': compressed,
        }
    )
    
    # If activity already exists, update the metrics
    if not created_activity:
        activity.avg_speed = avg_speed
        activity.compressed_trail = compressed
        activity.description = f'GPS tracking: {len(locations)} location points recorded'
        activity.save(update_fields=['avg_speed', 'compressed_trail', 'description'])
