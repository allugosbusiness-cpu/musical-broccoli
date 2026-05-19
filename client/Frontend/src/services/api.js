import axios from 'axios';
import API_CONFIG, { RETRY_CONFIG, getValidatedApiUrl, checkApiHealth } from '../config/apiConfig';

// Log environment info
console.log(`🌍 Environment: ${import.meta.env.MODE}`);

// Initialize axios with retry logic
const api = axios.create({
  baseURL: getValidatedApiUrl(),
  headers: API_CONFIG.headers,
  timeout: API_CONFIG.timeout,
  withCredentials: true, // Important: Include cookies in cross-origin requests
});

// Helper function to get CSRF token from cookies
const getCsrfToken = () => {
  const name = 'csrftoken';
  let cookieValue = null;
  if (document.cookie && document.cookie !== '') {
    const cookies = document.cookie.split(';');
    for (let i = 0; i < cookies.length; i++) {
      const cookie = cookies[i].trim();
      if (cookie.substring(0, name.length + 1) === (name + '=')) {
        cookieValue = decodeURIComponent(cookie.substring(name.length + 1));
        break;
      }
    }
  }
  return cookieValue;
};

// Request interceptor to add CSRF token to state-changing requests
api.interceptors.request.use(
  config => {
    // Add CSRF token for POST, PUT, PATCH, DELETE requests
    if (['post', 'put', 'patch', 'delete'].includes(config.method)) {
      const csrfToken = getCsrfToken();
      if (csrfToken) {
        config.headers['X-CSRFToken'] = csrfToken;
      }
    }
    return config;
  },
  error => {
    return Promise.reject(error);
  }
);

// Log API base URL on startup
console.log(`🔗 Frontend API Base: ${API_CONFIG.baseUrl}`);

// Trucks
export const getTrucks = async (filters = {}) => {
  try {
    const response = await api.get('/trucks/', { params: filters });
    return response.data.results || response.data;
  } catch (error) {
    console.error('Error fetching trucks:', error);
    return [];
  }
};

export const getTruck = async (id) => {
  try {
    const response = await api.get(`/trucks/${id}/`);
    return response.data;
  } catch (error) {
    console.error('Error fetching truck:', error);
    return null;
  }
};

export const createTruck = async (data) => {
  try {
    const response = await api.post('/trucks/', data);
    return response.data;
  } catch (error) {
    console.error('Error creating truck:', error);
    throw error;
  }
};

export const updateTruck = async (id, data) => {
  try {
    const response = await api.patch(`/trucks/${id}/`, data);
    return response.data;
  } catch (error) {
    console.error('Error updating truck:', error);
    return null;
  }
};

export const deleteTruck = async (id) => {
  try {
    const response = await api.delete(`/trucks/${id}/`);
    return response.data;
  } catch (error) {
    console.error('Error deleting truck:', error);
    throw error;
  }
};

export const updateTruckStatus = async (id, status, location, speed, progress) => {
  try {
    const response = await api.patch(`/trucks/${id}/update_status/`, {
      status,
      location,
      speed,
      progress,
    });
    return response.data;
  } catch (error) {
    console.error('Error updating truck status:', error);
    return null;
  }
};

// Checkpoints
export const getCheckpoints = async (truckId) => {
  try {
    const response = await api.get('/checkpoints/', { params: { truck: truckId } });
    return response.data.results || response.data;
  } catch (error) {
    console.error('Error fetching checkpoints:', error);
    return [];
  }
};

export const createCheckpoint = async (truckId, data) => {
  try {
    const response = await api.post('/checkpoints/', {
      truck: truckId,
      ...data,
    });
    return response.data;
  } catch (error) {
    console.error('Error creating checkpoint:', error);
    return null;
  }
};

// Alerts - with extended timeout (30s) for large alert batches
export const getAlerts = async (filters = {}) => {
  try {
    // Alerts can have large response sizes, use longer timeout (30 seconds instead of 15)
    // Also add limit parameter to prevent loading thousands of alerts (default 100)
    const params = {
      limit: 100,  // Get last 100 alerts
      ...filters   // Can override with custom limit if needed
    };
    
    const response = await api.get('/alerts/', { 
      params,
      timeout: 30000  // 30 seconds for alerts endpoint
    });
    return response.data.results || response.data;
  } catch (error) {
    console.error('Error fetching alerts:', error);
    return [];
  }
};

