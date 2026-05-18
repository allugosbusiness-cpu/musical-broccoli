import React, { useState, useEffect } from 'react';
import {
  MapPin, Navigation, Zap, TrendingUp, AlertTriangle, Cloud,
  PlayCircle, CheckCircle, Clock, Gauge, Fuel, BarChart3,
  ChevronDown, Info, X, Loader
} from 'lucide-react';
import { GLOBAL_LOCATIONS } from '../data/locations';
import {
  createOptimizedRoute, getTruckRoutes, getActiveRoutes,
  startRoute, completeRoute, updateRouteProgress, getTrucks
} from '../services/api';

export default function RoutePlanner() {
  // State Management
  const [trucks, setTrucks] = useState([]);
  const [selectedTruck, setSelectedTruck] = useState(null);
  const [origin, setOrigin] = useState('Harare');
  const [destination, setDestination] = useState('Bulawayo');
  const [routes, setRoutes] = useState([]);
  const [activeRoutes, setActiveRoutes] = useState([]);
  const [selectedRoute, setSelectedRoute] = useState(null);
  const [loading, setLoading] = useState(false);
  const [showModal, setShowModal] = useState(false);
  const [routeCreated, setRouteCreated] = useState(false);

  // Suggestions for autocomplete
  const locationOptions = Object.keys(GLOBAL_LOCATIONS);

  // Fetch trucks on mount
  useEffect(() => {
    const fetchTrucks = async () => {
      const data = await getTrucks();
      setTrucks(data);
      if (data.length > 0) {
        setSelectedTruck(data[0].id);
      }
    };
    fetchTrucks();
  }, []);

  // Fetch active routes periodically
  useEffect(() => {
    const fetchRoutes = async () => {
      const data = await getActiveRoutes();
      setActiveRoutes(data);
    };

    fetchRoutes();
    const interval = setInterval(fetchRoutes, 10000); // Update every 10 seconds
    return () => clearInterval(interval);
  }, []);

  // Fetch truck-specific routes
  useEffect(() => {
    if (selectedTruck) {
      const fetchRoutes = async () => {
        const data = await getTruckRoutes(selectedTruck);
        setRoutes(data);
      };
      fetchRoutes();
    }
  }, [selectedTruck]);

  // Handle route creation
  const handleCreateRoute = async () => {
    if (!selectedTruck || !origin || !destination) {
      alert('Please select truck, origin, and destination');
      return;
    }

    if (origin === destination) {
      alert('Origin and destination must be different');
      return;
    }

    setLoading(true);
    try {
      const originCoords = GLOBAL_LOCATIONS[origin];
      const destCoords = GLOBAL_LOCATIONS[destination];

      const route = await createOptimizedRoute(
        selectedTruck,
        origin,
        destination,
        originCoords,
        destCoords
      );

      setSelectedRoute(route);
      setRoutes([route, ...routes]);
      setRouteCreated(true);
      setShowModal(true);

      // Auto-close success message after 3 seconds
      setTimeout(() => setRouteCreated(false), 3000);
    } catch (error) {
      console.error('Error creating route:', error);
      alert('Failed to create route');
    } finally {
      setLoading(false);
    }
  };

  // Handle route start
  const handleStartRoute = async (routeId) => {
    try {
      const updatedRoute = await startRoute(routeId);
      setSelectedRoute(updatedRoute);
      setRoutes(routes.map(r => r.id === routeId ? updatedRoute : r));
    } catch (error) {
      console.error('Error starting route:', error);
    }
  };

  // Handle route completion
  const handleCompleteRoute = async (routeId) => {
    try {
      const updatedRoute = await completeRoute(routeId);
      setSelectedRoute(updatedRoute);
      setRoutes(routes.map(r => r.id === routeId ? updatedRoute : r));
    } catch (error) {
      console.error('Error completing route:', error);
    }
  };

  // Get truck name
  const getTruckName = (truckId) => {
    const truck = trucks.find(t => t.id === truckId);
    return truck ? `${truck.plate} - ${truck.driver}` : 'Unknown';
  };

  // Format time in hours
  const formatTime = (hours) => {
    const h = Math.floor(hours);
    const m = Math.round((hours - h) * 60);
    return `${h}h ${m}m`;
  };

  return (
    <div className="min-h-screen bg-slate-900 text-white p-6">
      <div className="max-w-7xl mx-auto">
        {/* Header */}
        <div className="mb-8">
          <h1 className="text-4xl font-bold flex items-center gap-3 mb-2">
            <Navigation className="w-8 h-8 text-blue-500" />
            Smart Route Planner
          </h1>
          <p className="text-gray-400">AI-powered routing with live directions, speed optimization & traffic prediction</p>
        </div>

        {/* Success Message */}
        {routeCreated && (
          <div className="mb-6 p-4 bg-green-900/30 border border-green-500 rounded-lg flex items-center gap-3">
            <CheckCircle className="w-5 h-5 text-green-500" />
            <span className="text-green-200">Route created successfully!</span>
          </div>
        )}

        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
          {/* Left: Route Creation */}
          <div className="lg:col-span-1">
            <div className="bg-slate-800 border border-slate-700 rounded-xl p-6 sticky top-6">
              <h2 className="text-xl font-bold mb-6 flex items-center gap-2">
                <MapPin className="w-5 h-5 text-blue-500" />
                Create Route
              </h2>

              {/* Truck Selection */}
              <div className="mb-5">
                <label className="block text-sm font-semibold text-gray-300 mb-2">Select Truck</label>
                <select
                  value={selectedTruck || ''}
                  onChange={(e) => setSelectedTruck(e.target.value)}
                  className="w-full px-4 py-2 bg-slate-700 border border-slate-600 rounded-lg text-white focus:outline-none focus:border-blue-500"
                >
                  <option value="">Choose a truck...</option>
                  {trucks.map((truck) => (
                    <option key={truck.id} value={truck.id}>
                      {truck.plate} - {truck.driver} ({truck.status})
                    </option>
                  ))}
                </select>
              </div>

              {/* Origin Selection */}
              <div className="mb-5">
                <label className="block text-sm font-semibold text-gray-300 mb-2">Origin</label>
                <select
                  value={origin}
                  onChange={(e) => setOrigin(e.target.value)}
                  className="w-full px-4 py-2 bg-slate-700 border border-slate-600 rounded-lg text-white focus:outline-none focus:border-blue-500"
                >
                  {locationOptions.map((loc) => (
                    <option key={loc} value={loc}>
                      {loc}
                    </option>
                  ))}
                </select>
              </div>

              {/* Destination Selection */}
              <div className="mb-6">
                <label className="block text-sm font-semibold text-gray-300 mb-2">Destination</label>
                <select
                  value={destination}
                  onChange={(e) => setDestination(e.target.value)}
                  className="w-full px-4 py-2 bg-slate-700 border border-slate-600 rounded-lg text-white focus:outline-none focus:border-blue-500"
                >
                  {locationOptions.map((loc) => (
                    <option key={loc} value={loc}>
                      {loc}
                    </option>
                  ))}
                </select>
              </div>

              {/* Create Button */}
              <button
                onClick={handleCreateRoute}
                disabled={loading || !selectedTruck}
                className="w-full px-4 py-3 bg-blue-600 hover:bg-blue-700 disabled:bg-gray-600 disabled:opacity-50 text-white font-bold rounded-lg transition-all flex items-center justify-center gap-2"
              >
                {loading ? (
                  <>
                    <Loader className="w-5 h-5 animate-spin" />
                    Computing...
                  </>
                ) : (
                  <>
                    <Zap className="w-5 h-5" />
                    Generate Route
                  </>
                )}
              </button>
            </div>
          </div>

          {/* Right: Route Details & Active Routes */}
          <div className="lg:col-span-2 space-y-6">
            {/* Selected Route Details */}
            {selectedRoute && (
              <div className="bg-slate-800 border border-slate-700 rounded-xl p-6">
                <div className="flex items-center justify-between mb-6">
                  <h2 className="text-xl font-bold flex items-center gap-2">
                    <TrendingUp className="w-5 h-5 text-green-500" />
                    Route Details
                  </h2>
                  <span className={`px-3 py-1 rounded-full text-xs font-bold ${
                    selectedRoute.status === 'completed' ? 'bg-green-900/30 text-green-300' :
                    selectedRoute.status === 'in_progress' ? 'bg-blue-900/30 text-blue-300' :
                    'bg-amber-900/30 text-amber-300'
                  }`}>
                    {selectedRoute.status.toUpperCase()}
                  </span>
                </div>

                {/* Route Overview */}
                <div className="grid grid-cols-2 gap-4 mb-6">
                  <div className="bg-slate-700/50 rounded-lg p-4">
                    <p className="text-xs text-gray-400 mb-1">Truck</p>
                    <p className="font-semibold">{selectedRoute.truck_plate}</p>
                    <p className="text-sm text-gray-400">{selectedRoute.driver_name}</p>
                  </div>
                  <div className="bg-slate-700/50 rounded-lg p-4">
                    <p className="text-xs text-gray-400 mb-1">Distance</p>
                    <p className="font-bold text-blue-400">{selectedRoute.distance_km} km</p>
                  </div>
                  <div className="bg-slate-700/50 rounded-lg p-4">
                    <p className="text-xs text-gray-400 mb-1">Est. Time</p>
                    <p className="font-bold text-green-400">{formatTime(selectedRoute.estimated_duration_hours)}</p>
                  </div>
                  <div className="bg-slate-700/50 rounded-lg p-4">
                    <p className="text-xs text-gray-400 mb-1">Optimization</p>
                    <p className="font-bold text-purple-400">{Number.isFinite(selectedRoute.optimization_score) ? Number(selectedRoute.optimization_score).toFixed(1) : '0.0'}/100</p>
                  </div>
                </div>

                {/* Route Path */}
                <div className="mb-6 pb-6 border-b border-slate-700">
                  <h3 className="text-sm font-bold text-gray-300 mb-3">Route Path</h3>
                  <div className="flex items-start gap-2">
                    <MapPin className="w-5 h-5 text-blue-500 flex-shrink-0 mt-1" />
                    <div className="flex-1">
                      <p className="font-semibold text-blue-400">{selectedRoute.origin}</p>
                      <p className="text-xs text-gray-400">{selectedRoute.waypoints.length} waypoints</p>
                    </div>
                  </div>
                  <div className="ml-2.5 w-0.5 h-8 bg-slate-600 my-2"></div>
                  <div className="flex items-start gap-2">
                    <MapPin className="w-5 h-5 text-red-500 flex-shrink-0 mt-1" />
                    <div className="flex-1">
                      <p className="font-semibold text-red-400">{selectedRoute.destination}</p>
                      <p className="text-xs text-gray-400">Final destination</p>
                    </div>
                  </div>
                </div>

                {/* Speed Suggestions */}
                <div className="mb-6 pb-6 border-b border-slate-700">
                  <h3 className="text-sm font-bold text-gray-300 mb-3 flex items-center gap-2">
                    <Gauge className="w-4 h-4 text-yellow-500" />
                    Speed Recommendations
                  </h3>
                  <div className="space-y-2">
                    {Object.entries(selectedRoute.suggested_speeds).slice(0, 3).map(([segment, data]) => (
                      <div key={segment} className="flex items-center justify-between bg-slate-700/30 px-3 py-2 rounded">
                        <div>
                          <p className="text-xs font-semibold text-gray-300 capitalize">{data.road_type} Road</p>
                          <p className="text-xs text-gray-400">Segment {segment.split('_')[1]}</p>
                        </div>
                        <div className="text-right">
                          <p className="font-bold text-blue-400">{data.suggested_speed_kmh} km/h</p>
                          <p className="text-xs text-gray-400">Suggested</p>
                        </div>
                      </div>
                    ))}
                  </div>
                </div>

                {/* Weather Info */}
                <div className="mb-6 pb-6 border-b border-slate-700">
                  <h3 className="text-sm font-bold text-gray-300 mb-3 flex items-center gap-2">
                    <Cloud className="w-4 h-4 text-cyan-500" />
                    Weather Conditions
                  </h3>
                  <div className="grid grid-cols-2 gap-3">
                    <div className="bg-slate-700/30 px-3 py-2 rounded">
                      <p className="text-xs text-gray-400">Temperature</p>
                      <p className="font-bold text-cyan-400">{selectedRoute.weather_factors.temperature_celsius}°C</p>
                    </div>
                    <div className="bg-slate-700/30 px-3 py-2 rounded">
                      <p className="text-xs text-gray-400">Condition</p>
                      <p className="font-bold text-cyan-400">{selectedRoute.weather_factors.weather_condition}</p>
                    </div>
                    <div className="bg-slate-700/30 px-3 py-2 rounded">
                      <p className="text-xs text-gray-400">Wind</p>
                      <p className="font-bold text-cyan-400">{selectedRoute.weather_factors.wind_speed_kmh} km/h</p>
                    </div>
                    <div className="bg-slate-700/30 px-3 py-2 rounded">
                      <p className="text-xs text-gray-400">Visibility</p>
                      <p className="font-bold text-cyan-400">{selectedRoute.weather_factors.visibility_km} km</p>
                    </div>
                  </div>
                </div>

                {/* Action Buttons */}
                <div className="flex gap-3">
                  {selectedRoute.status === 'planned' && (
                    <button
                      onClick={() => handleStartRoute(selectedRoute.id)}
                      className="flex-1 px-4 py-2 bg-green-600 hover:bg-green-700 text-white font-bold rounded-lg transition-all flex items-center justify-center gap-2"
                    >
                      <PlayCircle className="w-4 h-4" />
                      Start Route
                    </button>
                  )}
                  {selectedRoute.status === 'in_progress' && (
                    <button
                      onClick={() => handleCompleteRoute(selectedRoute.id)}
                      className="flex-1 px-4 py-2 bg-green-600 hover:bg-green-700 text-white font-bold rounded-lg transition-all flex items-center justify-center gap-2"
                    >
                      <CheckCircle className="w-4 h-4" />
                      Complete Route
                    </button>
                  )}
                </div>
              </div>
            )}

            {/* Active Routes List */}
            {activeRoutes.length > 0 && (
              <div className="bg-slate-800 border border-slate-700 rounded-xl p-6">
                <h2 className="text-lg font-bold mb-4 flex items-center gap-2">
                  <Navigation className="w-5 h-5 text-green-500" />
                  Active Routes ({activeRoutes.length})
                </h2>
                <div className="space-y-3 max-h-96 overflow-y-auto">
                  {activeRoutes.map((route) => (
                    <div
                      key={route.id}
                      onClick={() => setSelectedRoute(route)}
                      className={`p-4 rounded-lg cursor-pointer transition-all ${
                        selectedRoute?.id === route.id
                          ? 'bg-blue-600/20 border-2 border-blue-500'
                          : 'bg-slate-700/50 border border-slate-600 hover:border-slate-500'
                      }`}
                    >
                      <div className="flex items-center justify-between mb-2">
                        <div>
                          <p className="font-bold">{route.origin} → {route.destination}</p>
                          <p className="text-xs text-gray-400">{route.truck_plate} | {route.driver_name}</p>
                        </div>
                        <div className="text-right">
                          <p className="font-bold text-blue-400">{route.distance_km} km</p>
                          <p className="text-xs text-gray-400">{formatTime(route.estimated_duration_hours)}</p>
                        </div>
                      </div>
                      <div className="flex items-center justify-between text-xs">
                        <span className={`px-2 py-1 rounded ${
                          route.status === 'completed' ? 'bg-green-900/30 text-green-300' :
                          route.status === 'in_progress' ? 'bg-blue-900/30 text-blue-300' :
                          'bg-amber-900/30 text-amber-300'
                        }`}>
                          {route.status.toUpperCase()}
                        </span>
                        <span className="text-blue-400 font-semibold">Score: {Number.isFinite(route.optimization_score) ? Number(route.optimization_score).toFixed(1) : '0.0'}</span>
                      </div>
                    </div>
                  ))}
                </div>
              </div>
            )}

            {/* Route History */}
            {routes.length > 0 && (
              <div className="bg-slate-800 border border-slate-700 rounded-xl p-6">
                <h2 className="text-lg font-bold mb-4">Route History</h2>
                <div className="space-y-2 max-h-64 overflow-y-auto">
                  {routes.slice(0, 5).map((route) => (
                    <div key={route.id} className="text-sm p-3 bg-slate-700/30 rounded">
                      <p className="font-semibold">{route.origin} → {route.destination}</p>
                      <p className="text-xs text-gray-400">{route.distance_km} km | {formatTime(route.estimated_duration_hours)}</p>
                    </div>
                  ))}
                </div>
              </div>
            )}
          </div>
        </div>
      </div>
    </div>
  );
}
