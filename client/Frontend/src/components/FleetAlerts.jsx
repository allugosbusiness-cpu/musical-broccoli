import { useEffect, useState } from 'react';
import { AlertTriangle, CheckCircle, Zap, AlertCircle, Clock } from 'lucide-react';
import { getAlerts, resolveAlert } from '../services/api.js';

/**
 * Fleet Alerts Component
 * Displays persistent alerts from backend (off-route, overspeeding, delays, etc.)
 * Shows in a dedicated panel at the bottom
 */
export default function FleetAlerts({ selectedDriver = null, refreshTrigger = 0 }) {
  const [alerts, setAlerts] = useState([]);
  const [loading, setLoading] = useState(false);

  // Fetch alerts periodically
  useEffect(() => {
    const fetchAlerts = async () => {
      try {
        setLoading(true);
        const data = await getAlerts({ is_resolved: false });
        
        if (Array.isArray(data)) {
          // Group by truck and alert type - keep only most recent of each type per truck
          const grouped = {};
          data.forEach(alert => {
            const key = `${alert.truck}-${alert.alert_type}`;
            if (!grouped[key] || new Date(alert.created_at) > new Date(grouped[key].created_at)) {
              grouped[key] = alert;
            }
          });
          
          // Limit to 10 active alerts total
          let sorted = Object.values(grouped)
            .sort((a, b) => new Date(b.created_at) - new Date(a.created_at))
            .slice(0, 10);

          // Filter by selected driver if specified
          if (selectedDriver) {
            sorted = sorted.filter(a => a.driver_id === selectedDriver.id || a.driver === selectedDriver.first_name);
          }
          
          setAlerts(sorted);
        }
      } catch (error) {
        console.error('Error fetching alerts (silently continuing):', error.message);
        // Silently fail - don't block the page - just show no alerts
        setAlerts([]);
      } finally {
        setLoading(false);
      }
    };

    fetchAlerts();
    const interval = setInterval(fetchAlerts, 10000); // Fetch every 10 seconds

    return () => clearInterval(interval);
  }, [selectedDriver, refreshTrigger]);

  const handleResolveAlert = async (alertId) => {
    try {
      await resolveAlert(alertId);
      setAlerts((prev) => prev.filter((a) => a.id !== alertId));
    } catch (error) {
      console.error('Error resolving alert:', error);
    }
  };

  const getAlertIcon = (alertType) => {
    switch (alertType) {
      case 'critical':
        return <AlertTriangle className="w-5 h-5" />;
      case 'warning':
        return <Zap className="w-5 h-5" />;
      case 'info':
        return <AlertCircle className="w-5 h-5" />;
      case 'success':
        return <CheckCircle className="w-5 h-5" />;
      default:
        return <Clock className="w-5 h-5" />;
    }
  };

  const getAlertColor = (alertType) => {
    switch (alertType) {
      case 'critical':
        return 'bg-red-50 border-red-200 text-red-800';
      case 'warning':
        return 'bg-amber-50 border-amber-200 text-amber-800';
      case 'info':
        return 'bg-blue-50 border-blue-200 text-blue-800';
      case 'success':
        return 'bg-green-50 border-green-200 text-green-800';
      default:
        return 'bg-gray-50 border-gray-200 text-gray-800';
    }
  };

  const formatTime = (timestamp) => {
    if (!timestamp) return 'unknown time';
    
    try {
      const now = new Date();
      const time = new Date(timestamp);
      
      // Check if date is valid
      if (isNaN(time.getTime())) {
        console.warn('Invalid timestamp:', timestamp);
        return 'unknown time';
      }
      
      const diff = Math.floor((now - time) / 1000);
      
      if (diff < 60) return 'just now';
      if (diff < 3600) return `${Math.floor(diff / 60)}m ago`;
      if (diff < 86400) return `${Math.floor(diff / 3600)}h ago`;
      return time.toLocaleDateString();
    } catch (error) {
      console.error('Error formatting time:', error, timestamp);
      return 'unknown time';
    }
  };

  if (alerts.length === 0) return null;

  return (
    <div className="fixed bottom-0 left-0 right-0 bg-gradient-to-t from-gray-50 via-white to-transparent border-t border-gray-200 p-4 z-40">
      <div className="max-w-7xl mx-auto">
        <div className="flex items-center gap-2 mb-3">
          <AlertTriangle className="w-5 h-5 text-red-500" />
          <h3 className="font-semibold text-gray-900">{alerts.length} Active Alert{alerts.length !== 1 ? 's' : ''}</h3>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-3 max-h-64 overflow-y-auto">
          {alerts.map((alert) => (
            <div
              key={alert.id}
              className={`border rounded-lg p-3 flex items-start gap-3 ${getAlertColor(alert.alert_type)}`}
            >
              <div className="flex-shrink-0 mt-0.5">
                {getAlertIcon(alert.alert_type)}
              </div>

              <div className="flex-1 min-w-0">
                <div className="flex items-start justify-between gap-2">
                  <div className="flex-1">
                    <div className="font-semibold text-sm">
                      Truck {alert.truck}
                    </div>
                    {alert.driver_name && (
                      <div className="text-xs opacity-75">
                        Driver: {alert.driver_name}
                      </div>
                    )}
                    <p className="text-xs mt-1 line-clamp-2">
                      {alert.message}
                    </p>
                  </div>
                  <button
                    onClick={() => handleResolveAlert(alert.id)}
                    className="flex-shrink-0 text-xs font-medium opacity-60 hover:opacity-100 transition-opacity"
                    title="Mark as resolved"
                  >
                    ✕
                  </button>
                </div>

                <div className="text-xs opacity-60 mt-2">
                  {formatTime(alert.created_at)}
                </div>
              </div>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
}
