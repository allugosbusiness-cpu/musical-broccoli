import { useState, useEffect, useRef } from 'react';
import { AlertTriangle, AlertCircle, Info, CheckCircle2, X } from "lucide-react";
import { getAlerts, resolveAlert } from '../services/api.js';

export default function Alerts({ selectedTruck = null, refreshTrigger = 0 }) {
  const [alerts, setAlerts] = useState([]);
  const [loading, setLoading] = useState(false);
  const lastAlertKeysRef = useRef(new Set()); // Track last alert keys to detect duplicates

  // Fetch alerts from backend
  useEffect(() => {
    const fetchAlerts = async () => {
      try {
        setLoading(true);
        const data = await getAlerts({ is_resolved: false });
        
        if (Array.isArray(data)) {
          // Step 1: Deduplicate by ID (if same alert appears multiple times)
          const byId = {};
          data.forEach(alert => {
            if (!byId[alert.id] || new Date(alert.created_at) > new Date(byId[alert.id].created_at)) {
              byId[alert.id] = alert;
            }
          });

          // Step 2: Group by truck + alert_type, keep only most recent
          const grouped = {};
          Object.values(byId).forEach(alert => {
            const key = `${alert.truck}-${alert.alert_type}`;
            if (!grouped[key] || new Date(alert.created_at) > new Date(grouped[key].created_at)) {
              grouped[key] = alert;
            }
          });
          
          // Step 3: Map and format, limit to 10
          let formattedAlerts = Object.values(grouped)
            .sort((a, b) => new Date(b.created_at) - new Date(a.created_at))
            .slice(0, 10)
            .map(alert => ({
              id: alert.id,
              type: mapAlertTypeToComponent(alert.alert_type),
              message: alert.message,
              time: formatTime(alert.created_at),
              truck: alert.truck || 'Unknown',
              alertId: alert.id,
              createdAt: alert.created_at,
              alertType: alert.alert_type
            }));

          // Filter by selected truck if specified
          if (selectedTruck) {
            formattedAlerts = formattedAlerts.filter(a => a.truck === selectedTruck.plate || a.truck === selectedTruck.id || a.truck === selectedTruck.truck_identifier);
          }
          
          setAlerts(formattedAlerts);
          
          // Track keys for next cycle
          const newKeys = new Set(Object.keys(grouped));
          lastAlertKeysRef.current = newKeys;
        }
      } catch (error) {
        console.error('Error fetching alerts:', error);
      } finally {
        setLoading(false);
      }
    };

    fetchAlerts();
    const interval = setInterval(fetchAlerts, 10000); // Fetch every 10 seconds

    return () => clearInterval(interval);
  }, [selectedTruck, refreshTrigger]);

  const mapAlertTypeToComponent = (alertType) => {
    switch(alertType) {
      case 'critical':
      case 'off_route':
      case 'off-route-detected':
        return 'error';
      case 'warning':
      case 'overspeed':
        return 'warning';
      case 'info':
        return 'info';
      case 'success':
        return 'success';
      default:
        return 'info';
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
      return time.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });
    } catch (error) {
      console.error('Error formatting time:', error, timestamp);
      return 'unknown time';
    }
  };

  const handleResolveAlert = async (alertId) => {
    try {
      await resolveAlert(alertId);
      setAlerts((prev) => prev.filter((a) => a.id !== alertId));
    } catch (error) {
      console.error('Error resolving alert:', error);
    }
  };
  const getAlertConfig = (type) => {
    const configs = {
      error: { bg: 'bg-red-50', border: 'border-red-200', text: 'text-red-700', Icon: AlertTriangle, label: 'Critical' },
      warning: { bg: 'bg-amber-50', border: 'border-amber-200', text: 'text-amber-700', Icon: AlertCircle, label: 'Warning' },
      info: { bg: 'bg-blue-50', border: 'border-blue-200', text: 'text-blue-700', Icon: Info, label: 'Info' },
      success: { bg: 'bg-green-50', border: 'border-green-200', text: 'text-green-700', Icon: CheckCircle2, label: 'Good' },
    };
    return configs[type] || configs.info;
  };

  return (
    <div className="bg-white border border-gray-200 rounded-lg overflow-hidden shadow-sm">
      <div className="px-6 py-4 border-b border-gray-200">
        <h3 className="text-sm font-semibold text-gray-900 uppercase tracking-wide">Alerts ({alerts.length})</h3>
      </div>
      <div className="max-h-80 overflow-y-auto">
        {alerts.length === 0 ? (
          <div className="p-6 text-center text-gray-500 text-sm">No active alerts</div>
        ) : (
          alerts.map(alert => {
            const config = getAlertConfig(alert.type);
            return (
              <div
                key={alert.id}
                className={`p-4 border-b border-gray-100 ${config.bg} flex items-start justify-between gap-3`}
              >
                <div className="flex items-start gap-3 flex-1">
                  <config.Icon size={18} className={`flex-shrink-0 mt-0.5 ${config.text}`} />
                  <div className="flex-1">
                    <p className={`text-sm font-medium ${config.text}`}>{alert.message}</p>
                    <div className="flex items-center gap-2 mt-1 text-xs text-gray-600">
                      <span>{alert.time}</span>
                      <span>•</span>
                      <span className="font-mono">Truck {alert.truck}</span>
                    </div>
                  </div>
                </div>
                <button
                  onClick={() => handleResolveAlert(alert.alertId)}
                  className="text-gray-400 hover:text-gray-600 flex-shrink-0 transition-colors"
                  title="Resolve alert"
                >
                  <X size={16} />
                </button>
              </div>
            );
          })
        )}
      </div>
    </div>
  );
}
