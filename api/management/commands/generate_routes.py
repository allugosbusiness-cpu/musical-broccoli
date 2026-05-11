"""
Auto-routing management command
Automatically generates and updates routes for trucks based on their origin/destination
"""
from django.core.management.base import BaseCommand
from django.utils import timezone
from api.models import Truck, Route
from api.routing_service import RoutingService
from api.data_locations import GLOBAL_LOCATIONS
import logging

logger = logging.getLogger(__name__)


class Command(BaseCommand):
    help = 'Auto-generate routes for trucks with origin/destination set'

    def add_arguments(self, parser):
        parser.add_argument(
            '--truck-id',
            type=str,
            help='Specific truck ID to generate route for',
        )
        parser.add_argument(
            '--all',
            action='store_true',
            help='Generate routes for all trucks with auto-routing enabled',
        )

    def handle(self, *args, **options):
        truck_id = options.get('truck_id')
        all_trucks = options.get('all')

        if truck_id:
            self.generate_single_route(truck_id)
        elif all_trucks:
            self.generate_all_routes()
        else:
            # Default: generate for trucks with active routing but no current route
            self.generate_for_idle_trucks()

    def generate_single_route(self, truck_id):
        """Generate route for a specific truck"""
        try:
            truck = Truck.objects.get(id=truck_id)
            self.stdout.write(f"Generating route for truck {truck.plate}...")
            
            route = self._create_route_for_truck(truck)
            
            if route:
                self.stdout.write(
                    self.style.SUCCESS(
                        f"✓ Route created: {truck.origin} → {truck.destination} ({route.distance_km}km)"
                    )
                )
            else:
                self.stdout.write(
                    self.style.WARNING(f"✗ Could not create route for {truck.plate}")
                )
        except Truck.DoesNotExist:
            self.stdout.write(
                self.style.ERROR(f"Truck {truck_id} not found")
            )

    def generate_all_routes(self):
        """Generate routes for all trucks with auto-routing enabled"""
        trucks = Truck.objects.filter(auto_routing_enabled=True)
        
        self.stdout.write(f"Generating routes for {trucks.count()} trucks...")
        
        created_count = 0
        for truck in trucks:
            if self._create_route_for_truck(truck):
                created_count += 1
        
        self.stdout.write(
            self.style.SUCCESS(f"✓ Created {created_count} routes")
        )

    def generate_for_idle_trucks(self):
        """Generate routes for trucks without active routes"""
        # Get trucks that have origin/destination but no active route
        idle_trucks = Truck.objects.filter(
            auto_routing_enabled=True,
            current_route__isnull=True
        ).exclude(origin='', destination='')
        
        self.stdout.write(f"Found {idle_trucks.count()} trucks needing routes...")
        
        created_count = 0
        for truck in idle_trucks:
            if self._create_route_for_truck(truck):
                created_count += 1
        
        if created_count > 0:
            self.stdout.write(
                self.style.SUCCESS(f"✓ Created {created_count} routes automatically")
            )
        else:
            self.stdout.write(self.style.WARNING("No new routes created"))

    def _create_route_for_truck(self, truck):
        """Helper to create route for a truck"""
        try:
            # Get coordinates for origin/destination
            origin_loc = GLOBAL_LOCATIONS.get(truck.origin)
            dest_loc = GLOBAL_LOCATIONS.get(truck.destination)
            
            if not origin_loc or not dest_loc:
                logger.warning(f"Invalid location for truck {truck.id}: {truck.origin} → {truck.destination}")
                return None
            
            origin_coords = {'lat': origin_loc['lat'], 'lng': origin_loc['lng']}
            dest_coords = {'lat': dest_loc['lat'], 'lng': dest_loc['lng']}
            
            # Create optimized route
            route = RoutingService.create_optimized_route(
                truck.id,
                truck.origin,
                truck.destination,
                origin_coords,
                dest_coords
            )
            
            # Set as current route for truck
            truck.current_route = route
            truck.origin_coordinates = origin_coords
            truck.destination_coordinates = dest_coords
            truck.save()
            
            return route
        except Exception as e:
            logger.error(f"Error creating route for truck {truck.id}: {str(e)}")
            return None
