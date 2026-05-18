import axios from 'axios';

const API_BASE = import.meta.env.MODE === 'development' ? 'http://localhost:8000/api' : 'https://pulsetrack-back.onrender.com/api/v1';

/**
 * Advanced Route Optimizer Service
 * Features: Multi-waypoint optimization, dynamic rerouting, fuel optimization, predictive ETA
 */

class RouteOptimizer {
  constructor() {
    this.trafficCache = new Map();
    this.routeCache = new Map();
    this.cacheExpiry = 5 * 60 * 1000; // 5 minutes
  }

  /**
   * Calculate optimized route with multiple waypoints
   */
  async calculateOptimizedRoute(origin, destination, waypoints = [], options = {}) {
    try {
      const cacheKey = `${origin.lat},${origin.lng}→${destination.lat},${destination.lng}→${waypoints.map(w => `${w.lat},${w.lng}`).join('→')}`;
      
      if (this.routeCache.has(cacheKey)) {
        const cached = this.routeCache.get(cacheKey);
        if (Date.now() - cached.timestamp < this.cacheExpiry) {
          return cached.data;
        }
      }

      const response = await axios.post(`${API_BASE}/routes/calculate-advanced/`, {
        origin,
        destination,
        waypoints,
        profile: options.profile || 'balanced', // balanced, fastest, fuel_optimal, safest
        avoidHazards: options.avoidHazards !== false,
        useRealTimeTraffic: options.useRealTimeTraffic !== false,
        vehicleId: options.vehicleId,
        weight: options.weight || 0,
        fuelTankCapacity: options.fuelTankCapacity || 250,
      });

      const routeData = this.enrichRouteData(response.data);
      this.routeCache.set(cacheKey, { data: routeData, timestamp: Date.now() });
      return routeData;
    } catch (error) {
      console.error('Error calculating optimized route:', error);
      throw error;
    }
  }

  /**
   * Get dynamic re-route based on current conditions
   */
  async getDynamicReroute(currentLocation, destination, originalRoute, options = {}) {
    try {
      const response = await axios.post(`${API_BASE}/routes/reroute/`, {
        currentLocation,
        destination,
        originalRoute,
        reason: options.reason || 'traffic', // traffic, hazard, fuel, accident
        vehicleId: options.vehicleId,
      });

      return {
        ...response.data,
        savings: this.calculateSavings(originalRoute, response.data),
        changeReason: options.reason,
      };
    } catch (error) {
      console.error('Error calculating dynamic reroute:', error);
      throw error;
    }
  }

  /**
   * Predict traffic conditions for a route segment
   */
  async predictTraffic(route, departureTime = new Date()) {
    try {
      const response = await axios.post(`${API_BASE}/traffic/predict/`, {
        route,
        departureTime,
        lookAheadHours: 3,
      });

      return {
        segments: response.data.segments,
        averageDelay: response.data.averageDelay,
        peakCongestionTime: response.data.peakCongestionTime,
        congestionIndex: response.data.congestionIndex, // 0-1, where 1 is complete gridlock
      };
    } catch (error) {
      console.error('Error predicting traffic:', error);
      return { segments: [], averageDelay: 0, congestionIndex: 0 };
    }
  }

  /**
   * Optimize for fuel consumption
   */
  async optimizeForFuel(route, vehicleProfile = {}) {
    try {
      const response = await axios.post(`${API_BASE}/routes/optimize-fuel/`, {
        route,
        vehicleProfile: {
          fuelConsumption: vehicleProfile.fuelConsumption || 8, // km/liter
          maxSpeed: vehicleProfile.maxSpeed || 120,
          weight: vehicleProfile.weight || 5000,
          type: vehicleProfile.type || 'truck',
        },
        fuelPrice: vehicleProfile.fuelPrice || 1.5,
      });

      return {
        ...response.data,
        estimatedCost: response.data.totalFuel * vehicleProfile.fuelPrice,
        co2Emissions: response.data.totalFuel * 2.31, // kg (average for diesel)
      };
    } catch (error) {
      console.error('Error optimizing for fuel:', error);
      throw error;
    }
  }

  /**
   * Calculate accurate ETA with traffic prediction
   */
  async calculateAdvancedETA(route, currentLocation, vehicleProfile = {}) {
    try {
      const response = await axios.post(`${API_BASE}/routes/calculate-eta/`, {
        route,
        currentLocation,
        vehicleProfile,
        includeConfidenceInterval: true,
      });

      return {
        eta: new Date(response.data.eta),
        estimatedTravelTime: response.data.estimatedTravelTime, // minutes
        confidence: response.data.confidence, // 0-1
        confidenceInterval: {
          optimistic: response.data.optimistic, // Best case in minutes
          pessimistic: response.data.pessimistic, // Worst case in minutes
        },
        breakSuggestions: response.data.breakSuggestions || [],
        factorsAffectingETA: response.data.factors || [],
      };
    } catch (error) {
      console.error('Error calculating advanced ETA:', error);
      throw error;
    }
  }

  /**
   * Detect hazards along route
   */
  async detectHazards(route, options = {}) {
    try {
      const response = await axios.post(`${API_BASE}/routes/hazards/`, {
        route,
        hazardTypes: options.hazardTypes || [
          'construction',
          'accident',
          'weather',
          'congestion',
          'roadwork',
          'pothole',
        ],
      });

      return {
        hazards: response.data.hazards || [],
        severityLevel: response.data.severityLevel, // low, medium, high, critical
        recommendations: response.data.recommendations || [],
      };
    } catch (error) {
      console.error('Error detecting hazards:', error);
      return { hazards: [], severityLevel: 'low', recommendations: [] };
    }
  }

