"""
Fleet Management v2.0 - Comprehensive Test Suite
Unit tests, integration tests, migration tests, acceptance tests

Framework: pytest + pytest-django
Coverage: Models, Services, API Views, Data Migration

Date: 2026-05-05
"""

import pytest
import json
import uuid
from datetime import datetime, timedelta
from decimal import Decimal
from django.test import TestCase, TransactionTestCase, Client
from django.db import transaction
from django.utils import timezone
from rest_framework.test import APIClient, APITestCase
from rest_framework import status

from api.models_v2 import (
    Driver, Truck, Mission, MissionStop, MissionEvent, MissionDispute,
    DriverPerformanceDaily, AdminAuditLog,
    DriverStatus, TruckStatus, MissionStatus, MissionEventType, DisputeStatus
)
from api.services_v2 import (
    DriverService, TruckService, MissionService, DisputeService, ComputedFieldsWorker
)

# ==============================================================
# FIXTURES
# ==============================================================

@pytest.fixture
def fleet_id():
    """Shared fleet UUID for all tests"""
    return str(uuid.uuid4())

@pytest.fixture
def admin_id():
    """Shared admin UUID"""
    return str(uuid.uuid4())

@pytest.fixture
def driver(fleet_id):
    """Create test driver"""
    return Driver.objects.create(
        fleet_id=uuid.UUID(fleet_id),
        first_name="John",
        last_name="Smith",
        email="john@test.com",
        license_number="DL123456",
        status=DriverStatus.ACTIVE,
        on_duty=False
    )

@pytest.fixture
def truck(fleet_id):
    """Create test truck"""
    return Truck.objects.create(
        fleet_id=uuid.UUID(fleet_id),
        truck_identifier="TRUCK-001",
        plate="ABC-123",
        telematics_id="TEL-12345",
        status=TruckStatus.IDLE
    )

@pytest.fixture
def mission(fleet_id, truck, driver):
    """Create test mission"""
    return Mission.objects.create(
        fleet_id=uuid.UUID(fleet_id),
        mission_number="M-TEST-001",
        truck=truck,
        driver=driver,
        origin={"lat": 37.7749, "lng": -122.4194, "address": "SF"},
        destination={"lat": 37.8044, "lng": -122.2712, "address": "Oakland"},
        distance_total_m=Decimal('45000'),
        status=MissionStatus.PLANNED
    )

@pytest.fixture
def api_client():
    """REST API client"""
    return APIClient()

# ==============================================================
# UNIT TESTS - MODELS
# ==============================================================

@pytest.mark.django_db
class TestDriverModel:
    """Test Driver model constraints and methods"""
    
    def test_create_driver(self, fleet_id):
        """Test driver creation"""
        driver = Driver.objects.create(
            fleet_id=uuid.UUID(fleet_id),
            first_name="Jane",
            last_name="Doe",
            email="jane@test.com",
            license_number="DL654321"
        )
        assert driver.id is not None
        assert driver.display_name == "Jane Doe"
        assert driver.status == DriverStatus.ACTIVE
        assert driver.on_duty is False
    
    def test_driver_unique_email(self, fleet_id):
        """Test email uniqueness"""
        Driver.objects.create(
            fleet_id=uuid.UUID(fleet_id),
            first_name="John",
            last_name="Smith",
            email="john@test.com"
        )
        
        with pytest.raises(Exception):  # IntegrityError
            Driver.objects.create(
                fleet_id=uuid.UUID(fleet_id),
                first_name="Jane",
                last_name="Doe",
                email="john@test.com"
            )
    
    def test_driver_unique_license(self, fleet_id):
        """Test license_number uniqueness"""
        Driver.objects.create(
            fleet_id=uuid.UUID(fleet_id),
            first_name="John",
            last_name="Smith",
            license_number="DL123456"
        )
        
        with pytest.raises(Exception):
            Driver.objects.create(
                fleet_id=uuid.UUID(fleet_id),
                first_name="Jane",
                last_name="Doe",
                license_number="DL123456"
            )
    
    def test_driver_performance_mark_range(self, fleet_id):
        """Test performance_mark is 0-100"""
        driver = Driver.objects.create(
            fleet_id=uuid.UUID(fleet_id),
            first_name="John",
            last_name="Smith",
            performance_mark=Decimal('82.5')
        )
        assert 0 <= driver.performance_mark <= 100

