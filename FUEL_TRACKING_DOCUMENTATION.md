# Fuel Consumption Tracking System - Documentation

## Overview

The Fleet Management Platform now includes a **realistic fuel consumption tracking system** that calculates fuel usage based on driving conditions, terrain, speed, load, and weather factors. This system simulates an actual fuel sensor to provide accurate consumption data.

## System Architecture

### Backend Components

#### 1. Fuel Calculator (`server/api/fuel_calculator.py`)
The core calculation engine that computes fuel consumption using realistic formulas.

**Key Classes:**
- `FuelCalculator` - Main class with static methods for fuel calculations

**Calculation Factors:**

##### Vehicle Profiles
```
light_truck:    8.0 L/100km base consumption, 60L tank
medium_truck:  10.0 L/100km base consumption, 100L tank
heavy_truck:   12.0 L/100km base consumption, 150L tank
semi_truck:    15.0 L/100km base consumption, 200L tank
```

##### Speed Factor (Multiplier)
Consumption varies significantly with speed. Optimal efficiency around 80-90 km/h:
```
< 1 km/h (idle):        3.0x (high consumption)
1-20 km/h (creeping):   1.8-2.0x
20-50 km/h (city):      1.3x
50-90 km/h (optimal):   0.9-1.0x
90-120 km/h (highway):  1.0-1.6x
> 120 km/h (overspeeding): 1.6+x
```

##### Load Factor (Multiplier)
Cargo weight increases consumption. Each 10% load = ~2-3% fuel increase:
```
< 20% load:    1.0x (empty/light)
20-50% load:   1.0-1.75x
50-80% load:   1.75-2.7x
> 80% load:    2.7+x (overloaded)
```

##### Terrain Factor (Multiplier)
Elevation changes significantly impact consumption:
```
< 10m elevation change:    1.0x (flat)
10-50m:                    1.15x (rolling)
50-100m:                   1.35x (hilly)
> 100m:                    1.65-2.0x (mountainous)
```

##### Weather Factor (Multiplier)
```
Base:                      1.0x
Rain conditions:           +0.08x (8% increase)
Fog/low visibility:        +0.05x (5% increase)
Headwind > 30 km/h:        +0.005x per km/h
Temperature < 0°C:         +0.01x per degree below zero
```

### Database Models

#### 1. TruckFuel
Tracks fuel tank information and current fuel status for each truck.

```python
Fields:
- vehicle_type: Choice field (light, medium, heavy, semi)
- tank_capacity_liters: Float (100L for medium truck)
- current_fuel_liters: Float (real-time fuel level)
- fuel_efficiency_kmpl: Float (calculated efficiency)
- warning_level_percent: Integer (default 25%)
- critical_level_percent: Integer (default 10%)
- total_fuel_consumed_liters: Float (cumulative)
- total_distance_traveled_km: Float (cumulative)
- is_low_fuel: Boolean (warning trigger)
- is_critical_fuel: Boolean (critical alert)
```

#### 2. FuelConsumption
Records each fuel consumption event with detailed metrics.

```python
Fields:
- consumption_type: Choice (segment, trip, idle, refuel)
- consumption_liters: Float (actual fuel consumed)
- distance_km: Float (distance traveled)
- duration_minutes: Integer (time taken)
- avg_speed_kmh: Float
- elevation_gain_m: Float
- load_percent: Float (cargo load %)
- weather_conditions: JSON (rain, wind, temp, etc.)
- efficiency_kmpl: Float (calculated km per liter)
- fuel_before_liters: Float (fuel at start)
- fuel_after_liters: Float (fuel at end)
- consumption_factors: JSON (speed, load, terrain, weather factors)
- was_predicted: Boolean (true if from ML prediction)
```

#### 3. FuelRefuel
Logs refueling events with cost and efficiency tracking.

```python
Fields:
- amount_liters: Float (amount refueled)
- cost_usd: Float (refuel cost)
- location: String (refuel station name)
- fuel_before_liters: Float
- fuel_after_liters: Float
- fuel_price_per_liter: Float
- driver_name: String
- driver_notes: TextField
- fuel_efficiency_kmpl_before: Float
- distance_since_last_refuel_km: Float
```

#### 4. FuelAlert
Alerts for fuel-related issues (low fuel, excessive consumption, etc.)

```python
Fields:
- alert_type: String (low_fuel_level, critical_fuel_level, excessive_consumption)
- severity: Choice (info, warning, critical)
- current_fuel_liters: Float
- current_fuel_percent: Float
- estimated_range_km: Float
- is_acknowledged: Boolean
- is_resolved: Boolean
```

