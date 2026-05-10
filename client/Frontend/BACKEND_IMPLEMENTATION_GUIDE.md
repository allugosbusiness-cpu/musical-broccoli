# Backend Implementation Guide - Advanced Routing System

## Overview
This guide provides the specifications for implementing the 20+ backend endpoints required for the new Advanced Routing System. The frontend has already been implemented and is waiting for these endpoints.

## Quick Reference

| Endpoint | Method | Purpose | Priority |
|----------|--------|---------|----------|
| `/routes/calculate-advanced/` | POST | Calculate optimized multi-waypoint route | CRITICAL |
| `/routes/reroute/` | POST | Dynamic rerouting for real-time conditions | CRITICAL |
| `/traffic/predict/` | POST | Predict traffic for time period | HIGH |
| `/fuel/predict/` | POST | Predict fuel consumption | HIGH |
| `/routes/hazards/` | POST | Detect hazards on route | HIGH |
| `/routes/alternatives/` | POST | Generate alternative routes | HIGH |
| `/routes/optimize-fuel/` | POST | Optimize for fuel efficiency | MEDIUM |
| `/routes/calculate-eta/` | POST | Calculate ETA with confidence | MEDIUM |
| `/routes/find-stops/` | POST | Find optimal fuel/rest stops | MEDIUM |
| `/routes/{id}/performance-analytics/` | GET | Get performance metrics | MEDIUM |
| `/routes/live-optimize/{vehicleId}/` | WS | WebSocket for live optimization | LOW |

---

## Detailed Endpoint Specifications

### 1. CRITICAL: Calculate Advanced Route
**Endpoint**: `POST /api/routes/calculate-advanced/`

**Request Body**:
```json
{
  "origin": {
    "name": "Harare",
    "lat": -17.8252,
    "lng": 31.0335
  },
  "destination": {
    "name": "Mutare",
    "lat": -18.9833,
    "lng": 32.6667
  },
  "waypoints": [
    {
      "name": "Marondera",
      "lat": -18.2145,
      "lng": 31.5516
    }
  ],
  "options": {
    "profile": "balanced",  // balanced | fastest | fuel_optimal | safest
    "vehicle": {
      "id": "TRUCK-001",
      "type": "truck",
      "capacity": 20,
      "fuelCapacity": 250,
      "currentFuel": 200,
      "weight": 5000,
      "axles": 3,
      "costPerKm": 2.50
    },
    "constraints": {
      "maxDistance": 500,
      "maxTime": 480,
      "preferHighways": true,
      "avoidTolls": false
    },
    "conditions": {
      "trafficLevel": "moderate",
      "weather": "clear",
      "roadConditions": "good"
    }
  }
}
```

**Expected Response**:
```json
{
  "status": "success",
  "route": {
    "id": "route_12345",
    "totalDistance": 324.5,  // km
    "totalDuration": 285,     // minutes
    "totalFuelNeeded": 45.2,  // liters
    "estimatedCost": 812.50,  // currency units
    "waypoints": [
      {
        "order": 1,
        "name": "Harare",
        "lat": -17.8252,
        "lng": 31.0335,
        "arrivalTime": "2024-04-29T08:00:00Z",
        "departureTime": "2024-04-29T08:00:00Z",
        "eta": 0
      },
      {
        "order": 2,
        "name": "Marondera",
        "lat": -18.2145,
        "lng": 31.5516,
        "arrivalTime": "2024-04-29T09:15:00Z",
        "departureTime": "2024-04-29T09:25:00Z",
        "eta": 75
      },
      {
        "order": 3,
        "name": "Mutare",
        "lat": -18.9833,
        "lng": 32.6667,
        "arrivalTime": "2024-04-29T12:00:00Z",
        "departureTime": null,
        "eta": 285
      }
    ],
    "segments": [
      {
        "from": "Harare",
        "to": "Marondera",
        "distance": 168.3,
        "duration": 75,
        "fuel": 23.5,
        "hazards": [],
        "trafficLevel": "light",
        "congestion": 0.2
      },
      {
        "from": "Marondera",
        "to": "Mutare",
        "distance": 156.2,
        "duration": 210,
        "fuel": 21.7,
        "hazards": ["construction"],
        "trafficLevel": "moderate",
        "congestion": 0.5
      }
    ],
    "profile": "balanced",
    "confidence": 0.85
  }
}
```