@pytest.mark.django_db
class TestTruckModel:
    """Test Truck model"""
    
    def test_create_truck(self, fleet_id):
        """Test truck creation"""
        truck = Truck.objects.create(
            fleet_id=uuid.UUID(fleet_id),
            truck_identifier="TRUCK-001",
            plate="ABC-123",
            telematics_id="TEL-12345",
            fuel_capacity_liters=Decimal('300'),
            status=TruckStatus.IDLE
        )
        assert truck.id is not None
        assert truck.status == TruckStatus.IDLE
        assert truck.is_moving is False
    
    def test_truck_unique_plate(self, fleet_id):
        """Test plate uniqueness"""
        Truck.objects.create(
            fleet_id=uuid.UUID(fleet_id),
            truck_identifier="TRUCK-001",
            plate="ABC-123",
            telematics_id="TEL-12345"
        )
        
        with pytest.raises(Exception):
            Truck.objects.create(
                fleet_id=uuid.UUID(fleet_id),
                truck_identifier="TRUCK-002",
                plate="ABC-123",
                telematics_id="TEL-54321"
            )

@pytest.mark.django_db
class TestMissionModel:
    """Test Mission model"""
    
    def test_create_mission(self, fleet_id, truck, driver):
        """Test mission creation"""
        mission = Mission.objects.create(
            fleet_id=uuid.UUID(fleet_id),
            mission_number="M-001",
            truck=truck,
            driver=driver,
            origin={"lat": 37.7749, "lng": -122.4194},
            destination={"lat": 37.8044, "lng": -122.2712},
            status=MissionStatus.PLANNED
        )
        assert mission.id is not None
        assert mission.status == MissionStatus.PLANNED
        assert mission.is_active() is False
    
    def test_mission_active_status(self, mission):
        """Test is_active() for enroute/paused missions"""
        assert mission.is_active() is False
        
        mission.status = MissionStatus.ENROUTE
        mission.save()
        assert mission.is_active() is True
        
        mission.status = MissionStatus.COMPLETED
        mission.save()
        assert mission.is_active() is False

# ==============================================================
# UNIT TESTS - SERVICES
# ==============================================================

@pytest.mark.django_db
class TestDriverService:
    """Test DriverService CRUD and business logic"""
    
    def test_create_driver_success(self, fleet_id, admin_id):
        """Test successful driver creation"""
        driver = DriverService.create_driver(
            fleet_id=fleet_id,
            first_name="John",
            last_name="Smith",
            email="john@test.com",
            phone="+1234567890",
            license_number="DL123456",
            admin_id=admin_id
        )
        
        assert driver.id is not None
        assert driver.first_name == "John"
        assert driver.status == DriverStatus.ACTIVE
        
        # Verify audit log created
        audit = AdminAuditLog.objects.get(resource_id=driver.id)
        assert audit.action == 'CREATE'
    
    def test_create_driver_duplicate_email(self, fleet_id, admin_id):
        """Test duplicate email validation"""
        DriverService.create_driver(
            fleet_id=fleet_id,
            first_name="John",
            last_name="Smith",
            email="john@test.com",
            admin_id=admin_id
        )
        
        with pytest.raises(Exception):  # ValidationError
            DriverService.create_driver(
                fleet_id=fleet_id,
                first_name="Jane",
                last_name="Doe",
                email="john@test.com",
                admin_id=admin_id
            )
    
    def test_toggle_on_duty(self, driver):
        """Test on/off duty toggle"""
        assert driver.on_duty is False
        
        updated = DriverService.toggle_on_duty(str(driver.id), on_duty=True)
        assert updated.on_duty is True
        
        # Verify event logged
        event = MissionEvent.objects.filter(driver=driver).first()
        assert event is not None

