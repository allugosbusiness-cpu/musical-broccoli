/**
 * PulseTrack Mobile Location Service
 * Handles GPS tracking, speed monitoring, and background location updates
 * Sends location data to backend every 2 minutes
 */

import * as Location from 'expo-location';
let TaskManager;
try {
  // eslint-disable-next-line global-require
  TaskManager = require('expo-task-manager');
} catch (e) {
  console.warn('expo-task-manager not available in this environment:', e && e.message);
  TaskManager = null;
}
import apiService from './apiService';
import storage from '../utils/storage';
import API_CONFIG from '../config/api';

const LOCATION_TASK_NAME = 'PULSETRACK_BACKGROUND_LOCATION';
const SPEED_TASK_NAME = 'PULSETRACK_SPEED_MONITORING';

let watchPositionSubscription = null;
let locationUpdateInterval = null;
let lastSentLocation = null;
let lastLocationTimestamp = null;
let lastLocationCoords = null;
let speedAlertThreshold = API_CONFIG.speedAlertThreshold;
let currentSpeed = 0;
let currentSpeedSource = 'gps';  // 'gps' or 'calculated'
let isTracking = false;
let driverId = null;
let onSpeedAlertCallback = null;
let onLocationUpdateCallback = null;
let networkMonitorInterval = null;
let isOnline = true;
let lastNetworkCheckTime = 0;

// Define background tasks only if TaskManager is available
if (TaskManager && TaskManager.defineTask) {
  // Define background location task
  TaskManager.defineTask(LOCATION_TASK_NAME, async ({ data, error }) => {
    if (error) {
      console.error('Background location task error:', error);
      return;
    }
    if (data) {
      const { locations } = data;
      if (locations && locations.length > 0) {
        const location = locations[locations.length - 1];
        await processLocationUpdate(location);
      }
    }
  });

  // Define speed monitoring task
  TaskManager.defineTask(SPEED_TASK_NAME, async ({ data, error }) => {
    if (error) {
      console.error('Speed monitoring error:', error);
      return;
    }
    if (data) {
      const { locations } = data;
      if (locations && locations.length > 0) {
        const location = locations[locations.length - 1];
        const speedKmh = (location.coords.speed || 0) * 3.6;
        currentSpeed = speedKmh;

        // Check for overspeeding
        if (speedKmh > speedAlertThreshold && onSpeedAlertCallback) {
          onSpeedAlertCallback({
            speed: speedKmh,
            threshold: speedAlertThreshold,
            latitude: location.coords.latitude,
            longitude: location.coords.longitude,
            timestamp: Date.now(),
          });
        }
      }
    }
  });
} else {
  console.warn('TaskManager.defineTask skipped because TaskManager is not available');
}

/**
 * Calculate speed from distance over time between two location updates.
 * Acts as fallback when GPS hardware speed is 0/null.
 */
function calculateSpeedFromDistance(location) {
  const coords = location.coords;
  const currentTime = Date.now();
  
  // First try GPS hardware speed (most accurate when available)
  if (coords.speed && coords.speed > 0) {
    currentSpeedSource = 'gps';
    return Math.round((coords.speed || 0) * 3.6 * 100) / 100;
  }
  
  // Fallback: calculate speed from distance between last two points
  if (lastLocationCoords && lastLocationTimestamp) {
    const distance = getDistanceFromLatLonInMeters(
      lastLocationCoords.latitude,
      lastLocationCoords.longitude,
      coords.latitude,
      coords.longitude
    );
    
    const timeDiffSeconds = (currentTime - lastLocationTimestamp) / 1000;
    
    // Only calculate if we moved > 5m and time diff is reasonable (0.5s - 30s)
    if (distance > 5 && timeDiffSeconds > 0.5 && timeDiffSeconds < 30) {
      const speedMs = distance / timeDiffSeconds;
      const speedKmh = speedMs * 3.6;
      currentSpeedSource = 'calculated';
      return Math.round(speedKmh * 100) / 100;
    }
  }
  
  // Update tracking vars even if no speed was calculated
  lastLocationCoords = coords;
  lastLocationTimestamp = currentTime;
  
  // If we truly can't get speed, return 0
  return 0;
}

