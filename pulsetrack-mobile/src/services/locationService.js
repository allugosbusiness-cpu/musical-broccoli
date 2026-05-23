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
let speedAlertThreshold = API_CONFIG.speedAlertThreshold;
let currentSpeed = 0;
let isTracking = false;
let driverId = null;
let onSpeedAlertCallback = null;
let onLocationUpdateCallback = null;

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

async function processLocationUpdate(location) {
  try {
    const coords = location.coords;
    const speedKmh = (coords.speed || 0) * 3.6;
    currentSpeed = speedKmh;

    const locationData = {
      latitude: coords.latitude,
      longitude: coords.longitude,
      speed: Math.round(speedKmh * 100) / 100,
      accuracy: coords.accuracy || 0,
      altitude: coords.altitude || 0,
      timestamp: Date.now(),
    };

    // Cache locally
    await storage.addLocationEntry(locationData);

    // Check distance moved since last sent
    if (lastSentLocation) {
      const distance = getDistanceFromLatLonInMeters(
        lastSentLocation.latitude,
        lastSentLocation.longitude,
        coords.latitude,
        coords.longitude
      );
      if (distance < API_CONFIG.locationDistanceFilter) {
        return; // Too close, skip sending
      }
    }

    // Send to backend
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

    // Notify listeners
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
   */
  async startTracking(driverIdParam, options = {}) {
    driverId = driverIdParam;
    isTracking = true;
    speedAlertThreshold = options.speedAlertThreshold || API_CONFIG.speedAlertThreshold;

    // Start foreground location watching
    watchPositionSubscription = await Location.watchPositionAsync(
      {
        accuracy: Location.Accuracy.Highest,
        timeInterval: options.timeInterval || API_CONFIG.locationUpdateInterval / 2,
        distanceInterval: options.distanceFilter || API_CONFIG.locationDistanceFilter / 2,
      },
      (location) => {
        processLocationUpdate(location);
      }
    );

    // Start background location updates
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
   * Get current speed (km/h)
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
}

export default new LocationService();