**Implementation Notes**:
- Use a TSP (Traveling Salesman Problem) solver for waypoint optimization
- Can integrate Google Maps API, OSRM, or custom implementation
- Calculate fuel based on vehicle profile and terrain
- Consider traffic data in ETA calculations
- Return multiple alternative routes if available

---

### 2. CRITICAL: Dynamic Rerouting
**Endpoint**: `POST /api/routes/reroute/`

**Request Body**:
```json
{
  "currentLocation": {
    "lat": -18.1234,
    "lng": 31.5678,
    "time": "2024-04-29T09:30:00Z"
  },
  "destination": {
    "name": "Mutare",
    "lat": -18.9833,
    "lng": 32.6667
  },
  "originalRoute": {
    "id": "route_12345",
    "remainingWaypoints": [
      {
        "name": "Mutare",
        "lat": -18.9833,
        "lng": 32.6667
      }
    ]
  },
  "options": {
    "vehicle": { "id": "TRUCK-001" },
    "reasons": ["accident", "traffic_jam", "construction"],
    "conditions": {
      "trafficLevel": "heavy",
      "weather": "rain",
      "roadConditions": "poor"
    }
  }
}
```

**Expected Response**:
```json
{
  "status": "success",
  "newRoute": {
    // Same structure as calculate-advanced response
    "rerouted": true,
    "reason": "traffic_jam",
    "timeSaved": 15,  // minutes
    "fuelSaved": 2.3,  // liters
    "costDelta": -12.50
  }
}
```

**Implementation Notes**:
- Should be faster than full re-optimization
- Consider only unvisited waypoints
- Account for real-time traffic data
- Update ETAs based on current position

---

### 3. HIGH: Predict Traffic
**Endpoint**: `POST /api/traffic/predict/`

**Request Body**:
```json
{
  "route": {
    "waypoints": [
      {"lat": -17.8252, "lng": 31.0335},
      {"lat": -18.2145, "lng": 31.5516}
    ]
  },
  "departureTime": "2024-04-29T08:00:00Z",
  "lookaheadHours": 3
}
```

**Expected Response**:
```json
{
  "status": "success",
  "predictions": [
    {
      "timestamp": "2024-04-29T08:00:00Z",
      "segments": [
        {
          "from": "Harare",
          "to": "Marondera",
          "trafficLevel": "light",
          "congestion": 0.15,
          "speed": 95,  // km/h
          "estimatedDuration": 76
        }
      ],
      "optimalDepartureTime": "2024-04-29T07:30:00Z"
    },
    {
      "timestamp": "2024-04-29T09:00:00Z",
      "segments": [
        {
          "from": "Harare",
          "to": "Marondera",
          "trafficLevel": "moderate",
          "congestion": 0.45,
          "speed": 60,
          "estimatedDuration": 95
        }
      ]
    },
    {
      "timestamp": "2024-04-29T11:00:00Z",
      "segments": [
        {
          "from": "Harare",
          "to": "Marondera",
          "trafficLevel": "heavy",
          "congestion": 0.85,
          "speed": 30,
          "estimatedDuration": 180
        }
      ]
    }
  ]
}
```

**Implementation Notes**:
- Use historical traffic data or third-party API
- Provide 3-hour lookahead in 1-hour intervals
- Suggest optimal departure time
- Calculate confidence intervals

---

### 4. HIGH: Predict Fuel Consumption
**Endpoint**: `POST /api/fuel/predict/`

