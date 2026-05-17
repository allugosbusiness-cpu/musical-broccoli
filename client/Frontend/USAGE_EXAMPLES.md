# 📚 Advanced Routing System - Usage Examples

## Quick Start Examples

### 1. Basic Multi-Waypoint Route Planning

```javascript
import EnhancedRoutePlanner from './components/EnhancedRoutePlanner';

export default function DeliveryApp() {
  return (
    <div className="min-h-screen">
      {/* This component handles everything */}
      <EnhancedRoutePlanner />
    </div>
  );
}
```

**User Experience:**
1. Select start location (Harare)
2. Add stops (Marondera, Rusape, Headlands)
3. Select destination (Mutare)
4. Choose route profile (Balanced, Fastest, Fuel Optimal, Safest)
5. View optimized route on map
6. See alternative routes
7. Export or start route

---

### 2. Real-Time Route Optimization During Delivery

```javascript
import routeOptimizer from './services/routeOptimizer';

function DeliveryTracking({ truckId, destination }) {
  const [route, setRoute] = useState(null);
  const [optimizations, setOptimizations] = useState([]);

  useEffect(() => {
    // Subscribe to live optimization
    const connection = routeOptimizer.subscribeToLiveOptimization(
      truckId,
      destination,
      
      // Position update callback
      (position) => {
        console.log('Vehicle position:', position.lat, position.lng);
      },
      
      // Optimization suggestion callback
      (suggestion) => {
        console.log('New optimization available:', suggestion);
        setOptimizations(prev => [...prev, suggestion]);
        
        // Show user notification
        if (suggestion.savings.timeSaved > 15) {
          notifyDriver(`Save ${suggestion.savings.timeSaved} minutes with new route`);
        }
      }
    );

    return () => connection.close();
  }, [truckId, destination]);

  return (
    <div>
      <MapDisplay />
      {optimizations.map(opt => (
        <OptimizationCard key={opt.id} suggestion={opt} />
      ))}
    </div>
  );
}
```

---

### 3. Fuel Stop Optimization

```javascript
import routeOptimizer from './services/routeOptimizer';

async function optimizeFuelStops(route, truck) {
  // Find optimal fuel and rest stops
  const stops = await routeOptimizer.findOptimalStops(route, {
    fuelTankCapacity: truck.fuelCapacity,     // 250L
    fuelConsumption: truck.consumption,       // 8 km/L
    driverRestRequirement: 4.5                // hours
  });

  return {
    fuelStops: stops.fuelStops.map(stop => ({
      name: stop.name,
      distance: stop.distanceFromStart,
      recommendedFuel: stop.recommendedFuel,
      amenities: stop.amenities,
      detour: stop.detour // extra km if not on direct route
    })),
    restStops: stops.restStops,
    maintenanceStops: stops.maintenanceStops,
    totalStopTime: stops.estimatedStopDuration
  };
}

// Usage
const fuelPlan = await optimizeFuelStops(route, {
  fuelCapacity: 250,
  consumption: 8
});

// Display to driver
<div className="fuel-plan">
  {fuelPlan.fuelStops.map(stop => (
    <div key={stop.name}>
      <h3>{stop.name}</h3>
      <p>Distance: {stop.distance}km</p>
      <p>Fill up: {stop.recommendedFuel}L</p>
      <p>Amenities: {stop.amenities.join(', ')}</p>
    </div>
  ))}
</div>
```

---

### 4. Traffic Prediction & Optimal Departure Time

