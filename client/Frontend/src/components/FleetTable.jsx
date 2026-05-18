import { useState, useEffect, useMemo } from "react";
import { Navigation, AlertTriangle, Square, CheckCircle, Zap } from "lucide-react";
import { getDashboardTrucks } from "../services/api";
import { reverseGeocode } from "../services/geocoding";

function StatusPill({ status }) {
  // Map v2 status values to display configs
  const statusMap = {
    'moving': 'moving',
    'delayed': 'delayed',
    'stopped': 'stopped',
    'delivered': 'delivered',
    'enroute': 'moving',  // Map v2 'enroute' to 'moving'
    'idle': 'stopped',    // Map v2 'idle' to 'stopped'
    'maintenance': 'delayed',
    'decommissioned': 'delivered',
  };
  
  const displayStatus = statusMap[status] || status;
  
  const configs = {
    moving: { bg: 'bg-blue-900/30', border: 'border-blue-700/50', text: 'text-blue-300', Icon: Navigation, label: 'Moving' },
    delayed: { bg: 'bg-amber-900/30', border: 'border-amber-700/50', text: 'text-amber-300', Icon: Zap, label: 'Delayed' },
    stopped: { bg: 'bg-red-900/30', border: 'border-red-700/50', text: 'text-red-300', Icon: AlertTriangle, label: 'Stopped' },
    delivered: { bg: 'bg-purple-900/30', border: 'border-purple-700/50', text: 'text-purple-300', Icon: CheckCircle, label: 'Delivered' },
  };
  const config = configs[displayStatus] || configs.delivered;

  return (
    <span className={`inline-flex items-center gap-1 px-2.5 py-1 rounded-lg text-xs font-semibold border ${config.bg} ${config.border} ${config.text}`}>
      <config.Icon size={12} />
      {config.label}
    </span>
  );
}

function ProgressBar({ progress, status }) {
  const colors = {
    delivered: 'bg-purple-500',
    stopped: 'bg-red-500',
    delayed: 'bg-amber-500',
    moving: 'bg-blue-500',
  };

  return (
    <div className="flex items-center gap-2">
      <div className="w-16 h-1.5 bg-slate-700 rounded-full overflow-hidden border border-slate-600">
        <div
          className={`h-full rounded-full transition-all duration-500 ${colors[status] || 'bg-blue-500'}`}
          style={{ width: `${progress}%` }}
        ></div>
      </div>
      <span className="text-xs text-slate-400 font-mono w-8">{progress}%</span>
    </div>
  );
}

