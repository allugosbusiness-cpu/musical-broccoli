/**
 * Trail Audit Service
 * Fetches full GPS trail data with audit logs for trucks.
 * Provides data for the TrailAuditViewer component to display
 * where the mobile app/phone has been for each truck.
 */

const getApiV1Base = () => {
  if (import.meta.env.MODE === 'development') return 'http://localhost:8000/api/v1';
  return 'https://pulsetrack-back.onrender.com/api/v1';
};

/**
 * Fetch full trail audit data for a specific truck
 * @param {string} truckId - UUID or truck_identifier
 * @param {object} options - { days: 30, limit: 500 }
 * @returns {Promise<{truck_id, truck_identifier, plate, driver_name, trail, audit_log, stats, count}>}
 */
export async function fetchTruckTrailAudit(truckId, options = {}) {
  const { days = 30, limit = 500 } = options;
  
  try {
    const url = `${getApiV1Base()}/trucks/${encodeURIComponent(truckId)}/trail-audit/?days=${days}&limit=${limit}`;
    console.log(`🚚 Fetching trail audit for truck ${truckId}: ${url}`);
    
    const response = await fetch(url, {
      method: 'GET',
      headers: { 'Content-Type': 'application/json' },
    });
    
    if (!response.ok) {
      if (response.status === 404) {
        console.debug(`⏭️ No trail data for truck ${truckId}`);
        return null;
      }
      throw new Error(`HTTP ${response.status}: ${response.statusText}`);
    }
    
    const data = await response.json();
    console.log(`✅ Trail audit for ${data.truck_identifier}: ${data.count} trail points, ${data.audit_log?.length || 0} audit entries`);
    return data;
  } catch (error) {
    console.error(`❌ Trail audit fetch error for ${truckId}:`, error.message);
    return null;
  }
}

/**
 * Fetch lightweight trail summary for all trucks
 * @param {number} days - Days to look back
 * @returns {Promise<{count, trucks: Array}>}
 */
export async function fetchAllTrucksTrailSummary(days = 7) {
  try {
    const url = `${getApiV1Base()}/trucks/trail-summary/?days=${days}`;
    console.log(`🚚 Fetching all trucks trail summary: ${url}`);
    
    const response = await fetch(url, {
      method: 'GET',
      headers: { 'Content-Type': 'application/json' },
    });
    
    if (!response.ok) {
      throw new Error(`HTTP ${response.status}: ${response.statusText}`);
    }
    
    const data = await response.json();
    console.log(`✅ Trail summary: ${data.count} trucks with trail data`);
    return data;
  } catch (error) {
    console.error(`❌ Trail summary fetch error:`, error.message);
    return { count: 0, trucks: [] };
  }
}

/**
 * Fetch lightweight trail summary for a single truck
 * @param {string} truckId - UUID or truck_identifier
 * @param {number} days - Days to look back
 * @returns {Promise<{truck_id, truck_identifier, plate, stats}>}
 */
export async function fetchTruckTrailSummary(truckId, days = 7) {
  try {
    const url = `${getApiV1Base()}/trucks/${encodeURIComponent(truckId)}/trail-summary/?days=${days}`;
    
    const response = await fetch(url, {
      method: 'GET',
      headers: { 'Content-Type': 'application/json' },
    });
    
    if (!response.ok) {
      if (response.status === 404) return null;
      throw new Error(`HTTP ${response.status}: ${response.statusText}`);
    }
    
    return await response.json();
  } catch (error) {
    console.error(`❌ Truck trail summary fetch error:`, error.message);
    return null;
  }
}

/**
 * Convert trail data to Leaflet-compatible polyline coordinates
 * @param {Array} trail - Array of {latitude, longitude} objects
 * @returns {Array<[number, number]>} Array of [lat, lng] pairs
 */
export function trailToLeafletCoords(trail) {
  if (!trail || !Array.isArray(trail)) return [];
  return trail
    .filter(p => typeof p.latitude === 'number' && typeof p.longitude === 'number')
    .map(p => [p.latitude, p.longitude]);
}

/**
 * Get trail statistics as formatted string
 * @param {object} stats - Stats object from trail audit API
 * @returns {Array<{label: string, value: string}>}
 */
export function formatTrailStats(stats) {
  if (!stats) return [];
  
  const formatted = [];
  
  if (stats.total_points != null) {
    formatted.push({ label: 'GPS Points', value: stats.total_points.toLocaleString() });
  }
  if (stats.total_distance_km != null) {
    formatted.push({ label: 'Total Distance', value: `${stats.total_distance_km.toFixed(1)} km` });
  }
  if (stats.avg_speed != null) {
    formatted.push({ label: 'Avg Speed', value: `${stats.avg_speed.toFixed(1)} km/h` });
  }
  if (stats.max_speed != null) {
    formatted.push({ label: 'Max Speed', value: `${stats.max_speed.toFixed(1)} km/h` });
  }
  if (stats.start_time) {
    formatted.push({ label: 'First Seen', value: new Date(stats.start_time).toLocaleString() });
  }
  if (stats.end_time) {
    formatted.push({ label: 'Last Seen', value: new Date(stats.end_time).toLocaleString() });
  }
  if (stats.duration_hours != null) {
    formatted.push({ label: 'Duration', value: `${stats.duration_hours.toFixed(1)} hrs` });
  }
  if (stats.trail_segments != null) {
    formatted.push({ label: 'Trail Segments', value: stats.trail_segments.toString() });
  }
  
  return formatted;
}