```javascript
import predictiveAnalytics from './services/predictiveAnalytics';

async function suggestBestDepartureTime(route) {
  // Check traffic for different departure times
  const prediction = await predictiveAnalytics.predictTrafficForTime(
    route,
    new Date()
  );

  console.log('Prediction results:');
  console.log('- Peak congestion hours:', prediction.peakHours);
  console.log('- Average delay:', prediction.totalDelay, 'minutes');
  console.log('- Confidence:', prediction.confidence);

  // Suggested optimal times
  return prediction.alternativeTimes.map(option => ({
    departAt: option.time,
    expectedDelay: option.congestionScore,
    timeSaving: option.timeSaving,
    isOptimal: option.timeSaving > 30
  }));
}

// Usage in UI
const bestTimes = await suggestBestDepartureTime(route);
<div className="departure-options">
  {bestTimes.map((time, idx) => (
    <button 
      key={idx}
      onClick={() => setDepartureTime(time.departAt)}
      className={time.isOptimal ? 'bg-green-500' : 'bg-slate-500'}
    >
      {time.departAt.toLocaleTimeString()}
      {time.isOptimal && '⭐ Save ' + time.timeSaving + 'min'}
    </button>
  ))}
</div>
```

---

### 5. Route Analytics & Performance Dashboard

```javascript
import RouteAnalyticsDashboard from './components/RouteAnalyticsDashboard';

function FleetPerformance() {
  const [route, setRoute] = useState(null);
  const [historicalData, setHistoricalData] = useState([]);

  useEffect(() => {
    // Fetch current route
    const currentRoute = await getActiveRoute(truckId);
    
    // Fetch historical data for trend analysis
    const history = await getRouteHistory(truckId, '7days');
    
    setRoute(currentRoute);
    setHistoricalData(history);
  }, []);

  return (
    <RouteAnalyticsDashboard 
      route={route}
      historicalData={historicalData}
    />
  );
}

// Dashboard automatically shows:
// - Route Efficiency %
// - Fuel Consumption (L)
// - Estimated Cost ($)
// - Travel Time (min)
// - Safety Score (0-100)
// - CO₂ Emissions (kg)
// - Segment Performance
// - Risk Assessment
// - Cost Breakdown
// - Environmental Impact
// - AI Recommendations
```

---

### 6. Hazard Detection & Safety Routing

```javascript
import routeOptimizer from './services/routeOptimizer';

async function checkRouteHazards(route) {
  const hazards = await routeOptimizer.detectHazards(route, {
    hazardTypes: [
      'construction',
      'accident',
      'weather',
      'congestion',
      'roadwork',
      'pothole'
    ]
  });

  if (hazards.severityLevel === 'critical') {
    // Suggest alternative route
    const safer = await routeOptimizer.getDynamicReroute(
      currentLocation,
      destination,
      route,
      { reason: 'hazard' }
    );

    return {
      warning: true,
      message: `${hazards.hazards.length} hazards detected. Safer route available`,
      recommendations: hazards.recommendations,
      alternativeRoute: safer
    };
  }

  return {
    warning: false,
    hazards: hazards.hazards
  };
}

// Usage
const safety = await checkRouteHazards(route);
if (safety.warning) {
  <AlertBanner>
    <AlertTriangle /> {safety.message}
    <button onClick={() => setRoute(safety.alternativeRoute)}>
      Use Safer Route
    </button>
  </AlertBanner>
}
```

---

### 7. Compare Alternative Routes

```javascript
import routeOptimizer from './services/routeOptimizer';

async function compareRoutes(origin, destination) {
  const alternatives = await routeOptimizer.getAlternativeRoutes(
    origin,
    destination,
    { 
      count: 3,
      compareBy: ['duration', 'distance', 'fuel', 'safety']
    }
  );

  return alternatives.map((route, idx) => ({
    rank: idx + 1,
    distance: route.comparison.distance,
    duration: route.comparison.duration,
    fuel: route.comparison.fuel,
    cost: route.comparison.cost,
    safety: route.comparison.safety,
    scenery: route.comparison.scenery,
    recommended: idx === 0
  }));
}

// Display comparison
const routeComparison = await compareRoutes(origin, destination);

<div className="route-comparison">
  {routeComparison.map(route => (
    <div 
      key={route.rank}
      className={route.recommended ? 'border-2 border-green-500' : ''}
    >
      <h3>Route {route.rank} {route.recommended && '⭐ Recommended'}</h3>
      <div className="grid grid-cols-4">
        <div>
          <label>Distance</label>
          <value>{route.distance}km</value>
        </div>
        <div>
          <label>Time</label>
          <value>{route.duration}min</value>
        </div>
        <div>
          <label>Fuel</label>
          <value className="text-green-400">{route.fuel}L</value>
        </div>
        <div>
          <label>Safety</label>
          <value>{route.safety}/100</value>
        </div>
      </div>
      <button onClick={() => selectRoute(route)}>Select</button>
    </div>
  ))}
</div>
```