export const createAlert = async (truckId, alertType, message) => {
  try {
    const response = await api.post('/alerts/', {
      truck: truckId,
      alert_type: alertType,
      message,
    });
    return response.data;
  } catch (error) {
    console.error('Error creating alert:', error);
    return null;
  }
};

export const resolveAlert = async (id) => {
  try {
    const response = await api.patch(`/alerts/${id}/resolve/`);
    return response.data;
  } catch (error) {
    console.error('Error resolving alert:', error);
    return null;
  }
};

// KPIs
export const getKPIs = async () => {
  try {
    const response = await api.get('/kpis/latest/');
    return response.data;
  } catch (error) {
    console.error('Error fetching KPIs:', error);
    return null;
  }
};

// Cargo
export const getCargo = async (truckId) => {
  try {
    const response = await api.get('/cargo/', { params: { truck: truckId } });
    return response.data.results || response.data;
  } catch (error) {
    console.error('Error fetching cargo:', error);
    return null;
  }
};

// Routes - ML-Powered Routing System
export const createOptimizedRoute = async (truckId, origin, destination, originCoordinates, destinationCoordinates) => {
  try {
    const response = await api.post('/routes/create_optimized_route/', {
      truck_id: truckId,
      origin,
      destination,
      origin_coordinates: originCoordinates,
      destination_coordinates: destinationCoordinates,
    });
    return response.data;
  } catch (error) {
    console.error('Error creating optimized route:', error);
    throw error;
  }
};

export const getRoutes = async (filters = {}) => {
  try {
    const response = await api.get('/routes/', { params: filters });
    return response.data.results || response.data;
  } catch (error) {
    console.error('Error fetching routes:', error);
    return [];
  }
};

export const getRoute = async (routeId) => {
  try {
    const response = await api.get(`/routes/${routeId}/`);
    return response.data;
  } catch (error) {
    console.error('Error fetching route:', error);
    return null;
  }
};

export const getActiveRoutes = async () => {
  try {
    const response = await api.get('/routes/active_routes/');
    return response.data.results || response.data;
  } catch (error) {
    console.error('Error fetching active routes:', error);
    return [];
  }
};

export const getTruckRoutes = async (truckId) => {
  try {
    const response = await api.get('/routes/truck_routes/', { params: { truck_id: truckId } });
    return response.data.results || response.data;
  } catch (error) {
    console.error('Error fetching truck routes:', error);
    return [];
  }
};

export const updateRouteProgress = async (routeId, distanceTravelled, timeElapsed, waypointIndex) => {
  try {
    const response = await api.patch(`/routes/${routeId}/update_progress/`, {
      distance_travelled_km: distanceTravelled,
      time_elapsed_hours: timeElapsed,
      current_waypoint_index: waypointIndex,
    });
    return response.data;
  } catch (error) {
    console.error('Error updating route progress:', error);
    return null;
  }
};

export const startRoute = async (routeId) => {
  try {
    const response = await api.patch(`/routes/${routeId}/start_route/`);
    return response.data;
  } catch (error) {
    console.error('Error starting route:', error);
    return null;
  }
};

export const completeRoute = async (routeId) => {
  try {
    const response = await api.patch(`/routes/${routeId}/complete_route/`);
    return response.data;
  } catch (error) {
    console.error('Error completing route:', error);
    return null;
  }
};

// Smart Routing - ML & AI Features
export const getTruckTrail = async (truckId, limit = 100) => {
  try {
    const response = await api.get(`/trucks/${truckId}/truck_trail/`, { 
      params: { limit } 
    });
    return response.data.trail_points || [];
  } catch (error) {
    console.error('Error fetching truck trail:', error);
    return [];
  }
};

export const getTruckTrailWithDirections = async (truckId, limit = 200) => {
  try {
    // Use v1 API endpoint
    const baseUrl = 'https://pulsetrack-back.onrender.com';
    const response = await axios.get(`${baseUrl}/api/v1/trucks/${truckId}/truck_trail_with_directions/`, { 
      params: { limit },
      withCredentials: true
    });
    return response.data;
  } catch (error) {
    console.error('Error fetching truck trail with directions:', error);
    return null;
  }
};

export const getQuickRoutes = async (truckId) => {
  try {
    const response = await api.get(`/trucks/${truckId}/quick_routes/`);
    return response.data.suggested_routes || [];
  } catch (error) {
    console.error('Error fetching quick routes:', error);
    return [];
  }
};

