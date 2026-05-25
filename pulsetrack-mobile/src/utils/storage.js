/**
 * PulseTrack Mobile Local Storage
 * Uses AsyncStorage for persisting driver session and app data
 */

import AsyncStorage from '@react-native-async-storage/async-storage';

const KEYS = {
  DRIVER_SESSION: '@pulsetrack_driver_session',
  DRIVER_PROFILE: '@pulsetrack_driver_profile',
  CURRENT_MISSION: '@pulsetrack_current_mission',
  LOCATION_HISTORY: '@pulsetrack_location_history',
  PENDING_LOCATION_UPDATES: '@pulsetrack_pending_location_updates',
  APP_SETTINGS: '@pulsetrack_app_settings',
};

class StorageService {
  // ===== DRIVER SESSION =====

  async saveDriverSession(sessionData) {
    try {
      await AsyncStorage.setItem(KEYS.DRIVER_SESSION, JSON.stringify(sessionData));
      return true;
    } catch (error) {
      console.error('Error saving driver session:', error);
      return false;
    }
  }

  async getDriverSession() {
    try {
      const data = await AsyncStorage.getItem(KEYS.DRIVER_SESSION);
      return data ? JSON.parse(data) : null;
    } catch (error) {
      console.error('Error getting driver session:', error);
      return null;
    }
  }

  async clearDriverSession() {
    try {
      await AsyncStorage.removeItem(KEYS.DRIVER_SESSION);
      await AsyncStorage.removeItem(KEYS.DRIVER_PROFILE);
      await AsyncStorage.removeItem(KEYS.CURRENT_MISSION);
      return true;
    } catch (error) {
      console.error('Error clearing driver session:', error);
      return false;
    }
  }

  // ===== DRIVER PROFILE =====

  async saveDriverProfile(profile) {
    try {
      await AsyncStorage.setItem(KEYS.DRIVER_PROFILE, JSON.stringify(profile));
      return true;
    } catch (error) {
      console.error('Error saving driver profile:', error);
      return false;
    }
  }

  async getDriverProfile() {
    try {
      const data = await AsyncStorage.getItem(KEYS.DRIVER_PROFILE);
      return data ? JSON.parse(data) : null;
    } catch (error) {
      console.error('Error getting driver profile:', error);
      return null;
    }
  }

  // ===== CURRENT MISSION =====

  async saveCurrentMission(mission) {
    try {
      await AsyncStorage.setItem(KEYS.CURRENT_MISSION, JSON.stringify(mission));
      return true;
    } catch (error) {
      console.error('Error saving current mission:', error);
      return false;
    }
  }

  async getCurrentMission() {
    try {
      const data = await AsyncStorage.getItem(KEYS.CURRENT_MISSION);
      return data ? JSON.parse(data) : null;
    } catch (error) {
      console.error('Error getting current mission:', error);
      return null;
    }
  }

  async clearCurrentMission() {
    try {
      await AsyncStorage.removeItem(KEYS.CURRENT_MISSION);
      return true;
    } catch (error) {
      console.error('Error clearing current mission:', error);
      return false;
    }
  }

  // ===== LOCATION HISTORY (Offline Cache) =====

  async addLocationEntry(entry) {
    try {
      const history = await this.getLocationHistory();
      history.push({
        ...entry,
        cached_at: Date.now(),
      });
      // Keep last 100 entries in cache
      const trimmed = history.slice(-100);
      await AsyncStorage.setItem(KEYS.LOCATION_HISTORY, JSON.stringify(trimmed));
      return true;
    } catch (error) {
      console.error('Error adding location entry:', error);
      return false;
    }
  }

  async getLocationHistory() {
    try {
      const data = await AsyncStorage.getItem(KEYS.LOCATION_HISTORY);
      return data ? JSON.parse(data) : [];
    } catch (error) {
      console.error('Error getting location history:', error);
      return [];
    }
  }

  async clearLocationHistory() {
    try {
      await AsyncStorage.removeItem(KEYS.LOCATION_HISTORY);
      return true;
    } catch (error) {
      console.error('Error clearing location history:', error);
      return false;
    }
  }

  // ===== APP SETTINGS =====

  async saveAppSettings(settings) {
    try {
      await AsyncStorage.setItem(KEYS.APP_SETTINGS, JSON.stringify(settings));
      return true;
    } catch (error) {
      console.error('Error saving app settings:', error);
      return false;
    }
  }

  async getAppSettings() {
    try {
      const data = await AsyncStorage.getItem(KEYS.APP_SETTINGS);
      if (data) {
        return JSON.parse(data);
      }
      // Return default settings
      return {
        locationUpdateInterval: 120000,
        speedAlertThreshold: 120,
        gpsTrackingEnabled: true,
        darkMode: false,
        notificationsEnabled: true,
      };
    } catch (error) {
      console.error('Error getting app settings:', error);
      return null;
    }
  }

  // ===== PENDING LOCATION UPDATES (Offline Queue) =====

  async addPendingLocationUpdate(driverId, locationData) {
    try {
      const queue = await this.getPendingLocationUpdates();
      queue.push({
        driver_id: driverId,
        ...locationData,
        queued_at: Date.now(),
      });
      // Keep last 200 pending updates
      const trimmed = queue.slice(-200);
      await AsyncStorage.setItem(KEYS.PENDING_LOCATION_UPDATES, JSON.stringify(trimmed));
      return true;
    } catch (error) {
      console.error('Error adding pending location update:', error);
      return false;
    }
  }

  async getPendingLocationUpdates() {
    try {
      const data = await AsyncStorage.getItem(KEYS.PENDING_LOCATION_UPDATES);
      return data ? JSON.parse(data) : [];
    } catch (error) {
      console.error('Error getting pending location updates:', error);
      return [];
    }
  }

  async removePendingLocationUpdate(queuedAt) {
    try {
      const queue = await this.getPendingLocationUpdates();
      const filtered = queue.filter(u => u.queued_at !== queuedAt);
      await AsyncStorage.setItem(KEYS.PENDING_LOCATION_UPDATES, JSON.stringify(filtered));
      return true;
    } catch (error) {
      console.error('Error removing pending location update:', error);
      return false;
    }
  }

  async clearPendingLocationUpdates() {
    try {
      await AsyncStorage.removeItem(KEYS.PENDING_LOCATION_UPDATES);
      return true;
    } catch (error) {
      console.error('Error clearing pending location updates:', error);
      return false;
    }
  }

  // ===== GENERAL =====

  async clearAll() {
    try {
      const keys = Object.values(KEYS);
      await AsyncStorage.multiRemove(keys);
      return true;
    } catch (error) {
      console.error('Error clearing all storage:', error);
      return false;
    }
  }
}

export default new StorageService();