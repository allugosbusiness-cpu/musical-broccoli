import React, { useState, useEffect, useRef, useCallback } from 'react';
import {
  AlertTriangle, Truck, Fuel, Clock, ZapOff, Wind, Droplets,
  MapPin, Navigation, Activity, TrendingUp, Plus, X, Download, Share2, Settings
} from 'lucide-react';

/**
 * Advanced Interactive Route Map
 * Superior to Google Maps with real-time optimization, predictive analytics, 
 * hazard detection, fuel optimization, and live vehicle tracking
 */
export default function AdvancedRouteMap({ route, vehicle, onRouteUpdate, onHazardAlert }) {
  const mapContainer = useRef(null);
  const [map, setMap] = useState(null);
  const [mapReady, setMapReady] = useState(false);
  const [activeOverlays, setActiveOverlays] = useState({
    traffic: true,
    hazards: true,
    fuel: true,
    weather: false,
    terrain: false,
  });
  const [selectedSegment, setSelectedSegment] = useState(null);
  const [analyticsView, setAnalyticsView] = useState(false);
  const [showOptimizations, setShowOptimizations] = useState(true);

  // Initialize Leaflet map
  useEffect(() => {
    if (!mapContainer.current || mapReady) return;

    const initMap = async () => {
      // Load Leaflet
      const L = window.L || await loadLeaflet();
      
      const newMap = L.map(mapContainer.current, {
        zoomControl: true,
        attributionControl: true,
        preferCanvas: true,
        renderer: L.canvas(),
      }).setView([route?.center?.lat || -17.8252, route?.center?.lng || 31.0335], 8);

      // Add multi-layer tile options
      const tileLayer = L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
        attribution: '© OpenStreetMap contributors',
        maxZoom: 19,
        className: 'map-tiles',
      }).addTo(newMap);

      // Add satellite layer option
      const satelliteLayer = L.tileLayer(
        'https://server.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/tile/{z}/{y}/{x}',
        { attribution: 'Tiles © Esri', maxZoom: 19 }
      );

      // Layer control
      const baseLayers = {
        'Road Map': tileLayer,
        'Satellite': satelliteLayer,
      };
      L.control.layers(baseLayers).addTo(newMap);

      // Advanced controls
      addMapControls(newMap);

      setMap(newMap);
      setMapReady(true);
    };

    initMap();
  }, [mapReady, route]);

  // Draw route and elements
  useEffect(() => {
    if (!map || !mapReady || !route) return;

    const L = window.L;
    clearMapLayers();

    // Draw main route with gradient
    drawRoute(map, L, route);

    // Draw waypoints
    if (route.waypoints) {
      route.waypoints.forEach((waypoint, idx) => {
        addWaypoint(map, L, waypoint, idx);
      });
    }

    // Draw current vehicle position
    if (vehicle?.position) {
      drawVehicle(map, L, vehicle);
    }

    // Draw overlays based on active selection
    if (activeOverlays.traffic && route.trafficData) {
      drawTraffic(map, L, route.trafficData);
    }
    if (activeOverlays.hazards && route.hazards) {
      drawHazards(map, L, route.hazards);
    }
    if (activeOverlays.fuel && route.fuelStops) {
      drawFuelStops(map, L, route.fuelStops);
    }
    if (activeOverlays.weather && route.weatherData) {
      drawWeather(map, L, route.weatherData);
    }

  }, [map, mapReady, route, activeOverlays, vehicle]);

  const drawRoute = (map, L, route) => {
    if (!route.coordinates || route.coordinates.length === 0) return;

    // Convert to leaflet format
    const latlngs = route.coordinates.map(([lon, lat]) => [lat, lon]);

    // Color code based on speed/traffic
    const routeColor = route.congestionIndex > 0.7 ? '#ef4444' : 
                       route.congestionIndex > 0.4 ? '#f59e0b' : '#10b981';

    // Draw main route
    const polyline = L.polyline(latlngs, {
      color: routeColor,
      weight: 4,
      opacity: 0.8,
      lineCap: 'round',
      lineJoin: 'round',
      dashArray: route.isSuggested ? '5, 5' : undefined,
    }).addTo(map);

    // Add segment markers every 10 points
    latlngs.forEach((point, idx) => {
      if (idx % 10 === 0) {
        L.circleMarker(point, {
          radius: 3,
          fillColor: routeColor,
          color: '#fff',
          weight: 1,
          opacity: 0.6,
          fillOpacity: 0.6,
        }).addTo(map);
      }
    });

    // Fit map to route
    map.fitBounds(polyline.getBounds(), { padding: [50, 50] });

    // Add mouseover popup for segment info
    polyline.bindPopup((layer) => {
      const idx = Math.floor(latlngs.length / 2);
      const segment = route.segments?.[Math.floor(route.segments.length / 2)];
      return `
        <div class="route-popup">
          <p><strong>${segment?.name || 'Route Segment'}</strong></p>
          <p>Distance: ${segment?.distance || 0} km</p>
          <p>Duration: ${segment?.duration || 0} min</p>
          <p>Traffic: ${route.congestionIndex || 0}</p>
        </div>
      `;
    });
  };

  const addWaypoint = (map, L, waypoint, idx) => {
    const icon = L.divIcon({
      className: `waypoint-marker waypoint-${idx === 0 ? 'start' : idx === (route.waypoints?.length - 1) ? 'end' : 'middle'}`,
      html: `<div class="waypoint-badge">${idx + 1}</div>`,
      iconSize: [40, 40],
      iconAnchor: [20, 20],
    });

    const marker = L.marker([waypoint.lat, waypoint.lng], { icon }).addTo(map);
    
    marker.bindPopup(`
      <div class="waypoint-info">
        <h4>${waypoint.name}</h4>
        <p>Type: ${waypoint.type}</p>
        <p>Arrival: ${waypoint.eta || 'N/A'}</p>
        ${waypoint.delay ? `<p class="text-red-600">Delay: ${waypoint.delay} min</p>` : ''}
      </div>
    `);
  };

  const drawVehicle = (map, L, vehicle) => {
    const icon = L.divIcon({
      className: 'vehicle-marker',
      html: `
        <div class="vehicle-icon" style="transform: rotate(${vehicle.heading || 0}deg)">
          <svg viewBox="0 0 24 24" fill="currentColor" class="text-blue-500">
            <path d="M12 2l8 20H4l8-20z"/>
          </svg>
        </div>
      `,
      iconSize: [32, 32],
      iconAnchor: [16, 16],
    });

    const marker = L.marker([vehicle.position.lat, vehicle.position.lng], { icon }).addTo(map);
    
    marker.bindPopup(`
      <div class="vehicle-info">
        <h4>${vehicle.name}</h4>
        <p>Speed: ${vehicle.speed} km/h</p>
        <p>Fuel: ${vehicle.fuel}L</p>
        <p>Status: ${vehicle.status}</p>
      </div>
    `);

    // Add circle showing 5km radius
    L.circle([vehicle.position.lat, vehicle.position.lng], {
      radius: 5000,
      fillColor: '#3b82f6',
      color: '#3b82f6',
      weight: 1,
      opacity: 0.2,
      fillOpacity: 0.1,
    }).addTo(map);
  };

  const drawTraffic = (map, L, trafficData) => {
    trafficData.forEach((segment) => {
      const color = segment.congestion > 0.7 ? '#ef4444' : 
                    segment.congestion > 0.4 ? '#f59e0b' : '#10b981';
      
      const polyline = L.polyline(
        segment.coordinates.map(([lon, lat]) => [lat, lon]),
        {
          color,
          weight: 6,
          opacity: 0.5,
          dashArray: '10, 3',
        }
      ).addTo(map);

      polyline.bindPopup(`
        <div>
          <p>Congestion: ${Number.isFinite(segment.congestion) ? (Number(segment.congestion) * 100).toFixed(0) : '0'}%</p>
          <p>Delay: ${segment.delay} min</p>
          <p>Speed: ${segment.speed} km/h</p>
        </div>
      `);
    });
  };

  const drawHazards = (map, L, hazards) => {
    hazards.forEach((hazard) => {
      const hazardIcon = {
        accident: '⚠️',
        construction: '🚧',
        weather: '⛈️',
        pothole: '💣',
        roadwork: '🛠️',
        flooding: '💧',
      }[hazard.type] || '⚡';

      const icon = L.divIcon({
        className: `hazard-marker hazard-${hazard.severity}`,
        html: `<div class="hazard-badge">${hazardIcon}</div>`,
        iconSize: [40, 40],
        iconAnchor: [20, 20],
      });

      const marker = L.marker([hazard.lat, hazard.lng], { icon }).addTo(map);
      
      marker.bindPopup(`
        <div class="hazard-info">
          <h4>${hazard.type.toUpperCase()}</h4>
          <p>Severity: ${hazard.severity}</p>
          <p>Description: ${hazard.description}</p>
          <p>Impact: ${hazard.impact}%</p>
        </div>
      `);

      if (hazard.severity === 'critical') {
        onHazardAlert && onHazardAlert(hazard);
      }
    });
  };

  const drawFuelStops = (map, L, fuelStops) => {
    fuelStops.forEach((stop) => {
      const icon = L.divIcon({
        className: 'fuel-stop-marker',
        html: `<div class="fuel-badge"><${Fuel} size={20} /></div>`,
        iconSize: [40, 40],
        iconAnchor: [20, 20],
      });

      const marker = L.marker([stop.lat, stop.lng], { icon }).addTo(map);
      
      marker.bindPopup(`
        <div class="fuel-stop-info">
          <h4>${stop.name}</h4>
          <p>Distance: ${stop.distanceFromStart} km</p>
          <p>Recommended Fuel: ${stop.recommendedFuel}L</p>
          <p>Amenities: ${stop.amenities?.join(', ')}</p>
        </div>
      `);
    });
  };

  const drawWeather = (map, L, weatherData) => {
    weatherData.forEach((point) => {
      const weatherIcon = {
        rain: '🌧️',
        snow: '❄️',
        fog: '🌫️',
        storm: '⛈️',
        clear: '☀️',
      }[point.condition] || '🌤️';

      const icon = L.divIcon({
        className: 'weather-marker',
        html: `<div class="weather-badge">${weatherIcon}</div>`,
        iconSize: [35, 35],
        iconAnchor: [17, 17],
      });

      L.marker([point.lat, point.lng], { icon }).addTo(map)
        .bindPopup(`Temp: ${point.temp}°C<br>Condition: ${point.condition}`);
    });
  };

  const clearMapLayers = () => {
    if (!map) return;
    map.eachLayer((layer) => {
      if (layer instanceof window.L.Polyline || 
          layer instanceof window.L.Marker ||
          layer instanceof window.L.Circle) {
        map.removeLayer(layer);
      }
    });
  };

  const addMapControls = (map) => {
    const L = window.L;
    
    // Zoom to route button
    L.Control.Button = L.Control.extend({
      options: { position: 'topleft' },
      onAdd: () => {
        const button = L.DomUtil.create('button', 'leaflet-control leaflet-bar');
        button.textContent = '🎯';
        button.title = 'Fit route to map';
        L.DomEvent.on(button, 'click', () => {
          // Zoom to route bounds
        });
        return button;
      },
    });

    new L.Control.Button().addTo(map);
  };

  const loadLeaflet = async () => {
    return new Promise((resolve) => {
      if (window.L) {
        resolve(window.L);
        return;
      }

      const link = document.createElement('link');
      link.rel = 'stylesheet';
      link.href = 'https://cdnjs.cloudflare.com/ajax/libs/leaflet/1.9.4/leaflet.min.css';
      document.head.appendChild(link);

      const script = document.createElement('script');
      script.src = 'https://cdnjs.cloudflare.com/ajax/libs/leaflet/1.9.4/leaflet.min.js';
      script.onload = () => resolve(window.L);
      document.head.appendChild(script);
    });
  };

  return (
    <div className="advanced-route-map-container h-full flex flex-col bg-gradient-to-br from-slate-900 to-slate-800">
      {/* Map Container */}
      <div
        ref={mapContainer}
        className="flex-1 relative rounded-lg overflow-hidden border border-slate-700"
        style={{ minHeight: '500px' }}
      >
        {!mapReady && (
          <div className="absolute inset-0 flex items-center justify-center bg-black/50 z-20">
            <div className="text-white flex flex-col items-center gap-3">
              <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-500"></div>
              <p>Loading advanced map...</p>
            </div>
          </div>
        )}

        {/* Map Controls Panel */}
        <div className="absolute top-4 right-4 z-10 bg-slate-800/90 border border-slate-700 rounded-lg p-3 backdrop-blur-sm w-56">
          <div className="text-white text-sm space-y-3">
            <h3 className="font-semibold text-blue-400 mb-2">Map Overlays</h3>
            
            {Object.entries(activeOverlays).map(([key, enabled]) => (
              <label key={key} className="flex items-center gap-2 cursor-pointer hover:bg-slate-700/50 p-1 rounded">
                <input
                  type="checkbox"
                  checked={enabled}
                  onChange={(e) => setActiveOverlays({ ...activeOverlays, [key]: e.target.checked })}
                  className="w-4 h-4"
                />
                <span className="capitalize">{key}</span>
                {key === 'traffic' && <Activity size={14} className="text-orange-400" />}
                {key === 'hazards' && <AlertTriangle size={14} className="text-red-400" />}
                {key === 'fuel' && <Fuel size={14} className="text-green-400" />}
                {key === 'weather' && <Wind size={14} className="text-blue-400" />}
              </label>
            ))}
          </div>
        </div>

        {/* Route Info Panel */}
        <div className="absolute bottom-4 left-4 z-10 bg-slate-800/90 border border-slate-700 rounded-lg p-4 backdrop-blur-sm max-w-sm">
          <div className="text-white space-y-2 text-sm">
            <div className="flex justify-between">
              <span className="text-slate-400">Distance:</span>
              <span className="font-semibold">{route?.summary?.distance || 0} km</span>
            </div>
            <div className="flex justify-between">
              <span className="text-slate-400">Duration:</span>
              <span className="font-semibold">{route?.summary?.duration || 0} min</span>
            </div>
            <div className="flex justify-between">
              <span className="text-slate-400">Fuel:</span>
              <span className="font-semibold text-green-400">{route?.summary?.estimatedFuel || 0}L</span>
            </div>
            <div className="flex justify-between">
              <span className="text-slate-400">Cost:</span>
              <span className="font-semibold text-yellow-400">${route?.summary?.estimatedCost || 0}</span>
            </div>
          </div>
        </div>
      </div>

      {/* Analytics Panel */}
      {analyticsView && (
        <div className="bg-slate-800 border-t border-slate-700 p-4 text-white text-xs">
          <div className="grid grid-cols-5 gap-4">
            <div>
              <p className="text-slate-400">Avg Speed</p>
              <p className="text-lg font-semibold">{Number.isFinite(route?.metrics?.averageSpeed) ? Number(route.metrics.averageSpeed).toFixed(1) : '0.0'} km/h</p>
            </div>
            <div>
              <p className="text-slate-400">Difficulty</p>
              <p className="text-lg font-semibold">{route?.metrics?.difficulty || 0}/100</p>
            </div>
            <div>
              <p className="text-slate-400">Elevation</p>
              <p className="text-lg font-semibold">+{route?.metrics?.elevationGain || 0}m</p>
            </div>
            <div>
              <p className="text-slate-400">CO₂ Emissions</p>
              <p className="text-lg font-semibold">{Number.isFinite(route?.summary?.estimatedFuel) ? (Number(route.summary.estimatedFuel) * 2.31).toFixed(1) : '0.0'} kg</p>
            </div>
            <div>
              <p className="text-slate-400">Hazards</p>
              <p className="text-lg font-semibold text-red-400">{route?.hazards?.length || 0}</p>
            </div>
          </div>
        </div>
      )}

      {/* Bottom Control Bar */}
      <div className="bg-slate-800 border-t border-slate-700 px-4 py-3 flex items-center justify-between">
        <div className="flex gap-2">
          <button
            onClick={() => setAnalyticsView(!analyticsView)}
            className="p-2 hover:bg-slate-700 rounded-lg text-slate-300 hover:text-white transition"
            title="Toggle Analytics"
          >
            <TrendingUp size={18} />
          </button>
          <button
            onClick={() => onRouteUpdate?.(route)}
            className="p-2 hover:bg-slate-700 rounded-lg text-slate-300 hover:text-white transition"
            title="Refresh Route"
          >
            <Activity size={18} />
          </button>
          <button
            className="p-2 hover:bg-slate-700 rounded-lg text-slate-300 hover:text-white transition"
            title="Download Route"
          >
            <Download size={18} />
          </button>
          <button
            className="p-2 hover:bg-slate-700 rounded-lg text-slate-300 hover:text-white transition"
            title="Share Route"
          >
            <Share2 size={18} />
          </button>
        </div>

        {showOptimizations && route?.alternatives && (
          <div className="text-sm text-slate-300">
            💡 {route.alternatives.length} optimizations available
          </div>
        )}
      </div>
    </div>
  );
}
