"""
Fleet Management v2.0 - Service Layer (Business Logic)
Implements CRUD, state machines, computed fields, RBAC, and event logging

Author: Backend Team
Date: 2026-05-05
"""

from django.db import transaction
from django.utils import timezone
from django.core.exceptions import ValidationError
import logging

from .models_v2 import (
    FleetDriver, FleetTruck, FleetMission, FleetMissionStop, FleetMissionEvent,
    FleetMissionDispute, FleetDriverPerformanceDaily, FleetAdminAuditLog,
    DriverStatus, TruckStatus, MissionStatus, MissionStopStatus, MissionEventType, DisputeStatus
)

logger = logging.getLogger(__name__)

# ============================================================
# DRIVER SERVICE
# ============================================================

class DriverService:
    """Service layer for driver operations"""
    
    @staticmethod
    def create_driver(fleet_id, first_name, last_name, email=None, phone=None, 
                     license_number=None, hire_date=None, admin_id=None):
        """Create new driver (admin only)"""
        try:
            driver = FleetDriver.objects.create(
                fleet_id=fleet_id,
                first_name=first_name,
                last_name=last_name,
                email=email,
                phone=phone,
                license_number=license_number,
                hire_date=hire_date,
                status=DriverStatus.ACTIVE
            )
            
            # Log admin action
            if admin_id:
                FleetAdminAuditLog.objects.create(
                    admin_id=admin_id,
                    action='CREATE',
                    resource_type='Driver',
                    resource_id=driver.id,
                    new_values={'first_name': first_name, 'last_name': last_name, 'email': email}
                )
            
            logger.info(f"Driver created: {driver.id} ({first_name} {last_name})")
            return driver
        except Exception as e:
            logger.error(f"Failed to create driver: {e}")
            raise ValidationError(f"Failed to create driver: {str(e)}")
    
    @staticmethod
    def get_driver(driver_id):
        """Get driver by ID"""
        return FleetDriver.objects.filter(id=driver_id).first()
    
    @staticmethod
    def list_drivers(fleet_id, status=None, on_duty=None):
        """List drivers with optional filters"""
        qs = FleetDriver.objects.filter(fleet_id=fleet_id)
        if status:
            qs = qs.filter(status=status)
        if on_duty is not None:
            qs = qs.filter(on_duty=on_duty)
        return qs
    
    @staticmethod
    def toggle_on_duty(driver_id, on_duty, admin_id=None):
        """Toggle driver on-duty status"""
        try:
            driver = FleetDriver.objects.get(id=driver_id)
            old_on_duty = driver.on_duty
            driver.on_duty = on_duty
            driver.save()
            
            # Log event
            FleetMissionEvent.objects.create(
                driver=driver,
                event_type=MissionEventType.DRIVER_ASSIGNED,
                payload={'on_duty': on_duty}
            )
            
            logger.info(f"Driver {driver_id} on_duty toggled: {old_on_duty} → {on_duty}")
            return driver
        except FleetDriver.DoesNotExist:
            raise ValidationError(f"Driver {driver_id} not found")
    
    @staticmethod
    def suspend_driver(driver_id, reason, admin_id):
        """Suspend driver (admin only)"""
        try:
            driver = FleetDriver.objects.get(id=driver_id)
            driver.status = DriverStatus.SUSPENDED
            driver.save()
            
            FleetAdminAuditLog.objects.create(
                admin_id=admin_id,
                action='SUSPEND',
                resource_type='Driver',
                resource_id=driver.id,
                new_values={'status': DriverStatus.SUSPENDED, 'reason': reason}
            )
            
            logger.info(f"Driver {driver_id} suspended. Reason: {reason}")
            return driver
        except FleetDriver.DoesNotExist:
            raise ValidationError(f"Driver {driver_id} not found")
    
    @staticmethod
    def _update_driver_deliveries(driver_id):
        """Update driver deliveries count from completed stops (last 30 days)"""
        try:
            deliveries = FleetMissionStop.objects.filter(
                mission__driver_id=driver_id,
                status=MissionStopStatus.COMPLETED,
                created_at__gte=timezone.now() - timezone.timedelta(days=30)
            ).count()
            
            driver = FleetDriver.objects.get(id=driver_id)
            driver.deliveries_count = deliveries
            driver.save()
            
            logger.info(f"Driver {driver_id} deliveries updated: {deliveries}")
        except Exception as e:
            logger.error(f"Failed to update driver deliveries: {e}")