async function processLocationUpdate(location) {
  try {
    const coords = location.coords;
    
    // SPEED FIX: Use GPS speed if available, otherwise calculate from distance/time
    const speedKmh = calculateSpeedFromDistance(location);
    currentSpeed = speedKmh;
    
    // Update last location for next calculation
    lastLocationCoords = coords;
    lastLocationTimestamp = Date.now();

    // Log speed updates for debugging (every 5th update to avoid log spam)
    if (Math.random() < 0.2) {
      console.log(`[LocationService] Speed: ${currentSpeed} km/h (source: ${currentSpeedSource}), Lat: ${coords.latitude.toFixed(4)}, Lon: ${coords.longitude.toFixed(4)}`);
    }

    const locationData = {
      latitude: coords.latitude,
      longitude: coords.longitude,
      speed: currentSpeed,
      accuracy: coords.accuracy || 0,
      altitude: coords.altitude || 0,
      timestamp: Date.now(),
    };

    // Cache locally
    await storage.addLocationEntry(locationData);

    // Send EVERY GPS ping to backend for complete trail coverage.
    // No distance filter - the backend records all TruckLocation points
    // and the offline queue handles network failures.
    if (driverId) {
      try {
        console.log('[LocationService] sending location update for driver:', driverId);
        const result = await apiService.sendLocationUpdate(driverId, locationData);
        console.log('[LocationService] location update result:', result);
        if (result && result.success) {
          lastSentLocation = coords;
        }
      } catch (error) {
        console.log('[LocationService] failed to send location update:', error.message);
        // Location is cached, will be sent on next successful attempt
      }
    }

    // Notify listeners of location AND speed change
    if (onLocationUpdateCallback) {
      onLocationUpdateCallback(locationData);
    }

    // Check for overspeeding
    if (speedKmh > speedAlertThreshold && onSpeedAlertCallback) {
      onSpeedAlertCallback({
        speed: speedKmh,
        threshold: speedAlertThreshold,
        latitude: coords.latitude,
        longitude: coords.longitude,
        timestamp: Date.now(),
      });
    }
  } catch (error) {
    console.error('Error processing location update:', error);
  }
}

/**
 * Calculate distance between two coordinates using Haversine formula
 */
function getDistanceFromLatLonInMeters(lat1, lon1, lat2, lon2) {
  const R = 6371000; // Earth's radius in meters
  const dLat = deg2rad(lat2 - lat1);
  const dLon = deg2rad(lon2 - lon1);
  const a =
    Math.sin(dLat / 2) * Math.sin(dLat / 2) +
    Math.cos(deg2rad(lat1)) * Math.cos(deg2rad(lat2)) *
    Math.sin(dLon / 2) * Math.sin(dLon / 2);
  const c = 2 * Math.atan2(Math.sqrt(a), Math.sqrt(1 - a));
  return R * c;
}

function deg2rad(deg) {
  return deg * (Math.PI / 180);
}

class LocationService {
  /**
   * Request location permissions
   */
  async requestPermissions() {
    const foreground = await Location.requestForegroundPermissionsAsync();
    if (foreground.status !== 'granted') {
      return { granted: false, message: 'Foreground location permission denied' };
    }

    const background = await Location.requestBackgroundPermissionsAsync();
    if (background.status !== 'granted') {
      console.warn('Background location permission not granted');
      return { granted: true, message: 'Only foreground tracking available', background: false };
    }

    return { granted: true, message: 'All permissions granted', background: true };
  }

  /**
   * Start continuous GPS tracking
   * For speed calculation, we need frequent updates (reduce distance filter for foreground)
   */
  async startTracking(driverIdParam, options = {}) {
    driverId = driverIdParam;
    isTracking = true;
    speedAlertThreshold = options.speedAlertThreshold || API_CONFIG.speedAlertThreshold;

    // Start foreground location watching - MINIMAL distance filter for speed updates
    // Speed requires frequent fixes, so we poll every 1-2 seconds instead of waiting for distance threshold
    watchPositionSubscription = await Location.watchPositionAsync(
      {
        accuracy: Location.Accuracy.Highest,
        timeInterval: 1000, // Poll every 1 second for responsive speed updates
        distanceInterval: 5, // Minimal distance to still get updates when stationary
      },
      (location) => {
        processLocationUpdate(location);
      }
    );

    // Start background location updates (for when app is minimized)
    try {
      await Location.startLocationUpdatesAsync(LOCATION_TASK_NAME, {
        accuracy: Location.Accuracy.Balanced,
        timeInterval: options.timeInterval || API_CONFIG.locationUpdateInterval,
        distanceInterval: options.distanceFilter || API_CONFIG.locationDistanceFilter,
        deferredUpdatesInterval: API_CONFIG.locationUpdateInterval,
        foregroundService: {
          notificationTitle: 'PulseTrack Active',
          notificationBody: 'Tracking your location for fleet management',
          notificationColor: '#1a237e',
        },
        pausesUpdatesAutomatically: false,
        showsBackgroundLocationIndicator: true,
      });
    } catch (error) {
      console.error('Failed to start background location updates:', error);
    }

    // Set up interval to send location updates (even if position hasn't changed much)
    locationUpdateInterval = setInterval(async () => {
      if (driverId && lastSentLocation) {
        try {
          const location = await Location.getCurrentPositionAsync({
            accuracy: Location.Accuracy.Highest,
          });
          await processLocationUpdate(location);
        } catch (error) {
          console.log('Interval location update failed:', error.message);
        }
      }
    }, API_CONFIG.locationUpdateInterval);

    console.log('[LocationService] Tracking started for driver:', driverId);
    return true;
  }