---

### 8. Advanced ETA Calculation with Confidence

```javascript
import routeOptimizer from './services/routeOptimizer';

async function getAccurateETA(route, currentLocation, vehicle) {
  const eta = await routeOptimizer.calculateAdvancedETA(
    route,
    currentLocation,
    vehicle
  );

  return {
    estimated: eta.eta,
    confidence: Math.round(eta.confidence * 100),
    mostLikely: eta.estimatedTravelTime,
    optimistic: eta.timeRange.optimistic,    // Best case
    pessimistic: eta.timeRange.pessimistic,  // Worst case
    factors: eta.factorsAffecting,
    suggestions: eta.breakSuggestions
  };
}

// Display ETA with range
const eta = await getAccurateETA(route, currentLocation, vehicle);

<div className="eta-display">
  <h2>Estimated Arrival</h2>
  <p className="time">{eta.estimated.toLocaleTimeString()}</p>
  <p className="confidence">
    {eta.confidence}% confidence
  </p>
  
  <div className="eta-range">
    <div>
      <label>Optimistic</label>
      <value>{eta.optimistic}m</value>
    </div>
    <div>
      <label>Most Likely</label>
      <value>{eta.mostLikely}m</value>
    </div>
    <div>
      <label>Pessimistic</label>
      <value>{eta.pessimistic}m</value>
    </div>
  </div>

  <div className="factors">
    <h4>Affecting ETA:</h4>
    <ul>
      {eta.factors.map((factor, idx) => (
        <li key={idx}>{factor}</li>
      ))}
    </ul>
  </div>
</div>
```

---

### 9. Fuel Consumption Prediction

```javascript
import predictiveAnalytics from './services/predictiveAnalytics';

async function predictFuel(route, vehicle, conditions = {}) {
  const prediction = await predictiveAnalytics.predictFuelConsumption(
    route,
    vehicle,
    {
      terrain: conditions.terrain || 'mixed',    // highway, city, offroad, mixed
      weather: conditions.weather || 'clear',    // clear, rain, fog, snow
      driverProfile: conditions.driverProfile || 'normal', // aggressive, normal, eco
      temperature: conditions.temperature || 25
    }
  );

  return {
    estimated: prediction.estimatedConsumption,
    range: prediction.range,                     // Can travel X km with full tank
    breakdown: prediction.consumptionBreakdown,  // Terrain, elevation, weather costs
    accuracy: prediction.accuracy,               // 0-1 confidence
    tips: prediction.tips                        // Optimization suggestions
  };
}

// Usage and display
const fuelPrediction = await predictFuel(route, vehicle, {
  terrain: 'highway',
  weather: 'rain'
});

<div className="fuel-prediction">
  <h3>Fuel Prediction</h3>
  <p>Estimated: {fuelPrediction.estimated}L</p>
  <p>Range: {fuelPrediction.range}km on full tank</p>
  <p>Accuracy: {Math.round(fuelPrediction.accuracy * 100)}%</p>

  <div className="breakdown">
    <h4>Consumption Factors:</h4>
    <ul>
      <li>Terrain: +{fuelPrediction.breakdown.terrain}%</li>
      <li>Elevation: +{fuelPrediction.breakdown.elevation}%</li>
      <li>Weather: +{fuelPrediction.breakdown.weather}%</li>
      <li>Speed: +{fuelPrediction.breakdown.speed}%</li>
    </ul>
  </div>

  <div className="tips">
    <h4>Optimization Tips:</h4>
    <ul>
      {fuelPrediction.tips.map((tip, idx) => (
        <li key={idx}>{tip}</li>
      ))}
    </ul>
  </div>
</div>
```

