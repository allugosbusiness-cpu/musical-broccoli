# Fuel Tracking System - Quick Start Guide

## What's New

The Fleet Management Platform now includes a **comprehensive fuel consumption tracking system** that realistically calculates fuel usage based on:
- ✅ Vehicle type and specifications
- ✅ Driving speed (optimal at 80-90 km/h)
- ✅ Cargo load percentage
- ✅ Terrain elevation changes
- ✅ Weather conditions (rain, wind, temperature)
- ✅ Idle time at stops

## Installation & Setup

### 1. Apply Database Migration
```bash
cd server
python manage.py migrate
```

This creates the following tables:
- `truck_fuel` - Fuel tank info for each truck
- `fuel_consumption` - Consumption records
- `fuel_refuel` - Refueling events
- `fuel_alerts` - Fuel-related alerts

### 2. Initialize Fuel Info for Trucks
```bash
python manage.py shell
```

```python
from api.models import Truck, TruckFuel

# Add fuel info for all trucks
for truck in Truck.objects.all():
    TruckFuel.objects.get_or_create(
        truck=truck,
        defaults={
            'vehicle_type': 'medium_truck',
            'tank_capacity_liters': 100,
            'current_fuel_liters': 100,
        }
    )
```

### 3. Access Frontend Component

The **FuelTracking** component is now integrated into the dashboard:

Location: Dashboard → Scroll down to find "Fuel Tracking System"

## How It Works

### Real-time Fuel Calculation

The system calculates consumption based on truck movement data:

```
Consumption (L) = Base Rate × Distance × Speed Factor × Load Factor × Terrain Factor × Weather Factor
```

**Example:**
- Medium truck traveling 50 km at average speed 67 km/h
- With 60% cargo load and 85m elevation gain
- Base consumption: 10 L/100km
- **Result: 14.14 L consumed, 3.54 km/L efficiency**

### Fuel Status Indicators

| Status | Fuel Level | Color | Action |
|--------|-----------|-------|--------|
| Normal | 50-100% | Green | Continue driving |
| Warning | 25-50% | Yellow | Plan refuel soon |
| Low | 10-25% | Amber | Refuel within 20km |
| Critical | <10% | Red | Find fuel immediately |

## Features

### 1. Fuel Gauge
- Real-time fuel percentage display
- Current fuel in liters
- Tank capacity information
- Color-coded status alerts

### 2. Consumption Metrics
- **Fuel Efficiency**: km/L and MPG
- **Estimated Range**: How far the truck can go with current fuel
- **Total Consumption**: Fuel used so far
- **Speed Factor**: Impact of current driving speed

### 3. Consumption Details
Shows breakdown of factors affecting consumption:
- Speed Factor (0.9-3.0x multiplier)
- Load Factor (cargo weight impact)
- Terrain Factor (elevation changes)
- Weather Factor (rain, wind, temperature)

### 4. Consumption History
- Last 20 consumption readings
- Time-stamped data
- Efficiency trends
- Easy to spot anomalies

## API Endpoints

### Get Fuel Status for a Truck
```bash
GET /api/fuel/TRK001/check_fuel_status/

Response:
{
  "fuel_info": {
    "truck_id": "TRK001",
    "current_fuel_liters": 65.5,
    "tank_capacity_liters": 100,
    "fuel_percentage": 65.5,
    "estimated_range_km": 632,
    "is_low_fuel": false,
    "is_critical_fuel": false
  },
  "active_alerts": []
}
```

### Calculate Fuel Consumption
```bash
POST /api/fuel/TRK001/calculate_consumption/

Request:
{
  "distance_km": 50.5,
  "duration_minutes": 45,
  "avg_speed_kmh": 67.3,
  "elevation_gain_m": 85,
  "load_percent": 60,
  "weather": {
    "rain": false,
    "wind_speed": 15,
    "temperature": 22
  }
}

Response:
{
  "success": true,
  "consumption": {
    "total_consumption_liters": 5.23,
    "efficiency_kmpl": 9.66,
    "estimated_range_km": 968
  },
  "fuel_status": { ... }
}
```

### Log Refueling Event
```bash
POST /api/fuel/TRK001/log_refuel/

Request:
{
  "amount_liters": 80,
  "cost_usd": 240,
  "location": "Harare Shell Station",
  "driver_name": "John Smith"
}

Response:
{
  "success": true,
  "refuel": {
    "amount_liters": 80,
    "cost_usd": 240,
    "fuel_efficiency_kmpl_before": 9.66,
    "distance_since_last_refuel_km": 487.5
  }
}
```

### Get Fleet Efficiency Report
```bash
GET /api/fuel-reports/fleet_efficiency/

Response:
{
  "period": "Last 30 days",
  "total_consumption_liters": 2345.67,
  "total_distance_km": 18934,
  "average_efficiency_kmpl": 8.08,
  "average_efficiency_mpg": 19.01
}
```

## Understanding Consumption Factors

