# Fleet Management v2.0 - Quick Start Guide

## Getting Started

### 1. Start the Development Server
```bash
cd server
py -3.14 manage.py runserver 127.0.0.1:8001
```

The API will be available at: `http://127.0.0.1:8001/api/v1/`

### 2. API Authentication
All v1 endpoints require authentication. You can:
- Use a Token from Django admin
- Pass `Authorization: Token <token>` header in requests
- Create a superuser for admin access

```bash
py -3.14 manage.py createsuperuser
```

## Core Endpoints

### Drivers
```
GET    /api/v1/drivers/                    # List all drivers
POST   /api/v1/drivers/                    # Create new driver
GET    /api/v1/drivers/{id}/               # Get driver details
PATCH  /api/v1/drivers/{id}/               # Update driver
DELETE /api/v1/drivers/{id}/               # Delete driver
POST   /api/v1/drivers/{id}/on-duty-toggle/ # Toggle on-duty status
```

### Trucks
```
GET    /api/v1/trucks/                     # List all trucks
POST   /api/v1/trucks/                     # Create new truck
GET    /api/v1/trucks/{id}/                # Get truck details
PATCH  /api/v1/trucks/{id}/                # Update truck
DELETE /api/v1/trucks/{id}/                # Delete truck
PATCH  /api/v1/trucks/{id}/assign/         # Assign driver
```

### Missions
```
GET    /api/v1/missions/                   # List all missions
POST   /api/v1/missions/                   # Create new mission
GET    /api/v1/missions/{id}/              # Get mission details
PATCH  /api/v1/missions/{id}/              # Update mission
DELETE /api/v1/missions/{id}/              # Delete mission
PATCH  /api/v1/missions/{id}/status/       # Change mission status
PATCH  /api/v1/missions/{id}/stops/{stop_id}/ # Complete mission stop
```

### Disputes
```
GET    /api/v1/disputes/                   # List all disputes
POST   /api/v1/disputes/                   # File new dispute
GET    /api/v1/disputes/{id}/              # Get dispute details
PATCH  /api/v1/disputes/{id}/resolve/      # Resolve dispute
```

### Performance Metrics
```
GET    /api/v1/performance/                # List driver performance
GET    /api/v1/performance/{id}/           # Get specific performance record
```

## Common Queries

### List Active Drivers
```bash
curl -H "Authorization: Token <token>" \
  "http://127.0.0.1:8001/api/v1/drivers/?fleet_id=<fleet_id>&status=ACTIVE"
```

### Search for Driver by Name
```bash
curl -H "Authorization: Token <token>" \
  "http://127.0.0.1:8001/api/v1/drivers/?search=john"
```

### List Enroute Missions
```bash
curl -H "Authorization: Token <token>" \
  "http://127.0.0.1:8001/api/v1/missions/?fleet_id=<fleet_id>&status=ENROUTE"
```

### Filter Trucks by Status
```bash
curl -H "Authorization: Token <token>" \
  "http://127.0.0.1:8001/api/v1/trucks/?fleet_id=<fleet_id>&status=IDLE"
```

## Data Models

### Fleet Driver
```
Fields:
- id (UUID)
- fleet_id (UUID)
- first_name (string)
- last_name (string)
- email (string, unique)
- phone (string)
- license_number (string, unique)
- hire_date (date)
- status (ACTIVE, SUSPENDED, TERMINATED, ON_LEAVE)
- on_duty (boolean)
- performance_mark (0-100)
- deliveries_count (integer)
- last_active_at (datetime)
```

### Fleet Truck
```
Fields:
- id (UUID)
- fleet_id (UUID)
- truck_identifier (string, unique)
- plate (string, unique)
- telematics_id (string, unique)
- make (string)
- model (string)
- year (integer)
- fuel_capacity_liters (decimal)
- fuel_consumed_liters (decimal)
- odometer_km (decimal)
- kilometers_travelled_km (decimal)
- status (IDLE, ENROUTE, MAINTENANCE, DECOMMISSIONED)
- is_moving (boolean)
- last_latitude (decimal)
- last_longitude (decimal)
- assigned_driver (FK → Driver)
```

### Fleet Mission
```
Fields:
- id (UUID)
- fleet_id (UUID)
- mission_number (string, unique)
- status (PLANNED, ASSIGNED, ENROUTE, PAUSED, COMPLETED, CANCELLED)
- priority (LOW, NORMAL, HIGH, URGENT)
- truck (FK → Truck)
- driver (FK → Driver)
- origin (JSON)
- destination (JSON)
- current_location (JSON)
- route_polyline (text)
- distance_total_m (decimal)
- distance_remaining_m (decimal)
- progress_pct (0-100)
- cargo (JSON)
- stops (JSON list)
- created_at (datetime)
- started_at (datetime)
- completed_at (datetime)
```

