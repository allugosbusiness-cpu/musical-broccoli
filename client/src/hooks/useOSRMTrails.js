import { useState, useCallback } from 'react';

/**
 * Hook for fetching OSRM trail data
 * Provides functionality to get trails that follow roads for truck tracking
 */
const useOSRMTrails = () => {
  const [trailCache, setTrailCache] = useState(new Map());
  const API_BASE_URL = process.env.REACT_APP_API_URL || 'http://localhost:8000/api/v1';

  // Get trail data for a specific truck
  const getTrailForTruck = useCallback(async (truckId, hours = 24) => {
    // Check cache first
    const cacheKey = `${truckId}-${hours}`;
    const cached = trailCache.get(cacheKey);
    if (cached && (Date.now() - cached.timestamp) < (5 * 60 * 1000)) { // 5 minute cache
      return cached.data;
    }
    
    try {
      const response = await fetch(
        `${API_BASE_URL}/dashboard/trucks/${truckId}/trail/?hours=${hours}`
      );
      
      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }
      
      const data = await response.json();
      
      // Update cache
      trailCache.set(cacheKey, {
        data,
        timestamp: Date.now()
      });
      
      // Limit cache size
      if (trailCache.size > 100) {
        const keys = Array.from(trailCache.keys());
        keys.slice(0, -50).forEach(key => trailCache.delete(key));
      }
      
      return data;
    } catch (error) {
      console.error(`Error fetching trail for truck ${truckId}:`, error);
      throw error;
    }
  }, [trailCache]);

  // Get trail data for multiple trucks
  const getTrailsForTrucks = useCallback(async (truckIds, hours = 24) => {
    const trails = {};
    for (const truckId of truckIds) {
      try {
        const trail = await getTrailForTruck(truckId, hours);
        trails[truckId] = trail;
      } catch (error) {
        console.warn(`Failed to get trail for truck ${truckId}:`, error);
        trails[truckId] = null;
      }
    }
    return trails;
  }, [getTrailForTruck]);

  // Clear trail cache
  const clearTrailCache = useCallback(() => {
    trailCache.clear();
    setTrailCache(new Map());
  }, []);

  return {
    getTrailForTruck,
    getTrailsForTrucks,
    clearTrailCache
  };
};

export default useOSRMTrails;