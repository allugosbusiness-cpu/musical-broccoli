import { useEffect, useRef, useState } from 'react';
import L from 'leaflet';
import 'leaflet/dist/leaflet.css';
import 'leaflet.markercluster/dist/MarkerCluster.css';
import 'leaflet.markercluster/dist/MarkerCluster.Default.css';
import 'leaflet.markercluster';
import { getDashboardTrucks, getDashboardMissions, getMissionRouteGeometry } from '../services/api';
import { reverseGeocode } from '../services/geocoding';
import { getCoordinates } from '../data/locations';
import { fetchTruckTrailAudit, trailToLeafletCoords } from '../services/trailAuditService';
import { locationSyncService } from '../services/locationSyncService';
import RoadMatchedTrailSystem from './RoadMatchedTrailSystem';
import DriverEventAlerts from './DriverEventAlerts';
import { driverEventTracker } from '../services/driverEventTracker';
import { extractCoordinates, isValidCoordinate, getLocationStatus } from '../utils/locationExtractor';
import '../styles/trailStyles.css';

// Helper to get API base URL for v1 endpoints
const getApiV1Base = () => {
  if (import.meta.env.MODE === 'development') return 'http://localhost:8000/api/v1';
  return 'https://pulsetrack-back.onrender.com/api/v1';
};

// Helper to get legacy API base URL (without v1)
const getApiBase = () => {
  if (import.meta.env.MODE === 'development') return 'http://localhost:8000/api';
  return 'https://pulsetrack-back.onrender.com/api';
};

// Fix Leaflet default marker icons
delete L.Icon.Default.prototype._getIconUrl;
L.Icon.Default.mergeOptions({
  iconRetinaUrl: 'https://cdnjs.cloudflare.com/ajax/libs/leaflet/1.9.4/images/marker-icon-2x.png',
  iconUrl: 'https://cdnjs.cloudflare.com/ajax/libs/leaflet/1.9.4/images/marker-icon.png',
  shadowUrl: 'https://cdnjs.cloudflare.com/ajax/libs/leaflet/1.9.4/images/marker-shadow.png',
});

const STATUS_COLORS = {
  moving: '#3b82f6',
  delayed: '#f59e0b',
  stopped: '#ef4444',
  delivered: '#8b5cf6',
  maintenance: '#ec4899',
};

// Distinct colors for truck routes (different from status colors)
const TRUCK_ROUTE_COLORS = [
  '#FF6B6B',  // Red
  '#4ECDC4',  // Teal
  '#45B7D1',  // Sky Blue
  '#FFA07A',  // Light Salmon
  '#98D8C8',  // Mint
  '#F7DC6F',  // Yellow
  '#BB8FCE',  // Purple
  '#85C1E2',  // Light Blue
  '#F8B195',  // Peach
  '#C7CEEA',  // Lavender
];

// Function to get unique color for each truck based on index
const getTruckRouteColor = (truckIndex) => {
  return TRUCK_ROUTE_COLORS[truckIndex % TRUCK_ROUTE_COLORS.length];
};