## Service Layer Usage

### Creating a Driver (Backend)
```python
from api.services_v2 import DriverService

driver = DriverService.create_driver(
    fleet_id='<uuid>',
    first_name='John',
    last_name='Doe',
    email='john@example.com',
    license_number='DL123456',
    admin_id='<admin_uuid>'
)
```

### Creating a Mission (Backend)
```python
from api.services_v2 import MissionService

mission = MissionService.create_mission(
    fleet_id='<uuid>',
    mission_number='MISSION-001',
    truck_id='<truck_uuid>',
    driver_id='<driver_uuid>',
    origin={'latitude': -17.825, 'longitude': 31.033},
    destination={'latitude': -17.825, 'longitude': 31.050},
    stops=[
        {'address': 'Stop 1', 'latitude': -17.825, 'longitude': 31.033},
        {'address': 'Stop 2', 'latitude': -17.825, 'longitude': 31.050}
    ],
    admin_id='<admin_uuid>'
)
```

### Completing a Stop (Backend)
```python
from api.services_v2 import MissionService

MissionService.complete_stop(
    mission_id='<mission_uuid>',
    stop_order=1,
    admin_id='<admin_uuid>'
)
```

## Frontend Integration (React)

### Fetch Drivers
```javascript
async function fetchDrivers(fleetId, token) {
    const response = await fetch(
        `/api/v1/drivers/?fleet_id=${fleetId}`,
        { headers: { Authorization: `Token ${token}` } }
    );
    return response.json();
}
```

### Create Mission
```javascript
async function createMission(missionData, token) {
    const response = await fetch(
        '/api/v1/missions/',
        {
            method: 'POST',
            headers: { 
                Authorization: `Token ${token}`,
                'Content-Type': 'application/json'
            },
            body: JSON.stringify(missionData)
        }
    );
    return response.json();
}
```

### Update Mission Status
```javascript
async function updateMissionStatus(missionId, newStatus, token) {
    const response = await fetch(
        `/api/v1/missions/${missionId}/status/`,
        {
            method: 'PATCH',
            headers: { 
                Authorization: `Token ${token}`,
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({ status: newStatus })
        }
    );
    return response.json();
}
```

## Database Management

### View Existing Migrations
```bash
py -3.14 manage.py showmigrations api
```

### Create New Migration
```bash
py -3.14 manage.py makemigrations api
```

### Apply Migrations
```bash
py -3.14 manage.py migrate api
```

### Reset Database (Development Only)
```bash
rm db.sqlite3
py -3.14 manage.py migrate
```

## Testing

### Check System Health
```bash
py -3.14 manage.py check
```

### Access Admin Interface
```
http://127.0.0.1:8001/admin/
```
Username: (from createsuperuser)  
Password: (from createsuperuser)

### View Logs
```bash
tail -f server/logs/app.log  # if logging configured
```

## Troubleshooting

### Authentication Errors (403)
- Ensure you have an active token
- Pass token in `Authorization: Token <token>` header
- Check token hasn't expired

### Object Not Found (404)
- Verify ID is correct UUID format
- Check object belongs to same fleet_id
- Ensure object hasn't been deleted

### Invalid Data (400)
- Check field types and constraints
- Required fields: fleet_id, first_name (driver), truck_identifier (truck), mission_number (mission)
- Ensure unique fields aren't duplicated

### Database Errors
- Run `py -3.14 manage.py migrate` to apply pending migrations
- Check SQLite file has write permissions
- Verify database path in settings.py

## Performance Tips

1. **Use Filtering:** Always filter by fleet_id to reduce data
2. **Search Sparingly:** Searching on multiple fields is slower
3. **Pagination:** Default is 20 items per page
4. **Caching:** API responses are cacheable with ETag headers
5. **Batch Operations:** Use bulk_create for multiple objects

## File Locations

- **Models:** `server/api/models_v2.py`
- **ViewSets:** `server/api/views_v2.py`
- **Services:** `server/api/services_v2.py`
- **Routes:** `server/api/urls.py`
- **Database:** `server/db.sqlite3`
- **Migrations:** `server/api/migrations/`

## Next Steps

1. Create React admin UI components
2. Integrate with mobile app driver interface
3. Set up real-time updates (WebSocket)
4. Implement background job scheduler
5. Deploy to production (PostgreSQL)

---

For detailed API documentation, see: `IMPLEMENTATION_STATUS_V2.md`  
For model details, see: `server/api/models_v2.py`  
For service documentation, see: `server/api/services_v2.py`