### API Endpoints

#### Fuel Information
**GET** `/api/fuel/`
- List all truck fuel information

**GET** `/api/fuel/{truck_id}/`
- Get fuel info for specific truck

#### Fuel Consumption Calculation
**POST** `/api/fuel/{truck_id}/calculate_consumption/`

Request body:
```json
{
  "distance_km": 50.5,
  "duration_minutes": 45,
  "avg_speed_kmh": 67.3,
  "elevation_gain_m": 85,
  "load_percent": 60,
  "stops_count": 2,
  "stop_duration_minutes": 10,
  "weather": {
    "rain": false,
    "wind_speed": 15,
    "temperature": 22
  }
}
```

Response:
```json
{
  "success": true,
  "consumption": {
    "total_consumption_liters": 5.23,
    "distance_consumption": 4.95,
    "idle_consumption": 0.28,
    "efficiency_kmpl": 9.66,
    "estimated_range_km": 968,
    "tank_capacity_liters": 100,
    "breakdown": {
      "speed_factor": 0.95,
      "load_factor": 1.65,
      "terrain_factor": 1.20,
      "weather_factor": 1.0
    }
  },
  "fuel_status": { ... }
}
```

#### Refueling
**POST** `/api/fuel/{truck_id}/log_refuel/`

Request body:
```json
{
  "amount_liters": 80,
  "cost_usd": 240,
  "location": "Harare Shell Station",
  "latitude": -17.8252,
  "longitude": 31.0335,
  "driver_name": "John Smith",
  "driver_notes": "Full tank"
}
```

#### Fuel Status Check
**GET** `/api/fuel/{truck_id}/check_fuel_status/`

Response includes current fuel info and active alerts.

#### Consumption History
**GET** `/api/fuel/{truck_id}/consumption_history/?days=7`

Returns consumption records for specified period.

#### Refuel History
**GET** `/api/fuel/{truck_id}/refuel_history/?days=30`

Returns refueling records with cost analysis.

#### Reports
**GET** `/api/fuel-reports/daily_summary/`
- Daily fuel consumption summary for all trucks

**GET** `/api/fuel-reports/monthly_summary/`
- Monthly fuel consumption summary

**GET** `/api/fuel-reports/fleet_efficiency/`
- Fleet-wide fuel efficiency metrics

### Frontend Component

#### FuelTracking Component (`client/Frontend/src/components/FuelTracking.jsx`)

**Features:**
1. **Overview Tab**
   - Circular fuel gauge showing current level
   - Real-time fuel status (Normal/Warning/Low/Critical)
   - Key metrics: Efficiency, Range, Consumption, Speed
   - Automatic alerts for low/critical fuel

2. **Consumption Details Tab**
   - Visual breakdown of consumption factors
   - Speed, load, terrain, weather impact
   - Consumption formula breakdown

3. **History Tab**
   - Last 20 fuel readings table
   - Time-stamped consumption records
   - Efficiency trends

**Props:**
- None (uses internal state and API calls)

**State:**
- `selectedTruck`: Currently selected truck
- `trucks`: List of available trucks
- `fuelData`: Current fuel calculations
- `consumptionHistory`: Historical readings
- `activeTab`: Current tab view
- `loading`: Data loading state

## Calculation Example

**Scenario:** Medium truck traveling 50km in 45 minutes

**Given:**
- Vehicle Type: Medium Truck
- Distance: 50 km
- Speed: 67 km/h (average)
- Elevation: 85m gain
- Load: 60%
- Weather: Clear, temp 22°C

**Calculation:**

```
Base Consumption = 10.0 L/100km

Speed Factor (67 km/h):
  Between 50-90 km/h optimal range
  = 0.9 + (67-90) * 0.001 = 0.977

Load Factor (60%):
  50-80% range: 1.75 + (60-50)*0.035 = 2.1

Terrain Factor (85m):
  50-100m = 1.35

Weather Factor:
  Clear conditions = 1.0

Total Consumption = 50/100 * 10 * 0.977 * 2.1 * 1.35 * 1.0
                 = 0.5 * 10 * 0.977 * 2.1 * 1.35
                 = 14.14 L

Efficiency = 50 / 14.14 = 3.54 km/L

Range with 100L tank = 100 * 3.54 = 354 km
```

## Fuel Alerts

### Alert Types

1. **Low Fuel** (Warning)
   - Triggered when: Fuel < 25%
   - Message: "Low fuel: X% remaining. Consider refueling soon."
   - Suggestion: Start looking for fuel station

