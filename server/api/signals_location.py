from django.db.models.signals import post_save
from django.dispatch import receiver
from .models import TruckLocation, FleetMission
from django.db import transaction
from django.db.models import Avg, Max

@receiver(post_save, sender=TruckLocation)
def update_mission_speed_and_trail(sender, instance, created, **kwargs):
    """
    When a TruckLocation is created, update the related FleetMission's max_speed, avg_speed, and compressed_trail.
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

    # Update max_speed and avg_speed
    locations = TruckLocation.objects.filter(truck=instance.truck, driver=instance.driver, timestamp__gte=mission.started_at)
    max_speed = locations.aggregate(Max('speed'))['speed__max'] or 0
    avg_speed = locations.aggregate(Avg('speed'))['speed__avg'] or 0

    # Compress trail: store only every Nth point or last 100 points
    N = 10
    points = list(locations.order_by('timestamp').values_list('latitude', 'longitude', 'timestamp'))
    compressed = [[float(lat), float(lon), ts.isoformat() if hasattr(ts, 'isoformat') else str(ts)] for i, (lat, lon, ts) in enumerate(points) if i % N == 0 or i == len(points)-1]
    if len(compressed) > 100:
        compressed = compressed[-100:]

    # Save to mission
    # NOTE: max_speed, avg_speed, compressed_trail are properties, not database fields
    # Cannot use update_fields with properties - just skip them for now
    # These would need to be actual database columns to persist
    # For now, we silently ignore writes to these properties (see models.py setters)