  /**
   * Stop GPS tracking
   */
  async stopTracking() {
    isTracking = false;
    currentSpeed = 0;

    if (watchPositionSubscription) {
      watchPositionSubscription.remove();
      watchPositionSubscription = null;
    }

    if (locationUpdateInterval) {
      clearInterval(locationUpdateInterval);
      locationUpdateInterval = null;
    }

    try {
      await Location.stopLocationUpdatesAsync(LOCATION_TASK_NAME);
      await Location.stopLocationUpdatesAsync(SPEED_TASK_NAME);
    } catch (error) {
      console.error('Failed to stop background location updates:', error);
    }

    lastSentLocation = null;
    driverId = null;
    return true;
  }

  /**
   * Get current location with latest GPS speed
   * This fetches fresh data from GPS instead of using cached speed
   */
  async getCurrentLocationWithSpeed() {
    try {
      const location = await Location.getCurrentPositionAsync({
        accuracy: Location.Accuracy.High,
      });
      const coords = location.coords;
      const speedKmh = (coords.speed || 0) * 3.6;
      return {
        latitude: coords.latitude,
        longitude: coords.longitude,
        speed: Math.round(speedKmh * 100) / 100,
        rawSpeed: coords.speed,
        accuracy: coords.accuracy || 0,
        altitude: coords.altitude || 0,
        timestamp: Date.now(),
      };
    } catch (error) {
      console.error('Error getting current location:', error);
      return null;
    }
  }

  /**
   * Get current speed (km/h) - returns cached value
   */
  getCurrentSpeed() {
    return currentSpeed;
  }

  /**
   * Check if tracking is active
   */
  isTrackingActive() {
    return isTracking;
  }

  /**
   * Update speed alert threshold
   */
  setSpeedAlertThreshold(threshold) {
    speedAlertThreshold = threshold;
  }

  /**
   * Get speed alert threshold
   */
  getSpeedAlertThreshold() {
    return speedAlertThreshold;
  }

  /**
   * Set callback for speed alerts
   */
  onSpeedAlert(callback) {
    onSpeedAlertCallback = callback;
  }

  /**
   * Set callback for location updates
   */
  onLocationUpdate(callback) {
    onLocationUpdateCallback = callback;
  }

  /**
   * Get current position once
   */
  async getCurrentPosition() {
    try {
      const location = await Location.getCurrentPositionAsync({
        accuracy: Location.Accuracy.Highest,
      });
      return {
        latitude: location.coords.latitude,
        longitude: location.coords.longitude,
        speed: (location.coords.speed || 0) * 3.6,
        accuracy: location.coords.accuracy || 0,
        altitude: location.coords.altitude || 0,
        timestamp: location.timestamp,
      };
    } catch (error) {
      console.error('Error getting current position:', error);
      return null;
    }
  }

  /**
   * Set driver ID for tracking
   */
  setDriverId(id) {
    driverId = id;
  }

  /**
   * Get driver ID
   */
  getDriverId() {
    return driverId;
  }

  async hasBackgroundPermission() {
    const { status } = await Location.getBackgroundPermissionsAsync();
    return status === 'granted';
  }

  async hasForegroundPermission() {
    const { status } = await Location.getForegroundPermissionsAsync();
    return status === 'granted';
  }

  /**
   * Start network monitoring to detect connectivity changes
   * When connectivity is restored, process offline queue
   */
  startNetworkMonitoring() {
    if (networkMonitorInterval) {
      console.log('[LocationService] Network monitoring already active');
      return;
    }

    console.log('[LocationService] Starting network monitoring');
    isOnline = true;

    // Check network status every 10 seconds
    networkMonitorInterval = setInterval(async () => {
      try {
        const wasOnline = isOnline;
        isOnline = await this.checkOnlineStatus();

        // Detect transition from offline to online
        if (!wasOnline && isOnline) {
          console.log('[LocationService] Connectivity restored! Processing offline queue');
          const result = await apiService.processOfflineQueue();
          console.log('[LocationService] Offline queue processed:', result);
        } else if (wasOnline && !isOnline) {
          console.log('[LocationService] Lost connectivity');
        }
      } catch (error) {
        console.log('[LocationService] Network check error:', error.message);
      }
    }, 10000); // Check every 10 seconds

    return true;
  }

  /**
   * Stop network monitoring
   */
  stopNetworkMonitoring() {
    if (networkMonitorInterval) {
      clearInterval(networkMonitorInterval);
      networkMonitorInterval = null;
      console.log('[LocationService] Network monitoring stopped');
    }
  }

  /**
   * Check if device is online by attempting to reach a lightweight endpoint
   */
  async checkOnlineStatus() {
    try {
      // Try a simple HTTP request to check connectivity
      // Using a lightweight endpoint that returns quickly
      const response = await Promise.race([
        fetch(`${API_CONFIG.baseUrl.split('/api')[0]}/api/v1/health/`, {
          method: 'GET',
          timeout: 5000,
        }),
        new Promise((_, reject) =>
          setTimeout(() => reject(new Error('Network check timeout')), 5000)
        ),
      ]);

      return response && (response.ok || response.status < 500);
    } catch (error) {
      console.log('[LocationService] Online check failed:', error.message);
      return false;
    }
  }

  /**
   * Get current online status
   */
  getOnlineStatus() {
    return isOnline;
  }
}

export default new LocationService();