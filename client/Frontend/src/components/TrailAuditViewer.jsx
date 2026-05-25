/**
 * TrailAuditViewer Component
 * 
 * Displays the FULL GPS trail of where a truck has been, sourced from
 * the mobile app / phone's location history.
 * 
 * Features:
 * - Interactive Leaflet map with trail polyline
 * - Audit log timeline with activity entries
 * - Trip statistics (distance, avg/max speed, duration)
 * - Per-truck trail selection
 * - Time range filter (7, 14, 30 days)
 */
import { useState, useEffect, useRef } from 'react';
import L from 'leaflet';
import 'leaflet/dist/leaflet.css';
import { fetchTruckTrailAudit, fetchAllTrucksTrailSummary, trailToLeafletCoords, formatTrailStats } from '../services/trailAuditService';
import '../styles/trailStyles.css';

// Fix Leaflet default marker icons
delete L.Icon.Default.prototype._getIconUrl;
L.Icon.Default.mergeOptions({
  iconRetinaUrl: 'https://cdnjs.cloudflare.com/ajax/libs/leaflet/1.9.4/images/marker-icon-2x.png',
  iconUrl: 'https://cdnjs.cloudflare.com/ajax/libs/leaflet/1.9.4/images/marker-icon.png',
  shadowUrl: 'https://cdnjs.cloudflare.com/ajax/libs/leaflet/1.9.4/images/marker-shadow.png',
});

// Trail color palette per truck
const TRAIL_COLORS = [
  '#FF6B6B', '#4ECDC4', '#45B7D1', '#FFA07A', '#98D8C8',
  '#F7DC6F', '#BB8FCE', '#85C1E2', '#F8B195', '#C7CEEA',
];

