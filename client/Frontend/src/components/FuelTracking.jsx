import { useState, useEffect } from 'react';
import { Zap, AlertTriangle, TrendingDown, Gauge, Droplet, MapPin } from 'lucide-react';
import { getTrucks } from '../services/api';

/**
 * FuelTracking Component
 * Displays real-time fuel consumption with realistic calculations
 * Based on terrain, speed, load, and weather factors
 */
export default function FuelTracking({ refreshTrigger = 0 }) {
  const [selectedTruck, setSelectedTruck] = useState(null);
  const [trucks, setTrucks] = useState([]);
  const [fuelData, setFuelData] = useState(null);
  const [consumptionHistory, setConsumptionHistory] = useState([]);
  const [loading, setLoading] = useState(true);
  const [activeTab, setActiveTab] = useState('overview');

  useEffect(() => {
    const fetchTrucks = async () => {
      try {
        const data = await getTrucks();
        setTrucks(Array.isArray(data) ? data : []);
        if (Array.isArray(data) && data.length > 0) {
          setSelectedTruck(data[0]);
        }
      } catch (error) {
        console.error('Error fetching trucks:', error);
      } finally {
        setLoading(false);
      }
    };

    fetchTrucks();
    const interval = setInterval(fetchTrucks, 10000);
    return () => clearInterval(interval);
  }, [refreshTrigger]);

  // Simulate fuel consumption based on truck movement
  useEffect(() => {
    if (!selectedTruck) return;

    // Calculate realistic fuel consumption
    const calculateFuelConsumption = () => {
      const baseConsumption = 10; // L/100km for medium truck
      const speed = selectedTruck.speed || 0;
      const distance = selectedTruck.distance_travelled || 0;

      // Speed factor (optimal at 80-90 km/h)
      let speedFactor = 1.0;
      if (speed < 20) {
        speedFactor = 1.8;
      } else if (speed < 50) {
        speedFactor = 1.3;
      } else if (speed <= 90) {
        speedFactor = 0.9;
      } else if (speed <= 120) {
        speedFactor = 1.0 + (speed - 90) * 0.02;
      } else {
        speedFactor = 1.6;
      }

      // Load factor (50% default load)
      const loadFactor = 1.5; // Assuming medium load

      // Terrain factor (simulate elevation)
      const terrainFactor = 1.2;

      // Weather factor
      const weatherFactor = 1.0;

      const consumption =
        ((distance / 100) * baseConsumption * speedFactor * loadFactor * terrainFactor * weatherFactor) || 0;

      // Tank capacity: 100L for medium truck
      const tankCapacity = 100;
      const currentFuel = Math.max(0, tankCapacity - consumption);
      const fuelPercent = (currentFuel / tankCapacity) * 100;
      const efficiency = distance > 0 ? distance / (consumption || 1) : 0;
      const range = currentFuel * efficiency;

      return {
        currentFuel: Math.round(currentFuel * 10) / 10,
        tankCapacity: tankCapacity,
        fuelPercent: Math.round(fuelPercent * 10) / 10,
        consumption: Math.round(consumption * 10) / 10,
        efficiency: Math.round(efficiency * 100) / 100,
        range: Math.round(range),
        speedFactor: Math.round(speedFactor * 100) / 100,
        loadFactor: Math.round(loadFactor * 100) / 100,
        terrainFactor: Math.round(terrainFactor * 100) / 100,
      };
    };

    const data = calculateFuelConsumption();
    setFuelData(data);

    // Add to history
    setConsumptionHistory((prev) => [
      ...prev.slice(-19),
      {
        time: new Date().toLocaleTimeString(),
        fuel: data.currentFuel,
        efficiency: data.efficiency,
      },
    ]);
  }, [selectedTruck]);

  const getFuelStatus = () => {
    if (!fuelData) return { status: 'unknown', color: 'gray' };
    if (fuelData.fuelPercent < 10) return { status: 'critical', color: 'red' };
    if (fuelData.fuelPercent < 25) return { status: 'low', color: 'amber' };
    if (fuelData.fuelPercent < 50) return { status: 'warning', color: 'yellow' };
    return { status: 'normal', color: 'green' };
  };

  const fuelStatus = getFuelStatus();

  if (loading) {
    return (
      <div className="w-full p-6 bg-white rounded-lg shadow-sm">
        <div className="flex items-center justify-center h-64">
          <p className="text-gray-500">Loading fuel data...</p>
        </div>
      </div>
    );
  }

  return (
    <div className="w-full bg-white rounded-lg shadow-sm">
      {/* Header */}
      <div className="px-6 py-4 border-b border-gray-200">
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-3">
            <Droplet className="w-6 h-6 text-blue-600" />
            <h2 className="text-lg font-semibold text-gray-900">Fuel Tracking System</h2>
          </div>
          <select
            value={selectedTruck?.id || ''}
            onChange={(e) => setSelectedTruck(trucks.find((t) => t.id === e.target.value))}
            className="px-3 py-2 bg-white border border-gray-300 rounded-lg text-sm text-gray-900 focus:outline-none focus:ring-2 focus:ring-blue-500"
          >
            <option value="">Select a truck</option>
            {trucks.map((truck) => (
              <option key={truck.id} value={truck.id}>
                {truck.id} - {truck.plate} ({truck.driver})
              </option>
            ))}
          </select>
        </div>
      </div>

      {/* Tabs */}
      <div className="flex border-b border-gray-200">
        <button
          onClick={() => setActiveTab('overview')}
          className={`flex-1 px-4 py-3 text-sm font-medium border-b-2 transition-colors ${
            activeTab === 'overview'
              ? 'border-blue-600 text-blue-600'
              : 'border-transparent text-gray-600 hover:text-gray-900'
          }`}
        >
          Overview
        </button>
        <button
          onClick={() => setActiveTab('details')}
          className={`flex-1 px-4 py-3 text-sm font-medium border-b-2 transition-colors ${
            activeTab === 'details'
              ? 'border-blue-600 text-blue-600'
              : 'border-transparent text-gray-600 hover:text-gray-900'
          }`}
        >
          Consumption Details
        </button>
        <button
          onClick={() => setActiveTab('history')}
          className={`flex-1 px-4 py-3 text-sm font-medium border-b-2 transition-colors ${
            activeTab === 'history'
              ? 'border-blue-600 text-blue-600'
              : 'border-transparent text-gray-600 hover:text-gray-900'
          }`}
        >
          History
        </button>
      </div>

      {/* Content */}
      <div className="p-6">
        {!selectedTruck ? (
          <div className="text-center py-8">
            <p className="text-gray-500">Select a truck to view fuel data</p>
          </div>
        ) : activeTab === 'overview' ? (
          // Overview Tab
          <div className="space-y-6">
            {/* Fuel Gauge */}
            <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
              {/* Main Fuel Indicator */}
              <div className="space-y-4">
                <h3 className="text-sm font-semibold text-gray-700">Current Fuel Level</h3>
                <div className="flex flex-col items-center justify-center py-8 bg-gray-50 rounded-lg">
                  <div className="relative w-32 h-32 mb-4">
                    <svg className="w-full h-full" viewBox="0 0 200 200">
                      {/* Background circle */}
                      <circle cx="100" cy="100" r="90" fill="none" stroke="#e5e7eb" strokeWidth="12" />
                      {/* Fuel circle */}
                      <circle
                        cx="100"
                        cy="100"
                        r="90"
                        fill="none"
                        stroke={`var(--color-${fuelStatus.color})`}
                        strokeWidth="12"
                        strokeDasharray={`${(fuelData?.fuelPercent || 0) * 5.65} 565`}
                        className={`transition-all duration-300 stroke-${fuelStatus.color}-500`}
                        style={{
                          stroke:
                            fuelStatus.color === 'red'
                              ? '#ef4444'
                              : fuelStatus.color === 'amber'
                              ? '#f59e0b'
                              : fuelStatus.color === 'yellow'
                              ? '#eab308'
                              : '#10b981',
                        }}
                      />
                    </svg>
                    <div className="absolute inset-0 flex flex-col items-center justify-center">
                      <span className="text-2xl font-bold text-gray-900">
                        {Number.isFinite(fuelData?.fuelPercent) ? Number(fuelData.fuelPercent).toFixed(1) : '0.0'}%
                      </span>
                      <span className="text-xs text-gray-600">{fuelData?.currentFuel}L</span>
                    </div>
                  </div>
                  <div className="text-center">
                    <p className="text-sm font-medium text-gray-900 capitalize">
                      Status: <span className={`text-${fuelStatus.color}-600`}>{fuelStatus.status}</span>
                    </p>
                    <p className="text-xs text-gray-600 mt-1">Tank: {fuelData?.tankCapacity}L</p>
                  </div>
                </div>
              </div>

              {/* Key Metrics */}
              <div className="space-y-4">
                <h3 className="text-sm font-semibold text-gray-700">Key Metrics</h3>
                <div className="space-y-3">
                  {/* Efficiency */}
                  <div className="flex items-start gap-3 p-3 bg-gray-50 rounded-lg">
                    <Gauge className="w-5 h-5 text-blue-600 mt-0.5 flex-shrink-0" />
                    <div>
                      <p className="text-xs text-gray-600">Fuel Efficiency</p>
                      <p className="text-lg font-bold text-gray-900">
                        {Number.isFinite(fuelData?.efficiency) ? Number(fuelData.efficiency).toFixed(2) : '0.00'} km/L
                      </p>
                      <p className="text-xs text-gray-500 mt-0.5">
                        ~{Number.isFinite(fuelData?.efficiency) ? (Number(fuelData.efficiency) * 2.352).toFixed(1) : '0.0'} MPG
                      </p>
                    </div>
                  </div>

                  {/* Estimated Range */}
                  <div className="flex items-start gap-3 p-3 bg-gray-50 rounded-lg">
                    <MapPin className="w-5 h-5 text-green-600 mt-0.5 flex-shrink-0" />
                    <div>
                      <p className="text-xs text-gray-600">Estimated Range</p>
                      <p className="text-lg font-bold text-gray-900">{fuelData?.range} km</p>
                      <p className="text-xs text-gray-500 mt-0.5">At current consumption rate</p>
                    </div>
                  </div>

                  {/* Consumption */}
                  <div className="flex items-start gap-3 p-3 bg-gray-50 rounded-lg">
                    <TrendingDown className="w-5 h-5 text-amber-600 mt-0.5 flex-shrink-0" />
                    <div>
                      <p className="text-xs text-gray-600">Total Consumption</p>
                      <p className="text-lg font-bold text-gray-900">{fuelData?.consumption}L</p>
                      <p className="text-xs text-gray-500 mt-0.5">
                        {selectedTruck?.distance_travelled}km traveled
                      </p>
                    </div>
                  </div>

                  {/* Speed */}
                  <div className="flex items-start gap-3 p-3 bg-gray-50 rounded-lg">
                    <Zap className="w-5 h-5 text-purple-600 mt-0.5 flex-shrink-0" />
                    <div>
                      <p className="text-xs text-gray-600">Current Speed</p>
                      <p className="text-lg font-bold text-gray-900">{selectedTruck?.speed} km/h</p>
                      <p className="text-xs text-gray-500 mt-0.5">Speed factor: {fuelData?.speedFactor}x</p>
                    </div>
                  </div>
                </div>
              </div>
            </div>

            {/* Alerts */}
            {fuelStatus.status !== 'normal' && (
              <div
                className={`flex gap-3 p-4 rounded-lg border-l-4 ${
                  fuelStatus.color === 'red'
                    ? 'bg-red-50 border-red-400'
                    : fuelStatus.color === 'amber'
                    ? 'bg-amber-50 border-amber-400'
                    : 'bg-yellow-50 border-yellow-400'
                }`}
              >
                <AlertTriangle
                  className={`w-5 h-5 flex-shrink-0 mt-0.5 ${
                    fuelStatus.color === 'red'
                      ? 'text-red-600'
                      : fuelStatus.color === 'amber'
                      ? 'text-amber-600'
                      : 'text-yellow-600'
                  }`}
                />
                <div>
                  <p
                    className={`font-medium ${
                      fuelStatus.color === 'red'
                        ? 'text-red-900'
                        : fuelStatus.color === 'amber'
                        ? 'text-amber-900'
                        : 'text-yellow-900'
                    }`}
                  >
                    {fuelStatus.status === 'critical'
                      ? 'CRITICAL: Refuel immediately!'
                      : fuelStatus.status === 'low'
                      ? 'Low fuel level detected'
                      : 'Fuel warning'}
                  </p>
                  <p
                    className={`text-sm mt-1 ${
                      fuelStatus.color === 'red'
                        ? 'text-red-800'
                        : fuelStatus.color === 'amber'
                        ? 'text-amber-800'
                        : 'text-yellow-800'
                    }`}
                  >
                    Current range: {fuelData?.range} km
                  </p>
                </div>
              </div>
            )}
          </div>
        ) : activeTab === 'details' ? (
          // Details Tab
          <div className="space-y-4">
            <h3 className="text-sm font-semibold text-gray-700">Consumption Factors</h3>
            <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
              <div className="p-4 bg-gradient-to-br from-blue-50 to-blue-100 rounded-lg">
                <p className="text-xs text-blue-700 font-medium">Speed Factor</p>
                <p className="text-2xl font-bold text-blue-900 mt-2">{fuelData?.speedFactor}x</p>
              </div>
              <div className="p-4 bg-gradient-to-br from-amber-50 to-amber-100 rounded-lg">
                <p className="text-xs text-amber-700 font-medium">Load Factor</p>
                <p className="text-2xl font-bold text-amber-900 mt-2">{fuelData?.loadFactor}x</p>
              </div>
              <div className="p-4 bg-gradient-to-br from-green-50 to-green-100 rounded-lg">
                <p className="text-xs text-green-700 font-medium">Terrain Factor</p>
                <p className="text-2xl font-bold text-green-900 mt-2">{fuelData?.terrainFactor}x</p>
              </div>
              <div className="p-4 bg-gradient-to-br from-purple-50 to-purple-100 rounded-lg">
                <p className="text-xs text-purple-700 font-medium">Weather Factor</p>
                <p className="text-2xl font-bold text-purple-900 mt-2">1.0x</p>
              </div>
            </div>

            <h3 className="text-sm font-semibold text-gray-700 mt-6">Consumption Breakdown</h3>
            <div className="space-y-2">
              <div className="flex justify-between items-center p-3 bg-gray-50 rounded">
                <span className="text-sm text-gray-600">Base consumption (L/100km)</span>
                <span className="font-medium text-gray-900">10.0L</span>
              </div>
              <div className="flex justify-between items-center p-3 bg-gray-50 rounded">
                <span className="text-sm text-gray-600">Speed impact</span>
                <span className="font-medium text-gray-900">{(fuelData?.speedFactor - 1) * 100}%</span>
              </div>
              <div className="flex justify-between items-center p-3 bg-gray-50 rounded">
                <span className="text-sm text-gray-600">Load impact</span>
                <span className="font-medium text-gray-900">{(fuelData?.loadFactor - 1) * 100}%</span>
              </div>
              <div className="flex justify-between items-center p-3 bg-gray-50 rounded">
                <span className="text-sm text-gray-600">Terrain impact</span>
                <span className="font-medium text-gray-900">{(fuelData?.terrainFactor - 1) * 100}%</span>
              </div>
            </div>
          </div>
        ) : (
          // History Tab
          <div className="space-y-4">
            <h3 className="text-sm font-semibold text-gray-700">Consumption History (Last 20 readings)</h3>
            <div className="overflow-x-auto">
              <table className="w-full text-sm">
                <thead>
                  <tr className="border-b border-gray-200">
                    <th className="text-left px-4 py-2 text-gray-700 font-medium">Time</th>
                    <th className="text-left px-4 py-2 text-gray-700 font-medium">Fuel (L)</th>
                    <th className="text-left px-4 py-2 text-gray-700 font-medium">Efficiency (km/L)</th>
                  </tr>
                </thead>
                <tbody>
                  {consumptionHistory.map((record, idx) => (
                    <tr key={idx} className="border-b border-gray-100 hover:bg-gray-50">
                      <td className="px-4 py-2 text-gray-900">{record.time}</td>
                      <td className="px-4 py-2 text-gray-900 font-medium">{record.fuel}L</td>
                      <td className="px-4 py-2 text-gray-900">{Number.isFinite(record.efficiency) ? Number(record.efficiency).toFixed(2) : '0.00'} km/L</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </div>
        )}
      </div>
    </div>
  );
}
