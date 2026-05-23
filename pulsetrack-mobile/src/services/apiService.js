/**
 * PulseTrack Mobile API Service
 * Handles all HTTP communication with the backend
 */

import API_CONFIG from '../config/api';

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
  async registerDriverByQR(qrData, phoneNumber) {
    return this.request(API_CONFIG.endpoints.driverRegistration, {
      method: 'POST',
      body: JSON.stringify({
        qr_data: qrData,
        phone_number: phoneNumber,
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
   * Send location update to backend
   */
  async sendLocationUpdate(driverId, locationData) {
    return this.request(API_CONFIG.endpoints.locationUpdate(driverId), {
      method: 'POST',
      body: JSON.stringify({
        driver_id: driverId,
        latitude: locationData.latitude,
        longitude: locationData.longitude,
        speed: locationData.speed || 0,
        accuracy: locationData.accuracy || 0,
        altitude: locationData.altitude || 0,
        timestamp: Date.now(),
      }),
    });
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