# ============================================================
# TRUCK SERVICE
# ============================================================

class TruckService:
    """Service layer for truck operations"""
    
    @staticmethod
    def create_truck(fleet_id, truck_identifier, plate, telematics_id=None, 
                    vin=None, make=None, model=None, year=None, 
                    fuel_capacity_liters=100, admin_id=None):
        """Create new truck (admin only)"""
        try:
            truck = FleetTruck.objects.create(
                fleet_id=fleet_id,
                truck_identifier=truck_identifier,
                plate=plate,
                telematics_id=telematics_id,
                vin=vin,
                make=make,
                model=model,
                year=year,
                fuel_capacity_liters=fuel_capacity_liters,
                status=TruckStatus.IDLE
            )
            
            if admin_id:
                FleetAdminAuditLog.objects.create(
                    admin_id=admin_id,
                    action='CREATE',
                    resource_type='Truck',
                    resource_id=truck.id,
                    new_values={'truck_identifier': truck_identifier, 'plate': plate}
                )
            
            logger.info(f"Truck created: {truck.id} ({plate})")
            return truck
        except Exception as e:
            logger.error(f"Failed to create truck: {e}")
            raise ValidationError(f"Failed to create truck: {str(e)}")
    
    @staticmethod
    def get_truck(truck_id):
        """Get truck by ID"""
        return FleetTruck.objects.filter(id=truck_id).first()
    
    @staticmethod
    def list_trucks(fleet_id, status=None):
        """List trucks with optional filters"""
        qs = FleetTruck.objects.filter(fleet_id=fleet_id)
        if status:
            qs = qs.filter(status=status)
        return qs
    
    @staticmethod
    def assign_driver(truck_id, driver_id, admin_id):
        """Assign driver to truck"""
        try:
            truck = FleetTruck.objects.get(id=truck_id)
            driver = FleetDriver.objects.get(id=driver_id)
            
            truck.assigned_driver = driver
            truck.save()
            
            FleetAdminAuditLog.objects.create(
                admin_id=admin_id,
                action='ASSIGN_DRIVER',
                resource_type='Truck',
                resource_id=truck.id,
                new_values={'assigned_driver_id': str(driver.id)}
            )
            
            logger.info(f"Driver {driver_id} assigned to truck {truck_id}")
            return truck
        except (FleetTruck.DoesNotExist, FleetDriver.DoesNotExist) as e:
            raise ValidationError(f"Truck or driver not found: {str(e)}")
    
    @staticmethod
    def update_telemetry(telematics_id, latitude, longitude, fuel_delta=0, odometer_delta=0):
        """Update truck telemetry (from GPS/telematics)"""
        try:
            truck = FleetTruck.objects.get(telematics_id=telematics_id)
            truck.last_latitude = latitude
            truck.last_longitude = longitude
            truck.last_location_ts = timezone.now()
            truck.is_moving = True
            
            if fuel_delta > 0:
                truck.fuel_consumed_liters += fuel_delta
            if odometer_delta > 0:
                truck.odometer_km += odometer_delta
                truck.kilometers_travelled_km += odometer_delta
            
            truck.save()
            
            logger.info(f"Truck {truck_id} telemetry updated: lat={latitude}, lng={longitude}")
        except FleetTruck.DoesNotExist:
            logger.warn(f"Truck with telematics_id {telematics_id} not found")

