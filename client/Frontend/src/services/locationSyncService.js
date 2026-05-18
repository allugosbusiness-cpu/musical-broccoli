/**
 * Location Sync Service
 * Real-time truck location updates from backend
 * Provides polling for truck position changes with intelligent retry logic
 */

import { extractCoordinates, isValidCoordinate } from '../utils/locationExtractor';

const getApiV1Base = () => {
  if (import.meta.env.MODE === 'development') return 'http://localhost:8000/api/v1';
  return 'https://pulsetrack-back.onrender.com/api/v1';
};

class LocationSyncService {
  constructor() {
    this.subscribers = [];
    this.syncInterval = null;
    this.lastUpdate = {};
    this.syncFrequency = 3000; // Update every 3 seconds for real-time feel
    this.consecutiveErrors = 0;
    this.maxRetries = 3;
    this.isConnected = false;
  }

  /**
   * Subscribe to location updates
   * Callback receives: { truck_id, truck_identifier, latitude, longitude, speed_kmh, timestamp, source }
   */
  subscribe(callback) {
    this.subscribers.push(callback);
    console.log(`✅ Location sync subscriber added (total: ${this.subscribers.length})`);
    return () => {
      this.subscribers = this.subscribers.filter(cb => cb !== callback);
      console.log(`✅ Location sync subscriber removed (total: ${this.subscribers.length})`);
    };
  }

  /**
   * Start polling for truck location updates
   */
  startSync() {
    if (this.syncInterval) {
      console.warn('⚠️ Location sync already running');
      return;
    }

    console.log(`🚀 Starting location sync (every ${this.syncFrequency}ms)...`);
    
    // Fetch immediately
    this.fetchLocations();
    
    // Then poll periodically
    this.syncInterval = setInterval(() => {
      this.fetchLocations();
    }, this.syncFrequency);
  }

  /**
   * Stop polling for updates
   */
  stopSync() {
    if (this.syncInterval) {
      clearInterval(this.syncInterval);
      this.syncInterval = null;
      this.isConnected = false;
      console.log('🛑 Location sync stopped');
    }
  }

  /**
   * Fetch all truck locations from backend
   */
  async fetchLocations() {
    try {
      const response = await fetch(`${getApiV1Base()}/truck-tracking/all-locations/`, {
        timeout: 10000  // 10 second timeout
      });
      
      if (!response.ok) {
        const errorText = await response.text();
        console.error(`❌ Location API returned ${response.status}:`, errorText);
        throw new Error(`API error: ${response.status} ${response.statusText}`);
      }

      const data = await response.json();
      console.log('📊 Location API response:', data);
      
      // Handle both response formats
      const trucks = data.trucks || data.results || (Array.isArray(data) ? data : []);
      
      if (!Array.isArray(trucks)) {
        console.warn('⚠️ Invalid truck data format:', data);
        this.consecutiveErrors++;
        return;
      }

      // ✅ IMPROVED: Better error tracking and connection status
      this.consecutiveErrors = 0;
      if (!this.isConnected) {
        console.log('✅ Location sync reconnected');
        this.isConnected = true;
      }

      console.log(`📡 Location sync: ${trucks.length} trucks received`);

      // Notify subscribers of location changes
      trucks.forEach(truck => {
        try {
          // ✅ IMPROVED: Use robust coordinate extraction
          const { lat, lon, source } = extractCoordinates(truck);
          
          // Only notify if location has changed AND is valid
          const cacheKey = `${truck.truck_id}`;
          const newHash = JSON.stringify({ lat, lon, speed: truck.speed_kmh });
          const oldHash = this.lastUpdate[cacheKey];

          if (newHash !== oldHash && isValidCoordinate(lat, lon)) {
            this.lastUpdate[cacheKey] = newHash;
            
            const safeLat = Number.isFinite(lat) ? lat.toFixed(4) : 'N/A';
            const safeLon = Number.isFinite(lon) ? lon.toFixed(4) : 'N/A';
            console.log(`📍 Location changed for ${truck.truck_identifier}: [${safeLat}, ${safeLon}]`);
            
            // Notify all subscribers
            this.subscribers.forEach(callback => {
              try {
                callback({
                  truck_id: truck.truck_id,
                  truck_identifier: truck.truck_identifier,
                  plate: truck.plate,
                  status: truck.status,
                  latitude: lat,
                  longitude: lon,
                  speed_kmh: truck.speed_kmh || 0,
                  timestamp: truck.updated_at,
                  source: source,  // ✅ NEW: Track data source
                });
              } catch (err) {
                console.error('❌ Subscriber callback error:', err);
              }
            });
          } else if (!isValidCoordinate(lat, lon)) {
            console.warn(`⚠️ Invalid coordinates for truck ${truck.truck_identifier}: [${lat}, ${lon}]`);
          }
        } catch (err) {
          console.error(`❌ Error processing truck ${truck.truck_id}:`, err.message);
        }
      });

    } catch (error) {
      this.consecutiveErrors++;
      
      if (this.consecutiveErrors === 1) {
        console.warn(`⚠️ Location fetch error (attempt ${this.consecutiveErrors}/${this.maxRetries}):`, error.message);
      } else if (this.consecutiveErrors === this.maxRetries) {
        console.error(`❌ Location fetch failed ${this.maxRetries} times, stopping sync`);
        this.isConnected = false;
      }
      
      // Only log after multiple failures to avoid spam
      if (this.consecutiveErrors > 1) {
        console.warn(`⏳ Location sync retry in progress... (${this.consecutiveErrors}/${this.maxRetries})`);
      }
    }
  }

  /**
   * Set sync frequency (in milliseconds)
   */
  setFrequency(ms) {
    if (ms < 1000) {
      console.warn('⚠️ Sync frequency too fast, using 1000ms minimum');
      ms = 1000;
    }
    if (ms > 60000) {
      console.warn('⚠️ Sync frequency too slow, using 60000ms maximum');
      ms = 60000;
    }
    this.syncFrequency = ms;
    
    console.log(`🔄 Sync frequency updated to ${ms}ms`);
    
    // Restart if already running
    if (this.syncInterval) {
      this.stopSync();
      this.startSync();
    }
  }

  /**
   * Force an immediate sync
   */
  async forceSyncNow() {
    console.log('🔄 Forcing immediate location sync...');
    await this.fetchLocations();
  }

  /**
   * Get current connection status
   */
  getConnectionStatus() {
    return {
      isConnected: this.isConnected,
      isRunning: !!this.syncInterval,
      consecutiveErrors: this.consecutiveErrors,
      maxRetries: this.maxRetries,
      syncFrequency: this.syncFrequency,
    };
  }

  /**
   * Get subscriber count
   */
  getSubscriberCount() {
    return this.subscribers.length;
  }
}

// Export singleton instance
export const locationSyncService = new LocationSyncService();

export default locationSyncService;
