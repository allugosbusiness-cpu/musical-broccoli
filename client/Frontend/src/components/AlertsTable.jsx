import { useState, useEffect, useRef } from 'react';
import { X, Bell, Trash2 } from 'lucide-react';
import { getAlerts, resolveAlert } from '../services/api';

export default function AlertsTable({ filterTruckId = null, onTruckAlert = () => {}, refreshTrigger = 0 }) {
  const [alerts, setAlerts] = useState([]);
  const [toastMsg, setToastMsg] = useState('');
  const isMountedRef = useRef(true);

  useEffect(() => {
    return () => {
      isMountedRef.current = false;
    };
  }, []);

  // Fetch alerts
  useEffect(() => {
    const fetchAlerts = async () => {
      if (!isMountedRef.current) return;
      
      try {
        const data = await getAlerts({ is_resolved: false });
        if (isMountedRef.current && Array.isArray(data)) {
          const grouped = {};
          data.forEach(alert => {
            const key = `${alert.truck}-${alert.alert_type}`;
            if (!grouped[key] || new Date(alert.timestamp || alert.created_at) > new Date(grouped[key].timestamp || grouped[key].created_at)) {
              grouped[key] = alert;
            }
          });
          
          let sorted = Object.values(grouped)
            .sort((a, b) => new Date(b.timestamp || b.created_at) - new Date(a.timestamp || a.created_at))
            .slice(0, 50);

          // Filter by truck if specified
          if (filterTruckId) {
            sorted = sorted.filter(a => a.truck_id === filterTruckId || a.truck === filterTruckId);
          }
          
          setAlerts(sorted);
        }
      } catch (error) {
        console.error('Error fetching alerts:', error);
      }
    };

    fetchAlerts();
    const interval = setInterval(fetchAlerts, 15000);
    return () => clearInterval(interval);
  }, [filterTruckId, refreshTrigger]);

  const handleDelete = async (alertId) => {
    try {
      await resolveAlert(alertId);
      setAlerts(prev => prev.filter(a => a.id !== alertId));
      setToastMsg('Alert dismissed');
      setTimeout(() => setToastMsg(''), 3000);
    } catch (error) {
      console.error('Error deleting alert:', error);
    }
  };

  const getAlertColor = (type) => {
    switch (type) {
      case 'off_route':
        return 'text-red-600 bg-red-50';
      case 'back_on_route':
        return 'text-green-600 bg-green-50';
      case 'overspeed':
        return 'text-yellow-600 bg-yellow-50';
      case 'delayed':
        return 'text-orange-600 bg-orange-50';
      case 'driver_alert':
        return 'text-purple-600 bg-purple-50';
      default:
        return 'text-gray-600 bg-gray-50';
    }
  };

  const formatTime = (ts) => {
    if (!ts) return 'unknown';
    try {
      const d = new Date(ts);
      if (isNaN(d.getTime())) return 'unknown';
      const diff = Math.floor((new Date() - d) / 1000);
      if (diff < 60) return 'just now';
      if (diff < 3600) return `${Math.floor(diff / 60)}m`;
      if (diff < 86400) return `${Math.floor(diff / 3600)}h`;
      return d.toLocaleDateString();
    } catch {
      return 'unknown';
    }
  };

  return (
    <div>
      {toastMsg && (
        <div className="fixed top-4 right-4 z-50 bg-black text-white px-6 py-3 rounded-lg shadow-lg flex items-center gap-3">
          <Bell className="w-5 h-5" />
          <span className="text-sm">{toastMsg}</span>
          <button onClick={() => setToastMsg('')}>
            <X className="w-4 h-4" />
          </button>
        </div>
      )}

      <div className="bg-white border border-gray-200 rounded-lg overflow-hidden shadow-sm">
        <div className="px-6 py-4 border-b border-gray-200 flex items-center gap-3">
          <Bell className="w-5 h-5 text-blue-600" />
          <div>
            <h2 className="text-lg font-semibold text-gray-900">Active Alerts</h2>
            <p className="text-xs text-gray-600 mt-0.5">{alerts.length} alerts</p>
          </div>
        </div>

        <div className="overflow-x-auto">
          {alerts.length === 0 ? (
            <div className="p-8 text-center">
              <Bell className="w-12 h-12 text-gray-300 mx-auto mb-3" />
              <p className="text-gray-500 text-sm">No active alerts</p>
            </div>
          ) : (
            <table className="w-full">
              <thead className="bg-gray-50 border-b border-gray-200">
                <tr>
                  <th className="px-6 py-3 text-left text-xs font-semibold text-gray-700 uppercase">Truck</th>
                  <th className="px-6 py-3 text-left text-xs font-semibold text-gray-700 uppercase">Type</th>
                  <th className="px-6 py-3 text-left text-xs font-semibold text-gray-700 uppercase">Message</th>
                  <th className="px-6 py-3 text-left text-xs font-semibold text-gray-700 uppercase">Time</th>
                  <th className="px-6 py-3 text-center text-xs font-semibold text-gray-700 uppercase">Action</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-gray-200">
                {alerts.map(alert => (
                  <tr key={alert.id} className="hover:bg-gray-50">
                    <td className="px-6 py-4 whitespace-nowrap text-sm font-medium text-gray-900">
                      {alert.truck || 'N/A'}
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap">
                      <span className={`px-2.5 py-0.5 rounded-full text-xs font-semibold ${getAlertColor(alert.alert_type)}`}>
                        {alert.alert_type?.replace(/_/g, ' ').toUpperCase() || 'UNKNOWN'}
                      </span>
                    </td>
                    <td className="px-6 py-4 text-sm text-gray-700 max-w-xs truncate">
                      {alert.message || 'No message'}
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-xs text-gray-600">
                      {formatTime(alert.created_at || alert.timestamp)}
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-center">
                      <button
                        onClick={() => handleDelete(alert.id)}
                        className="text-gray-400 hover:text-red-600 transition-colors"
                        title="Dismiss"
                      >
                        <Trash2 className="w-4 h-4" />
                      </button>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          )}
        </div>
      </div>
    </div>
  );
}
