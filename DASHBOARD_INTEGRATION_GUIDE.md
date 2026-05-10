# Dashboard Data Integration Guide

## Overview
The admin dashboard is now fully integrated with backend services that aggregate data from the drivers, trucks, and missions tables. This document explains the new data flow and how to implement it in the main dashboard.

---

## Architecture

### Data Flow
```
Missions Table → Dashboard Service Functions → API Endpoints → Frontend Components
      ↓                        ↓                      ↓                ↓
- current_location      - Calculations          - REST API         - KPI Cards
- status               - Aggregation            - JSON responses   - Tables
- distance_total_m     - Performance Points     - Real-time data   - Charts
- distance_remaining_m - Fuel Consumption
```

---

## Backend Architecture

### 1. Dashboard Service (`dashboard_service.py`)

**Core Functions:**

#### Driver Performance Calculation
```python
calculate_driver_performance_points(driver_id)
- Returns: int (total performance points)
- Calculation:
  * 5 points per completed mission
  * 5 points for on-time delivery (completed_at <= ETA)
  * Updates FleetDriver.performance_mark field

recalculate_all_drivers_performance()
- Recalculates all drivers' performance
- Returns: dict {driver_id: points}
```

#### Truck Data Aggregation from Missions
```python
get_truck_location_from_missions(truck_id)
- Returns: {'lat': float, 'lon': float}
- Gets current_location from latest mission

get_truck_status_from_missions(truck_id)
- Returns: str (TruckStatus.ENROUTE or TruckStatus.IDLE)
- Logic: ENROUTE if active mission exists, else IDLE

calculate_truck_fuel_consumption(truck_id)
- Returns: {
    'fuel_consumed_liters': float,
    'distance_travelled_km': float,
    'fuel_rate_per_100km': 8.0,  // Default: typical truck consumption
    'estimated_consumption': float
  }
- Formula: (Total Distance in km) × (8 L/100km) / 100
- Recommendation: Use 8 L/100km as default, calibrate per truck

sync_truck_data_from_missions(truck_id)
- Updates truck's location, status, fuel consumption
- Returns: aggregated truck data object
```

#### Unified Dashboard Summary
```python
get_dashboard_summary()
- Returns: {
    'timestamp': ISO datetime,
    'drivers': {
      'total': int,
      'active': int,
      'avg_performance_points': float
    },
    'trucks': {
      'total': int,
      'active': int,
      'idle': int
    },
    'missions': {
      'total': int,
      'completed': int,
      'enroute': int,
      'on_time_deliveries': int,
      'on_time_rate_percent': float
    },
    'metrics': {
      'total_distance_km': float,
      'total_fuel_consumed_liters': float,
      'avg_fuel_consumption_per_100km': 8.0
    }
  }

get_drivers_with_performance()
- Returns: List of drivers with calculated performance points

get_trucks_with_mission_data()
- Returns: List of trucks with synced mission data

get_missions_with_details()
- Returns: List of missions with full details
```

### 2. API Endpoints

**Base URL:** `http://localhost:8000/api/v1`

#### Dashboard Summary
```
GET /dashboard/summary/
Returns: Complete dashboard metrics
Used by: Main dashboard KPI cards
```

#### Drivers with Performance
```
GET /dashboard/drivers/
Returns: [
  {
    'id': UUID,
    'name': 'Driver Name',
    'performance_points': int,
    'deliveries_count': int,
    'status': 'active',
    'on_duty': bool
  }
]
Used by: Admin dashboard drivers table
```

#### Trucks with Mission Data
```
GET /dashboard/trucks/
Returns: [
  {
    'id': UUID,
    'truck_identifier': 'TRK1',
    'status': 'enroute',
    'location': {'lat': float, 'lon': float},
    'fuel_consumed_liters': float,
    'distance_travelled_km': float,
    'fuel_percent': float
  }
]
Used by: Admin dashboard trucks table, Main dashboard truck list
```

