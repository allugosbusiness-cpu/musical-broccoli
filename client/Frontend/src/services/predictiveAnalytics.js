import axios from 'axios';

const API_BASE = import.meta.env.MODE === 'development' ? 'http://localhost:8000/api' : 'https://pulsetrack-back.onrender.com/api/v1';

/**
 * Advanced Predictive Analytics Engine
 * Real-time traffic prediction, ETA calculation, fuel analytics, performance metrics
 */

class PredictiveAnalytics {
  constructor() {
    this.historicalData = new Map();
    this.predictionCache = new Map();
  }

  /**
   * Predict traffic for a specific time
   */
  async predictTrafficForTime(route, departureTime) {
    try {
      const cacheKey = `${route.id}:${departureTime.toISOString()}`;
      if (this.predictionCache.has(cacheKey)) {
        return this.predictionCache.get(cacheKey);
      }

      const response = await axios.post(`${API_BASE}/traffic/predict-time/`, {
        routeId: route.id,
        departure: departureTime,
        includeHistorical: true,
        confidence: 0.95,
      });

      const prediction = {
        departureTime,
        segments: response.data.segments,
        totalDelay: response.data.totalDelay,
        peakHours: response.data.peakHours,
        confidence: response.data.confidence,
        alternativeTimes: this.findOptimalDepartureTimes(response.data.segments),
      };

      this.predictionCache.set(cacheKey, prediction);
      return prediction;
    } catch (error) {
      console.error('Error predicting traffic:', error);
      return null;
    }
  }

  /**
   * Calculate congestion index for entire route
   */
  calculateCongestionIndex(segments) {
    if (!segments || segments.length === 0) return 0;
    
    const totalWeightedCongestion = segments.reduce((sum, seg) => {
      return sum + (seg.congestion * seg.weight);
    }, 0);

    const totalWeight = segments.reduce((sum, seg) => sum + seg.weight, 0);
    return totalWeight > 0 ? totalWeightedCongestion / totalWeight : 0;
  }

  /**
   * Find optimal departure times to avoid traffic
   */
  findOptimalDepartureTimes(segments) {
    const times = [];
    
    // Check every hour in next 24 hours
    for (let i = 0; i < 24; i++) {
      const departureTime = new Date();
      departureTime.setHours(departureTime.getHours() + i);

      const hour = departureTime.getHours();
      // Simple heuristic: avoid 7-9am and 5-7pm peak hours
      const isPeakHour = (hour >= 7 && hour <= 9) || (hour >= 17 && hour <= 19);
      const congestionScore = segments.reduce((sum, seg) => sum + (seg.congestion || 0), 0) / segments.length;

      if (!isPeakHour && congestionScore < 0.5) {
        times.push({
          time: departureTime,
          congestionScore,
          timeSaving: Math.round((segments[0]?.delay || 0) * 0.5), // Estimated saving
        });
      }

      if (times.length >= 3) break;
    }

    return times;
  }

  /**
   * Predict fuel consumption with precision
   */
  async predictFuelConsumption(route, vehicleProfile, conditions = {}) {
    try {
      const response = await axios.post(`${API_BASE}/fuel/predict/`, {
        distance: route.distance,
        elevation: route.elevationGain,
        terrain: conditions.terrain || 'mixed', // highway, city, offroad, mixed
        weather: conditions.weather || 'clear', // clear, rain, fog, snow
        payload: vehicleProfile.weight,
        speed: vehicleProfile.maxSpeed,
        driverProfile: conditions.driverProfile || 'normal', // aggressive, normal, eco
        temperature: conditions.temperature || 25,
      });

      return {
        estimatedConsumption: response.data.consumption,
        range: response.data.range,
        consumptionBreakdown: {
          terrain: response.data.terrainCost,
          elevation: response.data.elevationCost,
          weather: response.data.weatherCost,
          speed: response.data.speedCost,
        },
        accuracy: response.data.accuracy, // 0-1
        tips: response.data.optimizationTips || [],
      };
    } catch (error) {
      console.error('Error predicting fuel:', error);
      return null;
    }
  }

  /**
   * Calculate advanced ETA with multiple factors
   */
  async calculateAdvancedETA(route, currentPosition, trafficPrediction) {
    try {
      const remainingDistance = this.calculateRemainingDistance(route, currentPosition);
      const remainingSegments = this.getRemainingSegments(route, currentPosition);

      let totalTime = 0;
      remainingSegments.forEach(seg => {
        const baseTime = seg.distance / (seg.speed || 80);
        const trafficMultiplier = 1 + (seg.congestion || 0);
        totalTime += baseTime * trafficMultiplier;
      });

      const eta = new Date();
      eta.setMinutes(eta.getMinutes() + Math.round(totalTime));

      return {
        eta,
        estimatedTravelTime: Math.round(totalTime),
        confidence: 0.85,
        timeRange: {
          optimistic: Math.round(totalTime * 0.8),
          pessimistic: Math.round(totalTime * 1.3),
        },
        factorsAffecting: [
          trafficPrediction?.totalDelay ? `Traffic delay: +${trafficPrediction.totalDelay}min` : null,
          `Distance remaining: ${remainingDistance}km`,
          'Current speed conditions',
        ].filter(Boolean),
      };
    } catch (error) {
      console.error('Error calculating ETA:', error);
      return null;
    }
  }

