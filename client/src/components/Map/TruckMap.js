import React, { useEffect, useRef, useState } from 'react';
import { useTruckLocations } from '../../hooks/useTruckLocations';
import { useOSRMTrails } from '../../hooks/useOSRMTrails';

/**
 * Truck Map Component
 * Displays trucks on a map with real-time location updates and trail visualization
 */
const TruckMap = ({ missionId, driverId }) => {
  const mapRef = useRef(null);
  const [map, setMap] = useState(null);
  const [truckMarkers, setTruckMarkers] = useState(new Map());
  const [trails, setTrails] = useState(new Map());
  
  const { locations, loading, error } = useTruckLocations({ missionId, driverId });
  const { getTrailForTruck } = useOSRMTrails();

  // Initialize map
  useEffect(() => {
    if (mapRef.current && !map) {
      // Initialize Leaflet map (assuming Leaflet is available)
      const mapInstance = L.map(mapRef.current).setView([0, 0], 2);
      
      // Add OpenStreetMap tile layer
      L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
        attribution: '&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors'
      }).addTo(mapInstance);
      
      setMap(mapInstance);
    }
    
    // Cleanup
    return () => {
      if (map) {
        map.remove();
        setMap(null);
      }
    };
  }, [map]);

  // Update truck markers when locations change
  useEffect(() => {
    if (!map) return;
    
    // Clear existing markers
    truckMarkers.forEach(marker => {
      map.removeLayer(marker);
    });
    truckMarkers.clear();
    
    // Add new markers for each truck
    locations.forEach(location => {
      if (!location.latitude || !location.longitude) return;
      
      const marker = L.marker([location.latitude, location.longitude])
        .bindPopup(`
          <b>${location.truck_plate || 'Unknown Truck'}</b><br/>
          Driver: ${location.driver_name || 'Unknown'}<br/>
          Speed: ${location.speed || 0} km/h<br/>
          Updated: ${new Location(location.timestamp).toLocaleString()}
        `);
      
      marker.addTo(map);
      truckMarkers.set(location.id, marker);
    });
    
    // Fit map to show all markers if we have locations
    if (locations.length > 0 && map) {
      const group = new L.featureGroup(Array.from(truckMarkers.values()));
      if (group.getLayers().length > 0) {
        map.fitBounds(group.getBounds().pad(0.1));
      }
    }
  }, [locations, map, truckMarkers]);

  // Update trails when locations change
  useEffect(() => {
    if (!map) return;
    
    // Clear existing trails
    trails.forEach(trail => {
      if (trail.layer) map.removeLayer(trail.layer);
    });
    trails.clear();
    
    // Generate and add trails for each truck
    locations.forEach(async (location) => {
      if (!location.latitude || !location.longitude) return;
      
      try {
        const trailData = await getTrailForTruck(location.truck_id, 24); // Last 24 hours
        if (trailData && trailData.coordinates && trailData.coordinates.length > 1) {
          const trailLayer = L.polyline(trailData.coordinates, {
            color: '#007bff',
            weight: 3,
            opacity: 0.7
          }).addTo(map);
          
          trails.set(location.truck_id, {
            data: trailData,
            layer: trailLayer
          });
        }
      } catch (err) {
        console.warn(`Could not generate trail for truck ${location.truck_id}:`, err);
      }
    });
  }, [locations, map, getTrailForTruck, trails]);

  if (loading) {
    return <div className="map-loading">Loading map...</div>;
  }

  if (error) {
    return <div className="map-error">Error loading map: {error}</div>;
  }

  return (
    <div className="truck-map-container" style={{ height: '500px', width: '100%' }}>
      <div ref={mapRef} style={{ height: '100%', width: '100%' }} />
      {!locations.length && (
        <div className="map-empty-state">
          No truck location data available
        </div>
      )}
    </div>
  );
};

export default TruckMap;