#### Missions with Details
```
GET /dashboard/missions/
Returns: [
  {
    'id': UUID,
    'mission_number': 'M1',
    'driver': 'Driver Name',
    'truck': 'TRK1',
    'status': 'enroute',
    'progress': float,
    'origin': {'lat': float, 'lon': float},
    'destination': {'lat': float, 'lon': float},
    'current_location': {'lat': float, 'lon': float}
  }
]
Used by: Mission table, Map visualization
```

#### Recalculate Performance (Admin)
```
POST /dashboard/recalculate-performance/
Returns: {'status': 'success', 'results': {...}}
Trigger: Called after mission completion or periodically
```

#### Sync Truck Data (Admin)
```
POST /dashboard/sync-truck-data/
Body (optional): {'truck_id': 'uuid'}
Returns: Synced truck data
Trigger: Called periodically or on-demand
```

---

## Frontend Architecture

### New API Functions (`services/api.js`)

```javascript
// Fetch unified dashboard summary
getDashboardSummary() → Promise<object>

// Fetch drivers with performance points
getDashboardDrivers() → Promise<array>

// Fetch trucks with mission-synced data
getDashboardTrucks() → Promise<array>

// Fetch missions with full details
getDashboardMissions() → Promise<array>

// Trigger performance recalculation (admin)
recalculatePerformance() → Promise<object>

// Sync truck data from missions (admin)
syncTruckData(truckId = null) → Promise<object>
```

### Admin Dashboard Updates

**Tab 1: Drivers**
- Now displays `performance_points` (integer) instead of percentage
- Shows deliveries count
- Data sourced from `/dashboard/drivers/`
- Example: "45 pts" instead of "45%"

**Tab 2: Trucks**
- Location sourced from missions table (current_location)
- Status determined by active missions
- Fuel consumption calculated from distance
- Displays distance travelled
- Data sourced from `/dashboard/trucks/`

**Tab 3: Missions**
- Full mission details with driver/truck info
- Status from missions table
- Data sourced from `/dashboard/missions/`

---

## Implementation in Main Dashboard

### Step 1: Import Dashboard Functions
```javascript
import {
  getDashboardSummary,
  getDashboardDrivers,
  getDashboardTrucks,
  getDashboardMissions
} from '../services/api';
```

### Step 2: KPI Cards Update
```javascript
useEffect(() => {
  const fetchDashboardData = async () => {
    const summary = await getDashboardSummary();
    
    // Update KPI cards
    setActiveDrivers(summary.drivers.active);
    setAvgPerformance(summary.drivers.avg_performance_points);
    setOnTimeRate(summary.missions.on_time_rate_percent);
    setTotalDistance(summary.metrics.total_distance_km);
    setTotalFuel(summary.metrics.total_fuel_consumed_liters);
  };
  
  fetchDashboardData();
  // Call periodically: setInterval(fetchDashboardData, 30000);
}, []);
```

### Step 3: Truck Table Integration
```javascript
const trucks = await getDashboardTrucks();

// Map to existing truck display format
trucks.map(truck => ({
  id: truck.id,
  identifier: truck.truck_identifier,
  status: truck.status,
  location: truck.location,
  fuel: truck.fuel_consumed_liters,
  distance: truck.distance_travelled_km,
  fuelPercent: truck.fuel_percent
}))
```

### Step 4: Driver Performance Display
```javascript
const drivers = await getDashboardDrivers();

// Map to KPI or ranking display
drivers
  .sort((a, b) => b.performance_points - a.performance_points)
  .slice(0, 5) // Top 5
  .map(driver => ({
    name: driver.name,
    points: driver.performance_points,
    deliveries: driver.deliveries_count
  }))
```