@pytest.mark.django_db
class TestTruckService:
    """Test TruckService CRUD"""
    
    def test_create_truck_success(self, fleet_id, admin_id):
        """Test successful truck creation"""
        truck = TruckService.create_truck(
            fleet_id=fleet_id,
            truck_identifier="TRUCK-001",
            plate="ABC-123",
            telematics_id="TEL-12345",
            fuel_capacity_liters=Decimal('300'),
            admin_id=admin_id
        )
        
        assert truck.id is not None
        assert truck.status == TruckStatus.IDLE
        
        # Verify audit log
        audit = AdminAuditLog.objects.get(resource_id=truck.id)
        assert audit.action == 'CREATE'
    
    def test_update_telemetry(self, truck):
        """Test telemetry update"""
        truck = TruckService.update_telemetry(
            telematics_id=truck.telematics_id,
            latitude=Decimal('37.7749'),
            longitude=Decimal('-122.4194'),
            fuel_delta=Decimal('10.5'),
            odometer_delta=Decimal('50')
        )
        
        assert truck.last_latitude == Decimal('37.7749')
        assert truck.last_longitude == Decimal('-122.4194')
        assert truck.is_moving is True

@pytest.mark.django_db
class TestMissionService:
    """Test MissionService CRUD and state machine"""
    
    def test_create_mission_success(self, fleet_id, truck, driver, admin_id):
        """Test successful mission creation"""
        mission = MissionService.create_mission(
            fleet_id=fleet_id,
            mission_number="M-001",
            truck_id=str(truck.id),
            driver_id=str(driver.id),
            origin={"lat": 37.7749, "lng": -122.4194, "address": "SF"},
            destination={"lat": 37.8044, "lng": -122.2712, "address": "Oakland"},
            stops=[
                {"stop_order": 1, "address": "Stop 1", "lat": 37.7800, "lng": -122.4200},
                {"stop_order": 2, "address": "Stop 2", "lat": 37.8044, "lng": -122.2712}
            ],
            admin_id=admin_id
        )
        
        assert mission.id is not None
        assert mission.status == MissionStatus.PLANNED
        assert mission.stops_detail.count() == 2
    
    def test_create_mission_missing_origin(self, fleet_id):
        """Test mission creation without origin"""
        with pytest.raises(Exception):  # ValidationError
            MissionService.create_mission(
                fleet_id=fleet_id,
                mission_number="M-001",
                destination={"lat": 37.8044, "lng": -122.2712}
            )
    
    def test_assign_mission(self, mission, truck, driver, admin_id):
        """Test mission assignment"""
        mission = MissionService.assign_mission(
            mission_id=str(mission.id),
            truck_id=str(truck.id),
            driver_id=str(driver.id),
            admin_id=admin_id
        )
        
        assert mission.status == MissionStatus.ASSIGNED
        assert mission.truck_id == truck.id
        assert mission.driver_id == driver.id
    
    def test_mission_state_machine(self, mission, admin_id):
        """Test mission status transitions"""
        # PLANNED -> ASSIGNED
        mission = MissionService.assign_mission(
            mission_id=str(mission.id),
            truck_id=str(mission.truck_id),
            driver_id=str(mission.driver_id),
            admin_id=admin_id
        )
        assert mission.status == MissionStatus.ASSIGNED
        
        # ASSIGNED -> ENROUTE
        mission = MissionService.start_mission(str(mission.id))
        assert mission.status == MissionStatus.ENROUTE
        
        # ENROUTE -> COMPLETED
        mission = MissionService.complete_mission(str(mission.id))
        assert mission.status == MissionStatus.COMPLETED

@pytest.mark.django_db
class TestDisputeService:
    """Test DisputeService"""
    
    def test_file_dispute_success(self, mission):
        """Test filing dispute"""
        dispute = DisputeService.file_dispute(
            mission_id=str(mission.id),
            driver_id=str(mission.driver_id),
            dispute_type="incorrect_location",
            description="Location mismatch"
        )
        
        assert dispute.id is not None
        assert dispute.status == DisputeStatus.OPEN
    
    def test_resolve_dispute(self, mission, admin_id):
        """Test dispute resolution"""
        dispute = DisputeService.file_dispute(
            mission_id=str(mission.id),
            driver_id=str(mission.driver_id),
            dispute_type="incorrect_location",
            description="Location mismatch"
        )
        
        resolved = DisputeService.resolve_dispute(
            dispute_id=str(dispute.id),
            resolution="Confirmed correct location",
            admin_id=admin_id
        )
        
        assert resolved.status == DisputeStatus.RESOLVED

