import { useState, useEffect } from 'react';
import axios from 'axios';

const getApiBase = () => {
  if (import.meta.env.MODE === 'development') return 'http://localhost:8000/api';
  return 'https://pulsetrack-back.onrender.com/api';
};

/**
 * TruckLocationSpeedWidget Component
 * Displays real-time location and speed of all trucks
 * Updates every 5 seconds
 */
export default function TruckLocationSpeedWidget() {
  const [trucks, setTrucks] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [lastUpdate, setLastUpdate] = useState(null);

  // Fetch truck locations every 3 seconds from real-time tracking endpoint
  useEffect(() => {
    const fetchLocations = async () => {
      try {
        setLoading(true);
        const response = await axios.get(
          `${getApiBase()}/v1/truck-tracking/all-locations/`
        );

        if (response.data.trucks) {
          setTrucks(response.data.trucks);
          setLastUpdate(new Date());
          setError(null);
        } else if (response.data.results) {
          setTrucks(response.data.results);
          setLastUpdate(new Date());
          setError(null);
        } else if (Array.isArray(response.data)) {
          setTrucks(response.data);
          setLastUpdate(new Date());
          setError(null);
        }
      } catch (err) {
        console.error('❌ Error fetching truck locations:', err);
        setError('Failed to fetch truck locations');
      } finally {
        setLoading(false);
      }
    };

    fetchLocations();
    const interval = setInterval(fetchLocations, 3000); // Update every 3 seconds for real-time

    return () => clearInterval(interval);
  }, []);

  const getSpeedColor = (speed) => {
    if (speed === 0) return 'text-gray-400'; // Idle
    if (speed < 30) return 'text-blue-400'; // Slow
    if (speed < 60) return 'text-green-400'; // Normal
    if (speed < 100) return 'text-yellow-400'; // Fast
    return 'text-red-400'; // Very fast/speeding
  };

  const getStatusIcon = (status, speed) => {
    if (status === 'idle') return '🛑';
    if (speed === 0) return '⏸️';
    return '🚗';
  };

  return (
    <div className="bg-slate-900 border border-slate-700 rounded-lg p-6">
      <div className="flex justify-between items-center mb-4">
        <h2 className="text-lg font-bold text-white">📍 Truck Locations & Speed</h2>
        <div className="text-xs text-slate-400">
          {lastUpdate ? `Last update: ${lastUpdate.toLocaleTimeString()}` : 'Loading...'}
        </div>
      </div>

      {error && (
        <div className="bg-red-900/30 border border-red-600 rounded p-3 text-red-300 mb-4">
          ⚠️ {error}
        </div>
      )}

      {loading && trucks.length === 0 ? (
        <div className="text-slate-400 text-center py-8">Loading truck locations...</div>
      ) : (
        <div className="space-y-3 max-h-96 overflow-y-auto">
          {trucks.map((truck) => (
            <div
              key={truck.truck_id}
              className="bg-slate-800 border border-slate-700 rounded p-3 hover:border-blue-500 transition"
            >
              <div className="flex justify-between items-start">
                {/* Left: Truck Info */}
                <div className="flex-1">
                  <div className="flex items-center gap-2 mb-1">
                    <span className="text-xl">
                      {getStatusIcon(truck.status, truck.speed_kmh)}
                    </span>
                    <div>
                      <p className="font-bold text-white">
                        {truck.truck_identifier}
                      </p>
                      <p className="text-xs text-slate-400">📋 {truck.plate}</p>
                    </div>
                  </div>

                  {/* Status */}
                  <div className="text-xs mt-2">
                    <span
                      className={`inline-block px-2 py-1 rounded ${
                        truck.status === 'enroute'
                          ? 'bg-green-900/40 text-green-300'
                          : truck.status === 'idle'
                          ? 'bg-gray-900/40 text-gray-300'
                          : 'bg-yellow-900/40 text-yellow-300'
                      }`}
                    >
                      {truck.status.toUpperCase()}
                    </span>
                  </div>
                </div>

                {/* Right: Location & Speed */}
                <div className="text-right">
                  {/* Speed */}
                  <div className="mb-2">
                    <p className={`text-2xl font-bold ${getSpeedColor(truck.speed)}`}>
                      {Number.isFinite(truck.speed) ? Number(truck.speed).toFixed(1) : '0.0'}
                    </p>
                    <p className="text-xs text-slate-400">km/h</p>
                  </div>

                  {/* Coordinates */}
                  {Number.isFinite(truck.latitude) && Number.isFinite(truck.longitude) ? (
                    <div className="text-xs text-slate-400">
                      <p>
                        📍 {Number(truck.latitude).toFixed(3)}, {Number(truck.longitude).toFixed(3)}
                      </p>
                      <p className="text-xs text-slate-500 mt-1">
                        {truck.timestamp
                          ? new Date(truck.timestamp).toLocaleTimeString()
                          : 'No data'}
                      </p>
                    </div>
                  ) : (
                    <div className="text-xs text-slate-500">No location data</div>
                  )}
                </div>
              </div>

              {/* Speed Indicator Bar */}
              {truck.speed_kmh > 0 && (
                <div className="mt-3 bg-slate-700 rounded-full h-1 overflow-hidden">
                  <div
                    className={`h-full transition-all ${
                      truck.speed_kmh < 30
                        ? 'bg-blue-500'
                        : truck.speed_kmh < 60
                        ? 'bg-green-500'
                        : truck.speed_kmh < 100
                        ? 'bg-yellow-500'
                        : 'bg-red-500'
                    }`}
                    style={{
                      width: `${Math.min((truck.speed_kmh / 120) * 100, 100)}%`,
                    }}
                  ></div>
                </div>
              )}
            </div>
          ))}

          {trucks.length === 0 && (
            <div className="text-slate-400 text-center py-8">
              No trucks with location data available
            </div>
          )}
        </div>
      )}

      {/* Summary Stats */}
      <div className="mt-4 pt-4 border-t border-slate-700 grid grid-cols-3 gap-2 text-sm">
        <div>
          <p className="text-slate-400">Total Trucks</p>
          <p className="text-lg font-bold text-white">{trucks.length}</p>
        </div>
        <div>
          <p className="text-slate-400">In Motion</p>
          <p className="text-lg font-bold text-green-400">
            {trucks.filter((t) => t.speed_kmh > 0).length}
          </p>
        </div>
        <div>
          <p className="text-slate-400">Avg Speed</p>
          <p className="text-lg font-bold text-blue-400">
            {trucks.length > 0
              ? Number.isFinite(
                  trucks.reduce((sum, t) => sum + (Number.isFinite(t.speed_kmh) ? t.speed_kmh : 0), 0) /
                  trucks.length
                ) ? (
                  (
                    trucks.reduce((sum, t) => sum + (Number.isFinite(t.speed_kmh) ? t.speed_kmh : 0), 0) /
                    trucks.length
                  ).toFixed(1)
                ) : '0.0'
              : '0'}{' '}
            km/h
          </p>
        </div>
      </div>
    </div>
  );
}