---

### 10. Complete Route Workflow

```javascript
import EnhancedRoutePlanner from './components/EnhancedRoutePlanner';
import AdvancedRouteMap from './components/AdvancedRouteMap';
import RouteAnalyticsDashboard from './components/RouteAnalyticsDashboard';
import routeOptimizer from './services/routeOptimizer';

export default function CompleteRouteManagement() {
  const [route, setRoute] = useState(null);
  const [alerts, setAlerts] = useState([]);
  const [stage, setStage] = useState('planning'); // planning, review, active, completed

  // Step 1: Plan route
  const handleRoutePlanned = (calculatedRoute) => {
    setRoute(calculatedRoute);
    
    // Check hazards
    checkAndAlert(calculatedRoute);
    
    setStage('review');
  };

  // Step 2: Review & Optimize
  const handleStartRoute = async () => {
    // Get fuel stops
    const stops = await routeOptimizer.findOptimalStops(route, {...});
    
    // Get ETA
    const eta = await routeOptimizer.calculateAdvancedETA(route, {...}, {...});
    
    // Show summary
    showSummary({ route, stops, eta });
    
    setStage('active');
  };

  // Step 3: Monitor & Optimize
  const handleMonitoring = () => {
    // Subscribe to live updates
    routeOptimizer.subscribeToLiveOptimization(vehicleId, destination, 
      (position) => updateVehicleLocation(position),
      (suggestion) => showOptimization(suggestion)
    );
  };

  return (
    <div className="space-y-6">
      {/* Planner */}
      {stage === 'planning' && (
        <EnhancedRoutePlanner onComplete={handleRoutePlanned} />
      )}

      {/* Review */}
      {stage === 'review' && (
        <div>
          <AdvancedRouteMap route={route} />
          <RouteAnalyticsDashboard route={route} />
          <button onClick={handleStartRoute}>Start Route</button>
        </div>
      )}

      {/* Active */}
      {stage === 'active' && (
        <div>
          <LiveTracking route={route} onMonitoring={handleMonitoring} />
          {alerts.map(alert => <AlertCard key={alert.id} alert={alert} />)}
        </div>
      )}

      {/* Alerts */}
      {alerts.length > 0 && (
        <div className="alerts">
          {alerts.map(alert => (
            <div key={alert.id} className={`alert alert-${alert.severity}`}>
              {alert.message}
            </div>
          ))}
        </div>
      )}
    </div>
  );
}
```

---

## Advanced Patterns

### Caching and Performance
```javascript
// Services automatically cache for 5 minutes
// To force refresh:
routeOptimizer.clearCache();
```

### Error Handling
```javascript
try {
  const route = await routeOptimizer.calculateOptimizedRoute(...);
} catch (error) {
  console.error('Route calculation failed:', error);
  // System will gracefully degrade
}
```

### WebSocket Integration
```javascript
const ws = routeOptimizer.subscribeToLiveOptimization(vehicleId, destination, ...);

if (ws.isConnected()) {
  // Process live updates
} else {
  // Fall back to polling
}
```

---

## Performance Tips

1. **Cache results** - Don't recalculate identical routes
2. **Batch updates** - Update multiple waypoints before recalculating
3. **Use profiles** - Pre-defined profiles are faster than custom settings
4. **Limit history** - Only load relevant historical data for trends
5. **Progressive loading** - Show map while data loads

---

**These examples cover 95% of common use cases!**