# ============================================================
# MISSION SERVICE
# ============================================================

class MissionService:
    """Service layer for mission operations"""
    
    @staticmethod
    def create_mission(fleet_id, mission_number, truck_id, driver_id, origin, destination,
                      stops=None, priority='normal', cargo=None, route_polyline=None, 
                      distance_total_m=0, admin_id=None, status=None, progress_pct=0, current_location=None):
        """Create new mission with stops"""
        try:
            with transaction.atomic():
                # Use provided status or default to PLANNED
                mission_status = status if status else MissionStatus.PLANNED
                
                mission = FleetMission.objects.create(
                    fleet_id=fleet_id,
                    mission_number=mission_number,
                    truck_id=truck_id,
                    driver_id=driver_id,
                    origin=origin,
                    destination=destination,
                    current_location=current_location,
                    status=mission_status,
                    priority=priority,
                    cargo=cargo or {},
                    route_polyline=route_polyline,
                    distance_total_m=distance_total_m,
                    progress_pct=progress_pct,
                    created_by_admin_id=admin_id
                )
                
                # Create mission stops if provided
                if stops:
                    for idx, stop in enumerate(stops, 1):
                        FleetMissionStop.objects.create(
                            mission=mission,
                            stop_order=idx,
                            address=stop.get('address'),
                            latitude=stop.get('latitude'),
                            longitude=stop.get('longitude')
                        )
                
                # Log event
                FleetMissionEvent.objects.create(
                    mission=mission,
                    event_type=MissionEventType.STATUS_CHANGED,
                    payload={'status': mission_status}
                )
                
                # Log audit
                if admin_id:
                    FleetAdminAuditLog.objects.create(
                        admin_id=admin_id,
                        action='CREATE',
                        resource_type='Mission',
                        resource_id=mission.id,
                        new_values={'mission_number': mission_number, 'status': MissionStatus.PLANNED}
                    )
                
                logger.info(f"Mission created: {mission.id} ({mission_number}) with {len(stops)} stops")
                return mission
        except Exception as e:
            logger.error(f"Failed to create mission: {e}")
            raise ValidationError(f"Failed to create mission: {str(e)}")
    
    @staticmethod
    def get_mission(mission_id):
        """Get mission by ID"""
        return FleetMission.objects.filter(id=mission_id).first()
    
    @staticmethod
    def list_missions(fleet_id, status=None, truck_id=None, driver_id=None):
        """List missions with optional filters"""
        qs = FleetMission.objects.filter(fleet_id=fleet_id)
        if status:
            qs = qs.filter(status=status)
        if truck_id:
            qs = qs.filter(truck_id=truck_id)
        if driver_id:
            qs = qs.filter(driver_id=driver_id)
        return qs
    
    @staticmethod
    def assign_mission(mission_id, truck_id=None, driver_id=None, admin_id=None):
        """Assign truck/driver to mission"""
        try:
            mission = FleetMission.objects.get(id=mission_id)
            
            if mission.status != MissionStatus.PLANNED:
                raise ValidationError(f"Cannot assign mission in {mission.status} status")
            
            if truck_id:
                mission.truck_id = truck_id
            if driver_id:
                mission.driver_id = driver_id
            
            mission.status = MissionStatus.ASSIGNED
            mission.save()
            
            FleetMissionEvent.objects.create(
                mission=mission,
                event_type=MissionEventType.STATUS_CHANGED,
                payload={'old_status': MissionStatus.PLANNED, 'new_status': MissionStatus.ASSIGNED}
            )
            
            logger.info(f"Mission {mission_id} assigned")
            return mission
        except FleetMission.DoesNotExist:
            raise ValidationError(f"Mission {mission_id} not found")
    
    @staticmethod
    def start_mission(mission_id, admin_id=None):
        """Start mission (change status to ENROUTE)"""
        try:
            mission = FleetMission.objects.get(id=mission_id)
            
            if mission.status != MissionStatus.ASSIGNED:
                raise ValidationError(f"Cannot start mission in {mission.status} status")
            
            mission.status = MissionStatus.ENROUTE
            mission.started_at = timezone.now()
            mission.save()
            
            FleetMissionEvent.objects.create(
                mission=mission,
                event_type=MissionEventType.STATUS_CHANGED,
                payload={'old_status': MissionStatus.ASSIGNED, 'new_status': MissionStatus.ENROUTE}
            )
            
            logger.info(f"Mission {mission_id} started")
            return mission
        except FleetMission.DoesNotExist:
            raise ValidationError(f"Mission {mission_id} not found")
    
    @staticmethod
    def complete_stop(mission_id, stop_order, admin_id=None):
        """Mark mission stop as completed"""
        try:
            stop = FleetMissionStop.objects.get(mission_id=mission_id, stop_order=stop_order)
            stop.status = MissionStopStatus.COMPLETED
            stop.arrived_at = stop.arrived_at or timezone.now()
            stop.departed_at = timezone.now()
            stop.save()
            
            mission = FleetMission.objects.get(id=mission_id)
            FleetMissionEvent.objects.create(
                mission=mission,
                event_type=MissionEventType.STOP_COMPLETED,
                payload={'stop_order': stop_order, 'address': stop.address}
            )
            
            # Update mission progress
            total_stops = mission.stops_detail.count()
            completed_stops = mission.stops_detail.filter(status=MissionStopStatus.COMPLETED).count()
            mission.progress_pct = (completed_stops / total_stops * 100) if total_stops > 0 else 0
            mission.save()
            
            logger.info(f"Mission {mission_id} stop {stop_order} completed")
        except FleetMissionStop.DoesNotExist:
            raise ValidationError(f"Stop {stop_order} not found in mission {mission_id}")
    
    @staticmethod
    def complete_mission(mission_id, admin_id=None):
        """Complete mission"""
        try:
            mission = FleetMission.objects.get(id=mission_id)
            
            mission.status = MissionStatus.COMPLETED
            mission.completed_at = timezone.now()
            mission.progress_pct = 100
            mission.distance_remaining_m = 0
            mission.save()
            
            FleetMissionEvent.objects.create(
                mission=mission,
                event_type=MissionEventType.STATUS_CHANGED,
                payload={'old_status': MissionStatus.ENROUTE, 'new_status': MissionStatus.COMPLETED}
            )
            
            # Update driver deliveries
            if mission.driver_id:
                DriverService._update_driver_deliveries(mission.driver_id)
            
            logger.info(f"Mission {mission_id} completed")
            return mission
        except FleetMission.DoesNotExist:
            raise ValidationError(f"Mission {mission_id} not found")
    
    @staticmethod
    def update_mission_progress(mission_id, latitude, longitude):
        """Update mission progress from telemetry"""
        try:
            mission = FleetMission.objects.get(id=mission_id)
            mission.current_location = {'latitude': float(latitude), 'longitude': float(longitude)}
            mission.save()
            
            FleetMissionEvent.objects.create(
                mission=mission,
                event_type=MissionEventType.LOCATION_UPDATED,
                payload={'latitude': float(latitude), 'longitude': float(longitude)}
            )
        except FleetMission.DoesNotExist:
            logger.warn(f"Mission {mission_id} not found for progress update")