### Step 5: Mission Progress Integration
```javascript
const missions = await getDashboardMissions();

// Filter active missions
const activeMissions = missions.filter(m => m.status === 'enroute');
const completedMissions = missions.filter(m => m.status === 'completed');
const onTimeCount = completedMissions.filter(m => m.on_time).length;
```

---

## Data Sync Strategy

### Real-Time Updates
1. **Mission Completion**: Trigger performance recalculation
   ```javascript
   // When mission status changes to COMPLETED
   await recalculatePerformance();
   ```

2. **Truck Location Updates**: Sync truck data
   ```javascript
   // Every 30 seconds or on mission update
   await syncTruckData();
   ```

3. **Dashboard Refresh**: Get latest summary
   ```javascript
   // Every 60 seconds or on user focus
   const summary = await getDashboardSummary();
   ```

### Recommended Polling Intervals
- **KPI Cards**: 60 seconds
- **Truck Locations**: 30 seconds
- **Performance Points**: On-demand (after mission completion)
- **Fuel Consumption**: 5 minutes
- **Overall Summary**: 60 seconds

---

## Performance Calculation Example

**Scenario**: Driver "Allan Mugogo" has:
- 8 completed missions → 8 × 5 = 40 points
- 6 on-time deliveries → 6 × 5 = 30 points
- **Total: 70 performance points**

Display: `Allan Mugogo - 70 pts - 8 deliveries`

---

## Fuel Consumption Calculation Example

**Scenario**: Truck TRK1 with missions:
- Mission 1: 50 km
- Mission 2: 80 km
- Mission 3: 120 km
- **Total Distance**: 250 km
- **Fuel Rate**: 8 L/100km (default)
- **Fuel Consumed**: (250 × 8) / 100 = **20 liters**

Display: `20L consumed | 250km travelled | 8L/100km rate`

---

## Truck Status Logic

| Condition | Status | Display |
|-----------|--------|---------|
| Has ENROUTE mission | ENROUTE | 🚚 Moving |
| Has PAUSED mission | ENROUTE | ⏸️ Paused |
| No active missions | IDLE | 🛑 Idle |
| Under maintenance | MAINTENANCE | 🔧 Maintenance |

---

## Future Enhancements

1. **Customizable Fuel Rates**: Per-truck calibration
2. **Performance Bonuses**: Speed achievements, safety records
3. **Predictive Analytics**: ETA improvements, fuel optimization
4. **Real-Time Alerts**: Performance thresholds, fuel warnings
5. **Historical Tracking**: Performance trends, fuel usage patterns
6. **Cost Calculations**: Fuel cost, driver efficiency metrics

---

## Testing Checklist

- [ ] Create mission: Harare → Mutare
- [ ] Set status to ENROUTE, current_location to Rusape
- [ ] Verify truck location updates in admin dashboard
- [ ] Verify truck status shows ENROUTE
- [ ] Complete mission and verify performance points increase
- [ ] Verify fuel consumption calculated correctly
- [ ] Verify on-time delivery bonus applied
- [ ] Test all 6 new API endpoints
- [ ] Verify data appears in main dashboard KPI cards
- [ ] Test polling intervals work correctly

---

## File Locations

- **Backend Service**: `server/api/dashboard_service.py`
- **API Endpoints**: `server/api/dashboard_endpoints.py`
- **URL Routing**: `server/api/urls.py`
- **Frontend API Client**: `client/Frontend/src/services/api.js`
- **Admin Dashboard**: `client/Frontend/src/components/AdminDashboard.jsx`
- **Main Dashboard**: `client/Frontend/src/components/Dashboard.jsx` (to be updated)

---

## Notes for Implementation Team

1. **Data Consistency**: Always fetch fresh data from API rather than caching
2. **Error Handling**: Wrap all API calls in try-catch
3. **Performance**: Use lazy loading for large data sets
4. **Accessibility**: Ensure KPI cards are screen-reader friendly
5. **Mobile**: Ensure responsive design for all new displays
6. **Monitoring**: Log API response times for optimization
