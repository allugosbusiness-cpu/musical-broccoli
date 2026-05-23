/**
 * PulseTrack Mobile API Configuration
 * Connect to the PulseTrack backend
 */

const API_BASE_URL = 'https://pulsetrack-back.onrender.com/api/v1';

export const API_CONFIG = {
  baseUrl: API_BASE_URL,
  
  // Mobile endpoints
  endpoints: {
    // Registration
    driverRegistration: `${API_BASE_URL}/mobile/driver-registration/`,
    validatePin: `${API_BASE_URL}/mobile/validate-pin/`,
    
    // Missions
    availableMissions: (driverId) => `${API_BASE_URL}/mobile/driver/${driverId}/available-missions/`,
    currentMission: (driverId) => `${API_BASE_URL}/mobile/driver/${driverId}/current-mission/`,
    startMissionTracking: `${API_BASE_URL}/mobile/mission/start-tracking/`,
    completeMission: (missionId) => `${API_BASE_URL}/mobile/mission/complete/${missionId}/`,
    
    // Location
    locationUpdate: (driverId) => `${API_BASE_URL}/mobile/driver/${driverId}/location/`,
    
    // Alerts
    sendAlert: `${API_BASE_URL}/mobile/alert/`,
    
    // Driver Profile
    driverProfile: (driverId) => `${API_BASE_URL}/mobile/driver/${driverId}/profile/`,
    driverMissions: (driverId) => `${API_BASE_URL}/mobile/driver/${driverId}/missions/`,
    
    // Debug
    debugInfo: `${API_BASE_URL}/mobile/debug/`,
  },
  
  // Default headers
  headers: {
    'Content-Type': 'application/json',
    'Accept': 'application/json',
  },
  
  // Location update interval in milliseconds (2 minutes)
  locationUpdateInterval: 120000,
  
  // Distance filter in meters (only send if moved at least this much)
  locationDistanceFilter: 50,
  
  // Speed threshold for alerts (km/h)
  speedAlertThreshold: 120,
};

export default API_CONFIG;