export default function FleetTable({ onTruckSelect, highlightedTruck = null, refreshTrigger = 0 }) {
  const [trucks, setTrucks] = useState([]);
  const [filter, setFilter] = useState('all');
  const [loading, setLoading] = useState(true);
  const [page, setPage] = useState(1);
  const [addresses, setAddresses] = useState({}); // Cache for addresses
  const [apiDebug, setApiDebug] = useState(null); // For debugging
  const ITEMS_PER_PAGE = 10;

  useEffect(() => {
    const fetchTrucks = async () => {
      try {
        console.log('🚚 FleetTable: Fetching trucks...');
        // First, let's test the API directly
        try {
          const testResponse = await fetch('https://pulsetrack-back.onrender.com/api/v1/dashboard/trucks/');
          console.log('🚚 Direct fetch test status:', testResponse.status);
          const testData = await testResponse.json();
          console.log('🚚 Direct fetch data:', testData);
          setApiDebug({ status: testResponse.status, dataLength: Array.isArray(testData) ? testData.length : 'not array' });
        } catch (fetchError) {
          console.error('🚚 Direct fetch error:', fetchError);
          setApiDebug({ error: fetchError.message });
        }
        
        const data = await getDashboardTrucks();
        console.log('🚚 FleetTable: Received data:', data);
        const trucksData = Array.isArray(data) ? data.slice(0, 50) : [];
        console.log('🚚 FleetTable: Processed trucks:', trucksData.length, 'trucks');
        
        // Geocode all truck locations
        const addressMap = {};
        for (const truck of trucksData) {
          if (truck.location && truck.location.lat && truck.location.lon) {
            try {
              const address = await reverseGeocode(truck.location.lat, truck.location.lon);
              addressMap[truck.truck_identifier] = address;
            } catch (error) {
              console.error(`Failed to geocode ${truck.truck_identifier}:`, error);
              addressMap[truck.truck_identifier] = (Number.isFinite(truck.location?.lat) && Number.isFinite(truck.location?.lon)) ? `${Number(truck.location.lat).toFixed(3)}, ${Number(truck.location.lon).toFixed(3)}` : 'No coords';
            }
          }
        }
        setAddresses(addressMap);
        setTrucks(trucksData);
        setPage(1);
      } catch (error) {
        console.error('Failed to fetch trucks:', error);
      } finally {
        setLoading(false);
      }
    };

    fetchTrucks();
    const interval = setInterval(fetchTrucks, 30000);
    return () => clearInterval(interval);
  }, [refreshTrigger]);

  // Memoize filtered and paginated trucks
  const filteredAndPaginatedTrucks = useMemo(() => {
    // Map v2 status values to filter status values
    const statusMap = {
      'enroute': 'moving',
      'idle': 'stopped',
      'maintenance': 'delayed',
      'decommissioned': 'delivered',
    };
    
    const filtered = filter === 'all' ? trucks : trucks.filter(t => {
      const displayStatus = statusMap[t.status] || t.status;
      return displayStatus === filter;
    });
    const startIdx = (page - 1) * ITEMS_PER_PAGE;
    return filtered.slice(startIdx, startIdx + ITEMS_PER_PAGE);
  }, [trucks, filter, page]);

  const filteredTrucks = useMemo(() => {
    const statusMap = {
      'enroute': 'moving',
      'idle': 'stopped',
      'maintenance': 'delayed',
      'decommissioned': 'delivered',
    };
    
    return filter === 'all' ? trucks : trucks.filter(t => {
      const displayStatus = statusMap[t.status] || t.status;
      return displayStatus === filter;
    });
  }, [trucks, filter]);

  const totalPages = Math.ceil(filteredTrucks.length / ITEMS_PER_PAGE);

  const filterButtons = [
    { key: 'all', label: 'All', count: trucks.length },
    { key: 'moving', label: 'Moving', count: trucks.filter(t => t.status === 'moving').length },
    { key: 'delayed', label: 'Delayed', count: trucks.filter(t => t.status === 'delayed').length },
    { key: 'stopped', label: 'Stopped', count: trucks.filter(t => t.status === 'stopped').length },
    { key: 'delivered', label: 'Delivered', count: trucks.filter(t => t.status === 'delivered').length },
  ];

  return (
    <div className="bg-slate-900/50 border border-slate-700/50 rounded-xl overflow-hidden shadow-lg backdrop-blur-sm">
      <div className="px-6 py-5 border-b border-slate-700/50 flex items-center justify-between bg-gradient-to-r from-slate-900 to-slate-800/50">
        <h2 className="text-sm font-bold text-slate-100 uppercase tracking-widest">Fleet Overview ({trucks.length})</h2>
        <div className="flex gap-2 flex-wrap">
          {filterButtons.map(btn => (
            <button
              key={btn.key}
              onClick={() => { setFilter(btn.key); setPage(1); }}
              className={`px-3 py-1.5 text-xs font-semibold rounded-lg border transition-all ${
                filter === btn.key
                  ? 'bg-gradient-to-r from-blue-600 to-blue-500 border-blue-400/50 text-white shadow-lg'
                  : 'bg-slate-800/50 border-slate-600/50 text-slate-300 hover:bg-slate-700/50'
              }`}
            >
              {btn.label} ({btn.count})
            </button>
          ))}
        </div>
      </div>

      {/* Debug Info */}
      {apiDebug && (
        <div className="px-6 py-3 bg-slate-800/50 border-b border-slate-700/30 text-xs text-slate-400">
          {apiDebug.error ? (
            <span>❌ API Error: {apiDebug.error}</span>
          ) : (
            <span>✅ API Status: {apiDebug.status}, Data: {apiDebug.dataLength} items</span>
          )}
        </div>
      )}

      <div className="overflow-x-auto">
        <table className="w-full text-sm">
          <thead className="bg-slate-800/50 border-b border-slate-700/50 sticky top-0">
            <tr>
              <th className="px-4 py-3 text-left font-semibold text-slate-300 text-xs uppercase tracking-widest">ID</th>
              <th className="px-4 py-3 text-left font-semibold text-slate-300 text-xs uppercase tracking-widest">Plate</th>
              <th className="px-4 py-3 text-left font-semibold text-slate-300 text-xs uppercase tracking-widest">Driver</th>
              <th className="px-4 py-3 text-left font-semibold text-slate-300 text-xs uppercase tracking-widest">Status</th>
              <th className="px-4 py-3 text-left font-semibold text-slate-300 text-xs uppercase tracking-widest">Location</th>
              <th className="px-4 py-3 text-left font-semibold text-slate-300 text-xs uppercase tracking-widest">Speed</th>
              <th className="px-4 py-3 text-left font-semibold text-slate-300 text-xs uppercase tracking-widest">ETA</th>
              <th className="px-4 py-3 text-left font-semibold text-slate-300 text-xs uppercase tracking-widest">Progress</th>
            </tr>
          </thead>
          <tbody>
            {loading ? (
              <tr><td colSpan="8" className="text-center py-8 text-slate-400">Loading trucks...</td></tr>
            ) : filteredAndPaginatedTrucks.length === 0 ? (
              <tr><td colSpan="8" className="text-center py-8 text-slate-400">No trucks found</td></tr>
            ) : (
              filteredAndPaginatedTrucks.map(truck => (
                <tr 
                  key={truck.id} 
                  className={`border-b border-slate-700/30 hover:bg-slate-800/70 transition-colors cursor-pointer ${
                    highlightedTruck && (highlightedTruck.id === truck.id || highlightedTruck.truck_identifier === truck.id || highlightedTruck.plate === truck.plate)
                      ? 'bg-blue-900/20 border-blue-700/50'
                      : ''
                  }`}
                  onClick={() => onTruckSelect?.(truck)}
                >
                  <td className="px-4 py-3 font-mono font-semibold text-slate-100">{truck.truck_identifier || truck.id}</td>
                  <td className="px-4 py-3 font-mono text-slate-300">{truck.plate}</td>
                  <td className="px-4 py-3 text-slate-200">{truck.assigned_driver || '—'}</td>
                  <td className="px-4 py-3"><StatusPill status={truck.status} /></td>
                  <td className="px-4 py-3 text-slate-300 text-xs">{addresses[truck.truck_identifier] || (Number.isFinite(truck.latitude) && Number.isFinite(truck.longitude) ? `${Number(truck.latitude).toFixed(3)}, ${Number(truck.longitude).toFixed(3)}` : '—')}</td>
                  <td className="px-4 py-3 font-mono text-slate-300">{'—'}</td>
                  <td className="px-4 py-3 text-slate-400 text-xs">{'—'}</td>
                  <td className="px-4 py-3"><ProgressBar progress={0} status={truck.status} /></td>
                </tr>
              ))
            )}
          </tbody>
        </table>
      </div>

      {/* Pagination */}
      {totalPages > 1 && (
        <div className="px-6 py-4 border-t border-slate-700/50 flex items-center justify-between bg-slate-800/30">
          <span className="text-xs text-slate-400">Page {page} of {totalPages}</span>
          <div className="flex gap-2">
            <button
              onClick={() => setPage(p => Math.max(1, p - 1))}
              disabled={page === 1}
              className="px-3 py-1.5 text-xs font-medium bg-slate-800/50 border border-slate-600/50 text-slate-300 rounded-lg hover:bg-slate-700/50 disabled:opacity-50 transition-colors"
            >
              Previous
            </button>
            <button
              onClick={() => setPage(p => Math.min(totalPages, p + 1))}
              disabled={page === totalPages}
              className="px-3 py-1.5 text-xs font-medium bg-slate-800/50 border border-slate-600/50 text-slate-300 rounded-lg hover:bg-slate-700/50 disabled:opacity-50 transition-colors"
            >
              Next
            </button>
          </div>
        </div>
      )}
    </div>
  );
}
