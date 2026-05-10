import React, { useState, useEffect, useRef } from 'react';
import {
  MapPin, Plus, Trash2, Navigation, Zap, TrendingUp, AlertTriangle,
  Clock, Fuel, DollarSign, ChevronDown, ChevronUp, Filter, Settings,
  Share2, Download, RotateCcw, BarChart3, Layers, Sparkles
} from 'lucide-react';
import routeOptimizer from '../services/routeOptimizer';
import AdvancedRouteMap from './AdvancedRouteMap';
import { GLOBAL_LOCATIONS } from '../data/locations';

/**
 * Enhanced Route Planner v2
 * Superior features: Multi-waypoint, real-time optimization, predictive analytics, fuel management
 */
export default function EnhancedRoutePlanner() {
  // State Management
  const [waypoints, setWaypoints] = useState([
    { id: 1, name: 'Harare', lat: -17.8252, lng: 31.0335, type: 'pickup' },
    { id: 2, name: 'Mutare', lat: -18.9663, lng: 32.6678, type: 'delivery' },
  ]);
  const [vehicleProfile, setVehicleProfile] = useState({
    id: 'TRUCK-001',
    name: 'Volvo FH16',
    fuelConsumption: 8, // km/L
    fuelTankCapacity: 250, // L
    maxSpeed: 120, // km/h
    weight: 5000, // kg
    type: 'truck',
  });
  const [routeProfile, setRouteProfile] = useState('balanced'); // balanced, fastest, fuel_optimal, safest
  const [currentRoute, setCurrentRoute] = useState(null);
  const [alternativeRoutes, setAlternativeRoutes] = useState([]);
  const [loading, setLoading] = useState(false);
  const [expandedSections, setExpandedSections] = useState({
    waypoints: true,
    options: true,
    alternatives: false,
    analytics: false,
  });
  const [optimizations, setOptimizations] = useState([]);
  const [liveOptimization, setLiveOptimization] = useState(null);
  const [showAdvancedOptions, setShowAdvancedOptions] = useState(false);

  const locationOptions = Object.keys(GLOBAL_LOCATIONS);
  const waypointIdRef = useRef(Math.max(...waypoints.map(w => w.id), 0) + 1);

  // Calculate route on waypoint change
  useEffect(() => {
    if (waypoints.length >= 2) {
      calculateRoute();
    }
  }, [waypoints, vehicleProfile.id, routeProfile]);

  /**
   * Calculate optimized route with all waypoints
   */
  const calculateRoute = async () => {
    if (waypoints.length < 2) return;

    setLoading(true);
    try {
      const origin = waypoints[0];
      const destination = waypoints[waypoints.length - 1];
      const intermediateWaypoints = waypoints.slice(1, -1);

      const route = await routeOptimizer.calculateOptimizedRoute(
        { lat: origin.lat, lng: origin.lng },
        { lat: destination.lat, lng: destination.lng },
        intermediateWaypoints.map(w => ({ lat: w.lat, lng: w.lng, name: w.name })),
        {
          profile: routeProfile,
          vehicleId: vehicleProfile.id,
          fuelTankCapacity: vehicleProfile.fuelTankCapacity,
        }
      );

      setCurrentRoute(route);

      // Get alternatives
      const alternatives = await routeOptimizer.getAlternativeRoutes(
        { lat: origin.lat, lng: origin.lng },
        { lat: destination.lat, lng: destination.lng },
        { count: 3, compareBy: ['duration', 'distance', 'fuel'] }
      );
      setAlternativeRoutes(alternatives);

      // Check for hazards
      const hazards = await routeOptimizer.detectHazards(route);
      if (hazards.severityLevel === 'critical') {
        // Suggest reroute
        suggestOptimization('hazard_detection', hazards);
      }

      // Get fuel stops
      const fuelStops = await routeOptimizer.findOptimalStops(route, vehicleProfile);
      setCurrentRoute(prev => ({ ...prev, fuelStops: fuelStops.fuelStops }));

    } catch (error) {
      console.error('Error calculating route:', error);
    } finally {
      setLoading(false);
    }
  };

  /**
   * Suggest optimizations
   */
  const suggestOptimization = (type, data) => {
    const optimization = {
      id: Date.now(),
      type, // 'hazard_detection', 'traffic_prediction', 'fuel_optimization'
      severity: data.severityLevel || 'medium',
      message: data.recommendations?.[0] || 'Optimization available',
      savings: data.savings,
      action: () => applyOptimization(type, data),
    };
    setOptimizations(prev => [...prev, optimization]);
  };

  /**
   * Apply optimization
   */
  const applyOptimization = async (type, data) => {
    if (type === 'hazard_detection' && data.newRoute) {
      setCurrentRoute(data.newRoute);
      setOptimizations(prev => prev.filter(o => o.type !== type));
    }
  };

  /**
   * Add waypoint
   */
  const addWaypoint = () => {
    const newWaypoint = {
      id: waypointIdRef.current++,
      name: '',
      lat: -17.8252,
      lng: 31.0335,
      type: 'stop',
    };
    setWaypoints([...waypoints.slice(0, -1), newWaypoint, waypoints[waypoints.length - 1]]);
  };

  /**
   * Remove waypoint
   */
  const removeWaypoint = (id) => {
    if (waypoints.length <= 2) return;
    setWaypoints(waypoints.filter(w => w.id !== id));
  };

  /**
   * Update waypoint
   */
  const updateWaypoint = (id, field, value) => {
    setWaypoints(waypoints.map(w => 
      w.id === id ? { ...w, [field]: value } : w
    ));
  };

  /**
   * Set waypoint from location search
   */
  const setWaypointFromLocation = (id, locationName) => {
    const loc = GLOBAL_LOCATIONS[locationName];
    if (loc) {
      updateWaypoint(id, 'name', locationName);
      updateWaypoint(id, 'lat', loc.lat);
      updateWaypoint(id, 'lng', loc.lng);
    }
  };

  /**
   * Swap waypoints
   */
  const swapWaypoints = () => {
    setWaypoints([...waypoints].reverse());
  };

  /**
   * Optimize route order (TSP)
   */
  const optimizeWaypointOrder = async () => {
    try {
      setLoading(true);
      // API call to optimize waypoint order
      // For now, just recalculate
      await calculateRoute();
    } finally {
      setLoading(false);
    }
  };

  /**
   * Export route
   */
  const exportRoute = (format = 'json') => {
    const data = {
      waypoints,
      route: currentRoute,
      vehicle: vehicleProfile,
      timestamp: new Date().toISOString(),
    };

    const element = document.createElement('a');
    element.setAttribute('href', 'data:text/plain;charset=utf-8,' + encodeURIComponent(JSON.stringify(data, null, 2)));
    element.setAttribute('download', `route-${Date.now()}.${format}`);
    element.style.display = 'none';
    document.body.appendChild(element);
    element.click();
    document.body.removeChild(element);
  };

  /**
   * Share route
   */
  const shareRoute = async () => {
    if (navigator.share) {
      try {
        await navigator.share({
          title: 'Route Plan',
          text: `Route from ${waypoints[0].name} to ${waypoints[waypoints.length - 1].name}`,
          url: window.location.href,
        });
      } catch (err) {
        console.error('Error sharing:', err);
      }
    } else {
      // Fallback: copy to clipboard
      const shareText = `Route: ${waypoints.map(w => w.name).join(' → ')} (${currentRoute?.summary?.distance}km, ${currentRoute?.summary?.duration}min)`;
      navigator.clipboard.writeText(shareText);
      alert('Route info copied to clipboard!');
    }
  };

  const toggleSection = (section) => {
    setExpandedSections(prev => ({ ...prev, [section]: !prev[section] }));
  };

  return (
    <div className="enhanced-route-planner min-h-screen bg-gradient-to-br from-slate-900 via-slate-800 to-slate-900 p-6">
      <div className="max-w-7xl mx-auto">
        {/* Header */}
        <div className="mb-6">
          <h1 className="text-4xl font-bold text-white flex items-center gap-3 mb-2">
            <Navigation className="text-blue-400" size={36} />
            Advanced Route Planner
          </h1>
          <p className="text-slate-400">
            Multi-waypoint optimization with real-time traffic, fuel management, and predictive analytics
          </p>
        </div>

        <div className="grid grid-cols-1 lg:grid-cols-4 gap-6">
          {/* Left Sidebar - Controls */}
          <div className="lg:col-span-1 space-y-4">
            {/* Optimization Alerts */}
            {optimizations.length > 0 && (
              <div className="bg-red-900/20 border border-red-600 rounded-lg p-4">
                <p className="text-red-400 text-sm font-semibold mb-2">⚠️ {optimizations.length} optimization(s)</p>
                {optimizations.map(opt => (
                  <div key={opt.id} className="text-xs text-red-300 mb-2">
                    <p>{opt.message}</p>
                    {opt.savings && <p className="text-green-400">💾 Save {opt.savings.timeSaved}min</p>}
                    <button
                      onClick={opt.action}
                      className="mt-1 bg-red-600 hover:bg-red-700 px-2 py-1 rounded text-xs transition"
                    >
                      Apply
                    </button>
                  </div>
                ))}
              </div>
            )}

            {/* Waypoints Section */}
            <div className="bg-slate-800 rounded-lg border border-slate-700">
              <button
                onClick={() => toggleSection('waypoints')}
                className="w-full px-4 py-3 flex items-center justify-between hover:bg-slate-700/50 transition"
              >
                <span className="text-white font-semibold flex items-center gap-2">
                  <MapPin size={18} /> Waypoints
                </span>
                {expandedSections.waypoints ? <ChevronUp size={18} /> : <ChevronDown size={18} />}
              </button>

              {expandedSections.waypoints && (
                <div className="px-4 py-3 space-y-2 border-t border-slate-700">
                  {waypoints.map((waypoint, idx) => (
                    <div key={waypoint.id} className="space-y-2">
                      <div className="text-xs text-slate-400 font-semibold">
                        {idx === 0 ? '🟢 START' : idx === waypoints.length - 1 ? '🔴 END' : '🟡 STOP'} #{idx + 1}
                      </div>
                      <div className="flex gap-2 items-center">
                        <select
                          value={waypoint.name}
                          onChange={(e) => setWaypointFromLocation(waypoint.id, e.target.value)}
                          className="flex-1 bg-slate-700 border border-slate-600 text-white text-sm rounded px-2 py-1.5"
                        >
                          <option value="">Select location</option>
                          {locationOptions.slice(0, 20).map(loc => (
                            <option key={loc} value={loc}>{loc}</option>
                          ))}
                        </select>
                        {waypoints.length > 2 && (
                          <button
                            onClick={() => removeWaypoint(waypoint.id)}
                            className="p-1.5 hover:bg-red-600 text-slate-400 hover:text-white rounded transition"
                          >
                            <Trash2 size={16} />
                          </button>
                        )}
                      </div>
                    </div>
                  ))}

                  <button
                    onClick={addWaypoint}
                    className="w-full mt-3 px-3 py-2 bg-blue-600 hover:bg-blue-700 text-white text-sm rounded transition flex items-center justify-center gap-2"
                  >
                    <Plus size={16} /> Add Stop
                  </button>

                  <button
                    onClick={swapWaypoints}
                    className="w-full px-3 py-2 bg-slate-700 hover:bg-slate-600 text-white text-sm rounded transition"
                  >
                    ↔️ Reverse Route
                  </button>

                  <button
                    onClick={optimizeWaypointOrder}
                    className="w-full px-3 py-2 bg-purple-600 hover:bg-purple-700 text-white text-sm rounded transition flex items-center justify-center gap-2"
                  >
                    <Sparkles size={16} /> Optimize Order
                  </button>
                </div>
              )}
            </div>

            {/* Vehicle Section */}
            <div className="bg-slate-800 rounded-lg border border-slate-700 p-4">
              <h3 className="text-white font-semibold mb-3 flex items-center gap-2">
                <Layers size={18} /> Vehicle
              </h3>
              <select
                value={vehicleProfile.id}
                onChange={(e) => setVehicleProfile({ ...vehicleProfile, id: e.target.value })}
                className="w-full bg-slate-700 border border-slate-600 text-white text-sm rounded px-2 py-2"
              >
                <option value="TRUCK-001">TRUCK-001 (Volvo FH16)</option>
                <option value="TRUCK-002">TRUCK-002 (Scania R450)</option>
                <option value="VAN-001">VAN-001 (Sprinter Van)</option>
              </select>
            </div>

            {/* Route Profile Section */}
            <div className="bg-slate-800 rounded-lg border border-slate-700 p-4">
              <h3 className="text-white font-semibold mb-3">Route Profile</h3>
              <div className="space-y-2">
                {['balanced', 'fastest', 'fuel_optimal', 'safest'].map(profile => (
                  <label key={profile} className="flex items-center gap-2 cursor-pointer text-sm text-slate-300 hover:text-white">
                    <input
                      type="radio"
                      value={profile}
                      checked={routeProfile === profile}
                      onChange={(e) => setRouteProfile(e.target.value)}
                      className="w-3 h-3"
                    />
                    <span className="capitalize">{profile.replace('_', ' ')}</span>
                  </label>
                ))}
              </div>
            </div>

            {/* Actions */}
            <div className="grid grid-cols-2 gap-2">
              <button
                onClick={() => exportRoute()}
                className="px-3 py-2 bg-green-600 hover:bg-green-700 text-white text-sm rounded transition flex items-center justify-center gap-1"
              >
                <Download size={14} /> Export
              </button>
              <button
                onClick={shareRoute}
                className="px-3 py-2 bg-blue-600 hover:bg-blue-700 text-white text-sm rounded transition flex items-center justify-center gap-1"
              >
                <Share2 size={14} /> Share
              </button>
            </div>
          </div>

          {/* Right Content Area */}
          <div className="lg:col-span-3 space-y-4">
            {/* Map */}
            {currentRoute && (
              <AdvancedRouteMap
                route={currentRoute}
                vehicle={vehicleProfile}
                onRouteUpdate={calculateRoute}
              />
            )}

            {loading && (
              <div className="bg-slate-800 border border-slate-700 rounded-lg p-8 text-center">
                <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-500 mx-auto mb-4"></div>
                <p className="text-slate-300">Calculating optimal route...</p>
              </div>
            )}

            {/* Route Metrics */}
            {currentRoute && !loading && (
              <div className="grid grid-cols-4 gap-3">
                <div className="bg-slate-800 border border-slate-700 rounded-lg p-3 text-center">
                  <p className="text-slate-400 text-xs mb-1">Distance</p>
                  <p className="text-white font-bold text-xl">{currentRoute.summary?.distance} km</p>
                </div>
                <div className="bg-slate-800 border border-slate-700 rounded-lg p-3 text-center">
                  <p className="text-slate-400 text-xs mb-1">Duration</p>
                  <p className="text-white font-bold text-xl">{currentRoute.summary?.duration} min</p>
                </div>
                <div className="bg-slate-800 border border-slate-700 rounded-lg p-3 text-center">
                  <p className="text-slate-400 text-xs mb-1">Fuel</p>
                  <p className="text-green-400 font-bold text-xl">{currentRoute.summary?.estimatedFuel} L</p>
                </div>
                <div className="bg-slate-800 border border-slate-700 rounded-lg p-3 text-center">
                  <p className="text-slate-400 text-xs mb-1">Cost</p>
                  <p className="text-yellow-400 font-bold text-xl">${currentRoute.summary?.estimatedCost}</p>
                </div>
              </div>
            )}

            {/* Alternative Routes */}
            {alternativeRoutes.length > 0 && (
              <div className="bg-slate-800 rounded-lg border border-slate-700 overflow-hidden">
                <button
                  onClick={() => toggleSection('alternatives')}
                  className="w-full px-4 py-3 flex items-center justify-between hover:bg-slate-700/50 transition"
                >
                  <span className="text-white font-semibold">Alternative Routes</span>
                  {expandedSections.alternatives ? <ChevronUp /> : <ChevronDown />}
                </button>

                {expandedSections.alternatives && (
                  <div className="px-4 py-3 space-y-3 border-t border-slate-700">
                    {alternativeRoutes.map((alt) => (
                      <div
                        key={alt.rank}
                        className="bg-slate-700/50 p-3 rounded cursor-pointer hover:bg-slate-700 transition"
                        onClick={() => setCurrentRoute(alt)}
                      >
                        <div className="flex justify-between items-center mb-2">
                          <span className="text-white font-semibold">Route {alt.rank}</span>
                          <span className="text-xs text-slate-400">{alt.rank === 1 ? '⭐ Recommended' : ''}</span>
                        </div>
                        <div className="grid grid-cols-4 gap-2 text-xs">
                          <div><span className="text-slate-400">Distance:</span> <span className="text-white">{alt.comparison?.distance}km</span></div>
                          <div><span className="text-slate-400">Time:</span> <span className="text-white">{alt.comparison?.duration}min</span></div>
                          <div><span className="text-slate-400">Fuel:</span> <span className="text-green-400">{alt.comparison?.fuel}L</span></div>
                          <div><span className="text-slate-400">Safety:</span> <span className="text-blue-400">{alt.comparison?.safety}/100</span></div>
                        </div>
                      </div>
                    ))}
                  </div>
                )}
              </div>
            )}
          </div>
        </div>
      </div>
    </div>
  );
}