export default function TrailAuditViewer({ onClose, initialTruckId = null }) {
  const mapRef = useRef(null);
  const mapInstance = useRef(null);
  const trailPolyline = useRef(null);
  const startMarker = useRef(null);
  const endMarker = useRef(null);
  
  const [trucks, setTrucks] = useState([]);
  const [selectedTruckId, setSelectedTruckId] = useState(initialTruckId);
  const [trailData, setTrailData] = useState(null);
  const [loading, setLoading] = useState(false);
  const [loadingTrail, setLoadingTrail] = useState(false);
  const [days, setDays] = useState(7);
  const [error, setError] = useState(null);
  const [showAudit, setShowAudit] = useState(true);

  // Fetch all trucks trail summary on mount
  useEffect(() => {
    loadTrucks();
  }, [days]);

  // Fetch trail data when truck selected
  useEffect(() => {
    if (selectedTruckId) {
      loadTrailData(selectedTruckId);
    }
  }, [selectedTruckId, days]);

  // Initialize map when trail data changes
  useEffect(() => {
    if (!mapRef.current || !trailData) return;
    
    // Initialize map if not already done
    if (!mapInstance.current) {
      mapInstance.current = L.map(mapRef.current).setView([-17.8252, 31.0335], 6);
      L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
        attribution: '© OpenStreetMap',
        maxZoom: 19,
        minZoom: 3,
      }).addTo(mapInstance.current);
    }

    // Clear previous trail
    if (trailPolyline.current) {
      mapInstance.current.removeLayer(trailPolyline.current);
    }
    if (startMarker.current) {
      mapInstance.current.removeLayer(startMarker.current);
    }
    if (endMarker.current) {
      mapInstance.current.removeLayer(endMarker.current);
    }

    const coords = trailToLeafletCoords(trailData.trail);
    if (coords.length < 2) {
      setError('Not enough trail points to draw route');
      return;
    }

    const truckColor = TRAIL_COLORS[trucks.findIndex(t => t.truck_id === selectedTruckId) % TRAIL_COLORS.length] || '#0066cc';

    // Draw main trail polyline
    trailPolyline.current = L.polyline(coords, {
      color: truckColor,
      weight: 3,
      opacity: 0.8,
      lineCap: 'round',
      lineJoin: 'round',
      zIndex: 100,
    }).addTo(mapInstance.current);

    // Add start marker
    const startCoord = coords[0];
    startMarker.current = L.marker(startCoord, {
      icon: L.divIcon({
        html: '<div style="background:#22c55e;width:16px;height:16px;border-radius:50%;border:3px solid white;box-shadow:0 2px 6px rgba(0,0,0,0.3);"></div>',
        className: 'trail-start-marker',
        iconSize: [16, 16],
        iconAnchor: [8, 8],
      }),
    }).addTo(mapInstance.current);
    startMarker.current.bindPopup(`<b>Start</b><br/>${new Date(trailData.trail[0].timestamp).toLocaleString()}`);

    // Add end marker
    const endCoord = coords[coords.length - 1];
    endMarker.current = L.marker(endCoord, {
      icon: L.divIcon({
        html: '<div style="background:#ef4444;width:16px;height:16px;border-radius:50%;border:3px solid white;box-shadow:0 2px 6px rgba(0,0,0,0.3);"></div>',
        className: 'trail-end-marker',
        iconSize: [16, 16],
        iconAnchor: [8, 8],
      }),
    }).addTo(mapInstance.current);
    endMarker.current.bindPopup(`<b>End</b><br/>${new Date(trailData.trail[trailData.trail.length - 1].timestamp).toLocaleString()}`);

    // Fit bounds to show whole trail
    mapInstance.current.fitBounds(trailPolyline.current.getBounds().pad(0.1));

    setError(null);
  }, [trailData, selectedTruckId]);

  const loadTrucks = async () => {
    setLoading(true);
    try {
      const data = await fetchAllTrucksTrailSummary(days);
      setTrucks(data.trucks || []);
    } catch (err) {
      setError('Failed to load trucks');
    } finally {
      setLoading(false);
    }
  };

  const loadTrailData = async (truckId) => {
    setLoadingTrail(true);
    setError(null);
    setTrailData(null);
    try {
      const data = await fetchTruckTrailAudit(truckId, { days, limit: 2000 });
      if (data) {
        setTrailData(data);
      } else {
        setError('No trail data available for this truck in the selected period');
      }
    } catch (err) {
      setError('Failed to load trail data');
    } finally {
      setLoadingTrail(false);
    }
  };

  const formatTimestamp = (ts) => {
    try {
      return new Date(ts).toLocaleString();
    } catch {
      return ts;
    }
  };

  const stats = trailData ? formatTrailStats(trailData.stats) : [];

  return (
    <div className="fixed inset-0 bg-black/60 backdrop-blur-sm z-50 flex items-center justify-center p-4">
      <div className="bg-slate-900 border border-slate-700 rounded-lg shadow-2xl w-full max-w-6xl max-h-[90vh] flex flex-col">
        {/* Header */}
        <div className="flex items-center justify-between px-6 py-4 border-b border-slate-700">
          <h2 className="text-xl font-bold text-white flex items-center gap-2">
            🗺️ Trail & Audit Viewer
          </h2>
          <div className="flex items-center gap-4">
            {/* Time range selector */}
            <div className="flex gap-1 bg-slate-800 rounded-lg p-1">
              {[7, 14, 30].map(d => (
                <button
                  key={d}
                  onClick={() => setDays(d)}
                  className={`px-3 py-1 text-xs font-semibold rounded transition ${
                    days === d
                      ? 'bg-blue-600 text-white'
                      : 'text-slate-400 hover:text-white'
                  }`}
                >
                  {d}d
                </button>
              ))}
            </div>
            <button
              onClick={loadTrucks}
              className="px-3 py-1.5 bg-slate-700 hover:bg-slate-600 text-white text-sm rounded transition"
            >
              🔄 Refresh
            </button>
            {onClose && (
              <button onClick={onClose} className="text-slate-400 hover:text-white text-lg font-bold">
                ✕
              </button>
            )}
          </div>
        </div>

        <div className="flex flex-1 overflow-hidden" style={{ height: 'calc(90vh - 60px)' }}>
          {/* Left Panel - Truck List & Audit Log */}
          <div className="w-80 border-r border-slate-700 flex flex-col">
            {/* Truck Selector */}
            <div className="p-4 border-b border-slate-700">
              <label className="block text-xs font-semibold text-slate-400 mb-2 uppercase tracking-wider">
                Select Truck
              </label>
              <select
                value={selectedTruckId || ''}
                onChange={(e) => setSelectedTruckId(e.target.value)}
                className="w-full bg-slate-800 border border-slate-600 text-white px-3 py-2 rounded text-sm"
              >
                <option value="">-- Select a truck --</option>
                {trucks
                  .filter(t => t.has_trail)
                  .map(truck => (
                    <option key={truck.truck_id} value={truck.truck_id}>
                      {truck.truck_identifier} ({truck.plate}) - {truck.trail_points} pts
                    </option>
                  ))}
              </select>
              {trucks.filter(t => !t.has_trail).length > 0 && (
                <div className="mt-2 text-xs text-slate-500">
                  {trucks.filter(t => !t.has_trail).length} trucks have no trail data
                </div>
              )}
            </div>

            {/* Statistics */}
            {trailData && trailData.stats && (
              <div className="p-4 border-b border-slate-700">
                <h3 className="text-xs font-semibold text-slate-400 uppercase tracking-wider mb-2">
                  📊 Trip Statistics
                </h3>
                <div className="grid grid-cols-2 gap-2">
                  {stats.map((stat, i) => (
                    <div key={i} className="bg-slate-800 p-2 rounded">
                      <div className="text-[10px] text-slate-500">{stat.label}</div>
                      <div className="text-sm font-bold text-slate-200">{stat.value}</div>
                    </div>
                  ))}
                </div>
              </div>
            )}

            {/* Audit Log Toggle */}
            <div className="p-2 border-b border-slate-700 flex items-center justify-between">
              <span className="text-xs font-semibold text-slate-400 uppercase tracking-wider">
                📋 Audit Log
              </span>
              <button
                onClick={() => setShowAudit(!showAudit)}
                className="text-xs text-blue-400 hover:text-blue-300"
              >
                {showAudit ? 'Hide' : 'Show'} ({trailData?.audit_log?.length || 0})
              </button>
            </div>

            {/* Audit Log Entries */}
            {showAudit && trailData && trailData.audit_log && (
              <div className="flex-1 overflow-y-auto p-2 space-y-1">
                {trailData.audit_log.length === 0 ? (
                  <div className="text-center text-slate-500 text-xs py-8">
                    No audit entries recorded yet
                  </div>
                ) : (
                  trailData.audit_log.map((entry) => (
                    <div key={entry.id} className="bg-slate-800/50 p-2 rounded text-xs hover:bg-slate-800 transition">
                      <div className="flex items-center gap-2 mb-1">
                        <span className={`px-1.5 py-0.5 rounded text-[10px] font-semibold ${
                          entry.activity_category === 'trail' ? 'bg-blue-900/50 text-blue-300' :
                          entry.activity_category === 'location' ? 'bg-green-900/50 text-green-300' :
                          entry.activity_category === 'speed' ? 'bg-yellow-900/50 text-yellow-300' :
                          entry.is_critical ? 'bg-red-900/50 text-red-300' :
                          'bg-slate-700 text-slate-300'
                        }`}>
                          {entry.activity_type_display || entry.activity_type}
                        </span>
                        {entry.alert_level && (
                          <span className={`px-1 py-0.5 rounded text-[10px] font-semibold ${
                            entry.alert_level === 'critical' ? 'bg-red-900/50 text-red-300' :
                            entry.alert_level === 'high' ? 'bg-orange-900/50 text-orange-300' :
                            'bg-yellow-900/50 text-yellow-300'
                          }`}>
                            {entry.alert_level}
                          </span>
                        )}
                      </div>
                      {entry.location_name && (
                        <div className="text-slate-400">📍 {entry.location_name}</div>
                      )}
                      <div className="flex justify-between text-slate-500 mt-1">
                        <span>{formatTimestamp(entry.timestamp)}</span>
                        {entry.speed_kmh != null && (
                          <span>{entry.speed_kmh.toFixed(1)} km/h</span>
                        )}
                      </div>
                      {entry.notes && (
                        <div className="text-slate-500 italic mt-1">{entry.notes}</div>
                      )}
                    </div>
                  ))
                )}
              </div>
            )}
          </div>

          {/* Right Panel - Map */}
          <div className="flex-1 relative">
            {/* Loading overlay */}
            {loadingTrail && (
              <div className="absolute inset-0 bg-slate-900/80 flex items-center justify-center z-50">
                <div className="text-center">
                  <div className="text-3xl mb-2">🗺️</div>
                  <div className="text-slate-300 font-semibold">Loading trail data...</div>
                </div>
              </div>
            )}

            {/* Error display */}
            {error && (
              <div className="absolute top-4 left-4 right-4 bg-red-900/80 border border-red-700 text-red-200 px-4 py-3 rounded-lg z-50 text-sm">
                ⚠️ {error}
                <button onClick={() => setError(null)} className="ml-2 text-red-300 hover:text-white">✕</button>
              </div>
            )}

            {/* No truck selected */}
            {!selectedTruckId && !loadingTrail && (
              <div className="absolute inset-0 bg-slate-900/60 flex items-center justify-center z-40">
                <div className="text-center">
                  <div className="text-5xl mb-4">🗺️</div>
                  <h3 className="text-xl font-bold text-white mb-2">Trail & Audit Viewer</h3>
                  <p className="text-slate-400">Select a truck from the left panel to view its trail</p>
                  <p className="text-slate-500 text-sm mt-2">
                    Shows GPS trail of where the mobile app/phone has been
                  </p>
                </div>
              </div>
            )}

            {/* Map Container */}
            <div ref={mapRef} className="w-full h-full" />
          </div>
        </div>
      </div>
    </div>
  );
}