# ============================================================
# DISPUTE SERVICE
# ============================================================

class DisputeService:
    """Service layer for dispute operations"""
    
    @staticmethod
    def file_dispute(mission_id, driver_id, dispute_type, description, photo_url=None, stop_id=None):
        """File new dispute (driver only)"""
        try:
            mission = FleetMission.objects.get(id=mission_id)
            
            dispute = FleetMissionDispute.objects.create(
                mission=mission,
                driver_id=driver_id,
                stop_id=stop_id,
                dispute_type=dispute_type,
                description=description,
                photo_url=photo_url,
                status=DisputeStatus.OPEN
            )
            
            FleetMissionEvent.objects.create(
                mission=mission,
                driver_id=driver_id,
                event_type=MissionEventType.DISPUTE_FILED,
                payload={'dispute_type': dispute_type, 'description': description}
            )
            
            logger.info(f"Dispute filed: {dispute.id} for mission {mission_id}")
            return dispute
        except FleetMission.DoesNotExist:
            raise ValidationError(f"Mission {mission_id} not found")
    
    @staticmethod
    def resolve_dispute(dispute_id, resolution, admin_id):
        """Resolve dispute (admin only)"""
        try:
            dispute = FleetMissionDispute.objects.get(id=dispute_id)
            dispute.status = DisputeStatus.RESOLVED
            dispute.resolved_at = timezone.now()
            dispute.resolved_by_admin_id = admin_id
            dispute.save()
            
            FleetAdminAuditLog.objects.create(
                admin_id=admin_id,
                action='RESOLVE_DISPUTE',
                resource_type='Dispute',
                resource_id=dispute.id,
                new_values={'status': DisputeStatus.RESOLVED, 'resolution': resolution}
            )
            
            logger.info(f"Dispute {dispute_id} resolved")
            return dispute
        except FleetMissionDispute.DoesNotExist:
            raise ValidationError(f"Dispute {dispute_id} not found")

