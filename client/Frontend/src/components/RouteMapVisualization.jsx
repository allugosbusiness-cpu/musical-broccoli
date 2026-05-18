import React, { useState, useEffect, useRef } from 'react';
import { AlertTriangle, Truck, Navigation, Heart, Wind, Zap } from 'lucide-react';

const API_BASE = 'http://localhost:8000/api/v2';

export function RouteMapVisualization({ vehicleId = 'TRUCK-001', routeId }) {
  const mapContainer = useRef(null);
  const [map, setMap] = useState(null);
  const [route, setRoute] = useState(null);
  const [trail, setTrail] = useState(null);
  const [hazards, setHazards] = useState([]);
  const [trafficEvents, setTrafficEvents] = useState([]);
  const [loading, setLoading] = useState(true);
  const [mapReady, setMapReady] = useState(false);

  // Initialize Leaflet map
  useEffect(() => {
    if (typeof window !== 'undefined' && mapContainer.current && !mapReady) {
      // Dynamically load Leaflet
      const L = window.L;
      if (!L) {
        // Load Leaflet CSS
        const link = document.createElement('link');
        link.rel = 'stylesheet';
        link.href = 'https://cdnjs.cloudflare.com/ajax/libs/leaflet/1.9.4/leaflet.min.css';
        document.head.appendChild(link);

        // Load Leaflet JS
        const script = document.createElement('script');
        script.src = 'https://cdnjs.cloudflare.com/ajax/libs/leaflet/1.9.4/leaflet.min.js';
        script.async = true;
        script.onload = () => {
          initializeMap();
        };
        document.head.appendChild(script);
      } else {
        initializeMap();
      }
    }

    function initializeMap() {
      const L = window.L;
      const newMap = L.map(mapContainer.current).setView([17.8252, 25.2753], 8);

      L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
        attribution: '© OpenStreetMap contributors',
        maxZoom: 19,
      }).addTo(newMap);

      setMap(newMap);
      setMapReady(true);
    }
  }, [mapReady]);

  // Fetch route data
  useEffect(() => {
    if (routeId) {
      fetch(`${API_BASE}/routes/${routeId}`)
        .then((res) => res.json())
        .then((data) => setRoute(data))
        .catch((err) => console.error('Error fetching route:', err));
    }
  }, [routeId]);

  // Fetch trail data
  useEffect(() => {
    if (vehicleId) {
      fetch(`${API_BASE}/trails/${vehicleId}?simplify=true`)
        .then((res) => res.json())
        .then((data) => setTrail(data))
        .catch((err) => console.error('Error fetching trail:', err));
    }
  }, [vehicleId]);

  // Fetch hazards
  useEffect(() => {
    if (route?.polyline) {
      const bbox = computeBoundingBox(route.polyline.coordinates);
      fetch(`${API_BASE}/hazards?bounds=${bbox.minLon},${bbox.minLat},${bbox.maxLon},${bbox.maxLat}`)
        .then((res) => res.json())
        .then((data) => setHazards(data.hazards || []))
        .catch((err) => console.error('Error fetching hazards:', err));
    }
  }, [route]);

  // WebSocket subscription for real-time traffic
  useEffect(() => {
    if (!route?.polyline) return;

    const bbox = computeBoundingBox(route.polyline.coordinates);
    const ws = new WebSocket('ws://localhost:8000/api/v2/traffic/subscribe');

    ws.onopen = () => {
      ws.send(
        JSON.stringify({
          action: 'subscribe',
          bounds: {
            minLon: bbox.minLon,
            minLat: bbox.minLat,
            maxLon: bbox.maxLon,
            maxLat: bbox.maxLat,
          },
          event_types: ['accident', 'congestion', 'construction'],
        })
      );
    };

    ws.onmessage = (event) => {
      try {
        const trafficEvent = JSON.parse(event.data);
        setTrafficEvents((prev) => [
          ...prev.filter((e) => e.event_id !== trafficEvent.event_id),
          trafficEvent,
        ]);
      } catch (err) {
        console.error('Error parsing traffic event:', err);
      }
    };

    return () => {
      if (ws.readyState === WebSocket.OPEN) {
        ws.close();
      }
    };
  }, [route]);

  // Render map elements
  useEffect(() => {
    if (!map || !mapReady) return;

    const L = window.L;

    // Clear existing layers
    map.eachLayer((layer) => {
      if (layer instanceof L.Polyline || layer instanceof L.Marker) {
        map.removeLayer(layer);
      }
    });

    // Draw planned route (blue, dashed)
    if (route?.polyline?.coordinates) {
      const routeCoords = route.polyline.coordinates.map(([lon, lat]) => [lat, lon]);
      L.polyline(routeCoords, {
        color: '#0066cc',
        weight: 3,
        dashArray: '5, 5',
        opacity: 0.7,
      }).addTo(map);

      // Fit map to route
      const group = L.featureGroup(
        [L.polyline(routeCoords, { color: '#0066cc' })]
      );
      map.fitBounds(group.getBounds());
    }

    // Draw actual trail (green, solid)
    if (trail?.polyline?.coordinates) {
      const trailCoords = trail.polyline.coordinates.map(([lon, lat]) => [lat, lon]);
      L.polyline(trailCoords, {
        color: '#00aa00',
        weight: 2,
        opacity: 0.8,
      }).addTo(map);
    }

    // Draw hazards
    hazards.forEach((hazard) => {
      const iconColor = hazard.severity_score > 0.7 ? '#ff0000' : '#ffaa00';
      const icon = L.divIcon({
        html: `<div style="width: 24px; height: 24px; background: ${iconColor}; border-radius: 50%; display: flex; align-items: center; justify-content: center; color: white; font-weight: bold; font-size: 12px;">!</div>`,
        iconSize: [24, 24],
        className: 'hazard-marker',
      });

      L.marker([hazard.location.lat, hazard.location.lon], { icon })
        .bindPopup(
          `<div class="text-sm"><b>${hazard.type.replace(/_/g, ' ')}</b><br/>${hazard.recommendation}</div>`
        )
        .addTo(map);
    });

    // Draw traffic events
    trafficEvents.forEach((event) => {
      const icon = L.divIcon({
        html: `<div style="width: 20px; height: 20px; background: #ff6b35; border-radius: 50%; border: 2px solid #ffaa00;"></div>`,
        iconSize: [20, 20],
        className: 'traffic-marker',
      });

      L.marker([event.location.lat, event.location.lon], { icon })
        .bindPopup(
          `<div class="text-sm"><b>${event.type}</b><br/>Delay: ${event.delay_minutes} min<br/>${event.description}</div>`
        )
        .addTo(map);
    });

    setLoading(false);
  }, [map, mapReady, route, trail, hazards, trafficEvents]);

  return (
    <div className="w-full h-screen bg-slate-900 flex flex-col">
      {/* Header */}
      <div className="bg-slate-800 border-b border-slate-700 p-4 flex justify-between items-center">
        <div>
          <h2 className="text-xl font-bold text-white flex items-center gap-2">
            <Navigation size={24} className="text-blue-400" />
            Route Map - {vehicleId}
          </h2>
          <p className="text-sm text-slate-400">Real-time route tracking with hazards & traffic</p>
        </div>
        {loading && <div className="text-slate-400 text-sm">Loading...</div>}
      </div>

      {/* Map Container */}
      <div
        ref={mapContainer}
        className="flex-1 relative"
        style={{ minHeight: '400px' }}
      />

      {/* Stats Panel */}
      <div className="bg-slate-800 border-t border-slate-700 p-4 grid grid-cols-4 gap-4">
        {route && (
          <>
            <div className="bg-slate-700/50 rounded-lg p-3 border border-slate-600">
              <p className="text-xs text-slate-400 mb-1">Distance</p>
              <p className="text-lg font-bold text-white">{Number.isFinite(route?.distance_km) ? Number(route.distance_km).toFixed(1) : '0.0'} km</p>
            </div>
            <div className="bg-slate-700/50 rounded-lg p-3 border border-slate-600">
              <p className="text-xs text-slate-400 mb-1">Duration</p>
              <p className="text-lg font-bold text-white">
                {Number.isFinite((route?.duration_seconds || 0) / 3600) ? (Number((route.duration_seconds || 0) / 3600)).toFixed(1) : '0.0'} h
              </p>
            </div>
            <div className="bg-slate-700/50 rounded-lg p-3 border border-slate-600">
              <p className="text-xs text-slate-400 mb-1">Fuel</p>
              <p className="text-lg font-bold text-white">{Number.isFinite(route?.fuel_liters) ? Number(route.fuel_liters).toFixed(1) : '0.0'} L</p>
            </div>
            <div className="bg-slate-700/50 rounded-lg p-3 border border-slate-600">
              <p className="text-xs text-slate-400 mb-1">Hazards</p>
              <p className="text-lg font-bold text-yellow-400">{hazards.length}</p>
            </div>
          </>
        )}
      </div>
    </div>
  );
}

function computeBoundingBox(coordinates) {
  const lats = coordinates.map((c) => c[1]);
  const lons = coordinates.map((c) => c[0]);
  return {
    minLat: Math.min(...lats),
    maxLat: Math.max(...lats),
    minLon: Math.min(...lons),
    maxLon: Math.max(...lons),
  };
}

export default RouteMapVisualization;