### Speed Factor
| Speed | Factor | Consumption Impact |
|-------|--------|-------------------|
| 20 km/h (city) | 1.8x | 80% more fuel |
| 50 km/h (mixed) | 1.3x | 30% more fuel |
| 80 km/h (optimal) | 0.9x | 10% less fuel |
| 120 km/h (highway) | 1.2x | 20% more fuel |
| 140 km/h (overspeeding) | 1.6x | 60% more fuel |

### Load Factor
| Load | Factor | Impact |
|------|--------|--------|
| 20% (light) | 1.0x | No impact |
| 50% (half load) | 1.75x | 75% more fuel |
| 80% (full) | 2.7x | 170% more fuel |
| 100% (overloaded) | 3.1x | 210% more fuel |

### Terrain Factor
| Elevation Change | Factor | Impact |
|------------------|--------|--------|
| <10m (flat) | 1.0x | No impact |
| 30m (rolling) | 1.15x | 15% more fuel |
| 75m (hilly) | 1.35x | 35% more fuel |
| 150m (mountainous) | 1.65x | 65% more fuel |

### Weather Factor
| Condition | Impact |
|-----------|--------|
| Clear | No impact |
| Light rain | +8% consumption |
| Fog | +5% consumption |
| Strong headwind (>30 km/h) | +0.5% per km/h |
| Cold (<0°C) | +1% per degree |

## Common Tasks

### 1. Check Current Fuel Level
1. Open Dashboard
2. Navigate to "Fuel Tracking System"
3. Select truck from dropdown
4. View fuel gauge in Overview tab

### 2. Log a Refuel Event
1. Go to Fuel Tracking component
2. Click "Refuel" button (in production with modal)
3. Enter refuel amount, location, cost
4. System automatically updates fuel level

### 3. Analyze Consumption Trends
1. Open "History" tab
2. Review last 20 readings
3. Check for anomalies (unusually high consumption)
4. Identify improvement opportunities

### 4. View Consumption Factors
1. Open "Consumption Details" tab
2. See visual breakdown of factors
3. Understand what's driving high/low consumption
4. Adjust driving behavior if needed

## Best Practices

### For Fleet Managers
1. **Monitor Efficiency**
   - Check weekly efficiency reports
   - Compare trucks to identify outliers
   - Investigate unusual consumption patterns

2. **Fuel Cost Control**
   - Track refuel costs over time
   - Compare fuel prices at different stations
   - Plan refueling during low-price periods

3. **Driver Management**
   - Share efficiency metrics with drivers
   - Reward fuel-efficient driving
   - Identify need for driver training

### For Drivers
1. **Optimize Driving**
   - Maintain steady speed (80-90 km/h optimal)
   - Avoid excessive acceleration
   - Minimize idle time

2. **Load Management**
   - Don't overload vehicles
   - Distribute weight evenly
   - Remove unnecessary cargo

3. **Route Planning**
   - Avoid mountainous terrain when possible
   - Plan refueling stops strategically
   - Check traffic to reduce stop-and-go driving

## Troubleshooting

### Q: Consumption seems too high
**A:** Check:
1. Speed - Average speed <50 km/h increases consumption
2. Load - Over 80% load significantly increases consumption
3. Terrain - Mountainous routes consume more fuel
4. Weather - Rain and cold increase consumption

### Q: Fuel level not updating
**A:** Ensure:
1. `calculate_consumption` API is called after trips
2. Truck has TruckFuel record (created during init)
3. Distance and time data is being recorded

### Q: Alerts not showing
**A:** Check:
1. Fuel percentage is calculated correctly
2. Alert thresholds are set (default 25% warning, 10% critical)
3. Database migration was applied

### Q: Range estimate seems wrong
**A:** Range calculation:
```
Range = Current Fuel × Efficiency
```
- **High consumption** → Low efficiency → Lower range
- Verify efficiency is realistic for your vehicle type
- Check if load/terrain/weather factors apply

## System Limitations

1. **Simulated Fuel Sensor**: Uses GPS and trip data, not actual fuel sensor
   - Accuracy depends on data quality
   - May differ slightly from real sensor

2. **Weather Data**: Uses basic weather factors, not real-time weather
   - Assume normal weather unless specified
   - Real weather integration planned for future

3. **Terrain Data**: Uses elevation from GPS track
   - Requires actual GPS data with altitude
   - Flat terrain assumed if altitude data unavailable

4. **Load Estimation**: Manual input required
   - System doesn't know actual cargo weight
   - Driver must input or estimate load percentage

## Future Enhancements

🔄 **Planned Features:**
- Real fuel sensor integration (with hardware)
- Real-time weather API integration
- ML-based consumption predictions
- Automatic refuel station recommendations
- Carbon emissions tracking
- Integration with fuel price APIs
- Predictive maintenance alerts
- Advanced driver analytics

## Support

For issues or questions:
1. Check FUEL_TRACKING_DOCUMENTATION.md for detailed information
2. Review API endpoint examples
3. Test calculation formulas locally
4. Check database migration logs

---

**System Version:** 1.0  
**Framework:** Django 6.0.4, React 19.2.5  
**Database:** SQLite (dev), PostgreSQL (production ready)  
**Status:** Production Ready ✅