**Request Body**:
```json
{
  "route": {
    "distance": 324.5,
    "elevation": [1200, 1250, 1100],
    "terrain": ["highway", "secondary", "highway"],
    "speedProfile": [100, 80, 100]
  },
  "vehicle": {
    "id": "TRUCK-001",
    "type": "truck",
    "weight": 5000,
    "engineType": "diesel",
    "engineSize": 12.8,
    "fuelCapacity": 250,
    "currentFuel": 200
  },
  "driver": {
    "experience": "expert",
    "style": "conservative"
  },
  "conditions": {
    "weather": "clear",
    "temperature": 22,
    "wind": 5,
    "traffic": "moderate"
  }
}
```

**Expected Response**:
```json
{
  "status": "success",
  "fuelPrediction": {
    "estimatedConsumption": 45.2,  // liters
    "baseFuelRate": 6.5,  // L/100km
    "factors": {
      "elevation": 1.2,  // multiplier
      "terrain": 0.95,
      "speed": 1.1,
      "weather": 1.05,
      "driver": 0.9,
      "traffic": 1.15
    },
    "fuelRemaining": 154.8,  // liters after trip
    "refuelRequired": false,
    "rangeRemaining": 2377,  // km
    "recommendations": [
      "Consider reducing speed on secondary roads to save fuel",
      "Current fuel level is adequate for trip"
    ]
  }
}
```

**Implementation Notes**:
- Base consumption from EPA/manufacturer data
- Apply multipliers for various factors
- Account for real-time conditions
- Recommend fuel stops if needed

---

### 5. HIGH: Detect Hazards
**Endpoint**: `POST /api/routes/hazards/`

**Request Body**:
```json
{
  "route": {
    "waypoints": [
      {"lat": -17.8252, "lng": 31.0335},
      {"lat": -18.2145, "lng": 31.5516},
      {"lat": -18.9833, "lng": 32.6667}
    ]
  },
  "vehicleType": "truck",
  "departureTime": "2024-04-29T08:00:00Z"
}
```

**Expected Response**:
```json
{
  "status": "success",
  "hazards": [
    {
      "type": "accident",
      "severity": "high",
      "location": {
        "lat": -18.3456,
        "lng": 31.6789,
        "distance": 45.2,  // km from start
        "eta": 120  // minutes from start
      },
      "description": "Multi-vehicle collision on N1 highway",
      "affectedSegments": ["Harare->Marondera"],
      "impact": {
        "timeDelay": 45,  // minutes
        "recommended": "consider alternative route"
      }
    },
    {
      "type": "construction",
      "severity": "medium",
      "location": {
        "lat": -18.5678,
        "lng": 31.8901
      },
      "description": "Road maintenance work in progress",
      "affectedSegments": ["Marondera->Mutare"],
      "impact": {
        "timeDelay": 15,
        "recommended": "expect delays"
      }
    },
    {
      "type": "weather",
      "severity": "low",
      "location": {
        "lat": -18.7890,
        "lng": 32.1234
      },
      "description": "Light rain forecast",
      "affectedSegments": ["Marondera->Mutare"],
      "impact": {
        "fuelIncrease": 2.5,
        "recommended": "reduce speed"
      }
    }
  ]
}
```

**Implementation Notes**:
- Integrate with incident reporting services
- Monitor weather data
- Track construction sites
- Assess severity and impact
- Provide recommendations

---

### 6. HIGH: Alternative Routes
**Endpoint**: `POST /api/routes/alternatives/`

**Request Body**:
```json
{
  "origin": {"name": "Harare", "lat": -17.8252, "lng": 31.0335},
  "destination": {"name": "Mutare", "lat": -18.9833, "lng": 32.6667},
  "count": 3,
  "vehicle": {"id": "TRUCK-001"},
  "options": {
    "includeDetails": true,
    "excludeHighways": false
  }
}
```

**Expected Response**:
```json
{
  "status": "success",
  "alternatives": [
    {
      "rank": 1,
      "distance": 324.5,
      "duration": 285,
      "fuel": 45.2,
      "cost": 812.50,
      "characteristics": "fastest_time",
      "hazardCount": 1,
      "hazardSeverity": "medium"
    },
    {
      "rank": 2,
      "distance": 335.8,
      "duration": 298,
      "fuel": 42.1,
      "cost": 798.30,
      "characteristics": "fuel_efficient",
      "hazardCount": 0,
      "hazardSeverity": "none"
    },
    {
      "rank": 3,
      "distance": 312.3,
      "duration": 310,
      "fuel": 50.2,
      "cost": 856.20,
      "characteristics": "scenic",
      "hazardCount": 2,
      "hazardSeverity": "low"
    }
  ]
}
```