  /**
   * Find optimal fuel/rest stops
   */
  async findOptimalStops(route, vehicleProfile = {}) {
    try {
      const response = await axios.post(`${API_BASE}/routes/find-stops/`, {
        route,
        stopTypes: ['fuel', 'rest', 'food', 'maintenance'],
        fuelTankCapacity: vehicleProfile.fuelTankCapacity || 250,
        fuelConsumption: vehicleProfile.fuelConsumption || 8,
        driverRestRequirement: vehicleProfile.driverRestRequirement || 4.5, // hours before rest
      });

      return {
        fuelStops: response.data.fuelStops || [],
        restStops: response.data.restStops || [],
        maintenanceStops: response.data.maintenanceStops || [],
        estimatedStopDuration: response.data.totalStopDuration || 0, // minutes
      };
    } catch (error) {
      console.error('Error finding optimal stops:', error);
      return { fuelStops: [], restStops: [], maintenanceStops: [], estimatedStopDuration: 0 };
    }
  }

  /**
   * Get alternative routes with comparisons
   */
  async getAlternativeRoutes(origin, destination, options = {}) {
    try {
      const response = await axios.post(`${API_BASE}/routes/alternatives/`, {
        origin,
        destination,
        count: options.count || 3,
        compareBy: options.compareBy || ['duration', 'distance', 'fuel'], // What to compare
      });

      return response.data.routes.map((route, index) => ({
        ...route,
        rank: index + 1,
        comparison: {
          duration: route.duration,
          distance: route.distance,
          fuel: route.estimatedFuel,
          cost: route.estimatedCost,
          safety: route.safetyScore, // 0-100
          scenery: route.sceneryScore, // 0-100
        },
      }));
    } catch (error) {
      console.error('Error getting alternative routes:', error);
      throw error;
    }
  }

  /**
   * Real-time route tracking with live optimization
   */
  subscribeToLiveOptimization(vehicleId, destination, onUpdate, onOptimization) {
    const ws = new WebSocket(`ws://localhost:8000/api/routes/live-optimize/${vehicleId}/?destination=${destination}`);

    ws.onmessage = (event) => {
      try {
        const data = JSON.parse(event.data);

        if (data.type === 'position_update') {
          onUpdate && onUpdate(data.position);
        } else if (data.type === 'optimization_suggestion') {
          onOptimization && onOptimization({
            newRoute: data.newRoute,
            reason: data.reason,
            savings: data.savings,
            recommendation: data.recommendation,
          });
        } else if (data.type === 'hazard_alert') {
          onUpdate && onUpdate({ hazardAlert: data });
        }
      } catch (err) {
        console.error('Error parsing live optimization data:', err);
      }
    };

    ws.onerror = (err) => console.error('WebSocket error:', err);

    return {
      close: () => ws.close(),
      isConnected: () => ws.readyState === WebSocket.OPEN,
    };
  }

  /**
   * Enrich route data with calculated metrics
   */
  enrichRouteData(route) {
    return {
      ...route,
      summary: {
        distance: route.distance || 0,
        duration: route.duration || 0,
        waypoints: route.waypoints?.length || 0,
        estimatedFuel: route.estimatedFuel || 0,
        estimatedCost: route.estimatedCost || 0,
      },
      metrics: {
        averageSpeed: route.distance / (route.duration / 60), // km/h
        elevationGain: route.elevationGain || 0,
        elevationLoss: route.elevationLoss || 0,
        difficulty: this.calculateRouteDifficulty(route),
      },
      timeline: this.generateRouteTimeline(route),
    };
  }

  /**
   * Calculate route difficulty (0-100)
   */
  calculateRouteDifficulty(route) {
    let difficulty = 0;
    
    if (route.hazardCount) difficulty += route.hazardCount * 10;
    if (route.elevationGain > 500) difficulty += 20;
    if (route.congestionIndex > 0.5) difficulty += 25;
    if (route.roadCondition === 'poor') difficulty += 15;
    
    return Math.min(difficulty, 100);
  }

  /**
   * Generate timeline with checkpoints and events
   */
  generateRouteTimeline(route) {
    const timeline = [];
    let cumulativeTime = 0;
    let cumulativeDistance = 0;

    route.segments?.forEach((segment, index) => {
      cumulativeTime += segment.duration;
      cumulativeDistance += segment.distance;

      timeline.push({
        step: index + 1,
        location: segment.name,
        time: cumulativeTime,
        distance: cumulativeDistance,
        type: segment.type, // checkpoint, hazard, stop, etc.
        action: segment.action,
      });
    });

    return timeline;
  }

  /**
   * Calculate savings from reroute
   */
  calculateSavings(originalRoute, newRoute) {
    return {
      timeSaved: (originalRoute.duration - newRoute.duration) / 60, // minutes
      distanceSaved: originalRoute.distance - newRoute.distance, // km
      fuelSaved: (originalRoute.estimatedFuel - newRoute.estimatedFuel) || 0, // liters
      costSaved: (originalRoute.estimatedCost - newRoute.estimatedCost) || 0, // currency
    };
  }

  /**
   * Clear cache
   */
  clearCache() {
    this.trafficCache.clear();
    this.routeCache.clear();
  }
}

export default new RouteOptimizer();
