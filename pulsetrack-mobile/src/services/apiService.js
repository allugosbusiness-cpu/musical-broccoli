/**
 * PulseTrack Mobile API Service
 * Handles all HTTP communication with the backend
 */

import API_CONFIG from '../config/api';
import storage from '../utils/storage';

class ApiService {
  constructor() {
    this.baseUrl = API_CONFIG.baseUrl;
    this.headers = { ...API_CONFIG.headers };
  }

  setAuthToken(token) {
    this.headers['Authorization'] = `Bearer ${token}`;
  }

  clearAuthToken() {
    delete this.headers['Authorization'];
  }

  async request(endpoint, options = {}) {
    const url = endpoint;
    const config = {
      headers: this.headers,
      ...options,
    };

    try {
      console.log('[ApiService] requesting:', { url, method: config.method });
      const response = await fetch(url, config);
      
      let data;
      try {
        const text = await response.text();
        console.log('[ApiService] raw response:', { status: response.status, textLength: text.length, firstChars: text.substring(0, 100) });
        data = JSON.parse(text);
      } catch (parseError) {
        console.log('[ApiService] JSON parse error:', parseError.message);
        throw new Error(`Invalid JSON response: ${parseError.message}`);
      }

      if (!response.ok) {
        throw new Error(data.error || data.message || `HTTP ${response.status}`);
      }

      return data;
    } catch (error) {
      console.log('[ApiService] request error:', error.message);
      if (error.message === 'Network request failed') {
        throw new Error('No internet connection. Please check your network.');
      }
      throw error;
    }
  }

  // ===== AUTHENTICATION & REGISTRATION =====

  /**
   * Register driver by scanning QR code
   */
  async registerDriverByQR(qrData, phoneNumber, driverName = null) {
    return this.request(API_CONFIG.endpoints.driverRegistration, {
      method: 'POST',
      body: JSON.stringify({
        qr_data: qrData,
        phone_number: phoneNumber,
        driver_name: driverName,
      }),
    });
  }

  /**
   * Validate PIN code and register driver to truck
   */
  async validatePin(pin, phoneNumber, firstName = '', lastName = '', location = null) {
    const body = {
      pin: pin,
      phone_number: phoneNumber,
      first_name: firstName,
      last_name: lastName,
    };
    if (location) {
      body.latitude = location.latitude;
      body.longitude = location.longitude;
      body.accuracy = location.accuracy || 0;
      body.altitude = location.altitude || 0;
    }
    return this.request(API_CONFIG.endpoints.validatePin, {
      method: 'POST',
      body: JSON.stringify(body),
    });
  }

  // ===== MISSIONS =====

  /**
   * Get available missions for a driver
   */
  async getAvailableMissions(driverId) {
    return this.request(API_CONFIG.endpoints.availableMissions(driverId), {
      method: 'GET',
    });
  }

  /**
   * Get current active mission for a driver
   */
  async getCurrentMission(driverId) {
    return this.request(API_CONFIG.endpoints.currentMission(driverId), {
      method: 'GET',
    });
  }

  /**
   * Start tracking a mission
   */
  async startMissionTracking(driverId, missionId, location = null) {
    const body = {
      driver_id: driverId,
      mission_id: missionId,
    };
    if (location) {
      body.latitude = location.latitude;
      body.longitude = location.longitude;
      body.accuracy = location.accuracy || 0;
      body.altitude = location.altitude || 0;
    }
    return this.request(API_CONFIG.endpoints.startMissionTracking, {
      method: 'POST',
      body: JSON.stringify(body),
    });
  }

  /**
   * Complete a mission
   */
  async completeMission(missionId) {
    return this.request(API_CONFIG.endpoints.completeMission(missionId), {
      method: 'POST',
    });
  }

  // ===== LOCATION TRACKING =====

  /**
   * Send location update to backend with offline fallback
   */
  async sendLocationUpdate(driverId, locationData) {
    const payload = {
      driver_id: driverId,
      latitude: locationData.latitude,
      longitude: locationData.longitude,
      speed: locationData.speed || 0,
      accuracy: locationData.accuracy || 0,
      altitude: locationData.altitude || 0,
      timestamp: Date.now(),
    };

    try {
      console.log('[ApiService] Sending location update for driver:', driverId);
      const result = await this.request(API_CONFIG.endpoints.locationUpdate(driverId), {
        method: 'POST',
        body: JSON.stringify(payload),
      });
      console.log('[ApiService] Location update sent successfully');
      return result;
    } catch (error) {
      console.log('[ApiService] Location update failed, queuing offline:', error.message);
      // Queue location update for later sending when connectivity is restored
      await storage.addPendingLocationUpdate(driverId, {
        ...locationData,
        timestamp: payload.timestamp,
      });
      // Return success-like response so app continues uninterrupted
      return { success: true, queued: true, message: 'Location queued for offline sync' };
    }
  }