# ============================================================
# COMPUTED FIELDS WORKER
# ============================================================

class ComputedFieldsWorker:
    """Background worker for computing aggregated fields"""
    
    @staticmethod
    def update_all_driver_performance_marks():
        """Nightly job: update all drivers' performance marks from daily metrics (last 30 days)"""
        try:
            drivers = FleetDriver.objects.all()
            for driver in drivers:
                daily_metrics = FleetDriverPerformanceDaily.objects.filter(
                    driver=driver,
                    date__gte=timezone.now().date() - timezone.timedelta(days=30)
                )
                
                if not daily_metrics.exists():
                    continue
                
                # Weighted average: on_time(40%) + safety(30%) + efficiency(30%)
                avg_on_time = sum(m.on_time_count for m in daily_metrics) / max(len(daily_metrics), 1)
                avg_safety = sum(float(m.safety_score) for m in daily_metrics) / len(daily_metrics)
                avg_efficiency = sum(float(m.efficiency_score) for m in daily_metrics) / len(daily_metrics)
                
                performance_mark = (avg_on_time * 0.4 + avg_safety * 0.3 + avg_efficiency * 0.3)
                driver.performance_mark = min(100, max(0, performance_mark))
                driver.save()
            
            logger.info(f"Updated performance marks for {drivers.count()} drivers")
        except Exception as e:
            logger.error(f"Failed to update performance marks: {e}")
    
    @staticmethod
    def update_all_driver_deliveries():
        """Nightly job: update all drivers' deliveries count (last 30 days)"""
        try:
            drivers = FleetDriver.objects.all()
            for driver in drivers:
                DriverService._update_driver_deliveries(driver.id)
            
            logger.info(f"Updated deliveries for {drivers.count()} drivers")
        except Exception as e:
            logger.error(f"Failed to update deliveries: {e}")
    
    @staticmethod
    def update_active_mission_progress():
        """Frequent job (5-10 min): update all enroute missions' progress"""
        try:
            missions = FleetMission.objects.filter(status=MissionStatus.ENROUTE)
            for mission in missions:
                total_stops = mission.stops_detail.count()
                completed_stops = mission.stops_detail.filter(status=MissionStopStatus.COMPLETED).count()
                mission.progress_pct = (completed_stops / total_stops * 100) if total_stops > 0 else 0
                mission.distance_remaining_m = mission.distance_total_m * (1 - mission.progress_pct / 100)
                mission.save()
            
            logger.info(f"Updated progress for {missions.count()} active missions")
        except Exception as e:
            logger.error(f"Failed to update mission progress: {e}")
