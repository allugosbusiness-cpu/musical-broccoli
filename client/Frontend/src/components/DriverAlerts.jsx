import { useState, useEffect, useRef } from 'react';
import { X, Bell, Trash2 } from 'lucide-react';
import { getTrucks, createAlert, getAlerts, resolveAlert } from '../services/api';

export default function DriverAlerts() {
  const [alerts, setAlerts] = useState([]);
  const [toastMessage, setToastMessage] = useState(null);
  const [loading, setLoading] = useState(false);
  
  const truckOffRouteStatusRef = useRef(new Map());
  const fetchIntervalRef = useRef(null);
  const isMountedRef = useRef(true);
  const shownToastsRef = useRef(new Set());

  // Cleanup on unmount
  useEffect(() => {
    return () => {
      isMountedRef.current = false;
      if (fetchIntervalRef.current) clearInterval(fetchIntervalRef.current);
      truckOffRouteStatusRef.current.clear();
      shownToastsRef.current.clear();
    };
  }, []);

  // Show toast notification
  const showToast = (message) => {
    if (!shownToastsRef.current.has(message)) {
      shownToastsRef.current.add(message);
      setToastMessage(message);
      setTimeout(() => {
        setToastMessage(null);
        shownToastsRef.current.delete(message);
      }, 5000);
    }
  };

  // Fetch alerts periodically
  useEffect(() => {
    const fetchAlerts = async () => {
      if (!isMountedRef.current) return;
      
      try {
        setLoading(true);
        const data = await getAlerts({ is_resolved: false });
        
        if (!isMountedRef.current) return;
        
        if (Array.isArray(data)) {
          const grouped = {};
          data.forEach(alert => {
            const key = `${alert.truck}-${alert.alert_type}`;
            if (!grouped[key] || new Date(alert.timestamp || alert.created_at) > new Date(grouped[key].timestamp || grouped[key].created_at)) {
              grouped[key] = alert;
            }
          });
          
          const deduplicatedAlerts = Object.values(grouped)
            .sort((a, b) => new Date(b.timestamp || b.created_at) - new Date(a.timestamp || a.created_at))
            .slice(0, 50);
          
          setAlerts(deduplicatedAlerts);
        }
      } catch (error) {
        console.error('Error fetching alerts:', error);
      } finally {
        setLoading(false);
      }
    };

    fetchAlerts();
    fetchIntervalRef.current = setInterval(fetchAlerts, 15000);
    return () => {
      if (fetchIntervalRef.current) clearInterval(fetchIntervalRef.current);
    };
  }, []);

  // Check route status and alert only on state changes
  useEffect(() => {
    const checkRouteStatus = async () => {
      if (!isMountedRef.current) return;
      
      try {
        const truckList = await getTrucks();
        
        if (!isMountedRef.current) return;
        
        (Array.isArray(truckList) ? truckList : []).forEach(truck => {
          const isCurrentlyOffRoute = truck.is_off_route || false;
          const wasPreviouslyOffRoute = truckOffRouteStatusRef.current.get(truck.id) || false;
          
          if (isCurrentlyOffRoute && !wasPreviouslyOffRoute) {
            createRouteAlert(truck.id, true, truck.location || truck.id);
          }
          
          if (!isCurrentlyOffRoute && wasPreviouslyOffRoute) {
            createRouteAlert(truck.id, false, truck.location || truck.id);
          }
          
          truckOffRouteStatusRef.current.set(truck.id, isCurrentlyOffRoute);
        });
      } catch (error) {
        console.error('Error checking route status:', error);
      }
    };

    checkRouteStatus();
    const routeCheckInterval = setInterval(checkRouteStatus, 30000);
    
    return () => clearInterval(routeCheckInterval);
  }, []);

  const createRouteAlert = async (truckId, isOffRoute, location) => {
    if (!isMountedRef.current) return;
    
    const message = isOffRoute 
      ? `Truck ${truckId} has deviated from route`
      : `Truck ${truckId} is back on route`;
    
    const alertType = isOffRoute ? 'off_route' : 'back_on_route';
    
    try {
      await createAlert(truckId, alertType, message);
      showToast(message);
    } catch (error) {
      console.error('Error creating route alert:', error);
    }
  };

  const handleDeleteAlert = async (alertId) => {
    try {
      await resolveAlert(alertId);
      setAlerts(prev => prev.filter(a => a.id !== alertId));
    } catch (error) {
      console.error('Error deleting alert:', error);
    }
  };

  const getAlertTypeColor = (alertType) => {
    switch (alertType) {
      case 'off_route':
        return 'text-red-600 bg-red-50';
      case 'back_on_route':
        return 'text-green-600 bg-green-50';
      case 'driver_report':
        return 'text-blue-600 bg-blue-50';
      default:
        return 'text-gray-600 bg-gray-50';
    }
  };

  const formatTime = (timestamp) => {
    if (!timestamp) return 'unknown';
    try {
      const date = new Date(timestamp);
      if (isNaN(date.getTime())) return 'unknown';
      const now = new Date();
      const diff = Math.floor((now - date) / 1000);
      if (diff < 60) return 'just now';
      if (diff < 3600) return `${Math.floor(diff / 60)}m`;
      if (diff < 86400) return `${Math.floor(diff / 3600)}h`;
      return date.toLocaleDateString();
    } catch (error) {
      return 'unknown';
    }
  };

  return (
    <div className="w-full">
      {/* Toast Notification */}
      {toastMessage && (
        <div className="fixed top-4 right-4 z-50 max-w-md">
          <div className="bg-black text-white px-6 py-3 rounded-lg shadow-lg flex items-center gap-3">
            <Bell className="w-5 h-5 flex-shrink-0" />
            <span className="text-sm font-medium">{toastMessage}</span>
            <button
              onClick={() => setToastMessage(null)}
              className="ml-auto text-gray-300 hover:text-white"
            >
              <X className="w-4 h-4" />
            </button>
          </div>
        </div>
      )}

      {/* Alerts Table */}
      <div className="bg-white border border-gray-200 rounded-lg overflow-hidden shadow-sm">
        <div className="px-6 py-4 border-b border-gray-200">
          <div className="flex items-center gap-3">
            <Bell className="w-5 h-5 text-blue-600" />
            <div>
              <h2 className="text-lg font-semibold text-gray-900">Active Alerts</h2>
              <p className="text-xs text-gray-600 mt-0.5">{alerts.length} alerts</p>
            </div>
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
                  <th className="px-6 py-3 text-left text-xs font-semibold text-gray-700 uppercase tracking-wider">Truck</th>
                  <th className="px-6 py-3 text-left text-xs font-semibold text-gray-700 uppercase tracking-wider">Alert Type</th>
                  <th className="px-6 py-3 text-left text-xs font-semibold text-gray-700 uppercase tracking-wider">Message</th>
                  <th className="px-6 py-3 text-left text-xs font-semibold text-gray-700 uppercase tracking-wider">Time</th>
                  <th className="px-6 py-3 text-center text-xs font-semibold text-gray-700 uppercase tracking-wider">Action</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-gray-200">
                {alerts.map(alert => (
                  <tr key={alert.id} className="hover:bg-gray-50 transition-colors">
                    <td className="px-6 py-4 whitespace-nowrap">
                      <span className="text-sm font-medium text-gray-900">{alert.truck || 'N/A'}</span>
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap">
                      <span className={`inline-block px-2.5 py-0.5 rounded-full text-xs font-semibold ${getAlertTypeColor(alert.alert_type)}`}>
                        {alert.alert_type?.replace(/_/g, ' ').toUpperCase() || 'UNKNOWN'}
                      </span>
                    </td>
                    <td className="px-6 py-4">
                      <p className="text-sm text-gray-700 line-clamp-2">{alert.message || 'No message'}</p>
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap">
                      <span className="text-xs text-gray-600">{formatTime(alert.created_at || alert.timestamp)}</span>
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-center">
                      <button
                        onClick={() => handleDeleteAlert(alert.id)}
                        className="text-gray-400 hover:text-red-600 transition-colors"
                        title="Dismiss alert"
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

                  {/* Alert Type */}
                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-2">Alert Type</label>
                    <select
                      name="alertType"
                      value={formData.alertType}
                      onChange={handleInputChange}
                      className="w-full px-3 py-2 bg-white border border-gray-300 rounded-lg text-gray-900 focus:outline-none focus:ring-2 focus:ring-blue-500"
                    >
                      {alertTypes.map(type => (
                        <option key={type.value} value={type.value}>
                          {type.label}
                        </option>
                      ))}
                    </select>
                  </div>

                  {/* Message */}
                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-2">Message</label>
                    <textarea
                      name="message"
                      value={formData.message}
                      onChange={handleInputChange}
                      onKeyDown={handleKeyDown}
                      placeholder="Describe the issue... (Ctrl+Enter to send)"
                      required
                      rows="4"
                      className="w-full px-3 py-2 bg-white border border-gray-300 rounded-lg text-gray-900 placeholder-gray-500 focus:outline-none focus:ring-2 focus:ring-blue-500 resize-none"
                    />
                  </div>
                </form>
              </div>

              {/* Footer - Fixed Buttons */}
              <div className="px-6 py-4 border-t border-gray-200 flex gap-3 flex-shrink-0">
                <button
                  form="alert-form"
                  type="submit"
                  disabled={loading}
                  className="flex-1 flex items-center justify-center gap-2 px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 disabled:opacity-50 font-medium transition-colors"
                >
                  <Send className="w-4 h-4" />
                  {loading ? 'Sending...' : 'Send Alert'}
                </button>
                <button
                  type="button"
                  onClick={() => setShowForm(false)}
                  className="flex-1 px-4 py-2 bg-gray-100 text-gray-700 rounded-lg hover:bg-gray-200 font-medium transition-colors"
                >
                  Cancel
                </button>
              </div>
            </div>
          </div>
        </>
      )}

      {/* Alerts List */}
      <div className="max-h-96 overflow-y-auto">
        {alerts.length > 0 ? (
          <div className="divide-y divide-border/30">
            {alerts.map(alert => {
              const AlertIcon = getAlertIcon(alert.alert_type);
              const truck = trucks.find(t => t.id === alert.truck);

              return (
                <div key={alert.id} className={`p-4 border-l-4 ${getAlertColor(alert.alert_type)}`}>
                  <div className="flex items-start justify-between gap-3">
                    <div className="flex items-start gap-3 flex-1">
                      <AlertIcon className="w-5 h-5 mt-0.5 flex-shrink-0" />
                      <div className="flex-1">
                        <div className="flex items-center gap-2">
                          <p className="font-semibold text-sm">
                            {truck ? `${truck.plate} - ${truck.driver}` : `Truck ${alert.truck}`}
                          </p>
                          <span className="text-xs font-mono capitalize px-2 py-0.5 bg-text3/10 rounded text-text3">
                            {alert.alert_type.replace(/_/g, ' ')}
                          </span>
                        </div>
                        <p className="text-sm text-text2 mt-1">{alert.message}</p>
                        <p className="text-xs text-text3 mt-2 font-mono">
                          {new Date(alert.timestamp).toLocaleString()}
                        </p>
                      </div>
                    </div>
                  </div>
                </div>
              );
            })}
          </div>
        ) : (
          <div className="p-8 text-center text-gray-500">
            <Bell className="w-12 h-12 mx-auto mb-3 opacity-30" />
            <p className="text-gray-700">No active alerts</p>
            <p className="text-xs mt-1 text-gray-600">All systems operating normally</p>
          </div>
        )}
      </div>
    </div>
  );
}