  /**
   * Process queued location updates when connectivity is restored
   */
  async processOfflineQueue() {
    try {
      const queuedUpdates = await storage.getPendingLocationUpdates();
      console.log('[ApiService] Processing offline queue with', queuedUpdates.length, 'updates');

      if (queuedUpdates.length === 0) {
        console.log('[ApiService] No queued updates to process');
        return { processed: 0, failed: 0 };
      }

      let processed = 0;
      let failed = 0;

      // Send updates in batches to avoid overwhelming backend
      for (const update of queuedUpdates) {
        try {
          await this.request(API_CONFIG.endpoints.locationUpdate(update.driver_id), {
            method: 'POST',
            body: JSON.stringify({
              driver_id: update.driver_id,
              latitude: update.latitude,
              longitude: update.longitude,
              speed: update.speed || 0,
              accuracy: update.accuracy || 0,
              altitude: update.altitude || 0,
              timestamp: update.timestamp,
            }),
          });
          // Remove from queue only after successful send
          await storage.removePendingLocationUpdate(update.queued_at);
          processed++;
          console.log('[ApiService] Processed queued update:', update.driver_id);
        } catch (error) {
          failed++;
          console.log('[ApiService] Failed to process queued update:', error.message);
        }
      }

      console.log('[ApiService] Queue processing complete:', { processed, failed });
      return { processed, failed };
    } catch (error) {
      console.log('[ApiService] Error processing offline queue:', error.message);
      return { processed: 0, failed: 0 };
    }
  }

  // ===== ALERTS =====

  /**
   * Send an alert to the backend
   */
  async sendAlert(driverId, alertType, message, location, speed = 0) {
    return this.request(API_CONFIG.endpoints.sendAlert, {
      method: 'POST',
      body: JSON.stringify({
        driver_id: driverId,
        alert_type: alertType,
        message: message,
        latitude: location.latitude,
        longitude: location.longitude,
        speed: speed,
      }),
    });
  }

  /**
   * Get active alerts for a driver (notifications)
   */
  async getDriverAlerts(driverId) {
    try {
      const result = await this.request(
        `${API_CONFIG.baseUrl}/alerts/?driver=${driverId}&is_resolved=false&limit=50`,
        { method: 'GET' }
      );
      return { alerts: Array.isArray(result) ? result : (result.results || []) };
    } catch (error) {
      console.log('[ApiService] Failed to fetch driver alerts:', error.message);
      return { alerts: [] };
    }
  }

  /**
   * Send a driver-crafted alert message to the fleet manager
   */
  async sendDriverAlert(driverId, truckId, message, category, latitude, longitude) {
    return this.request(
      `${API_CONFIG.baseUrl}/alerts/driver-send/`,
      {
        method: 'POST',
        body: JSON.stringify({
          driver_id: driverId,
          truck_id: truckId,
          message: message,
          alert_category: category || 'other',
          latitude: latitude || 0,
          longitude: longitude || 0,
        }),
      }
    );
  }

  /**
   * Check for overspeed/delayed alerts after a location update
   */
  async checkAlerts(driverId, truckId, latitude, longitude, speed, missionId = null) {
    try {
      return await this.request(
        `${API_CONFIG.baseUrl}/alerts/check/`,
        {
          method: 'POST',
          body: JSON.stringify({
            driver_id: driverId,
            truck_id: truckId,
            latitude: latitude,
            longitude: longitude,
            speed: speed,
            mission_id: missionId,
          }),
        }
      );
    } catch (error) {
      console.log('[ApiService] Alert check failed:', error.message);
      return { alerts_created: [], active_alerts: [] };
    }
  }

  // ===== DRIVER PROFILE =====

  /**
   * Get driver profile
   */
  async getDriverProfile(driverId) {
    return this.request(API_CONFIG.endpoints.driverProfile(driverId), {
      method: 'GET',
    });
  }

  /**
   * Get driver mission history
   */
  async getDriverMissions(driverId) {
    return this.request(API_CONFIG.endpoints.driverMissions(driverId), {
      method: 'GET',
    });
  }

  // ===== DEBUG =====

  /**
   * Get debug info from backend
   */
  async getDebugInfo() {
    return this.request(API_CONFIG.endpoints.debugInfo, {
      method: 'GET',
    });
  }
}

export default new ApiService();