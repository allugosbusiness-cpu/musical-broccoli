import { useState, useEffect, useCallback } from 'react';
import locationService from '../services/locationService';

/**
 * Hook for tracking truck locations in real-time
 * @param {Object} options - Configuration options
 * @param {string} options.missionId - Optional mission ID to filter by
 * @param {string} options.driverId - Optional driver ID to filter by
 * @param {number} options.pollingInterval - Polling interval in milliseconds (default: 5000)
 * @returns {Object} { locations, loading, error, refresh, startPolling, stopPolling }
 */
const useTruckLocations = ({ missionId, driverId, pollingInterval = 5000 } = {}) => {
  const [locations, setLocations] = useState([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);

  // Fetch locations based on filters
  const fetchLocations = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      let data;
      if (missionId) {
        data = await locationService.fetchCurrentLocationsByMission(missionId);
      } else if (driverId) {
        data = await locationService.fetchCurrentLocationsByDriver(driverId);
      } else {
        data = await locationService.fetchCurrentLocations();
      }
      setLocations(data);
    } catch (err) {
      setError(err.message);
      console.error('Failed to fetch truck locations:', err);
    } finally {
      setLoading(false);
    }
  }, [missionId, driverId]);

  // Start polling
  const startPolling = useCallback(() => {
    locationService.startPolling(pollingInterval);
  }, [pollingInterval]);

  // Stop polling
  const stopPolling = useCallback(() => {
    locationService.stopPolling();
  }, []);

  // Manual refresh
  const refresh = useCallback(() => {
    fetchLocations();
  }, [fetchLocations]);

  // Subscribe to location updates
  useEffect(() => {
    // Initial fetch
    fetchLocations();
    
    // Subscribe to updates
    const unsubscribe = locationService.subscribe(setLocations);
    
    // Start polling
    startPolling();
    
    // Cleanup
    return () => {
      unsubscribe();
      stopPolling();
    };
  }, [fetchLocations, startPolling, stopPolling]);

  return {
    locations,
    loading,
    error,
    refresh,
    startPolling,
    stopPolling
  };
};

export default useTruckLocations;