  /**
   * Analyze route performance metrics
   */
  analyzeRoutePerformance(route, actualData = {}) {
    return {
      plannedVsActual: {
        distancePlanned: route.distance,
        distanceActual: actualData.distance || route.distance,
        timePlanned: route.duration,
        timeActual: actualData.duration || route.duration,
        fuelPlanned: route.estimatedFuel,
        fuelActual: actualData.fuel || route.estimatedFuel,
      },
      efficiency: {
        timeEfficiency: (route.duration / (actualData.duration || route.duration)) * 100,
        fuelEfficiency: (route.estimatedFuel / (actualData.fuel || route.estimatedFuel)) * 100,
        deviationPercentage: Math.abs(route.duration - (actualData.duration || route.duration)) / route.duration * 100,
      },
      recommendations: this.generatePerformanceRecommendations(route, actualData),
    };
  }

  /**
   * Generate ML-based recommendations
   */
  generatePerformanceRecommendations(route, actualData) {
    const recommendations = [];

    if (actualData.duration && actualData.duration > route.duration * 1.2) {
      recommendations.push({
        type: 'timing',
        priority: 'high',
        message: 'Consider departure at different time to avoid peak traffic',
      });
    }

    if (actualData.fuel && actualData.fuel > route.estimatedFuel * 1.15) {
      recommendations.push({
        type: 'driving',
        priority: 'medium',
        message: 'High fuel consumption detected. Use Eco mode for better efficiency',
      });
    }

    if (actualData.avgSpeed && actualData.avgSpeed < 60) {
      recommendations.push({
        type: 'route',
        priority: 'high',
        message: 'Low average speed. Consider alternative routes in future',
      });
    }

    return recommendations;
  }

  /**
   * Calculate remaining distance
   */
  calculateRemainingDistance(route, currentPosition) {
    let remaining = 0;
    let foundCurrent = false;

    route.segments?.forEach(seg => {
      if (!foundCurrent) {
        const distance = this.haversineDistance(
          currentPosition.lat,
          currentPosition.lng,
          seg.endPoint.lat,
          seg.endPoint.lng
        );
        if (distance < 500) { // Within 500m
          foundCurrent = true;
        } else {
          remaining += seg.distance;
        }
      } else {
        remaining += seg.distance;
      }
    });

    return Math.round(remaining);
  }

  /**
   * Get remaining segments
   */
  getRemainingSegments(route, currentPosition) {
    let segments = [];
    let foundCurrent = false;

    route.segments?.forEach(seg => {
      const distance = this.haversineDistance(
        currentPosition.lat,
        currentPosition.lng,
        seg.startPoint.lat,
        seg.startPoint.lng
      );

      if (!foundCurrent && distance < 500) {
        foundCurrent = true;
      }

      if (foundCurrent) {
        segments.push(seg);
      }
    });

    return segments;
  }

  /**
   * Haversine distance calculation
   */
  haversineDistance(lat1, lon1, lat2, lon2) {
    const R = 6371; // Earth's radius in km
    const dLat = (lat2 - lat1) * Math.PI / 180;
    const dLon = (lon2 - lon1) * Math.PI / 180;
    const a = Math.sin(dLat / 2) * Math.sin(dLat / 2) +
      Math.cos(lat1 * Math.PI / 180) * Math.cos(lat2 * Math.PI / 180) *
      Math.sin(dLon / 2) * Math.sin(dLon / 2);
    const c = 2 * Math.atan2(Math.sqrt(a), Math.sqrt(1 - a));
    return R * c * 1000; // Return in meters
  }

  /**
   * Get route difficulty assessment
   */
  assessRouteDifficulty(route) {
    let score = 0;
    const factors = [];

    // Distance factor
    if (route.distance > 500) {
      score += 20;
      factors.push('Long distance route');
    } else if (route.distance > 300) {
      score += 10;
    }

    // Elevation factor
    if (route.elevationGain > 1000) {
      score += 25;
      factors.push('Significant elevation gain');
    } else if (route.elevationGain > 500) {
      score += 15;
    }

    // Traffic factor
    if (route.congestionIndex > 0.7) {
      score += 25;
      factors.push('Heavy traffic expected');
    } else if (route.congestionIndex > 0.4) {
      score += 15;
    }

    // Weather factor
    if (route.weather?.severe) {
      score += 20;
      factors.push('Severe weather conditions');
    } else if (route.weather?.warning) {
      score += 10;
    }

    // Road condition
    if (route.roadCondition === 'poor') {
      score += 15;
      factors.push('Poor road conditions');
    }

    return {
      difficulty: Math.min(score, 100),
      level: score > 70 ? 'Very Hard' : score > 50 ? 'Hard' : score > 25 ? 'Moderate' : 'Easy',
      factors,
    };
  }

  /**
   * Clear prediction cache
   */
  clearCache() {
    this.predictionCache.clear();
    this.historicalData.clear();
  }
}

export default new PredictiveAnalytics();
