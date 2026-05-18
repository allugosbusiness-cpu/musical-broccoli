import React, { useState, useEffect, useCallback } from 'react';
import { MapPin, Fuel, Clock, AlertTriangle, TrendingDown, Navigation } from 'lucide-react';
import axios from 'axios';

const API_BASE = 'http://localhost:8000/api/v2';

export function SmartRoutePlanner() {
  const [origin, setOrigin] = useState({ lat: 17.8252, lon: 25.2753 }); // Harare
  const [destination, setDestination] = useState({ lat: 17.8832, lon: 25.8232 }); // Bulawayo
  const [vehicleId, setVehicleId] = useState('TRUCK-001');
  const [profile, setProfile] = useState('fuel_optimal');
  const [avoidHazards, setAvoidHazards] = useState(true);
  const [loading, setLoading] = useState(false);
  const [route, setRoute] = useState(null);
  const [alternatives, setAlternatives] = useState([]);
  const [error, setError] = useState(null);
  const [selectedAlt, setSelectedAlt] = useState(0);

  const handleCalculateRoute = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const response = await axios.post(`${API_BASE}/routes/calculate`, {
        origin,
        destination,
        vehicle_id: vehicleId,
        profile,
        avoid_hazards: avoidHazards,
      });
      setRoute(response.data);
      setAlternatives(response.data.alternatives || []);
    } catch (err) {
      setError(err.response?.data?.error || err.message);
    } finally {
      setLoading(false);
    }
  }, [origin, destination, vehicleId, profile, avoidHazards]);

  const displayRoute = selectedAlt > 0 ? alternatives[selectedAlt - 1] : route;

  return (
    <div className="bg-gradient-to-br from-slate-900 via-slate-800 to-slate-900 min-h-screen p-6">
      <div className="max-w-7xl mx-auto">
        {/* Header */}
        <div className="mb-8">
          <h1 className="text-4xl font-bold text-white flex items-center gap-3 mb-2">
            <Navigation className="text-blue-400" size={32} />
            Smart Route Planner
          </h1>
          <p className="text-slate-400">
            AI-powered routing with fuel optimization, traffic awareness, and hazard detection
          </p>
        </div>

        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
          {/* Control Panel */}
          <div className="lg:col-span-1">
            <div className="bg-slate-800 rounded-xl shadow-xl p-6 border border-slate-700 space-y-4">
              {/* Vehicle Selection */}
              <div>
                <label className="block text-sm font-semibold text-white mb-2">
                  Vehicle
                </label>
                <select
                  value={vehicleId}
                  onChange={(e) => setVehicleId(e.target.value)}
                  className="w-full bg-slate-700 border border-slate-600 rounded-lg px-3 py-2 text-white focus:border-blue-500 focus:outline-none transition"
                >
                  <option value="TRUCK-001">TRUCK-001 (Volvo FH16)</option>
                  <option value="TRUCK-002">TRUCK-002 (Scania R450)</option>
                  <option value="VAN-001">VAN-001 (Sprinter)</option>
                </select>
              </div>

              {/* Route Profile */}
              <div>
                <label className="block text-sm font-semibold text-white mb-3">
                  Route Profile
                </label>
                <div className="space-y-2">
                  <label className="flex items-center cursor-pointer">
                    <input
                      type="radio"
                      value="fuel_optimal"
                      checked={profile === 'fuel_optimal'}
                      onChange={(e) => setProfile(e.target.value)}
                      className="w-4 h-4 text-blue-500"
                    />
                    <span className="ml-3 text-sm text-white flex items-center gap-2">
                      <Fuel size={16} className="text-green-400" />
                      Fuel Optimal
                    </span>
                  </label>
                  <label className="flex items-center cursor-pointer">
                    <input
                      type="radio"
                      value="fastest"
                      checked={profile === 'fastest'}
                      onChange={(e) => setProfile(e.target.value)}
                      className="w-4 h-4 text-blue-500"
                    />
                    <span className="ml-3 text-sm text-white flex items-center gap-2">
                      <Clock size={16} className="text-yellow-400" />
                      Fastest
                    </span>
                  </label>
                  <label className="flex items-center cursor-pointer">
                    <input
                      type="radio"
                      value="avoid_hazards"
                      checked={profile === 'avoid_hazards'}
                      onChange={(e) => setProfile(e.target.value)}
                      className="w-4 h-4 text-blue-500"
                    />
                    <span className="ml-3 text-sm text-white flex items-center gap-2">
                      <AlertTriangle size={16} className="text-red-400" />
                      Avoid Hazards
                    </span>
                  </label>
                </div>
              </div>

              {/* Hazard Avoidance Toggle */}
              <label className="flex items-center cursor-pointer bg-slate-700 p-3 rounded-lg">
                <input
                  type="checkbox"
                  checked={avoidHazards}
                  onChange={(e) => setAvoidHazards(e.target.checked)}
                  className="w-4 h-4 text-blue-500 rounded"
                />
                <span className="ml-3 text-sm font-medium text-white">
                  Avoid sharp curves & steep descents
                </span>
              </label>

              {/* Calculate Button */}
              <button
                onClick={handleCalculateRoute}
                disabled={loading}
                className="w-full bg-gradient-to-r from-blue-600 to-blue-500 hover:from-blue-700 hover:to-blue-600 disabled:from-gray-500 disabled:to-gray-500 text-white font-semibold py-3 rounded-lg transition transform hover:scale-105 active:scale-95"
              >
                {loading ? 'Calculating...' : 'Calculate Route'}
              </button>

              {error && (
                <div className="bg-red-900/20 border border-red-600 rounded-lg p-3 text-sm text-red-300">
                  {error}
                </div>
              )}
            </div>
          </div>

          {/* Results Panel */}
          <div className="lg:col-span-2">
            {displayRoute ? (
              <div className="space-y-4">
                {/* Primary Route Card */}
                <div className="bg-gradient-to-br from-blue-900 to-blue-800 rounded-xl shadow-xl p-6 border border-blue-700">
                  <h3 className="text-lg font-bold text-white mb-4 flex items-center gap-2">
                    <MapPin size={20} className="text-blue-300" />
                    {selectedAlt === 0 ? 'Primary Route' : `Alternative ${selectedAlt}`}
                  </h3>

                  <div className="grid grid-cols-2 gap-4 mb-4">
                    {/* Distance */}
                    <div className="bg-slate-900/40 rounded-lg p-4 border border-blue-700/50">
                      <p className="text-xs text-blue-300 mb-1">Distance</p>
                      <p className="text-2xl font-bold text-white">
                        {Number.isFinite(displayRoute?.distance_km) ? Number(displayRoute.distance_km).toFixed(1) : '0.0'} <span className="text-sm">km</span>
                      </p>
                    </div>

                    {/* Duration */}
                    <div className="bg-slate-900/40 rounded-lg p-4 border border-blue-700/50">
                      <p className="text-xs text-blue-300 mb-1">Duration</p>
                      <p className="text-2xl font-bold text-white">
                        {Number.isFinite((displayRoute?.duration_seconds || 0) / 3600) ? (Number((displayRoute.duration_seconds || 0) / 3600)).toFixed(1) : '0.0'}
                        <span className="text-sm"> h</span>
                      </p>
                    </div>

                    {/* Fuel */}
                    <div className="bg-slate-900/40 rounded-lg p-4 border border-green-700/50">
                      <p className="text-xs text-green-300 mb-1">Fuel</p>
                      <p className="text-2xl font-bold text-white">
                        {Number.isFinite(displayRoute?.fuel_liters) ? Number(displayRoute.fuel_liters).toFixed(1) : '0.0'} <span className="text-sm">L</span>
                      </p>
                    </div>

                    {/* Cost */}
                    <div className="bg-slate-900/40 rounded-lg p-4 border border-green-700/50">
                      <p className="text-xs text-green-300 mb-1">Cost</p>
                      <p className="text-2xl font-bold text-white">
                        ${Number.isFinite(displayRoute?.estimated_cost) ? Number(displayRoute.estimated_cost).toFixed(2) : '0.00'}
                      </p>
                    </div>
                  </div>

                  {displayRoute.hazards && displayRoute.hazards.length > 0 && (
                    <div className="bg-yellow-900/20 border border-yellow-600 rounded-lg p-3 mt-4">
                      <p className="text-sm font-semibold text-yellow-300 mb-2">
                        ⚠️ {displayRoute.hazards.length} hazard{displayRoute.hazards.length !== 1 ? 's' : ''} detected
                      </p>
                      <ul className="text-xs text-yellow-200 space-y-1">
                        {displayRoute.hazards.slice(0, 3).map((h, i) => (
                          <li key={i}>
                            • {h.type.replace(/_/g, ' ')}: {h.recommendation}
                          </li>
                        ))}
                      </ul>
                    </div>
                  )}
                </div>

                {/* Alternative Routes */}
                {alternatives.length > 0 && (
                  <div className="bg-slate-800 rounded-xl shadow-xl p-6 border border-slate-700">
                    <h4 className="font-semibold text-white mb-3 flex items-center gap-2">
                      <TrendingDown size={18} className="text-purple-400" />
                      Alternative Routes
                    </h4>
                    <div className="space-y-2">
                      {alternatives.map((alt, idx) => (
                        <button
                          key={idx}
                          onClick={() => setSelectedAlt(idx + 1)}
                          className={`w-full text-left p-3 rounded-lg border transition ${
                            selectedAlt === idx + 1
                              ? 'bg-purple-900/40 border-purple-500'
                              : 'bg-slate-900/40 border-slate-600 hover:border-slate-500'
                          }`}
                        >
                          <div className="flex justify-between items-start">
                            <div>
                              <p className="font-semibold text-white text-sm">
                                {alt.reason || `Route ${idx + 1}`}
                              </p>
                              <p className="text-xs text-slate-400 mt-1">
                                {Number.isFinite(alt?.distance_km) ? Number(alt.distance_km).toFixed(1) : '0.0'} km • {Number.isFinite((alt?.duration_seconds || 0) / 3600) ? (Number((alt.duration_seconds || 0) / 3600)).toFixed(1) : '0.0'} h • {Number.isFinite(alt?.fuel_liters) ? Number(alt.fuel_liters).toFixed(1) : '0.0'} L
                              </p>
                            </div>
                            {selectedAlt === idx + 1 && (
                              <div className="text-purple-400">✓</div>
                            )}
                          </div>
                        </button>
                      ))}
                    </div>
                  </div>
                )}
              </div>
            ) : (
              <div className="bg-slate-800 rounded-xl shadow-xl p-12 border border-slate-700 text-center">
                <MapPin size={48} className="mx-auto text-slate-600 mb-4" />
                <p className="text-slate-400">
                  {error ? 'Error calculating route' : 'Enter route details and click "Calculate Route"'}
                </p>
              </div>
            )}
          </div>
        </div>

        {/* Route Details */}
        {displayRoute && displayRoute.segments && displayRoute.segments.length > 0 && (
          <div className="mt-6 bg-slate-800 rounded-xl shadow-xl p-6 border border-slate-700">
            <h3 className="text-lg font-bold text-white mb-4">Route Segments</h3>
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4 max-h-64 overflow-y-auto">
              {displayRoute.segments.slice(0, 9).map((seg, idx) => (
                <div
                  key={idx}
                  className="bg-slate-900/40 rounded-lg p-3 border border-slate-600"
                >
                  <p className="font-semibold text-white text-sm mb-1">{seg.name || `Segment ${idx + 1}`}</p>
                  <p className="text-xs text-slate-400">
                    {Number.isFinite(seg?.length_km) ? Number(seg.length_km).toFixed(1) : '0.0'} km @ {seg.speed_kmh} km/h
                  </p>
                </div>
              ))}
            </div>
          </div>
        )}
      </div>
    </div>
  );
}

export default SmartRoutePlanner;