---

### 7-10. MEDIUM Priority Endpoints

**POST `/routes/optimize-fuel/`** - Fuel optimization
**POST `/routes/calculate-eta/`** - ETA with confidence intervals
**POST `/routes/find-stops/`** - Optimal fuel/rest stops
**GET `/routes/{id}/performance-analytics/`** - Performance metrics

(Similar structure to above - request/response patterns)

---

### 11. LOW: Live Optimization WebSocket
**Endpoint**: `WS /api/routes/live-optimize/{vehicleId}/`

**Message Format (Server → Client)**:
```json
{
  "type": "optimization",
  "timestamp": "2024-04-29T09:35:00Z",
  "vehicleId": "TRUCK-001",
  "currentLocation": {
    "lat": -18.1234,
    "lng": 31.5678
  },
  "optimization": {
    "action": "reroute",
    "reason": "traffic_jam",
    "newRoute": { /* full route object */ }
  }
}
```

---

## Implementation Priority

### Phase 1 (Week 1 - Critical)
- [ ] `/routes/calculate-advanced/` - Core functionality
- [ ] `/routes/reroute/` - Real-time updates

### Phase 2 (Week 2 - High Priority)
- [ ] `/traffic/predict/` - Traffic forecasting
- [ ] `/fuel/predict/` - Fuel optimization
- [ ] `/routes/hazards/` - Safety features
- [ ] `/routes/alternatives/` - Route comparison

### Phase 3 (Week 3 - Medium)
- [ ] `/routes/optimize-fuel/`
- [ ] `/routes/calculate-eta/`
- [ ] `/routes/find-stops/`
- [ ] `/routes/{id}/performance-analytics/`

### Phase 4 (Week 4 - Integration)
- [ ] WebSocket `/routes/live-optimize/{vehicleId}/`
- [ ] Integration testing
- [ ] Performance optimization

---

## Technology Recommendations

### Routing Engine
- **OSRM** (Open Source): Free, local deployment
- **Google Maps Platform**: Enterprise solution
- **Mapbox**: Developer-friendly, good documentation

### TSP Solver
- **OR-Tools** (Google): Fast, production-ready
- **Lin-Kernighan Heuristic**: For very large problems
- **Concorde TSP**: Optimal solutions (slower)

### Traffic Data
- **TomTom**: Real-time traffic
- **Here Maps**: Historical + real-time
- **Local traffic sensors**: For regional data

### Fuel Consumption Models
- **EPA vehicle database**: Baseline consumption
- **Custom telemetry**: From vehicle CAN bus
- **Machine learning**: Predict based on driver/conditions

---

## Testing Strategy

1. **Unit Tests**: Individual endpoint functions
2. **Integration Tests**: Full route calculation workflow
3. **Performance Tests**: Load testing with 100+ simultaneous requests
4. **Accuracy Tests**: Compare against known routes
5. **Edge Cases**: Extreme waypoints, missing data, network errors

---

## Security Considerations

- Validate all input coordinates (within bounds)
- Rate limit API calls per vehicle/user
- Sanitize location names
- Encrypt sensitive vehicle data
- Log all optimization requests
- Implement user authentication

---

## Deployment Checklist

- [ ] All endpoints implemented
- [ ] Unit tests passing
- [ ] Integration tests passing
- [ ] Performance tests acceptable
- [ ] Error handling for edge cases
- [ ] API documentation complete
- [ ] CORS configured
- [ ] Database migrations applied
- [ ] Cache strategy implemented
- [ ] Monitoring/logging in place
- [ ] Load balancing configured
- [ ] SSL certificates installed

---

**Next Steps**: Contact the frontend team once endpoints are ready for integration testing.