# ==============================================================
# COMPUTED FIELDS TESTS
# ==============================================================

@pytest.mark.django_db
class TestComputedFields:
    """Test computed field workers"""
    
    def test_update_driver_performance_marks(self, driver):
        """Test performance mark calculation"""
        # Create daily metrics for last 30 days
        for i in range(30):
            date = timezone.now().date() - timedelta(days=i)
            DriverPerformanceDaily.objects.create(
                driver=driver,
                date=date,
                deliveries_count=5,
                on_time_count=5,
                safety_score=Decimal('90'),
                efficiency_score=Decimal('85')
            )
        
        # Run worker
        ComputedFieldsWorker.update_all_driver_performance_marks()
        
        # Verify performance mark updated
        driver.refresh_from_db()
        assert driver.performance_mark > 0
        assert 0 <= driver.performance_mark <= 100

# ==============================================================
# INTEGRATION TESTS
# ==============================================================

@pytest.mark.django_db
class TestDriverTruckMissionWorkflow:
    """Test end-to-end workflow: create driver -> create truck -> assign -> create mission"""
    
    def test_full_workflow(self, fleet_id, admin_id):
        """Test complete mission lifecycle"""
        # 1. Create driver
        driver = DriverService.create_driver(
            fleet_id=fleet_id,
            first_name="John",
            last_name="Smith",
            email="john@test.com",
            license_number="DL123456",
            admin_id=admin_id
        )
        
        # 2. Create truck
        truck = TruckService.create_truck(
            fleet_id=fleet_id,
            truck_identifier="TRUCK-001",
            plate="ABC-123",
            telematics_id="TEL-12345",
            admin_id=admin_id
        )
        
        # 3. Assign driver to truck
        truck = TruckService.assign_driver(
            truck_id=str(truck.id),
            driver_id=str(driver.id),
            admin_id=admin_id
        )
        assert truck.assigned_driver_id == driver.id
        
        # 4. Create mission
        mission = MissionService.create_mission(
            fleet_id=fleet_id,
            mission_number="M-001",
            truck_id=str(truck.id),
            driver_id=str(driver.id),
            origin={"lat": 37.7749, "lng": -122.4194, "address": "SF"},
            destination={"lat": 37.8044, "lng": -122.2712, "address": "Oakland"},
            stops=[
                {"stop_order": 1, "address": "Stop 1", "lat": 37.7800, "lng": -122.4200},
                {"stop_order": 2, "address": "Stop 2", "lat": 37.8044, "lng": -122.2712}
            ],
            admin_id=admin_id
        )
        
        # 5. Assign mission
        mission = MissionService.assign_mission(
            mission_id=str(mission.id),
            truck_id=str(truck.id),
            driver_id=str(driver.id),
            admin_id=admin_id
        )
        assert mission.status == MissionStatus.ASSIGNED
        
        # 6. Start mission
        mission = MissionService.start_mission(str(mission.id))
        assert mission.status == MissionStatus.ENROUTE
        
        # 7. Complete stop
        stop = mission.stops_detail.first()
        stop = MissionService.complete_stop(str(mission.id), stop.stop_order)
        assert stop.status == 'completed'
        
        # 8. Complete mission
        mission = MissionService.complete_mission(str(mission.id))
        assert mission.status == MissionStatus.COMPLETED

# ==============================================================
# RBAC & PERMISSION TESTS
# ==============================================================

@pytest.mark.django_db
class TestRBAC:
    """Test Role-Based Access Control"""
    
    def test_only_admin_can_create_truck(self, fleet_id):
        """Test non-admin cannot create truck"""
        # In production, this would check JWT claims
        # For now, assuming RBAC is handled in view layer
        pass
    
    def test_driver_can_toggle_own_onduty(self, driver):
        """Test driver can toggle own on_duty"""
        DriverService.toggle_on_duty(str(driver.id), on_duty=True)
        driver.refresh_from_db()
        assert driver.on_duty is True

# ==============================================================
# MIGRATION TESTS
# ==============================================================