export const recordTruckPosition = async (truckId, latitude, longitude, speed = 0, heading = null, altitude = null, accuracy = null, routeId = null) => {
  try {
    const response = await api.post(`/trucks/${truckId}/record_position/`, {
      latitude,
      longitude,
      speed,
      heading,
      altitude,
      accuracy,
      route_id: routeId,
    });
    return response.data;
  } catch (error) {
    console.error('Error recording truck position:', error);
    return null;
  }
};

// Real-time GPS Position Recording for Mobile App
export const recordGPSPosition = async (truckId, latitude, longitude, speed = 0, heading = null, altitude = null, accuracy = null) => {
  try {
    const response = await api.post(`/trucks/${truckId}/record_gps_position/`, {
      latitude,
      longitude,
      speed,
      heading,
      altitude,
      accuracy,
    });
    return response.data;
  } catch (error) {
    console.error('Error recording GPS position:', error);
    throw error;
  }
};

// Get All Trucks with Real-Time Trails (V2 API)
export const getAllTrucksWithTrails = async () => {
  try {
    // Using V2 API endpoint for trucks
    const response = await apiV1.get('/trucks/');
    return response.data.results || response.data || [];
  } catch (error) {
    console.error('Error fetching trucks with trails:', error);
    // Fallback to empty array
    return [];
  }
};

export const calculateOptimalRoute = async (truckId, destination, currentLocation = null) => {
  try {
    const response = await api.post('/trucks/calculate_optimal_route/', {
      truck_id: truckId,
      destination,
      current_location: currentLocation,
    });
    return response.data;
  } catch (error) {
    console.error('Error calculating optimal route:', error);
    return null;
  }
};

// ==================== Advanced Routing Features ====================

/**
 * Calculate advanced optimized route with multi-waypoint support
 */
export const calculateAdvancedRoute = async (origin, destination, waypoints = [], options = {}) => {
  try {
    const response = await api.post('/routes/calculate-advanced/', {
      origin,
      destination,
      waypoints,
      profile: options.profile || 'balanced',
      avoidHazards: options.avoidHazards !== false,
      useRealTimeTraffic: options.useRealTimeTraffic !== false,
      vehicleId: options.vehicleId,
      weight: options.weight || 0,
      fuelTankCapacity: options.fuelTankCapacity || 250,
    });
    return response.data;
  } catch (error) {
    console.error('Error calculating advanced route:', error);
    throw error;
  }
};

/**
 * Get dynamic reroute suggestions
 */
export const getDynamicReroute = async (currentLocation, destination, originalRoute, options = {}) => {
  try {
    const response = await api.post('/routes/reroute/', {
      currentLocation,
      destination,
      originalRoute,
      reason: options.reason || 'traffic',
      vehicleId: options.vehicleId,
    });
    return response.data;
  } catch (error) {
    console.error('Error getting dynamic reroute:', error);
    throw error;
  }
};

/**
 * Predict traffic for route
 */
export const predictTraffic = async (route, departureTime = new Date()) => {
  try {
    const response = await api.post('/traffic/predict/', {
      route,
      departureTime,
      lookAheadHours: 3,
    });
    return response.data;
  } catch (error) {
    console.error('Error predicting traffic:', error);
    return { segments: [], averageDelay: 0, congestionIndex: 0 };
  }
};

/**
 * Optimize route for fuel consumption
 */
export const optimizeForFuel = async (route, vehicleProfile = {}) => {
  try {
    const response = await api.post('/routes/optimize-fuel/', {
      route,
      vehicleProfile: {
        fuelConsumption: vehicleProfile.fuelConsumption || 8,
        maxSpeed: vehicleProfile.maxSpeed || 120,
        weight: vehicleProfile.weight || 5000,
        type: vehicleProfile.type || 'truck',
      },
      fuelPrice: vehicleProfile.fuelPrice || 1.5,
    });
    return response.data;
  } catch (error) {
    console.error('Error optimizing for fuel:', error);
    throw error;
  }
};

/**
 * Calculate advanced ETA with traffic prediction
 */
export const calculateAdvancedETA = async (route, currentLocation, vehicleProfile = {}) => {
  try {
    const response = await api.post('/routes/calculate-eta/', {
      route,
      currentLocation,
      vehicleProfile,
      includeConfidenceInterval: true,
    });
    return response.data;
  } catch (error) {
    console.error('Error calculating advanced ETA:', error);
    throw error;
  }
};

