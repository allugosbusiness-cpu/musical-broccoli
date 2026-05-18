/**
 * Road-Matched Trail System Component
 * Handles trail rendering, off-route detection, and automatic rerouting
 */

import React, { useEffect, useRef, useState, useCallback } from 'react';
import L from 'leaflet';
import {
  getRoute,
  detectOffRoute,
  scheduleReroute,
  updateTrailState,
  getTrailState,
} from '../services/roadMatchedTrailService.js';
import {
  colorStore,
  getTrailStyle,
} from '../utils/truckColorUtils.js';
import {
  detectOverlap,
  renderTrailPolyline,
} from '../utils/trailOverlapRenderer.js';
import { driverEventTracker } from '../services/driverEventTracker.js';
import { alertManager } from '../services/alertManager.js';
import { createAlert } from '../services/api.js';
import '../styles/trailStyles.css';

export default function RoadMatchedTrailSystem({ mapInstance, trucks = [] }) {
  const [enableRawTraces, setEnableRawTraces] = useState(false);
  const [colorblindMode, setColorblindMode] = useState(null);
  const [highContrastMode, setHighContrastMode] = useState(false);
  const [showToast, setShowToast] = useState(null);
  const [reroutes, setReroutes] = useState({});

  const trailLayersRef = useRef({});
  const markerLayersRef = useRef({});
  const offRouteStateRef = useRef({});
  const rerouteInProgressRef = useRef({});
  const lastAlertTimeRef = useRef({}); // Track last alert creation time per truck

  // Cleanup on unmount
  useEffect(() => {
    return () => {
      Object.values(trailLayersRef.current).forEach((layer) => {
        if (layer && layer.polyline) {
          try {
            mapInstance.removeLayer(layer.polyline);
          } catch (e) {}
        }
      });
      Object.values(markerLayersRef.current).forEach((marker) => {
        if (marker) {
          try {
            mapInstance.removeLayer(marker);
          } catch (e) {}
        }
      });
    };
  }, [mapInstance]);

  /**
   * Render a truck's trail on the map
   */
  const renderTruckTrail = useCallback(
    async (truck) => {
      if (!mapInstance || !truck || !truck.coordinates) return;

      try {
        const truckId = truck.id;
        const currentCoords = truck.coordinates;
        const originCoords = truck.origin_coordinates;
        const destCoords = truck.destination_coordinates;

        // Skip if missing required coordinates
        if (!originCoords || !destCoords) {
          console.warn(`⚠️ Missing coordinates for ${truckId}`);
          return;
        }

        // Get route from OSRM
        const routeData = await getRoute(
          originCoords,
          currentCoords,
          destCoords
        );

        if (!routeData || !routeData.geometry) {
          console.error(`❌ No route data for ${truckId}`);
          return;
        }

        // Decode polyline geometry
        const geometry = routeData.geometry || [];

        // Detect if truck is off-route
        const offRouteCheck = detectOffRoute(geometry, currentCoords.lat, currentCoords.lng);

        // Remove old trail
        if (trailLayersRef.current[truckId]?.polyline) {
          mapInstance.removeLayer(trailLayersRef.current[truckId].polyline);
        }

        // Draw new trail
        const trailColor = truck.route_color || '#3b82f6';
        const trailStyle = getTrailStyle(truckId, {
          primary: trailColor,
          highContrast: highContrastMode,
        });

        const polylineCoords = geometry.map((p) => [p.lat, p.lng]);
        const polyline = L.polyline(polylineCoords, {
          color: trailColor,
          weight: 3,
          opacity: 0.8,
          dashArray: offRouteCheck.isOffRoute ? '5, 5' : null,
          className: 'trail-polyline',
          zIndex: 100,
        }).addTo(mapInstance);

        trailLayersRef.current[truckId] = {
          polyline,
          geometry,
          offRoute: offRouteCheck.isOffRoute,
        };

        // Update trail state
        updateTrailState(truckId, {
          route: routeData,
          trailLayers: { polyline },
          offRoute: offRouteCheck.isOffRoute,
        });

        // Handle off-route detection with deduplication
        if (offRouteCheck.isOffRoute) {
          // Check if this is a new off-route detection (state change)
          if (!offRouteStateRef.current[truckId]) {
            offRouteStateRef.current[truckId] = true;

            console.warn(`⚠️ ${truckId} is OFF ROUTE!`, offRouteCheck);

            const alertData = {
              truckId: truckId,
              truck: truck,
              location: truck.location,
              coordinates: currentCoords,
              deviationDistance: offRouteCheck.distanceOffRoute,
              timestamp: new Date(),
            };

            // Only emit if not recently emitted for this truck
            if (alertManager.emitIfNew(truckId, 'off-route-detected', alertData)) {
              // Track alert in manager
              alertManager.setActive(truckId, 'off-route', alertData);
              
              // Check if we've created an alert recently (within 30 seconds) for this truck
              const now = Date.now();
              const lastAlertTime = lastAlertTimeRef.current[truckId] || 0;
              const timeSinceLastAlert = now - lastAlertTime;
              
              if (timeSinceLastAlert >= 30000) { // 30 second cooldown between alerts
                lastAlertTimeRef.current[truckId] = now;
                
                // Persist to backend
                createAlert(
                  truckId,
                  'critical',
                  `Off-route detected: ${Number.isFinite(offRouteCheck?.distanceOffRoute) ? Number(offRouteCheck.distanceOffRoute).toFixed(0) : '0'}m deviation`
                ).catch(e => console.error('Failed to create alert:', e));
              }
            }

            // Schedule automatic reroute
            if (!rerouteInProgressRef.current[truckId]) {
              rerouteInProgressRef.current[truckId] = true;

              scheduleReroute(
                truckId,
                originCoords,
                currentCoords,
                destCoords,
                (newRoute) => {
                  console.log(`✅ Reroute triggered for ${truckId}`, newRoute);
                  setReroutes((prev) => ({
                    ...prev,
                    [truckId]: newRoute,
                  }));

                  // Update backend with new route
                  fetch(`http://localhost:8000/api/trucks/${truckId}/`, {
                    method: 'PATCH',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({
                      route_geojson: newRoute.geometry,
                      route_color: truck.route_color,
                    }),
                  }).catch((e) => console.error('Failed to update route:', e));

                  rerouteInProgressRef.current[truckId] = false;
                },
                5000 // 5s debounce
              );
            }
          }
        } else {
          // Back on route - clear the alert
          if (offRouteStateRef.current[truckId]) {
            offRouteStateRef.current[truckId] = false;

            console.log(`✅ ${truckId} back on route`);
            
            // Clear alert from manager
            alertManager.clearAlert(truckId, 'off-route');
            
            // Emit back-on-route event (no need for condition)
            driverEventTracker.emitEvent('back-on-route', {
              truckId: truckId,
              truck: truck,
              location: truck.location,
              coordinates: currentCoords,
              timestamp: new Date(),
            });
          }
        }
        
        // Periodic cleanup to prevent memory issues
        if (Math.random() < 0.1) { // 10% chance on each update
          alertManager.cleanup();
        }

        console.log(`✅ Trail rendered for ${truckId}`, {
          distanceKm: (Number.isFinite(routeData?.distance) ? Number(routeData.distance / 1000).toFixed(2) : '0.00'),
          offRoute: offRouteCheck.isOffRoute,
        });
      } catch (error) {
        console.error(`❌ Error rendering trail:`, error);
      }
    },
    [mapInstance, highContrastMode]
  );

  /**
   * Main effect: Render trails for all trucks
   */
  useEffect(() => {
    if (!mapInstance || !trucks.length) return;

    console.log('🗺️ Rendering trails for', trucks.length, 'trucks');

    trucks.forEach((truck) => {
      renderTruckTrail(truck);
    });
  }, [mapInstance, trucks, renderTruckTrail]);

  /**
   * Render origin and destination markers
   */
  useEffect(() => {
    if (!mapInstance || !trucks.length) return;

    trucks.forEach((truck) => {
      if (!truck.origin_coordinates || !truck.destination_coordinates) return;

      const truckId = truck.id;
      const truckColor = truck.route_color || '#3b82f6';

      // Remove old markers
      if (markerLayersRef.current[`${truckId}-origin`]) {
        mapInstance.removeLayer(markerLayersRef.current[`${truckId}-origin`]);
      }
      if (markerLayersRef.current[`${truckId}-destination`]) {
        mapInstance.removeLayer(markerLayersRef.current[`${truckId}-destination`]);
      }

      // Origin marker (green circle with "A")
      const originMarker = L.circleMarker(
        [truck.origin_coordinates.lat, truck.origin_coordinates.lng],
        {
          radius: 8,
          fillColor: '#10b981',
          color: '#059669',
          weight: 2,
          opacity: 1,
          fillOpacity: 0.8,
        }
      )
        .bindPopup(`<strong>${truckId}</strong><br/>Origin: ${truck.origin || 'Start'}`)
        .addTo(mapInstance);

      markerLayersRef.current[`${truckId}-origin`] = originMarker;

      // Destination marker (red circle with "B")
      const destMarker = L.circleMarker(
        [truck.destination_coordinates.lat, truck.destination_coordinates.lng],
        {
          radius: 8,
          fillColor: '#ef4444',
          color: '#dc2626',
          weight: 2,
          opacity: 1,
          fillOpacity: 0.8,
        }
      )
        .bindPopup(`<strong>${truckId}</strong><br/>Destination: ${truck.destination || 'End'}`)
        .addTo(mapInstance);

      markerLayersRef.current[`${truckId}-destination`] = destMarker;
    });
  }, [mapInstance, trucks]);

  return (
    <div className="trail-system-container">
      {/* Controls Panel */}
      <div className="trail-controls">
        <div className="trail-control-group">
          <input
            type="checkbox"
            id="raw-traces-toggle"
            checked={enableRawTraces}
            onChange={(e) => setEnableRawTraces(e.target.checked)}
          />
          <label htmlFor="raw-traces-toggle" className="trail-control-label">
            Show Raw GPS
          </label>
        </div>

        <div className="trail-control-group">
          <input
            type="checkbox"
            id="high-contrast-toggle"
            checked={highContrastMode}
            onChange={(e) => setHighContrastMode(e.target.checked)}
          />
          <label htmlFor="high-contrast-toggle" className="trail-control-label">
            High Contrast
          </label>
        </div>

        <div className="trail-control-group">
          <select
            value={colorblindMode || ''}
            onChange={(e) => setColorblindMode(e.target.value || null)}
            className="trail-control-select"
          >
            <option value="">Normal Colors</option>
            <option value="deuteranopia">Deuteranopia</option>
            <option value="protanopia">Protanopia</option>
            <option value="tritanopia">Tritanopia</option>
          </select>
        </div>
      </div>

      {/* Toast Notification */}
      {showToast && (
        <div className="trail-toast">
          {showToast}
        </div>
      )}
    </div>
  );
}
