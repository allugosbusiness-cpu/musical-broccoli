import React, { useState, useEffect } from 'react';
import { MapPin, Navigation, Plus, Trash2, Zap, TrendingUp, Clock, Gauge } from 'lucide-react';
import { getTrucks, createSmartRoute, getRoutes, startRoute, getRouteDirections, completeRoute } from '../services/api';
import { GLOBAL_LOCATIONS, getCoordinates } from '../data/locations.js';

const SmartRouter = () => {
  // State Management
  const [trucks, setTrucks] = useState([]);
  const [routes, setRoutes] = useState([]);
  const [showForm, setShowForm] = useState(false);
  const [selectedTruck, setSelectedTruck] = useState('');
  const [origin, setOrigin] = useState('');
  const [destination, setDestination] = useState('');
  const [waypoints, setWaypoints] = useState([]);
  const [newWaypoint, setNewWaypoint] = useState('');
  const [loading, setLoading] = useState(false);
  const [selectedRoute, setSelectedRoute] = useState(null);
  const [directions, setDirections] = useState(null);
  const [showDirections, setShowDirections] = useState(false);
  const [locationFilter, setLocationFilter] = useState('');

  // Fetch trucks on mount
  useEffect(() => {
    const loadTrucks = async () => {
      const data = await getTrucks();
      setTrucks(Array.isArray(data) ? data : []);
    };
    loadTrucks();
  }, []);

  // Fetch routes for selected truck
  useEffect(() => {
    if (selectedTruck) {
      const loadRoutes = async () => {
        const data = await getRoutes(selectedTruck);
        setRoutes(Array.isArray(data) ? data : []);
      };
      loadRoutes();
    }
  }, [selectedTruck]);

  // Available locations for dropdown
  const availableLocations = Object.keys(GLOBAL_LOCATIONS).filter(loc =>
    loc.toLowerCase().includes(locationFilter.toLowerCase())
  );

  // Handle Add Waypoint
  const handleAddWaypoint = () => {
    if (newWaypoint.trim() && !waypoints.includes(newWaypoint)) {
      setWaypoints([...waypoints, newWaypoint]);
      setNewWaypoint('');
    }
  };

  // Handle Remove Waypoint
  const handleRemoveWaypoint = (index) => {
    setWaypoints(waypoints.filter((_, i) => i !== index));
  };

  // Handle Create Smart Route
  const handleCreateRoute = async (e) => {
    e.preventDefault();
    if (!selectedTruck || !origin || !destination) {
      alert('Please select truck, origin, and destination');
      return;
    }

    setLoading(true);
    try {
      const originCoords = getCoordinates(origin);
      const destCoords = getCoordinates(destination);

      const routeData = {
        truck_id: selectedTruck,
        origin,
        destination,
        origin_coords: originCoords,
        destination_coords: destCoords,
        waypoints: waypoints.map(wp => {
          const coords = getCoordinates(wp);
          return {
            location: wp,
            lat: coords.lat,
            lng: coords.lng,
          };
        }),
      };

      const newRoute = await createSmartRoute(routeData);
      if (newRoute) {
        setRoutes([newRoute, ...routes]);
        setShowForm(false);
        setOrigin('');
        setDestination('');
        setWaypoints([]);
        alert('✅ Smart route created successfully!');
      }
    } catch (error) {
      alert('Error creating route: ' + error.message);
    } finally {
      setLoading(false);
    }
  };

  // Handle Start Route
  const handleStartRoute = async (routeId) => {
    try {
      const updatedRoute = await startRoute(routeId);
      if (updatedRoute) {
        setRoutes(routes.map(r => r.id === routeId ? updatedRoute : r));
        alert('🚀 Route started! Navigate using live directions.');
      }
    } catch (error) {
      alert('Error starting route');
    }
  };

  // Handle Complete Route
  const handleCompleteRoute = async (routeId) => {
    try {
      const updatedRoute = await completeRoute(routeId);
      if (updatedRoute) {
        setRoutes(routes.map(r => r.id === routeId ? updatedRoute : r));
        alert('✅ Route completed!');
      }
    } catch (error) {
      alert('Error completing route');
    }
  };

  // Handle View Directions
  const handleViewDirections = async (routeId) => {
    try {
      const dirs = await getRouteDirections(routeId);
      if (dirs) {
        setDirections(dirs);
        setShowDirections(true);
      }
    } catch (error) {
      alert('Error fetching directions');
    }
  };

  // Get status color
  const getStatusColor = (status) => {
    const colors = {
      pending: 'bg-slate-700 text-gray-300',
      active: 'bg-blue-700 text-blue-100',
      completed: 'bg-green-700 text-green-100',
      cancelled: 'bg-red-700 text-red-100',
    };
    return colors[status] || colors.pending;
  };

  const getStatusIcon = (status) => {
    switch (status) {
      case 'pending':
        return '⏳';
      case 'active':
        return '🚀';
      case 'completed':
        return '✅';
      case 'cancelled':
        return '❌';
      default:
        return '📍';
    }
  };

  return (
    <div className="w-full h-full bg-gradient-to-br from-slate-900 via-slate-800 to-slate-900 p-6 rounded-xl border border-blue-500/20">
      {/* Header */}
      <div className="flex items-center justify-between mb-6">
        <div className="flex items-center gap-3">
          <Navigation className="w-6 h-6 text-blue-400" />
          <h2 className="text-2xl font-bold text-white">🧠 Smart Route Planner</h2>
        </div>
        <button
          onClick={() => setShowForm(!showForm)}
          className="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-all flex items-center gap-2 font-semibold"
        >
          <Plus className="w-4 h-4" />
          New Route
        </button>
      </div>

      {/* Create Route Form */}
      {showForm && (
        <div className="mb-6 p-6 bg-slate-800/50 border border-blue-500/30 rounded-xl backdrop-blur">
          <h3 className="text-lg font-semibold text-white mb-4">Create ML-Optimized Route</h3>
          <form onSubmit={handleCreateRoute} className="space-y-4">
            {/* Truck Selection */}
            <div>
              <label className="block text-sm font-semibold text-gray-300 mb-2">Select Truck</label>
              <select
                value={selectedTruck}
                onChange={(e) => setSelectedTruck(e.target.value)}
                className="w-full px-3 py-2 bg-slate-700 border border-slate-600 rounded-lg text-white focus:border-blue-500 focus:outline-none"
                required
              >
                <option value="">-- Choose a truck --</option>
                {trucks.map(truck => (
                  <option key={truck.id} value={truck.id}>
                    {truck.plate} - {truck.driver} ({truck.location})
                  </option>
                ))}
              </select>
            </div>

            {/* Origin & Destination */}
            <div className="grid grid-cols-2 gap-4">
              <div>
                <label className="block text-sm font-semibold text-gray-300 mb-2">Origin</label>
                <input
                  type="text"
                  value={origin}
                  onChange={(e) => setOrigin(e.target.value)}
                  placeholder="Enter city or location"
                  list="locations-list"
                  className="w-full px-3 py-2 bg-slate-700 border border-slate-600 rounded-lg text-white placeholder-gray-500 focus:border-blue-500 focus:outline-none"
                  required
                />
              </div>
              <div>
                <label className="block text-sm font-semibold text-gray-300 mb-2">Destination</label>
                <input
                  type="text"
                  value={destination}
                  onChange={(e) => setDestination(e.target.value)}
                  placeholder="Enter city or location"
                  list="locations-list"
                  className="w-full px-3 py-2 bg-slate-700 border border-slate-600 rounded-lg text-white placeholder-gray-500 focus:border-blue-500 focus:outline-none"
                  required
                />
              </div>
            </div>

            {/* Waypoints */}
            <div>
              <label className="block text-sm font-semibold text-gray-300 mb-2">Add Waypoints (Optional)</label>
              <div className="flex gap-2 mb-2">
                <input
                  type="text"
                  value={newWaypoint}
                  onChange={(e) => setNewWaypoint(e.target.value)}
                  placeholder="Enter waypoint location"
                  list="locations-list"
                  onKeyPress={(e) => e.key === 'Enter' && (e.preventDefault(), handleAddWaypoint())}
                  className="flex-1 px-3 py-2 bg-slate-700 border border-slate-600 rounded-lg text-white placeholder-gray-500 focus:border-blue-500 focus:outline-none"
                />
                <button
                  type="button"
                  onClick={handleAddWaypoint}
                  className="px-3 py-2 bg-green-600 text-white rounded-lg hover:bg-green-700 transition-all"
                >
                  <Plus className="w-4 h-4" />
                </button>
              </div>

              {/* Waypoints List */}
              <div className="space-y-2">
                {waypoints.map((wp, idx) => (
                  <div key={idx} className="flex items-center justify-between bg-slate-700/50 p-2 rounded border border-slate-600">
                    <span className="text-white text-sm">{idx + 1}. {wp}</span>
                    <button
                      type="button"
                      onClick={() => handleRemoveWaypoint(idx)}
                      className="p-1 hover:bg-red-600/20 rounded transition-all"
                    >
                      <Trash2 className="w-4 h-4 text-red-400" />
                    </button>
                  </div>
                ))}
              </div>
            </div>

            {/* Buttons */}
            <div className="flex gap-3 pt-4 border-t border-slate-600">
              <button
                type="submit"
                disabled={loading}
                className="flex-1 px-4 py-2.5 bg-blue-600 text-white rounded-lg hover:bg-blue-700 active:bg-blue-800 transition-all disabled:opacity-50 font-semibold flex items-center justify-center gap-2"
              >
                <Zap className="w-4 h-4" />
                {loading ? 'Creating Route...' : 'Create Smart Route'}
              </button>
              <button
                type="button"
                onClick={() => setShowForm(false)}
                className="flex-1 px-4 py-2.5 bg-slate-700 border border-slate-600 text-gray-300 rounded-lg hover:bg-slate-600 transition-all font-semibold"
              >
                Cancel
              </button>
            </div>
          </form>

          <datalist id="locations-list">
            {availableLocations.map(loc => (
              <option key={loc} value={loc} />
            ))}
          </datalist>
        </div>
      )}

      {/* Routes List */}
      <div className="space-y-3 max-h-96 overflow-y-auto">
        {routes.length === 0 ? (
          <div className="text-center py-8 text-gray-400">
            <MapPin className="w-12 h-12 mx-auto mb-2 opacity-50" />
            <p>No routes created yet. Create one to get started!</p>
          </div>
        ) : (
          routes.map(route => (
            <div
              key={route.id}
              className="p-4 bg-slate-800/40 border border-slate-700/60 hover:border-blue-500/40 rounded-lg transition-all cursor-pointer"
              onClick={() => setSelectedRoute(selectedRoute?.id === route.id ? null : route)}
            >
              {/* Route Header */}
              <div className="flex items-start justify-between mb-3">
                <div className="flex-1">
                  <div className="flex items-center gap-2 mb-1">
                    <span className="text-2xl">{getStatusIcon(route.status)}</span>
                    <h4 className="text-white font-bold">
                      {route.origin} → {route.destination}
                    </h4>
                    <span className={`text-xs px-2 py-1 rounded-full font-semibold ${getStatusColor(route.status)}`}>
                      {route.status.toUpperCase()}
                    </span>
                  </div>
                  <p className="text-sm text-gray-400">
                    Truck: {route.truck_plate} | Driver: {route.truck_driver}
                  </p>
                </div>
              </div>

              {/* Route Details */}
              <div className="grid grid-cols-4 gap-3 mb-3">
                <div className="bg-slate-700/50 p-2 rounded border border-slate-600/50">
                  <p className="text-xs text-gray-400">Distance</p>
                  <p className="text-sm font-bold text-blue-400">{Number.isFinite(route?.total_distance) ? Number(route.total_distance).toFixed(1) : '0.0'} km</p>
                </div>
                <div className="bg-slate-700/50 p-2 rounded border border-slate-600/50">
                  <p className="text-xs text-gray-400 flex items-center gap-1">
                    <Clock className="w-3 h-3" /> Duration
                  </p>
                  <p className="text-sm font-bold text-green-400">{Math.round(route.estimated_duration)} min</p>
                </div>
                <div className="bg-slate-700/50 p-2 rounded border border-slate-600/50">
                  <p className="text-xs text-gray-400 flex items-center gap-1">
                    <Gauge className="w-3 h-3" /> Speed
                  </p>
                  <p className="text-sm font-bold text-amber-400">{route.suggested_avg_speed} km/h</p>
                </div>
                <div className="bg-slate-700/50 p-2 rounded border border-slate-600/50">
                  <p className="text-xs text-gray-400">Waypoints</p>
                  <p className="text-sm font-bold text-purple-400">{route.waypoints?.length || 0}</p>
                </div>
              </div>

              {/* Expanded Details */}
              {selectedRoute?.id === route.id && (
                <div className="border-t border-slate-600 pt-3 space-y-3">
                  {/* Waypoints */}
                  {route.waypoints && route.waypoints.length > 0 && (
                    <div>
                      <h5 className="text-sm font-semibold text-gray-300 mb-2">🗺️ Route Waypoints:</h5>
                      <div className="space-y-1 text-sm text-gray-400">
                        {route.waypoints.map((wp, idx) => (
                          <div key={idx} className="flex items-center gap-2 pl-2">
                            <span className="text-blue-400">→</span>
                            <span>{wp.order + 1}. {wp.location}</span>
                            <span className="text-xs text-gray-500">({Number.isFinite(wp?.distance_from_previous) ? Number(wp.distance_from_previous).toFixed(1) : '0.0'} km @ {wp.suggested_speed} km/h)</span>
                          </div>
                        ))}
                      </div>
                    </div>
                  )}

                  {/* Speed Recommendations */}
                  <div className="bg-amber-900/20 border border-amber-700/40 p-2 rounded text-sm text-amber-300">
                    <p className="font-semibold flex items-center gap-2">
                      <TrendingUp className="w-4 h-4" />
                      ML Speed Recommendation: {route.suggested_avg_speed} km/h
                    </p>
                    <p className="text-xs text-amber-200/70 mt-1">
                      Based on distance, vehicle load, and traffic patterns for optimal fuel efficiency and safety.
                    </p>
                  </div>

                  {/* Action Buttons */}
                  <div className="flex gap-2 pt-2">
                    {route.status === 'pending' && (
                      <button
                        onClick={() => handleStartRoute(route.id)}
                        className="flex-1 px-3 py-2 bg-green-600 text-white text-sm rounded-lg hover:bg-green-700 transition-all font-semibold flex items-center justify-center gap-1"
                      >
                        <Navigation className="w-3 h-3" />
                        Start Navigation
                      </button>
                    )}
                    {route.status === 'active' && (
                      <button
                        onClick={() => handleCompleteRoute(route.id)}
                        className="flex-1 px-3 py-2 bg-blue-600 text-white text-sm rounded-lg hover:bg-blue-700 transition-all font-semibold"
                      >
                        Complete Route
                      </button>
                    )}
                    <button
                      onClick={() => handleViewDirections(route.id)}
                      className="flex-1 px-3 py-2 bg-purple-600 text-white text-sm rounded-lg hover:bg-purple-700 transition-all font-semibold"
                    >
                      View Directions
                    </button>
                  </div>
                </div>
              )}
            </div>
          ))
        )}
      </div>

      {/* Directions Modal */}
      {showDirections && directions && (
        <div className="fixed inset-0 bg-black/80 z-40 backdrop-blur-sm flex items-center justify-center p-4">
          <div className="bg-slate-900 border-2 border-blue-500 rounded-xl max-w-2xl w-full max-h-96 overflow-y-auto shadow-2xl">
            {/* Header */}
            <div className="sticky top-0 px-6 py-4 border-b border-blue-500 bg-slate-800 flex items-center justify-between flex-shrink-0">
              <h3 className="text-lg font-bold text-white flex items-center gap-2">
                <Navigation className="w-5 h-5 text-blue-400" />
                Live Directions
              </h3>
              <button
                onClick={() => setShowDirections(false)}
                className="text-gray-400 hover:text-white transition-all"
              >
                ✕
              </button>
            </div>

            {/* Directions Content */}
            <div className="px-6 py-4 space-y-4 flex-1 overflow-y-auto">
              {/* Summary */}
              <div className="bg-gradient-to-r from-blue-900/30 to-purple-900/30 border border-blue-500/30 p-3 rounded-lg">
                <p className="text-sm text-blue-200 font-semibold">
                  📊 Route Summary: {Number.isFinite(directions?.summary?.total_distance) ? Number(directions.summary.total_distance).toFixed(1) : '0.0'} km in {Math.round(directions?.summary?.estimated_duration || 0)} minutes
                </p>
                <p className="text-xs text-gray-400 mt-1">
                  Recommended speed: {directions.summary.suggested_speed} km/h
                </p>
              </div>

              {/* Origin */}
              <div className="flex gap-3">
                <div className="text-blue-400 font-bold text-xl">📍</div>
                <div className="flex-1">
                  <p className="text-white font-semibold">{directions.origin.location}</p>
                  <p className="text-xs text-gray-400">{directions.origin.instruction}</p>
                </div>
              </div>

              {/* Waypoints */}
              {directions.waypoints.map((wp, idx) => (
                <div key={idx} className="flex gap-3 pl-6 border-l-2 border-blue-500/50">
                  <div className="text-amber-400 font-bold text-lg">⬇</div>
                  <div className="flex-1">
                    <div className="flex items-center gap-2">
                      <p className="text-white font-semibold">{wp.location}</p>
                      <span className={`text-xs px-2 py-0.5 rounded-full ${wp.status === 'visited' ? 'bg-green-700' : 'bg-slate-700'}`}>
                        {wp.status}
                      </span>
                    </div>
                    <p className="text-xs text-gray-400 mt-1">{wp.instruction}</p>
                    <p className="text-xs text-blue-300 mt-1 flex items-center gap-1">
                      <Gauge className="w-3 h-3" /> {Number.isFinite(wp?.distance_from_previous) ? Number(wp.distance_from_previous).toFixed(1) : '0.0'} km @ {wp.suggested_speed} km/h
                    </p>
                  </div>
                </div>
              ))}

              {/* Destination */}
              <div className="flex gap-3 pl-6 border-l-2 border-blue-500/50">
                <div className="text-green-400 font-bold text-xl">✓</div>
                <div className="flex-1">
                  <p className="text-white font-semibold">{directions.destination.location}</p>
                  <p className="text-xs text-gray-400">{directions.destination.instruction}</p>
                </div>
              </div>
            </div>

            {/* Footer */}
            <div className="px-6 py-4 border-t border-blue-500 bg-slate-800 flex-shrink-0">
              <button
                onClick={() => setShowDirections(false)}
                className="w-full px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-all font-semibold"
              >
                Close
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

export default SmartRouter;
