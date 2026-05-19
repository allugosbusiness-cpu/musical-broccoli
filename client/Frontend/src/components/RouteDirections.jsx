import { useEffect, useState } from 'react';
import axios from 'axios';

const getApiBase = () => {
  if (import.meta.env.MODE === 'development') return 'http://localhost:8000/api';
  return 'https://pulsetrack-back.onrender.com/api';
};

export default function RouteDirections({ truckId, truckPlate, onClose }) {
  const [directions, setDirections] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [expandedStep, setExpandedStep] = useState(null);

  useEffect(() => {
    const fetchDirections = async () => {
      try {
        setLoading(true);
        const response = await axios.get(
          `${getApiBase()}/v1/trucks/${truckId}/truck_trail_with_directions/`,
          { params: { limit: 300 } }
        );
        
        setDirections(response.data);
        setError(null);
      } catch (err) {
        console.error('Error fetching directions:', err);
        setError(err.response?.data?.error || 'Failed to load route directions');
      } finally {
        setLoading(false);
      }
    };

    if (truckId) {
      fetchDirections();
    }
  }, [truckId]);

  if (loading) {
    return (
      <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50">
        <div className="bg-white rounded-lg p-8 max-w-md w-full">
          <div className="text-center">
            <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-500 mx-auto mb-4"></div>
            <p className="text-gray-700">Loading route directions...</p>
          </div>
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50">
        <div className="bg-white rounded-lg p-8 max-w-md w-full">
          <div className="text-red-600 mb-4">
            <p className="font-bold">Error</p>
            <p className="text-sm">{error}</p>
          </div>
          <button
            onClick={onClose}
            className="w-full bg-gray-300 hover:bg-gray-400 text-gray-800 font-bold py-2 px-4 rounded"
          >
            Close
          </button>
        </div>
      </div>
    );
  }

  if (!directions) {
    return null;
  }

  // Handle both snapped and raw trail data
  const snappedPath = directions.snapped_path || directions.raw_trail || [];
  const turnInstructions = directions.turn_instructions || [];
  const distance = directions.total_distance_km || directions.distance_km || (snappedPath.length > 0 ? '~' : 0);
  const duration = directions.total_duration_hours || directions.duration_hours || 0;
  const pointCount = directions.raw_trail_count || snappedPath.length;
  const isSnapped = directions.snapped_path ? true : false;

  // Show empty state only if absolutely no data
  if (!snappedPath || snappedPath.length === 0) {
    return (
      <div className="fixed inset-0 bg-black/50 flex items-end z-50">
        <div className="bg-white w-full max-w-md rounded-t-2xl shadow-2xl p-6 h-auto">
          <div className="text-center">
            <p className="text-gray-700 mb-4">No trail data available yet for this truck</p>
            <button
              onClick={onClose}
              className="w-full bg-gray-300 hover:bg-gray-400 text-gray-800 font-bold py-2 px-4 rounded"
            >
              Close
            </button>
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className="fixed inset-0 bg-black/50 flex items-end z-50">
      <div className="bg-white w-full max-w-md rounded-t-2xl shadow-2xl flex flex-col h-[90vh]">
        {/* Header */}
        <div className="border-b border-gray-200 p-4 flex items-center justify-between bg-gradient-to-r from-blue-500 to-blue-600 text-white rounded-t-2xl">
          <div>
            <h2 className="font-bold text-lg">🚚 {truckPlate}</h2>
            <p className="text-sm opacity-90">Route Timeline & Directions</p>
          </div>
          <button
            onClick={onClose}
            className="text-white hover:bg-white/20 rounded-full p-2 transition-colors"
          >
            ✕
          </button>
        </div>

        {/* Route Summary */}
        <div className="bg-blue-50 border-b border-blue-200 p-4 space-y-2">
          <div className="flex justify-between items-center">
            <span className="text-sm text-gray-700">📍 Distance Travelled</span>
            <span className="font-bold text-blue-600">{typeof distance === 'string' ? distance : Number.isFinite(distance) ? Number(distance).toFixed(1) : '0.0'} km</span>
          </div>
          <div className="flex justify-between items-center">
            <span className="text-sm text-gray-700">⏱️ Duration</span>
            <span className="font-bold text-blue-600">{Number.isFinite(duration) ? Number(duration).toFixed(1) : '0.0'}h</span>
          </div>
          <div className="flex justify-between items-center">
            <span className="text-sm text-gray-700">📡 GPS Points</span>
            <span className="font-bold text-blue-600">{pointCount} recorded</span>
          </div>
          {isSnapped && (
            <div className="text-xs text-green-600 bg-green-50 p-2 rounded border border-green-200">
              ✓ Snapped to actual roads using OSRM
            </div>
          )}
          {!isSnapped && snappedPath.length > 0 && (
            <div className="text-xs text-amber-600 bg-amber-50 p-2 rounded border border-amber-200">
              ℹ️ Displaying raw GPS trail (snapping unavailable)
            </div>
          )}
        </div>

        {/* Turn-by-Turn Directions / GPS Trail */}
        <div className="flex-1 overflow-y-auto">
          {turnInstructions && turnInstructions.length > 0 ? (
            <div className="p-4 space-y-3">
              <h3 className="font-bold text-gray-800 sticky top-0 bg-white py-2 border-b">
                📋 {turnInstructions.length} Turn Instructions
              </h3>
              
              {turnInstructions.map((instruction, idx) => (
                <div
                  key={idx}
                  className="border border-gray-200 rounded-lg p-3 hover:bg-blue-50 cursor-pointer transition-colors"
                  onClick={() => setExpandedStep(expandedStep === idx ? null : idx)}
                >
                  <div className="flex items-start gap-3">
                    <div className="flex-shrink-0 w-8 h-8 bg-blue-500 text-white rounded-full flex items-center justify-center font-bold text-sm">
                      {idx + 1}
                    </div>
                    <div className="flex-1 min-w-0">
                      <p className="text-sm font-semibold text-gray-800 line-clamp-2">
                        {instruction.instruction}
                      </p>
                      <div className="flex gap-4 mt-1 text-xs text-gray-600">
                        <span className="flex items-center gap-1">
                          <span className="text-lg">📏</span>
                          {Number.isFinite(instruction.distance_km) ? Number(instruction.distance_km).toFixed(1) : '0.0'} km
                        </span>
                        <span className="flex items-center gap-1">
                          <span className="text-lg">⏱️</span>
                          {Math.round(instruction.duration_seconds / 60)} min
                        </span>
                      </div>
                    </div>
                    <div className="flex-shrink-0 text-gray-400">
                      {expandedStep === idx ? '▼' : '▶'}
                    </div>
                  </div>

                  {expandedStep === idx && (
                    <div className="mt-2 pt-2 border-t border-gray-200 text-xs text-gray-600 bg-gray-50 p-2 rounded">
                      <p className="line-break">{instruction.instruction}</p>
                      <div className="grid grid-cols-2 gap-2 mt-2">
                        <div>
                          <span className="text-gray-500">Distance:</span>
                          <p className="font-mono">{instruction.distance_m}m</p>
                        </div>
                        <div>
                          <span className="text-gray-500">Time:</span>
                          <p className="font-mono">{instruction.duration_seconds}s</p>
                        </div>
                      </div>
                    </div>
                  )}
                </div>
              ))}
            </div>
          ) : snappedPath && snappedPath.length > 0 ? (
            <div className="p-4 space-y-3">
              <h3 className="font-bold text-gray-800 sticky top-0 bg-white py-2 border-b">
                📍 GPS Trail ({snappedPath.length} points)
              </h3>
              <p className="text-xs text-amber-600 bg-amber-50 p-2 rounded border border-amber-200">
                Turn-by-turn directions not available. Showing raw GPS coordinates.
              </p>
              {snappedPath.slice(0, 30).map((point, idx) => (
                <div key={idx} className="bg-gray-50 p-2 rounded text-xs border border-gray-200 font-mono">
                  <div className="font-bold text-gray-700">📍 Point {idx + 1}</div>
                  <div className="text-gray-600">{Number.isFinite(point.lat) ? Number(point.lat).toFixed(6) : 'N/A'}, {Number.isFinite(point.lng) ? Number(point.lng).toFixed(6) : 'N/A'}</div>
                </div>
              ))}
              {snappedPath.length > 30 && (
                <div className="text-xs text-gray-500 text-center py-2 bg-gray-50 rounded border border-gray-200">
                  ... and {snappedPath.length - 30} more points
                </div>
              )}
            </div>
          ) : (
            <div className="p-4 text-center text-gray-500">
              <p className="text-sm">No trail data available</p>
              <p className="text-xs text-gray-400 mt-1">Try selecting another truck</p>
            </div>
          )}
        </div>

        {/* Footer */}
        <div className="border-t border-gray-200 p-4 bg-gray-50 space-y-2">
          <button
            onClick={onClose}
            className="w-full bg-blue-600 hover:bg-blue-700 text-white font-bold py-2 px-4 rounded-lg transition-colors"
          >
            Close Directions
          </button>
          <p className="text-xs text-gray-500 text-center">
            💡 Tap any instruction to view details
          </p>
        </div>
      </div>
    </div>
  );
}
