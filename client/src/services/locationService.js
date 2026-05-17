// Location Service for Fleet Management System
// Handles fetching and updating truck location data for real-time map display

const API_BASE_URL = process.env.REACT_APP_API_URL || 'http://localhost:8000/api/v1';

class LocationService {
  constructor() {
    this.subscribers = new Set();
    this.pollingInterval = null;
    this.currentLocations = new Map(); // truckId -> location data
  }

  // Subscribe to location updates
  subscribe(callback) {
    this.subscribers.add(callback);
    // Immediately send current data to new subscriber
    callback(Array.from(this.currentLocations.values()));
    return () => this.unsubscribe(callback);
  }

  // Unsubscribe from location updates
  unsubscribe(callback) {
    this.subscribers.delete(callback);
  }

  // Notify all subscribers of new location data
  notifySubscribers(locations) {
    this.subscribers.forEach(callback => {
      try {
        callback(locations);
      } catch (error) {
        console.error('Error in location subscriber:', error);
      }
    });
  }

  // Fetch current locations from API
  async fetchCurrentLocations() {
    try {
      const response = await fetch(`${API_BASE_URL}/dashboard/current-locations/all/`);
      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }
      const data = await response.json();
      
      // Update internal map
      data.forEach(location => {
        this.currentLocations.set(location.id, location);
      });
      
      // Notify subscribers
      this.notifySubscribers(Array.from(this.currentLocations.values()));
      
      return data;
    } catch (error) {
      console.error('Error fetching current locations:', error);
      throw error;
    }
  }

  // Fetch current locations for a specific mission
  async fetchCurrentLocationsByMission(missionId) {
    try {
      const response = await fetch(`${API_BASE_URL}/dashboard/current-locations/by_mission/?mission_id=${missionId}`);
      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }
      const data = await response.json();
      
      // Update internal map for these trucks
      data.forEach(location => {
        this.currentLocations.set(location.id, location);
      });
      
      // Notify subscribers
      this.notifySubscribers(Array.from(this.currentLocations.values()));
      
      return data;
    } catch (error) {
      console.error(`Error fetching current locations for mission ${missionId}:`, error);
      throw error;
    }
  }

  // Start polling for location updates
  startPolling(intervalMs = 5000) {
    // Clear any existing interval
    if (this.pollingInterval) {
      clearInterval(this.pollingInterval);
    }
    
    // Fetch initial data
    this.fetchCurrentLocations().catch(console.error);
    
    // Set up polling interval
    this.pollingInterval = setInterval(() => {
      this.fetchCurrentLocations().catch(console.error);
    }, intervalMs);
    
    return this.pollingInterval;
  }

  // Stop polling for location updates
  stopPolling() {
    if (this.pollingInterval) {
      clearInterval(this.pollingInterval);
      this.pollingInterval = null;
    }
  }

  // Get current location for a specific truck
  getTruckLocation(truckId) {
    return this.currentLocations.get(truckId) || null;
  }

  // Get all current locations
  getAllLocations() {
    return Array.from(this.currentLocations.values());
  }

  // Clear all location data
  clearLocations() {
    this.currentLocations.clear();
    this.notifySubscribers([]);
  }
}

// Create and export singleton instance
const locationService = new LocationService();
export default locationService;