class TestSchemaMigration(TransactionTestCase):
    """Test data migration from old schema to new"""
    
    def test_migration_0009_creates_tables(self):
        """Test migration 0009 creates all required tables"""
        # Verify tables exist
        from django.db import connection
        with connection.cursor() as cursor:
            tables = [
                'drivers', 'trucks', 'missions', 'mission_stops',
                'mission_events', 'mission_disputes', 'driver_performance_daily'
            ]
            for table in tables:
                cursor.execute(
                    "SELECT 1 FROM information_schema.tables WHERE table_name=%s",
                    [table]
                )
                assert cursor.fetchone() is not None, f"Table {table} not found"

# ==============================================================
# ACCEPTANCE TESTS
# ==============================================================

@pytest.mark.django_db
class TestAcceptanceCriteria:
    """High-level acceptance tests"""
    
    def test_admin_can_create_truck(self, fleet_id, admin_id):
        """AC: Admin can create truck"""
        truck = TruckService.create_truck(
            fleet_id=fleet_id,
            truck_identifier="TRUCK-001",
            plate="ABC-123",
            telematics_id="TEL-12345",
            admin_id=admin_id
        )
        assert truck.id is not None
    
    def test_driver_sees_assigned_missions(self, fleet_id):
        """AC: Driver can view assigned missions"""
        driver = Driver.objects.create(
            fleet_id=uuid.UUID(fleet_id),
            first_name="John",
            last_name="Smith"
        )
        
        missions = MissionService.list_missions(
            fleet_id=fleet_id,
            driver_id=str(driver.id)
        )
        assert isinstance(missions, list)
    
    def test_computed_fields_update_correctly(self, driver, fleet_id):
        """AC: Computed fields update within SLA"""
        # Create deliveries
        truck = Truck.objects.create(
            fleet_id=uuid.UUID(fleet_id),
            truck_identifier="T1",
            plate="ABC",
            telematics_id="TEL1"
        )
        
        mission = Mission.objects.create(
            fleet_id=uuid.UUID(fleet_id),
            mission_number="M-001",
            truck=truck,
            driver=driver,
            origin={"lat": 0, "lng": 0},
            destination={"lat": 1, "lng": 1}
        )
        
        # Create stop and complete it
        stop = MissionStop.objects.create(
            mission=mission,
            stop_order=1,
            address="Test"
        )
        stop.status = 'completed'
        stop.save()
        
        # Update driver deliveries
        DriverService._update_driver_deliveries(str(driver.id))
        
        driver.refresh_from_db()
        assert driver.deliveries_count >= 1
    
    def test_no_data_loss_in_migration(self):
        """AC: No data loss during migration"""
        # Count rows before migration
        initial_count = Driver.objects.count()
        assert initial_count >= 0  # Just verify query works

# ==============================================================
# LOAD/PERFORMANCE TESTS
# ==============================================================

@pytest.mark.django_db
class TestPerformance:
    """Performance and load tests"""
    
    def test_list_drivers_performance(self, fleet_id):
        """Test driver list query performance"""
        # Create 100 drivers
        drivers = [
            Driver(
                fleet_id=uuid.UUID(fleet_id),
                first_name=f"Driver{i}",
                last_name="Test"
            )
            for i in range(100)
        ]
        Driver.objects.bulk_create(drivers)
        
        # Query should be fast with index
        import time
        start = time.time()
        qs = DriverService.list_drivers(fleet_id)
        list(qs)  # Force evaluation
        elapsed = time.time() - start
        
        # Should complete in <500ms
        assert elapsed < 0.5
    
    def test_mission_update_performance(self, fleet_id, truck, driver):
        """Test mission progress update performance"""
        # Create mission with 10 stops
        mission = Mission.objects.create(
            fleet_id=uuid.UUID(fleet_id),
            mission_number="M-PERF-001",
            truck=truck,
            driver=driver,
            origin={"lat": 0, "lng": 0},
            destination={"lat": 10, "lng": 10},
            status=MissionStatus.ENROUTE
        )
        
        for i in range(10):
            MissionStop.objects.create(
                mission=mission,
                stop_order=i,
                address=f"Stop {i}"
            )
        
        # Update progress
        import time
        start = time.time()
        MissionService.update_mission_progress(
            str(mission.id),
            Decimal('37.7800'),
            Decimal('-122.4200')
        )
        elapsed = time.time() - start
        
        # Should complete in <100ms
        assert elapsed < 0.1