/**
 * Detect hazards along route
 */
export const detectHazards = async (route, options = {}) => {
  try {
    const response = await api.post('/routes/hazards/', {
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
    return response.data;
  } catch (error) {
    console.error('Error detecting hazards:', error);
    return { hazards: [], severityLevel: 'low', recommendations: [] };
  }
};

/**
 * Find optimal fuel/rest stops
 */
export const findOptimalStops = async (route, vehicleProfile = {}) => {
  try {
    const response = await api.post('/routes/find-stops/', {
      route,
      stopTypes: ['fuel', 'rest', 'food', 'maintenance'],
      fuelTankCapacity: vehicleProfile.fuelTankCapacity || 250,
      fuelConsumption: vehicleProfile.fuelConsumption || 8,
      driverRestRequirement: vehicleProfile.driverRestRequirement || 4.5,
    });
    return response.data;
  } catch (error) {
    console.error('Error finding optimal stops:', error);
    return { fuelStops: [], restStops: [], maintenanceStops: [], estimatedStopDuration: 0 };
  }
};

/**
 * Get alternative routes for comparison
 */
export const getAlternativeRoutes = async (origin, destination, options = {}) => {
  try {
    const response = await api.post('/routes/alternatives/', {
      origin,
      destination,
      count: options.count || 3,
      compareBy: options.compareBy || ['duration', 'distance', 'fuel'],
    });
    return response.data;
  } catch (error) {
    console.error('Error getting alternative routes:', error);
    throw error;
  }
};

/**
 * Predict fuel consumption for route
 */
export const predictFuelConsumption = async (route, vehicleProfile, conditions = {}) => {
  try {
    const response = await api.post('/fuel/predict/', {
      distance: route.distance,
      elevation: route.elevationGain,
      terrain: conditions.terrain || 'mixed',
      weather: conditions.weather || 'clear',
      payload: vehicleProfile.weight,
      speed: vehicleProfile.maxSpeed,
      driverProfile: conditions.driverProfile || 'normal',
      temperature: conditions.temperature || 25,
    });
    return response.data;
  } catch (error) {
    console.error('Error predicting fuel consumption:', error);
    return null;
  }
};

/**
 * Analyze route performance
 */
export const analyzeRoutePerformance = async (routeId) => {
  try {
    const response = await api.get(`/routes/${routeId}/performance-analytics/`);
    return response.data;
  } catch (error) {
    console.error('Error analyzing route performance:', error);
    return null;
  }
};

/**
 * Get traffic predictions for multiple routes
 */
export const predictTrafficMultiRoute = async (routes, departureTime = new Date()) => {
  try {
    const response = await api.post('/traffic/predict-multi/', {
      routes,
      departureTime,
    });
    return response.data;
  } catch (error) {
    console.error('Error predicting traffic for multiple routes:', error);
    return [];
  }
};

/**
 * Subscribe to live route optimization
 */
export const subscribeLiveOptimization = (vehicleId, destination) => {
  // Note: WebSocket not currently supported for production
  const wsUrl = `wss://pulsetrack-back.onrender.com/api/routes/live-optimize/${vehicleId}/?destination=${destination}`;
  return new WebSocket(wsUrl);
};

// ============================================================
// V2 API ENDPOINTS (New Fleet Management System)
// ============================================================

// Dynamic API URL based on environment
const getApiV1Base = () => {
  if (import.meta.env.MODE === 'development') {
    return 'http://localhost:8000/api/v1';
  }
  // Production: use Render backend
  return 'https://pulsetrack-back.onrender.com/api/v1';
};

const API_V1_BASE = getApiV1Base();

const apiV1 = axios.create({
  baseURL: API_V1_BASE,
  headers: {
    'Content-Type': 'application/json',
  },
  timeout: API_CONFIG.timeout,
  withCredentials: true, // ✅ CRITICAL: Include cookies (for CSRF token, session auth)
});

// ✅ Add CSRF token interceptor to apiV1 (disabled - backend is CSRF-exempt for API endpoints)
apiV1.interceptors.request.use(
  config => {
    // CSSF token disabled for REST API endpoints - backend uses @csrf_exempt
    // If CSRF is re-enabled in future, uncomment code below:
    // if (['post', 'put', 'patch', 'delete'].includes(config.method)) {
    //   const csrfToken = getCsrfToken();
    //   if (csrfToken) {
    //     config.headers['X-CSRFToken'] = csrfToken;
    //     console.log('🔐 [API V1] Added CSRF token to request headers');
    //   } else {
    //     console.warn('⚠️ [API V1] No CSRF token found - request may be rejected');
    //   }
    // }
    return config;
  },
  error => {
    return Promise.reject(error);
  }
);

// V1 Drivers
export const getV1Drivers = async (filters = {}) => {
  try {
    const response = await apiV1.get('/drivers/', { params: filters });
    return response.data.results || response.data || [];
  } catch (error) {
    console.error('Error fetching v1 drivers:', error);
    return [];
  }
};

export const getV1Driver = async (id) => {
  try {
    const response = await apiV1.get(`/drivers/${id}/`);
    return response.data;
  } catch (error) {
    console.error('Error fetching v1 driver:', error);
    return null;
  }
};

export const createV1Driver = async (data) => {
  try {
    const response = await apiV1.post('/drivers/', data);
    return response.data;
  } catch (error) {
    console.error('Error creating v1 driver:', error);
    throw error;
  }
};

export const updateV1Driver = async (id, data) => {
  try {
    const response = await apiV1.patch(`/drivers/${id}/`, data);
    return response.data;
  } catch (error) {
    console.error('Error updating v1 driver:', error);
    return null;
  }
};

export const deleteV1Driver = async (id) => {
  try {
    const response = await apiV1.delete(`/drivers/${id}/`);
    return response.data;
  } catch (error) {
    console.error('Error deleting v1 driver:', error);
    throw error;
  }
};

// V1 Trucks
export const getV1Trucks = async (filters = {}) => {
  try {
    const response = await apiV1.get('/trucks/', { params: filters });
    return response.data.results || response.data || [];
  } catch (error) {
    console.error('Error fetching v1 trucks:', error);
    return [];
  }
};

export const getV1Truck = async (id) => {
  try {
    const response = await apiV1.get(`/trucks/${id}/`);
    return response.data;
  } catch (error) {
    console.error('Error fetching v1 truck:', error);
    return null;
  }
};

export const createV1Truck = async (data) => {
  try {
    console.log('🚚 [API] Creating truck with data:', JSON.stringify(data, null, 2));
    
    // Add default coordinates if not provided (Harare city center)
    const enhancedData = {
      ...data,
      last_latitude: data.last_latitude || -17.8252,
      last_longitude: data.last_longitude || 31.0335
    };
    
    console.log('📤 [API] POST /trucks/ with:', JSON.stringify(enhancedData, null, 2));
    const response = await apiV1.post('/trucks/', enhancedData);
    
    console.log('✅ [API] Response status:', response.status);
    console.log('✅ [API] Response headers:', response.headers);
    console.log('✅ [API] Truck created successfully:', JSON.stringify(response.data, null, 2));
    return response.data;
  } catch (error) {
    console.error('❌ [API] Error creating v1 truck:');
    console.error('   Error name:', error.name);
    console.error('   Error message:', error.message);
    console.error('   Error code:', error.code);
    console.error('   Response Status:', error.response?.status);
    console.error('   Response StatusText:', error.response?.statusText);
    console.error('   Response Data:', error.response?.data);
    console.error('   Response Headers:', error.response?.headers);
    console.error('   Request URL:', error.config?.url);
    console.error('   Request method:', error.config?.method);
    console.error('   Request headers:', error.config?.headers);
    console.error('   Full error object:', error);
    throw error;
  }
};

export const updateV1Truck = async (id, data) => {
  try {
    const response = await apiV1.patch(`/trucks/${id}/`, data);
    return response.data;
  } catch (error) {
    console.error('Error updating v1 truck:', error);
    return null;
  }
};

export const deleteV1Truck = async (id) => {
  try {
    const response = await apiV1.delete(`/trucks/${id}/`);
    return response.data;
  } catch (error) {
    console.error('Error deleting v1 truck:', error);
    throw error;
  }
};

// V1 Missions
export const getV1Missions = async (filters = {}) => {
  try {
    const response = await apiV1.get('/missions/', { params: filters });
    return response.data.results || response.data || [];
  } catch (error) {
    console.error('Error fetching v1 missions:', error);
    return [];
  }
};

export const getV1Mission = async (id) => {
  try {
    const response = await apiV1.get(`/missions/${id}/`);
    return response.data;
  } catch (error) {
    console.error('Error fetching v1 mission:', error);
    return null;
  }
};

export const createV1Mission = async (data) => {
  try {
    const response = await apiV1.post('/missions/', data);
    return response.data;
  } catch (error) {
    console.error('Error creating v1 mission:', error);
    if (error.response) {
      console.error('Error response data:', error.response.data);
      console.error('Error response status:', error.response.status);
      console.error('Error response headers:', error.response.headers);
    }
    throw error;
  }
};


export const updateV1Mission = async (id, data) => {
  try {
    const response = await apiV1.patch(`/missions/${id}/`, data);
    return response.data;
  } catch (error) {
    console.error('Error updating v1 mission:', error);
    return null;
  }
};

export const deleteV1Mission = async (id) => {
  try {
    const response = await apiV1.delete(`/missions/${id}/`);
    return response.data;
  } catch (error) {
    console.error('Error deleting v1 mission:', error);
    throw error;
  }
};

// ✅ NEW: Location tracking and updates
export const updateTruckLocationTracking = async (truckId, latitude, longitude, speedKmh = 0, timestamp = null) => {
  try {
    const response = await apiV1.post('/truck-tracking/location-speed/', {
      truck_id: truckId,
      latitude,
      longitude,
      speed_kmh: speedKmh,
      timestamp: timestamp || new Date().toISOString()
    });
    console.log('✅ Truck location updated:', response.data);
    return response.data;
  } catch (error) {
    console.error('Error updating truck location:', error);
    throw error;
  }
};

export const getTruckCurrentLocation = async (truckId) => {
  try {
    const response = await apiV1.get(`/truck-tracking/location-speed/${truckId}/`);
    return response.data;
  } catch (error) {
    console.error('Error getting truck location:', error);
    return null;
  }
};

export const getAllTrucksLocations = async () => {
  try {
    const response = await apiV1.get('/truck-tracking/all-locations/');
    return response.data;
  } catch (error) {
    console.error('Error getting all trucks locations:', error);
    return [];
  }
};

export const reverseGeocodeLocation = async (latitude, longitude) => {
  try {
    const response = await apiV1.get('/locations/reverse-geocode/', {
      params: { lat: latitude, lon: longitude }
    });
    return response.data;
  } catch (error) {
    console.error('Error reverse geocoding location:', error);
    return {
      lat: latitude,
      lon: longitude,
      name: `Location (${latitude.toFixed(4)}, ${longitude.toFixed(4)})`,
      accuracy: 'custom'
    };
  }
};

export const sendMissionLocationUpdate = async (missionId, latitude, longitude, status = null) => {
  try {
    const data = {
      current_latitude: latitude,
      current_longitude: longitude
    };
    if (status) data.status = status;
    
    const response = await apiV1.patch(`/api-missions/${missionId}/status/`, data);
    console.log('✅ Mission location updated:', response.data);
    return response.data;
  } catch (error) {
    console.error('Error updating mission location:', error);
    throw error;
  }
};

// V1 Disputes
export const getV1Disputes = async (filters = {}) => {
  try {
    const response = await apiV1.get('/disputes/', { params: filters });
    return response.data.results || response.data || [];
  } catch (error) {
    console.error('Error fetching v1 disputes:', error);
    return [];
  }
};

export const getV1Dispute = async (id) => {
  try {
    const response = await apiV1.get(`/disputes/${id}/`);
    return response.data;
  } catch (error) {
    console.error('Error fetching v1 dispute:', error);
    return null;
  }
};

export const createV1Dispute = async (data) => {
  try {
    const response = await apiV1.post('/disputes/', data);
    return response.data;
  } catch (error) {
    console.error('Error creating v1 dispute:', error);
    throw error;
  }
};

// V1 Performance Metrics
export const getV1Performance = async (filters = {}) => {
  try {
    const response = await apiV1.get('/performance/', { params: filters });
    return response.data.results || response.data || [];
  } catch (error) {
    console.error('Error fetching v1 performance:', error);
    return [];
  }
};

// Dashboard Endpoints - Unified data from drivers, trucks, and missions
export const getDashboardSummary = async () => {
  try {
    const response = await apiV1.get('/dashboard/summary/');
    return response.data || null;
  } catch (error) {
    console.error('Error fetching dashboard summary:', error);
    return null;
  }
};

export const getDashboardDrivers = async () => {
  try {
    const response = await apiV1.get('/dashboard/drivers/');
    return response.data || [];
  } catch (error) {
    console.error('Error fetching dashboard drivers:', error);
    return [];
  }
};

export const getDashboardTrucks = async () => {
  try {
    console.log('📡 Fetching trucks from:', apiV1.defaults.baseURL + '/dashboard/trucks/');
    const response = await apiV1.get('/dashboard/trucks/');
    console.log('✅ Trucks response:', response.data);
    return response.data || [];
  } catch (error) {
    console.error('❌ Error fetching dashboard trucks:', error.message);
    console.error('   URL:', error.config?.url);
    console.error('   Status:', error.response?.status);
    console.error('   Data:', error.response?.data);
    return [];
  }
};

export const getDashboardMissions = async () => {
  try {
    const response = await apiV1.get('/dashboard/missions/');
    return response.data || [];
  } catch (error) {
    console.error('Error fetching dashboard missions:', error);
    return [];
  }
};

export const recalculatePerformance = async () => {
  try {
    const response = await apiV1.post('/dashboard/recalculate-performance/');
    return response.data;
  } catch (error) {
    console.error('Error recalculating performance:', error);
    throw error;
  }
};

export const syncTruckData = async (truckId = null) => {
  try {
    const payload = truckId ? { truck_id: truckId } : {};
    const response = await apiV1.post('/dashboard/sync-truck-data/', payload);
    return response.data;
  } catch (error) {
    console.error('Error syncing truck data:', error);
    throw error;
  }
};

export const getMissionRouteGeometry = async (missionId) => {
  try {
    const response = await apiV1.get(`/dashboard/missions/${missionId}/route-geometry/`);
    return response.data;
  } catch (error) {
    console.error('Error fetching mission route geometry:', error);
    return null;
  }
};

// 🚨 INITIALIZE INTERCEPTORS AFTER MODULE IS FULLY LOADED 🚨
function initializeInterceptors() {
  // Regular API instance interceptor (moved from top level)
  api.interceptors.response.use(
    response => response,
    async error => {
      const config = error.config;
      if (!config || !config.retryCount) config.retryCount = 0;
      
      const isRetryable = 
        RETRY_CONFIG.retryableStatusCodes.includes(error.response?.status) ||
        error.code === 'ECONNABORTED' ||
        error.code === 'ECONNREFUSED' ||
        error.code === 'ETIMEDOUT' ||
        !error.response;
        
      if (isRetryable && config.retryCount < RETRY_CONFIG.maxRetries) {
        config.retryCount += 1;
        const delay = RETRY_CONFIG.retryDelay * Math.pow(RETRY_CONFIG.backoffMultiplier, config.retryCount - 1);
        
        console.warn(
          `⚠️ API Request failed (attempt ${config.retryCount}/${RETRY_CONFIG.maxRetries}). ` +
          `Retrying in ${delay}ms... [${error.message}]`
        );
        
        await new Promise(resolve => setTimeout(resolve, delay));
        return api(config);
      }
      return Promise.reject(error);
    }
  );

  // API V1 instance interceptor (moved from top level)
  apiV1.interceptors.response.use(
    response => response,
    async error => {
      const config = error.config;
      if (!config || !config.retryCount) config.retryCount = 0;
      
      const isRetryable = 
        RETRY_CONFIG.retryableStatusCodes.includes(error.response?.status) ||
        error.code === 'ECONNABORTED' ||
        error.code === 'ECONNREFUSED' ||
        error.code === 'ETIMEDOUT' ||
        !error.response;
        
      if (isRetryable && config.retryCount < RETRY_CONFIG.maxRetries) {
        config.retryCount += 1;
        const delay = RETRY_CONFIG.retryDelay * Math.pow(RETRY_CONFIG.backoffMultiplier, config.retryCount - 1);
        
        console.warn(
          `⚠️ [API V1] Request failed (attempt ${config.retryCount}/${RETRY_CONFIG.maxRetries}). ` +
          `Retrying in ${delay}ms... [${error.message}]`
        );
        
        await new Promise(resolve => setTimeout(resolve, delay));
        return apiV1(config);
      }
      return Promise.reject(error);
    }
  );
}

// Initialize interceptors after module definition
initializeInterceptors();

export default api;