export default function GlobalMap({ onTruckSelect, highlightedTruck = null, refreshTrigger = 0 }) {
  const mapRef = useRef(null);
  const map = useRef(null);
  const markersRef = useRef({});
  const markerClusterGroup = useRef(null);  // ✅ NEW: Marker cluster group for overlapping trucks
  const matchedLayersRef = useRef({});      // Persistent matched routes (FINAL)
  const rawPreviewLayersRef = useRef({});   // Debug preview layers only
  const trailLayersRef = useRef({});        // Trail polylines
  const routeLayersRef = useRef({});        // OSRM mission route polylines
  const gpsBufferRef = useRef({});          // GPS points buffer per truck
  const matchTimeoutRef = useRef({});       // Debounce timers

  const [trucks, setTrucks] = useState([]);
  const [previousTrucks, setPreviousTrucks] = useState({}); // For event tracking
  const [loading, setLoading] = useState(true);
  const [selectedTruck, setSelectedTruck] = useState(null);
  const [showRawTraces, setShowRawTraces] = useState(false);
  const [legend, setLegend] = useState([]);
  const [selectedTruckData, setSelectedTruckData] = useState(null);
  const [showFullTrails, setShowFullTrails] = useState(true);
  
  // ✅ NEW: Cache to prevent duplicate updates to same truck location
  const lastTruckHashRef = useRef({});  // Tracks hash of last known truck state

  // ✅ FIXED: Sync selected truck data when selection changes
  useEffect(() => {
    if (selectedTruck && trucks.length > 0) {
      const truck = trucks.find(t => t.id === selectedTruck);
      if (truck) {
        console.log(`📍 Syncing selected truck data for: ${truck.identifier}`);
        setSelectedTruckData({
          id: truck.id,
          plate: truck.plate,
          identifier: truck.identifier,
          status: truck.status,
          location: truck.location_name || 'Unknown',
          latitude: truck.latitude,
          longitude: truck.longitude,
          speed: truck.speed || 0,
          coordinates: (Number.isFinite(truck.latitude) && Number.isFinite(truck.longitude)) ? `${Number(truck.latitude).toFixed(4)}, ${Number(truck.longitude).toFixed(4)}` : 'Not set',
        });
      }
    } else {
      setSelectedTruckData(null);
    }
  }, [selectedTruck, trucks]);

  // Initialize map with persistent feature groups
  useEffect(() => {
    console.log('🗺️ useEffect: map init starting', { mapCurrent: !!map.current, mapRefCurrent: !!mapRef.current });
    
    if (map.current) {
      console.log('ℹ️ Map already initialized, skipping');
      return;
    }
    if (!mapRef.current) {
      console.log('⚠️ mapRef.current is null, deferring initialization');
      return; // Guard: mapRef not yet attached
    }

    try {
      console.log('🗺️ Initializing Leaflet map...', { 
        elementExists: !!mapRef.current,
        elementSize: mapRef.current ? `${mapRef.current.offsetWidth}x${mapRef.current.offsetHeight}` : 'N/A'
      });
      
      map.current = L.map(mapRef.current).setView([-17.8252, 31.0335], 5);
      console.log('✅ Leaflet map created');

      L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
        attribution: '© OpenStreetMap',
        maxZoom: 19,
        minZoom: 3,
      }).addTo(map.current);
      console.log('✅ Tile layer added');

      // Create persistent feature groups (never removed)
      const matchedGroup = L.featureGroup().addTo(map.current);
      const rawPreviewGroup = L.featureGroup().addTo(map.current);

      // ✅ NEW: Create marker cluster group to handle overlapping truck markers
      markerClusterGroup.current = L.markerClusterGroup({
        maxClusterRadius: 60,  // Cluster trucks within 60px
        iconCreateFunction: (cluster) => {
          const count = cluster.getChildCount();
          const size = count < 10 ? 'small' : count < 100 ? 'medium' : 'large';
          return L.divIcon({
            html: `<div style="
              background-color: #ef4444;
              color: white;
              border-radius: 50%;
              width: ${size === 'small' ? 30 : size === 'medium' ? 40 : 50}px;
              height: ${size === 'small' ? 30 : size === 'medium' ? 40 : 50}px;
              display: flex;
              align-items: center;
              justify-content: center;
              font-weight: bold;
              font-size: ${size === 'small' ? 12 : size === 'medium' ? 14 : 16}px;
              border: 2px solid white;
              box-shadow: 0 2px 8px rgba(0,0,0,0.3);
            ">${count}</div>`,
            className: 'truck-cluster',
            iconSize: [40, 40],
            iconAnchor: [20, 20],
          });
        },
      }).addTo(map.current);

      window.matchedGroup = matchedGroup;
      window.rawPreviewGroup = rawPreviewGroup;

      console.log('✅ Map initialized with feature groups and marker clustering');

      // ✅ NEW: Auto-refresh truck locations when user pans/zooms map
      // Debounced to avoid excessive API calls
      let autoRefreshTimeout;
      const handleMapInteraction = () => {
        clearTimeout(autoRefreshTimeout);
        // Refresh after 2 seconds of no map movement
        autoRefreshTimeout = setTimeout(() => {
          console.log('🔄 Auto-refreshing truck locations after map interaction');
          // Force location sync to get latest data
          locationSyncService.forceSyncNow().catch(err => console.warn('Auto-refresh error:', err));
        }, 2000);
      };

      // Listen for map interactions
      map.current.on('moveend', handleMapInteraction);
      map.current.on('zoomend', handleMapInteraction);

      return () => {
        clearTimeout(autoRefreshTimeout);
        if (map.current) {
          map.current.off('moveend', handleMapInteraction);
          map.current.off('zoomend', handleMapInteraction);
        }
      };
    } catch (error) {
      console.error('❌ Map initialization error:', error);
    }

    return () => {
      if (map.current) {
        console.log('🗺️ Removing map on unmount');
        map.current.remove();
        map.current = null;
      }
    };
  }, []);

  /**
   * UPDATE MATCHED ROUTE - FINAL RENDERING ONLY
   * Uses OSRM geometry with halo + main line in truck color
   */
  const updateMatchedRoute = (truckId, geojson, routeColor) => {
    if (!map.current || !geojson || !geojson.coordinates) return;

    const matchedGroup = window.matchedGroup;

    // Remove old matched route for this truck
    if (matchedLayersRef.current[truckId]) {
      matchedGroup.removeLayer(matchedLayersRef.current[truckId]);
    }

    if (geojson.coordinates.length < 2) return;

    // Convert GeoJSON [lng,lat] to Leaflet [lat,lng]
    const coords = geojson.coordinates.map(([lng, lat]) => [lat, lng]);

    const zoomWidth = (zoom) => Math.max(2, Math.min(6, zoom - 12));
    const mainWeight = zoomWidth(map.current.getZoom());
    const haloWeight = mainWeight + 6;

    // HALO layer (under) - pale white
    const haloPolyline = L.polyline(coords, {
      color: '#ffffff',
      weight: haloWeight,
      opacity: 0.3,
      lineCap: 'round',
      lineJoin: 'round',
      zIndex: 100,
      interactive: false,
    }).addTo(matchedGroup);

    // MAIN layer (over) - truck color
    const mainPolyline = L.polyline(coords, {
      color: routeColor || '#0066cc',
      weight: mainWeight,
      opacity: 0.85,
      lineCap: 'round',
      lineJoin: 'round',
      zIndex: 110,
    }).addTo(matchedGroup);

    const popup = `
      <div style="font-family: monospace; font-size: 11px;">
        <strong style="color: ${routeColor};">🛣️ Route</strong>
        <p>${coords.length} points (snapped to roads)</p>
      </div>
    `;
    mainPolyline.bindPopup(popup);

    const group = L.featureGroup([haloPolyline, mainPolyline]);
    matchedGroup.addLayer(group);
    matchedLayersRef.current[truckId] = group;

    // Update zoom-dependent widths
    map.current.on('zoomend', () => {
      const newWeight = zoomWidth(map.current.getZoom());
      haloPolyline.setStyle({ weight: newWeight + 6 });
      mainPolyline.setStyle({ weight: newWeight });
    });

    console.log(`✅ Matched route for ${truckId}: ${coords.length} points (${routeColor})`);
  };

  /**
   * UPDATE RAW PREVIEW - DEBUG ONLY
   * Shows faint dashed lines only when showRawTraces is true
   */
  const updateRawPreview = (truckId, gpsPoints, routeColor) => {
    const rawGroup = window.rawPreviewGroup;

    // Remove old preview
    if (rawPreviewLayersRef.current[truckId]) {
      rawGroup.removeLayer(rawPreviewLayersRef.current[truckId]);
      delete rawPreviewLayersRef.current[truckId];
    }

    if (!showRawTraces || !gpsPoints || gpsPoints.length < 2) return;

    const previewPolyline = L.polyline(gpsPoints, {
      color: routeColor || '#0066cc',
      weight: 2,
      opacity: 0.3,
      dashArray: '5, 5',
      lineCap: 'round',
      lineJoin: 'round',
      zIndex: 50,
    }).addTo(rawGroup);

    rawPreviewLayersRef.current[truckId] = previewPolyline;
  };

  /**
   * Add truck marker to map with label
   */
  const addTruckMarker = (truck) => {
    console.log(`🚚 addTruckMarker called for truck ${truck.identifier}:`, {
      id: truck.id,
      lat: truck.latitude,
      lon: truck.longitude,
      status: truck.status,
      location_status: truck.location_status,
      hasMap: !!map.current,
    });

    if (!map.current) {
      console.error(`❌ Map not initialized for truck ${truck.identifier}`);
      return;
    }
    
    // ✅ IMPROVED: Use robust validation and default fallback
    let markerLat = truck.latitude;
    let markerLon = truck.longitude;
    let locationPending = truck.location_status === 'pending';
    const defaultCoords = { lat: -17.8252, lon: 31.0335 }; // Harare center
    
    // Check if we have valid coordinates using utility function
    if (!isValidCoordinate(markerLat, markerLon)) {
      console.warn(`⚠️ Invalid coordinates for truck ${truck.identifier} (status: ${truck.location_status}), using default location`);
      markerLat = defaultCoords.lat;
      markerLon = defaultCoords.lon;
      locationPending = true;
    }

    // Remove old marker if exists
    if (markersRef.current[truck.id]) {
      console.log(`🗑️ Removing old marker for truck ${truck.identifier}`);
      markerClusterGroup.current.removeLayer(markersRef.current[truck.id]);
    }

    // Create custom icon for truck with name label
    const statusColors = {
      moving: '#3b82f6',
      stopped: '#ef4444',
      delayed: '#f59e0b',
      idle: '#ef4444',
      enroute: '#3b82f6',
      maintenance: '#ec4899',
    };

    const truckColor = statusColors[truck.status] || '#0066cc';

    const customIcon = L.divIcon({
      html: `
        <div style="
          position: relative;
          text-align: center;
          opacity: ${locationPending ? '0.6' : '1'};
        ">
          <div style="
            width: 40px;
            height: 40px;
            background-color: ${truckColor};
            border: 3px solid white;
            border-radius: 50%;
            display: flex;
            align-items: center;
            justify-content: center;
            font-weight: bold;
            color: white;
            font-size: 18px;
            box-shadow: 0 2px 8px rgba(0,0,0,0.3);
            cursor: pointer;
            margin: 0 auto;
            ${locationPending ? 'animation: pulse 2s infinite;' : ''}
          ">
            🚚
          </div>
          <div style="
            position: absolute;
            top: 42px;
            left: 50%;
            transform: translateX(-50%);
            background-color: ${truckColor};
            color: white;
            padding: 2px 6px;
            border-radius: 3px;
            font-size: 11px;
            font-weight: bold;
            white-space: nowrap;
            box-shadow: 0 1px 4px rgba(0,0,0,0.2);
          ">
            ${truck.identifier} ${locationPending ? '(pending)' : ''}
          </div>
        </div>
      `,
      className: 'truck-marker',
      iconSize: [48, 70],
      iconAnchor: [24, 70],
      popupAnchor: [0, -70],
    });

    const marker = L.marker([markerLat || 0, markerLon || 0], { icon: customIcon })
      .bindPopup(`
        <div style="font-family: sans-serif; width: 220px;">
          <strong style="color: ${truckColor};">📍 ${truck.plate}</strong>
          <p style="margin: 5px 0;"><strong>Truck ID:</strong> ${truck.identifier}</p>
          <p style="margin: 5px 0;"><strong>Status:</strong> <span style="color: ${truckColor}; font-weight: bold;">${truck.status.toUpperCase()}</span></p>
          <p style="margin: 5px 0;"><strong>Location:</strong> ${truck.location_name}</p>
          <p style="margin: 5px 0;"><strong>Coordinates:</strong> ${(Number.isFinite(markerLat) && Number.isFinite(markerLon)) ? Number(markerLat).toFixed(4) + ', ' + Number(markerLon).toFixed(4) : 'N/A'}</p>
          <p style="margin: 5px 0;"><strong>Speed:</strong> ${truck.speed || 0} km/h</p>
          ${locationPending ? '<p style="margin: 5px 0; color: #f59e0b;"><em>\u26a0️ Location update pending...</em></p>' : ''}
        </div>
      `, { maxWidth: 250, maxHeight: 300 })
      .addTo(markerClusterGroup.current);  // ✅ CHANGED: Add to cluster group instead of map.current

    // ✅ FIXED: Add click event handler for marker selection
    marker.on('click', () => {
      console.log(`🖱️ Marker clicked for ${truck.identifier}`);
      setSelectedTruck(truck.id);  // Update local state
      if (onTruckSelect) {
        onTruckSelect(truck);  // Notify parent component
      }
      marker.openPopup();  // Open popup with details
    });

    // ✅ FIXED: Auto-highlight and pan logic
    if (highlightedTruck === truck.id) {
      console.log(`✨ Auto-highlighting truck: ${truck.identifier}`);
      marker.openPopup();
      if (map.current) {
        map.current.setView([markerLat, markerLon], map.current.getZoom());
      }
    }

    markersRef.current[truck.id] = marker;

    // Log marker creation
    console.log(`📋 Marker added for ${truck.identifier} at ${(Number.isFinite(markerLat) && Number.isFinite(markerLon)) ? Number(markerLat).toFixed(3) + ', ' + Number(markerLon).toFixed(3) : 'N/A'}${locationPending ? ' (pending real-time update)' : ''}`);
  };

  /**
   * Update truck marker when location changes
   */
  const updateTruckMarker = (truck) => {
    if (!markersRef.current[truck.id]) {
      addTruckMarker(truck);
      return;
    }

    const marker = markersRef.current[truck.id];
    const defaultCoords = { lat: -17.8252, lon: 31.0335 }; // Harare center
    
    // ✅ IMPROVED: Use robust validation
    let markerLat = truck.latitude;
    let markerLon = truck.longitude;
    
    if (!isValidCoordinate(markerLat, markerLon)) {
      markerLat = defaultCoords.lat;
      markerLon = defaultCoords.lon;
    }
    
    marker.setLatLng([markerLat, markerLon]);
    console.log(`✅ Updated marker for ${truck.identifier} → [${(Number.isFinite(markerLat) && Number.isFinite(markerLon)) ? Number(markerLat).toFixed(4) + ', ' + Number(markerLon).toFixed(4) : 'N/A'}]`);
  };

  /**
   * Buffer GPS update with debounced matching
   */
  const onGpsUpdate = (truckId, lat, lon) => {
    if (!gpsBufferRef.current[truckId]) {
      gpsBufferRef.current[truckId] = [];
    }
    gpsBufferRef.current[truckId].push([lat, lon]);

    // Show faint debug preview
    const truck = trucks.find(t => t.id === truckId);
    updateRawPreview(truckId, gpsBufferRef.current[truckId], truck?.route_color);

    scheduleMatch(truckId);
  };

  /**
   * Debounced match scheduling
   */
  const scheduleMatch = (truckId, options = {}) => {
    const { batchSize = 10, interval = 3000 } = options;

    if (matchTimeoutRef.current[truckId]) {
      clearTimeout(matchTimeoutRef.current[truckId]);
    }

    const buffer = gpsBufferRef.current[truckId] || [];
    if (buffer.length >= batchSize) {
      runMatch(truckId);
    } else {
      matchTimeoutRef.current[truckId] = setTimeout(() => {
        if ((gpsBufferRef.current[truckId] || []).length > 0) {
          runMatch(truckId);
        }
      }, interval);
    }
  };

  /**
   * Call backend /match to snap GPS to roads
   */
  const runMatch = async (truckId) => {
    const buffer = gpsBufferRef.current[truckId];
    if (!buffer || buffer.length < 2) return;

    try {
      console.log(`🔄 Matching ${buffer.length} points for ${truckId}...`);

      const response = await fetch(
        `http://localhost:8000/api/trucks/${truckId}/route`,
        {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({
            gps_points: buffer.map(([lat, lon]) => ({ lat, lon })),
          }),
        }
      );

      const data = await response.json();

      if (data.route_geojson && data.route_geojson.coordinates) {
        // Update FINAL matched route
        updateMatchedRoute(truckId, data.route_geojson, data.route_color);

        // Clear buffer and preview
        gpsBufferRef.current[truckId] = [];
        updateRawPreview(truckId, [], data.route_color);

        console.log(`✅ Matched route received`);
      } else {
        console.warn(`⚠️ No geometry, retrying...`);
        setTimeout(() => runMatch(truckId), 2000);
      }
    } catch (error) {
      console.error(`❌ Match failed: ${error.message}`);
      setTimeout(() => runMatch(truckId), 2000);
    }
  };

  /**
   * Load trucks on mount
   */
  useEffect(() => {
    // Only fetch trucks if map is initialized
    if (!map.current) {
      console.log('⏳ Waiting for map to initialize before fetching trucks...');
      return;
    }

    const fetchTrucks = async () => {
      try {
        console.log('📍 Fetching trucks from dashboard API...');
        const data = await getDashboardTrucks();
        console.log('✅ Trucks fetched:', data?.length || 0, 'trucks', data);
        
        const trucksArray = Array.isArray(data) ? data : [];
        console.log(`🚚 Processing ${trucksArray.length} trucks for transformation`);
        
        // Transform v2 truck data to match expected format
        const transformedTrucks = await Promise.all(trucksArray.map(async (truck, index) => {
          console.log(`  🔄 Transforming truck ${index + 1}/${trucksArray.length}:`, truck.truck_identifier);
          
          // ✅ NEW: Use robust location extractor - handles all coordinate formats
          const { lat: coordLat, lon: coordLon, source } = extractCoordinates(truck);
          const locationStatus = getLocationStatus(truck);
          
          console.log(`    📍 Location extraction: source=${source}, status=${locationStatus}, coords=[${Number.isFinite(coordLat) ? Number(coordLat).toFixed(4) : 'N/A'}, ${Number.isFinite(coordLon) ? Number(coordLon).toFixed(4) : 'N/A'}]`);
          
          // Get address from coordinates
          let location_name = 'Unknown Location';
          if (isValidCoordinate(coordLat, coordLon)) {
            try {
              location_name = await reverseGeocode(coordLat, coordLon);
            } catch (err) {
              console.warn(`⚠️ Geocoding failed for truck ${truck.truck_identifier}:`, err.message);
              location_name = (Number.isFinite(coordLat) && Number.isFinite(coordLon)) ? `Location (${Number(coordLat).toFixed(4)}, ${Number(coordLon).toFixed(4)})` : 'Location unknown';
            }
          }
          
          // Assign unique color to each truck based on index
          const routeColor = getTruckRouteColor(index);
          
          const transformed = {
            id: truck.id,
            plate: truck.plate,
            identifier: truck.truck_identifier,
            status: truck.status === 'enroute' ? 'moving' : truck.status === 'idle' ? 'stopped' : truck.status,
            location: (Number.isFinite(coordLat) && Number.isFinite(coordLon) && isValidCoordinate(coordLat, coordLon)) ? `${Number(coordLat).toFixed(3)}, ${Number(coordLon).toFixed(3)}` : null,
            location_name: location_name,
            latitude: coordLat,
            longitude: coordLon,
            location_status: locationStatus,  // ✅ NEW: Track location status for UI
            location_source: source,  // ✅ NEW: Track data source for debugging
            route_color: routeColor,  // Unique color for this truck
            route_geojson: null,  // Will be fetched separately if needed
            speed: truck.speed_kmh || 0,
            progress: 0,
          };
          
          console.log(`    ✅ Transformed ${truck.truck_identifier}:`, transformed);
          return transformed;
        }));

        console.log(`✅ All ${transformedTrucks.length} trucks transformed`, transformedTrucks);

        // Track events for each truck
        transformedTrucks.forEach(truck => {
          const prevTruck = previousTrucks[truck.id];
          driverEventTracker.trackTruck(truck, prevTruck);
        });

        // Update previous trucks state
        const newPreviousTrucks = {};
        transformedTrucks.forEach(t => {
          newPreviousTrucks[t.id] = { ...t };
        });
        setPreviousTrucks(newPreviousTrucks);

        setTrucks(transformedTrucks);
        setLegend(
          transformedTrucks.map(t => ({
            id: t.id,
            name: t.plate,
            color: t.route_color,  // Use assigned truck color
          }))
        );

        // Add truck markers to map (only if map is ready)
        if (map.current) {
          console.log(`🗺️ Adding/updating markers to map for ${transformedTrucks.length} trucks...`);
          transformedTrucks.forEach((truck, idx) => {
            // ✅ UPDATE instead of ADD: Check if marker exists
            if (markersRef.current[truck.id]) {
              console.log(`  🔄 Updating marker for: ${truck.identifier} → lat=${Number.isFinite(truck.latitude) ? Number(truck.latitude).toFixed(4) : 'N/A'}, lon=${Number.isFinite(truck.longitude) ? Number(truck.longitude).toFixed(4) : 'N/A'}`);
              updateTruckMarker(truck);  // Update position
            } else {
              console.log(`  📍 Adding new marker ${idx + 1}/${transformedTrucks.length}: ${truck.identifier}`);
              addTruckMarker(truck);  // Add new marker
            }
          });
          console.log(`✅ All ${transformedTrucks.length} markers processed`);
        }

        setLoading(false);
      } catch (error) {
        console.error('❌ Failed to fetch trucks:', error);
        setLoading(false);
      }
    };

    fetchTrucks();
    
    // ✅ CRITICAL FIX: Poll for real-time truck updates every 5 seconds
    // This ensures mobile app location updates appear on map immediately
    const interval = setInterval(fetchTrucks, 5000); // Update EVERY 5 SECONDS (was 30s)
    return () => clearInterval(interval);
  }, [map.current, previousTrucks, highlightedTruck, refreshTrigger]);

  /**
   * ✅ NEW: Real-time location sync from backend
   * Updates truck markers when locations change from mobile app
   */
  useEffect(() => {
    if (!map.current) return;

    console.log('📡 Setting up location sync service...');
    
    // Subscribe to location updates
    const unsubscribe = locationSyncService.subscribe((locationUpdate) => {
      console.log(`📍 Location update received for ${locationUpdate.truck_identifier}:`, {
        lat: Number.isFinite(locationUpdate.latitude) ? Number(locationUpdate.latitude).toFixed(4) : 'N/A',
        lon: Number.isFinite(locationUpdate.longitude) ? Number(locationUpdate.longitude).toFixed(4) : 'N/A',
        speed: locationUpdate.speed_kmh,
        source: locationUpdate.source,
      });

      // ✅ NEW: Deduplication - only update if location actually changed
      const cacheKey = locationUpdate.truck_id;
      const newHash = JSON.stringify({
        lat: locationUpdate.latitude,
        lon: locationUpdate.longitude,
        speed: locationUpdate.speed_kmh
      });
      const oldHash = lastTruckHashRef.current[cacheKey];

      if (newHash === oldHash) {
        console.debug(`⏭️ Skipping duplicate update for ${locationUpdate.truck_identifier}`);
        return;  // Skip - no change
      }

      // Update cache
      lastTruckHashRef.current[cacheKey] = newHash;

      // Find and update the truck in local state
      setTrucks(prevTrucks => {
        const updatedTrucks = prevTrucks.map(truck => {
          if (truck.id === locationUpdate.truck_id) {
            return {
              ...truck,
              latitude: locationUpdate.latitude,
              longitude: locationUpdate.longitude,
              speed: locationUpdate.speed_kmh,
              location_source: locationUpdate.source,  // Track source of update
            };
          }
          return truck;
        });
        return updatedTrucks;
      });

      // Update marker position if it exists
      if (markersRef.current[locationUpdate.truck_id]) {
        const marker = markersRef.current[locationUpdate.truck_id];
        if (isValidCoordinate(locationUpdate.latitude, locationUpdate.longitude)) {
          marker.setLatLng([locationUpdate.latitude, locationUpdate.longitude]);
          console.log(`✅ Marker updated for ${locationUpdate.truck_identifier}`);
        } else {
          console.warn(`⚠️ Invalid coordinates for marker update: [${locationUpdate.latitude}, ${locationUpdate.longitude}]`);
        }
      }
    });

    // Start syncing
    locationSyncService.startSync();
    
    // Cleanup
    return () => {
      unsubscribe();
      locationSyncService.stopSync();
      console.log('🛑 Location sync stopped');
    };
  }, [map.current]);

  /**
   * Update selectedTruckData when selectedTruck changes
   */
  useEffect(() => {
    if (selectedTruck && trucks.length > 0) {
      const truck = trucks.find(t => t.id === selectedTruck);
      if (truck) {
        setSelectedTruckData({
          plate: truck.plate,
          identifier: truck.identifier,
          status: truck.status,
          location: truck.location || 'Unknown',
          location_name: truck.location_name,
          speed: truck.speed || 0,
          latitude: truck.latitude,
          longitude: truck.longitude,
        });
      }
    }
  }, [selectedTruck, trucks]);

  /**
   * Load and display truck trails from BOTH:
   * 1. truck_trail_with_directions (legacy - returns data.trail[])
   * 2. trail-audit (new - returns data.trail[] with latitude/longitude format)
   */
  useEffect(() => {
    if (!map.current || !trucks.length) return;

    const loadTrails = async () => {
      for (const truck of trucks) {
        try {
          // TRY 1: New trail-audit endpoint (returns full GPS trail data)
          const auditResp = await fetch(
            `${getApiV1Base()}/trucks/${truck.id}/trail-audit/?days=7&limit=2000`
          );
          
          if (auditResp.ok) {
            const auditData = await auditResp.json();
            
            // trail-audit returns data.trail[] with {latitude, longitude, timestamp}
            if (auditData.trail && auditData.trail.length >= 2) {
              // Remove old trail
              if (trailLayersRef.current[truck.id]) {
                map.current.removeLayer(trailLayersRef.current[truck.id]);
              }

              // Convert {latitude, longitude} to Leaflet [lat, lng] format
              const coords = auditData.trail
                .filter(p => Number.isFinite(p.latitude) && Number.isFinite(p.longitude))
                .map(p => [p.latitude, p.longitude]);

              if (coords.length >= 2) {
                const trailColor = truck.route_color || '#0066cc';
                const trailPolyline = L.polyline(coords, {
                  color: trailColor,
                  weight: 2,
                  opacity: 0.6,
                  lineCap: 'round',
                  lineJoin: 'round',
                  zIndex: 90,
                }).addTo(map.current);

                trailLayersRef.current[truck.id] = trailPolyline;
                console.log(`✅ Trail audit loaded for ${truck.id}: ${coords.length} points`);
                continue;  // Skip legacy method - audit endpoint has full data
              }
            }
          }
        } catch (e) {
          // audit endpoint not available, fall through to legacy
        }

        // TRY 2: Legacy truck_trail_with_directions endpoint
        try {
          const response = await fetch(
            `${getApiBase()}/v1/trucks/${truck.id}/truck_trail_with_directions/?limit=100`
          );
          
          if (response.status === 404) {
            console.debug(`⏭️ No trail data for truck ${truck.id} (not tracked yet)`);
            continue;
          }
          if (!response.ok) {
            console.warn(`API error loading trail for ${truck.id}: ${response.status}`);
            continue;
          }

          const data = await response.json();

          // The endpoint returns data.trail[] with {latitude, longitude, timestamp, sequence}
          // OR data.snapped_path/data.raw_trail for legacy format
          const trail = data.trail || data.snapped_path || data.raw_trail || [];
          if (trail.length < 2) continue;

          // Remove old trail
          if (trailLayersRef.current[truck.id]) {
            map.current.removeLayer(trailLayersRef.current[truck.id]);
          }

          // Convert to Leaflet format [lat, lng]
          const coords = trail.map(p => [
            p.lat !== undefined ? p.lat : (p.latitude || 0),
            p.lng !== undefined ? p.lng : (p.longitude || 0)
          ]).filter(([lat, lng]) => Number.isFinite(lat) && Number.isFinite(lng));

          if (coords.length < 2) continue;

          const trailColor = truck.route_color || '#0066cc';
          const trailPolyline = L.polyline(coords, {
            color: trailColor,
            weight: 2,
            opacity: 0.6,
            lineCap: 'round',
            lineJoin: 'round',
            zIndex: 90,
          }).addTo(map.current);

          trailLayersRef.current[truck.id] = trailPolyline;
          console.log(`✅ Trail loaded for ${truck.id}: ${coords.length} points`);
        } catch (error) {
          if (error.message !== 'Failed to fetch') {
            console.debug(`⏭️ Trail not available for ${truck.id}`);
          } else {
            console.warn(`⚠️ Network error loading trail for ${truck.id}:`, error.message);
          }
        }
      }
    };

    loadTrails();
    const interval = setInterval(loadTrails, 10000);  // Reload trails every 10 seconds
    return () => clearInterval(interval);
  }, [trucks, showFullTrails]);

  /**
   * Load and display routes from mission origin to destination
   */
  useEffect(() => {
    if (!map.current || !trucks.length) return;

    const loadRoutes = async () => {
      try {
        const missions = await getDashboardMissions();

        if (!missions || !missions.length) {
          console.warn('⚠️ No missions found');
          return;
        }

        // Group missions by truck
        const missionsByTruck = {};
        missions.forEach(mission => {
          const truckId = mission.truck_identifier;
          if (!missionsByTruck[truckId]) {
            missionsByTruck[truckId] = [];
          }
          missionsByTruck[truckId].push(mission);
        });

        // For each truck, render OSRM-based route from origin to destination
        for (const truck of trucks) {
          const truckMissions = missionsByTruck[truck.id] || [];
          if (!truckMissions.length) continue;

          // Get the active/most recent mission
          const activeMission = truckMissions.find(m => 
            m.status === 'ENROUTE' || m.status === 'PAUSED'
          ) || truckMissions[truckMissions.length - 1];

          if (!activeMission || !activeMission.id) continue;

          // Fetch OSRM route geometry for this mission
          const routeData = await getMissionRouteGeometry(activeMission.id);
          
          if (!routeData || !routeData.geometry) {
            console.warn(`⚠️ No route geometry for mission ${activeMission.mission_number}`);
            continue;
          }

          // Remove old route if exists
          if (routeLayersRef.current[truck.id]) {
            map.current.removeLayer(routeLayersRef.current[truck.id]);
          }
          if (routeLayersRef.current[`route_glow_${truck.id}`]) {
            map.current.removeLayer(routeLayersRef.current[`route_glow_${truck.id}`]);
          }

          // Convert GeoJSON geometry to Leaflet format [lat, lng]
          const routeGeometry = routeData.geometry;
          let routeCoords = [];
          
          if (routeGeometry.type === 'LineString') {
            // GeoJSON uses [lon, lat], convert to [lat, lon] for Leaflet
            routeCoords = routeGeometry.coordinates.map(coord => [coord[1], coord[0]]);
          }

          if (routeCoords.length < 2) continue;

          // Draw white glow line underneath for visibility
          const glowPolyline = L.polyline(routeCoords, {
            color: 'white',
            weight: 6,
            opacity: 0.4,
            lineCap: 'round',
            lineJoin: 'round',
            zIndex: 79,
          }).addTo(map.current);

          routeLayersRef.current[`route_glow_${truck.id}`] = glowPolyline;

          // Draw main route polyline with truck's color
          const routeColor = truck.route_color || '#3b82f6';
          const routePolyline = L.polyline(routeCoords, {
            color: routeColor,
            weight: 3,
            opacity: 0.85,
            lineCap: 'round',
            lineJoin: 'round',
            dashArray: '4, 2',  // Dashed to distinguish from trails
            zIndex: 80,
          }).addTo(map.current);

          routeLayersRef.current[truck.id] = routePolyline;

          console.log(`✅ OSRM route loaded for ${truck.id}: ${routeCoords.length} points, ${routeData.distance || 0}m distance`);
        }
      } catch (error) {
        console.warn(`⚠️ Could not load routes:`, error.message);
      }
    };

    loadRoutes();
    const interval = setInterval(loadRoutes, 30000); // Update every 30 seconds
    return () => clearInterval(interval);
  }, [trucks]);

  return (
    <div className="border border-slate-700/50 rounded-xl overflow-hidden flex flex-col relative bg-slate-900/50 shadow-xl backdrop-blur-sm" style={{ height: '750px' }}>
      {/* Road-Matched Trail System */}
      {map.current && trucks.length > 0 && (
        <RoadMatchedTrailSystem 
          mapInstance={map.current} 
          trucks={trucks}
        />
      )}

          {/* Driver Event Alerts */}
          <DriverEventAlerts tracker={driverEventTracker} />

          {/* Header */}
          <div className="px-5 py-4 border-b border-slate-700/50 bg-gradient-to-r from-slate-900 via-slate-800 to-slate-900/50">
            <div className="flex items-center justify-between">
              <span className="text-sm font-bold text-slate-100 uppercase tracking-widest">
                🗺️ Smart Global Map
              </span>
              <div className="flex items-center gap-3">
                <label style={{ display: 'flex', alignItems: 'center', gap: '6px', fontSize: '11px', color: '#cbd5e1', cursor: 'pointer' }}>
                  <input
                    type="checkbox"
                    checked={showFullTrails}
                    onChange={(e) => setShowFullTrails(e.target.checked)}
                    style={{ cursor: 'pointer' }}
                  />
                  Full trails
                </label>
                <label style={{ display: 'flex', alignItems: 'center', gap: '6px', fontSize: '11px', color: '#cbd5e1', cursor: 'pointer' }}>
                  <input
                    type="checkbox"
                    checked={showRawTraces}
                    onChange={(e) => {
                      setShowRawTraces(e.target.checked);
                      // Update all previews
                      trucks.forEach(t => {
                        updateRawPreview(
                          t.id,
                          e.target.checked ? (gpsBufferRef.current[t.id] || []) : [],
                          t.route_color
                        );
                      });
                    }}
                    style={{ cursor: 'pointer' }}
                  />
                  Raw GPS
                </label>
              </div>
        </div>
      </div>

      {/* Selected Truck Info Panel */}
      {selectedTruck && selectedTruckData && (
        <div style={{
          padding: '12px 15px',
          background: '#f0f9ff',
          borderBottom: '1px solid #bfdbfe',
          display: 'grid',
          gridTemplateColumns: '1fr 1fr 1fr 1fr auto',
          gap: '12px',
          alignItems: 'center',
          fontSize: '12px',
          fontFamily: 'monospace',
        }}>
          <div>
            <div style={{ color: '#666', fontSize: '10px', marginBottom: '2px' }}>TRUCK</div>
            <div style={{ fontWeight: 'bold', fontSize: '13px' }}>{selectedTruckData.plate}</div>
          </div>
          
          <div>
            <div style={{ color: '#666', fontSize: '10px', marginBottom: '2px' }}>DRIVER</div>
            <div style={{ fontWeight: 'bold' }}>{selectedTruckData.driver || 'N/A'}</div>
          </div>
          
          <div>
            <div style={{ color: '#666', fontSize: '10px', marginBottom: '2px' }}>SPEED</div>
            <div style={{ fontWeight: 'bold', color: '#3b82f6', fontSize: '13px' }}>{selectedTruckData.speed || 0} km/h</div>
          </div>
          
          <div>
            <div style={{ color: '#666', fontSize: '10px', marginBottom: '2px' }}>LOCATION</div>
            <div style={{ fontWeight: 'bold' }}>{selectedTruckData.location}</div>
          </div>
          
          <button
            onClick={() => {
              setSelectedTruck(null);
              setSelectedTruckData(null);
            }}
            style={{
              padding: '4px 8px',
              background: '#ef4444',
              color: 'white',
              border: 'none',
              borderRadius: '4px',
              cursor: 'pointer',
              fontSize: '12px',
              fontWeight: 'bold',
            }}
          >
            ×
          </button>
        </div>
      )}

      {/* Map Container */}
      <div style={{ flex: 1, position: 'relative' }}>
        {/* Map */}
        <div ref={mapRef} style={{ width: '100%', height: '100%' }} />

        {/* Legend - Positioned absolute over map */}
        <div style={{
          position: 'absolute',
          top: 10,
          left: 10,
          background: 'white',
          padding: '10px',
          borderRadius: '4px',
          zIndex: 1000,
          fontSize: '12px',
          boxShadow: '0 2px 4px rgba(0,0,0,0.1)',
        }}>
          <strong>Trucks</strong>
          {legend.map(item => (
            <div key={item.id} style={{ display: 'flex', alignItems: 'center', gap: '8px', cursor: 'pointer', marginTop: '4px' }}>
              <div style={{ width: '16px', height: '3px', background: item.color }} />
              <span
                onClick={() => {
                  const truck = trucks.find(t => t.id === item.id);
                  if (truck) {
                    const coords = truck.coordinates || getCoordinates(truck.location);
                    if (coords) map.current.flyTo([coords.lat, coords.lng], 13);
                  }
                }}
              >
                {item.name}
              </span>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
}
