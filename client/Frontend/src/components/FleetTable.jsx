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
    moving: { bg: 'bg-blue-100', border: 'border-blue-300', text: 'text-blue-700', Icon: Navigation, label: 'Moving' },
    delayed: { bg: 'bg-amber-100', border: 'border-amber-300', text: 'text-amber-700', Icon: Zap, label: 'Delayed' },
    stopped: { bg: 'bg-red-100', border: 'border-red-300', text: 'text-red-700', Icon: AlertTriangle, label: 'Stopped' },
    delivered: { bg: 'bg-purple-100', border: 'border-purple-300', text: 'text-purple-700', Icon: CheckCircle, label: 'Delivered' },
  };
  const config = configs[displayStatus] || configs.delivered;

  return (
    <span className={`inline-flex items-center gap-1 px-2 py-1 rounded-md text-xs font-semibold border ${config.bg} ${config.border} ${config.text}`}>
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
      <div className="w-12 h-1.5 bg-gray-200 rounded-full overflow-hidden">
        <div
          className={`h-full rounded-full transition-all duration-500 ${colors[status] || 'bg-blue-500'}`}
          style={{ width: `${progress}%` }}
        ></div>
      </div>
      <span className="text-xs text-gray-600 font-mono w-7">{progress}%</span>
    </div>
  );
}

export default function FleetTable({ onTruckSelect, highlightedTruck = null, refreshTrigger = 0 }) {
  const [trucks, setTrucks] = useState([]);
  const [filter, setFilter] = useState('all');
  const [loading, setLoading] = useState(true);
  const [page, setPage] = useState(1);
  const [addresses, setAddresses] = useState({}); // Cache for addresses
  const ITEMS_PER_PAGE = 10;

  useEffect(() => {
    const fetchTrucks = async () => {
      try {
        const data = await getDashboardTrucks();
        const trucksData = Array.isArray(data) ? data.slice(0, 50) : [];
        
        // Geocode all truck locations
        const addressMap = {};
        for (const truck of trucksData) {
          if (truck.location && truck.location.lat && truck.location.lon) {
            try {
              const address = await reverseGeocode(truck.location.lat, truck.location.lon);
              addressMap[truck.truck_identifier] = address;
            } catch (error) {
              console.error(`Failed to geocode ${truck.truck_identifier}:`, error);
              addressMap[truck.truck_identifier] = `${truck.location.lat.toFixed(3)}, ${truck.location.lon.toFixed(3)}`;
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
    <div className="bg-white border border-gray-200 rounded-lg overflow-hidden shadow-sm">
      <div className="px-6 py-4 border-b border-gray-200 flex items-center justify-between">
        <h2 className="text-sm font-semibold text-gray-900 uppercase tracking-wide">Fleet Overview ({trucks.length})</h2>
        <div className="flex gap-2 flex-wrap">
          {filterButtons.map(btn => (
            <button
              key={btn.key}
              onClick={() => { setFilter(btn.key); setPage(1); }}
              className={`px-3 py-1.5 text-xs font-medium rounded-md border transition-all ${
                filter === btn.key
                  ? 'bg-blue-50 border-blue-300 text-blue-700'
                  : 'bg-white border-gray-300 text-gray-700 hover:bg-gray-50'
              }`}
            >
              {btn.label} ({btn.count})
            </button>
          ))}
        </div>
      </div>

      <div className="overflow-x-auto">
        <table className="w-full text-sm">
          <thead className="bg-gray-50 border-b border-gray-200">
            <tr>
              <th className="px-4 py-3 text-left font-semibold text-gray-700 text-xs uppercase">ID</th>
              <th className="px-4 py-3 text-left font-semibold text-gray-700 text-xs uppercase">Plate</th>
              <th className="px-4 py-3 text-left font-semibold text-gray-700 text-xs uppercase">Driver</th>
              <th className="px-4 py-3 text-left font-semibold text-gray-700 text-xs uppercase">Status</th>
              <th className="px-4 py-3 text-left font-semibold text-gray-700 text-xs uppercase">Location</th>
              <th className="px-4 py-3 text-left font-semibold text-gray-700 text-xs uppercase">Speed</th>
              <th className="px-4 py-3 text-left font-semibold text-gray-700 text-xs uppercase">ETA</th>
              <th className="px-4 py-3 text-left font-semibold text-gray-700 text-xs uppercase">Progress</th>
            </tr>
          </thead>
          <tbody>
            {loading ? (
              <tr><td colSpan="8" className="text-center py-8 text-gray-500">Loading trucks...</td></tr>
            ) : filteredAndPaginatedTrucks.length === 0 ? (
              <tr><td colSpan="8" className="text-center py-8 text-gray-500">No trucks found</td></tr>
            ) : (
              filteredAndPaginatedTrucks.map(truck => (
                <tr 
                  key={truck.id} 
                  className={`border-b border-gray-100 hover:bg-gray-50 transition-colors cursor-pointer ${
                    highlightedTruck && (highlightedTruck.id === truck.id || highlightedTruck.truck_identifier === truck.id || highlightedTruck.plate === truck.plate)
                      ? 'bg-blue-100 font-semibold'
                      : ''
                  }`}
                  onClick={() => onTruckSelect?.(truck)}
                >
                  <td className="px-4 py-3 font-mono font-semibold text-gray-900">{truck.truck_identifier || truck.id}</td>
                  <td className="px-4 py-3 font-mono text-gray-700">{truck.plate}</td>
                  <td className="px-4 py-3 text-gray-900">{truck.assigned_driver || '—'}</td>
                  <td className="px-4 py-3"><StatusPill status={truck.status} /></td>
                  <td className="px-4 py-3 text-gray-700">{addresses[truck.truck_identifier] || (truck.location ? `${truck.location.lat?.toFixed(3)}, ${truck.location.lon?.toFixed(3)}` : '—')}</td>
                  <td className="px-4 py-3 font-mono text-gray-900">{'—'}</td>
                  <td className="px-4 py-3 text-gray-700 text-xs">{'—'}</td>
                  <td className="px-4 py-3"><ProgressBar progress={0} status={truck.status} /></td>
                </tr>
              ))
            )}
          </tbody>
        </table>
      </div>

      {/* Pagination */}
      {totalPages > 1 && (
        <div className="px-6 py-4 border-t border-gray-200 flex items-center justify-between bg-gray-50">
          <span className="text-xs text-gray-600">Page {page} of {totalPages}</span>
          <div className="flex gap-2">
            <button
              onClick={() => setPage(p => Math.max(1, p - 1))}
              disabled={page === 1}
              className="px-3 py-1.5 text-xs font-medium bg-white border border-gray-300 rounded-md hover:bg-gray-50 disabled:opacity-50"
            >
              Previous
            </button>
            <button
              onClick={() => setPage(p => Math.min(totalPages, p + 1))}
              disabled={page === totalPages}
              className="px-3 py-1.5 text-xs font-medium bg-white border border-gray-300 rounded-md hover:bg-gray-50 disabled:opacity-50"
            >
              Next
            </button>
          </div>
        </div>
      )}
    </div>
  );
}