2. **Critical Fuel** (Critical)
   - Triggered when: Fuel < 10%
   - Message: "CRITICAL: Fuel level at X%. Refuel immediately!"
   - Suggestion: Find nearest fuel station urgently

3. **Excessive Consumption** (Warning)
   - Triggered when: Efficiency drops significantly below normal
   - Indicates potential issues (heavy load, poor driving, mechanical)

### Alert Resolution

Alerts are automatically resolved when:
- Fuel is refueled (low/critical alerts)
- Driver acknowledges alert
- Manual resolution with notes

## Performance Considerations

1. **Real-time Calculation**
   - Calculations are lightweight and instant
   - No external API calls required for calculation

2. **Data Storage**
   - FuelConsumption records indexed on truck_id and timestamp for fast queries
   - Old records can be archived for historical analysis

3. **Reporting**
   - Pre-calculated summaries available via report endpoints
   - Aggregations done at query time (can be cached)

## Integration with Other Systems

### Route Optimization
Fuel consumption data feeds into route optimization:
- Consider fuel capacity for long routes
- Suggest refuel points
- Avoid routes with excessive elevation if low on fuel

### Fleet Analytics
- Calculate fuel cost per km
- Track efficiency trends
- Identify driver behavior impacts
- Optimize fleet operation

### Driver Behavior Monitoring
- High speeds → High consumption
- Excessive idling → Wasted fuel
- Aggressive acceleration → Inefficient driving

## Future Enhancements

1. **Machine Learning Predictions**
   - Predict consumption before trip
   - Warn of excessive consumption
   - Recommend optimal routes by fuel efficiency

2. **Fuel Price Integration**
   - Real-time fuel price data
   - Calculate refuel cost estimates
   - Find cheapest stations nearby

3. **Carbon Emissions Tracking**
   - Calculate CO2 per trip
   - Track fleet emissions
   - Sustainability reporting

4. **Predictive Maintenance**
   - Efficiency degradation indicates service needed
   - Fuel sensor anomalies suggest mechanical issues

## Testing the System

### 1. Create Test Data
```bash
# Add trucks with fuel info
python manage.py shell
>>> from api.models import Truck, TruckFuel
>>> truck = Truck.objects.first()
>>> TruckFuel.objects.create(truck=truck, vehicle_type='medium_truck')
```

### 2. Test Consumption Calculation
```python
from api.fuel_calculator import FuelCalculator

result = FuelCalculator.calculate_trip_consumption(
    distance_km=50,
    duration_minutes=45,
    avg_speed_kmh=67,
    total_elevation_gain_m=85,
    load_percent=60,
    vehicle_type='medium_truck'
)
print(result)
```

### 3. Test API Endpoint
```bash
curl -X POST http://localhost:8000/api/fuel/TRK001/calculate_consumption/ \
  -H "Content-Type: application/json" \
  -d '{
    "distance_km": 50,
    "duration_minutes": 45,
    "avg_speed_kmh": 67,
    "elevation_gain_m": 85,
    "load_percent": 60
  }'
```

### 4. Test Refueling
```bash
curl -X POST http://localhost:8000/api/fuel/TRK001/log_refuel/ \
  -H "Content-Type: application/json" \
  -d '{
    "amount_liters": 80,
    "cost_usd": 240,
    "location": "Shell Station"
  }'
```

## Configuration

### Modify Consumption Base Rates
Edit `server/api/fuel_calculator.py`:
```python
VEHICLE_PROFILES = {
    'light_truck': {'base_consumption': 8.0, 'capacity': 60},
    # Adjust base_consumption for different vehicles
}
```

### Modify Alert Thresholds
Edit truck fuel record:
```python
truck_fuel.warning_level_percent = 25  # Alert at 25%
truck_fuel.critical_level_percent = 10  # Critical at 10%
truck_fuel.save()
```

### Weather Impact
Edit weather factors in `fuel_calculator.py`:
```python
if weather_conditions.get('rain', False):
    factor += 0.08  # Adjust rain impact
```

## Support & Troubleshooting

### Issue: Consumption seems too high
**Solution:** Check load_percent and elevation_gain_m values in requests

### Issue: Fuel status not updating
**Solution:** Ensure calculate_consumption endpoint is called after each trip

### Issue: Alerts not triggering
**Solution:** Check fuel percentage calculation: `current_fuel / tank_capacity * 100`

---

**Version:** 1.0  
**Last Updated:** May 2026  
**Author:** Fleet Management System Team
