import React, { useState, useEffect } from 'react';
import axios from 'axios';

const getApiV1Base = () => {
  if (import.meta.env.MODE === 'development') return 'http://localhost:8000/api/v1';
  return 'https://pulsetrack-back.onrender.com/api/v1';
};

const ActivityTable = () => {
  const [activities, setActivities] = useState([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  const [page, setPage] = useState(1);
  const [totalCount, setTotalCount] = useState(0);
  const [filters, setFilters] = useState({
    days: 7,
    activity_type: '',
    activity_category: '',
    truck_id: '',
    driver_id: '',
  });
  const [summary, setSummary] = useState(null);

  const API_BASE = getApiV1Base();
  const ITEMS_PER_PAGE = 50;

  // Fetch activities on component mount and when filters change
  useEffect(() => {
    fetchActivities();
    fetchSummary();
  }, [filters]);

  const fetchActivities = async () => {
    setLoading(true);
    setError('');
    try {
      const params = new URLSearchParams({
        days: filters.days,
        limit: ITEMS_PER_PAGE,
      });
      if (filters.activity_type) params.set('activity_type', filters.activity_type);
      if (filters.activity_category) params.set('activity_category', filters.activity_category);
      
      const response = await fetch(`${API_BASE}/activities/?${params.toString()}`, {
        method: 'GET',
        headers: { 'Content-Type': 'application/json' },
      });
      
      if (!response.ok) throw new Error(`HTTP ${response.status}`);
      
      const data = await response.json();
      setActivities(data.activities || []);
      setTotalCount(data.total_count || 0);
    } catch (err) {
      console.error('Error fetching activities:', err);
      setError('Failed to load activities');
    } finally {
      setLoading(false);
    }
  };

  const fetchSummary = async () => {
    try {
      const response = await fetch(`${API_BASE}/activities/summary/?days=${filters.days}`, {
        method: 'GET',
        headers: { 'Content-Type': 'application/json' },
      });
      if (response.ok) {
        const data = await response.json();
        setSummary(data);
      }
    } catch (err) {
      console.error('Error fetching summary:', err);
    }
  };

  const handleFilterChange = (e) => {
    const { name, value } = e.target;
    setFilters(prev => ({ ...prev, [name]: value }));
    setPage(1);
  };

  const handleExportCSV = () => {
    if (activities.length === 0) {
      alert('No activities to export');
      return;
    }

    // Prepare CSV headers
    const headers = [
      'Truck',
      'Driver',
      'Activity Type',
      'Category',
      'Location',
      'Speed (km/h)',
      'Distance (m)',
      'Fuel (%)',
      'Alert Level',
      'Critical',
      'Timestamp',
      'Notes',
    ];

    // Prepare CSV rows
    const rows = activities.map(activity => [
      activity.truck_identifier || 'N/A',
      activity.driver_name || 'N/A',
      activity.activity_type_display,
      activity.activity_category,
      activity.location || 'N/A',
      activity.speed_kmh || '',
      activity.distance_m || '',
      activity.fuel_percentage || '',
      activity.alert_level || 'N/A',
      activity.is_critical ? 'YES' : 'NO',
      new Date(activity.timestamp).toLocaleString(),
      activity.notes || '',
    ]);

    // Generate CSV string
    const csv = [
      headers.join(','),
      ...rows.map(row =>
        row
          .map(cell =>
            typeof cell === 'string' && cell.includes(',')
              ? `"${cell}"`
              : cell
          )
          .join(',')
      ),
    ].join('\n');

    // Download
    const blob = new Blob([csv], { type: 'text/csv' });
    const url = window.URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `activities_${new Date().toISOString().split('T')[0]}.csv`;
    document.body.appendChild(a);
    a.click();
    window.URL.revokeObjectURL(url);
    document.body.removeChild(a);
  };

  const getCategoryColor = (category) => {
    const colors = {
      mission: 'bg-blue-900 text-blue-200',
      location: 'bg-green-900 text-green-200',
      speed: 'bg-yellow-900 text-yellow-200',
      fuel: 'bg-orange-900 text-orange-200',
      alert: 'bg-red-900 text-red-200',
      breach: 'bg-purple-900 text-purple-200',
      driver: 'bg-indigo-900 text-indigo-200',
      maintenance: 'bg-gray-700 text-gray-200',
      trail: 'bg-teal-900 text-teal-200',
      cargo: 'bg-pink-900 text-pink-200',
    };
    return colors[category] || 'bg-gray-700 text-gray-200';
  };

  const getAlertLevelColor = (level) => {
    const colors = {
      low: 'text-green-600',
      medium: 'text-yellow-600',
      high: 'text-orange-600',
      critical: 'text-red-600',
    };
    return colors[level] || 'text-gray-600';
  };

  return (
    <div className="w-full max-w-7xl mx-auto p-4 bg-gray-900 rounded-lg shadow-lg">
      <h2 className="text-3xl font-bold mb-6 text-white">📊 Activity Audit Trail</h2>

      {/* Summary Cards */}
      {summary && (
        <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mb-6">
          <div className="bg-gradient-to-br from-blue-900 to-blue-800 p-4 rounded-lg border border-blue-700">
            <div className="text-sm text-blue-300 font-semibold">Total Activities</div>
            <div className="text-3xl font-bold text-blue-200">{summary.total_activities}</div>
          </div>
          <div className="bg-gradient-to-br from-red-900 to-red-800 p-4 rounded-lg border border-red-700">
            <div className="text-sm text-red-300 font-semibold">Critical Events</div>
            <div className="text-3xl font-bold text-red-200">{summary.critical_count}</div>
          </div>
          <div className="bg-gradient-to-br from-green-900 to-green-800 p-4 rounded-lg border border-green-700">
            <div className="text-sm text-green-300 font-semibold">Trucks Active</div>
            <div className="text-3xl font-bold text-green-200">{Object.keys(summary.by_truck || {}).length}</div>
          </div>
          <div className="bg-gradient-to-br from-purple-900 to-purple-800 p-4 rounded-lg border border-purple-700">
            <div className="text-sm text-purple-300 font-semibold">Drivers Active</div>
            <div className="text-3xl font-bold text-purple-200">{Object.keys(summary.by_driver || {}).length}</div>
          </div>
        </div>
      )}

      {/* Filters */}
      <div className="grid grid-cols-1 md:grid-cols-5 gap-4 mb-6 p-4 bg-gray-800 rounded-lg border border-gray-700">
        <div>
          <label className="block text-sm font-semibold text-gray-300 mb-1">Days Range</label>
          <select
            name="days"
            value={filters.days}
            onChange={handleFilterChange}
            className="w-full px-3 py-2 border border-gray-600 rounded-lg bg-gray-700 text-white focus:ring-2 focus:ring-blue-500 focus:border-transparent"
          >
            <option value={1}>Last 24 Hours</option>
            <option value={7}>Last 7 Days</option>
            <option value={14}>Last 14 Days</option>
            <option value={30}>Last 30 Days</option>
            <option value={60}>Last 60 Days</option>
          </select>
        </div>
        <div>
          <label className="block text-sm font-semibold text-gray-300 mb-1">Category</label>
          <select
            name="activity_category"
            value={filters.activity_category}
            onChange={handleFilterChange}
            className="w-full px-3 py-2 border border-gray-600 rounded-lg bg-gray-700 text-white focus:ring-2 focus:ring-blue-500 focus:border-transparent"
          >
            <option value="">All Categories</option>
            <option value="mission">Mission</option>
            <option value="location">Location</option>
            <option value="speed">Speed</option>
            <option value="fuel">Fuel</option>
            <option value="alert">Alert</option>
            <option value="breach">Breach</option>
            <option value="trail">Trail</option>
          </select>
        </div>
        <div>
          <label className="block text-sm font-semibold text-gray-300 mb-1">Activity Type</label>
          <select
            name="activity_type"
            value={filters.activity_type}
            onChange={handleFilterChange}
            className="w-full px-3 py-2 border border-gray-600 rounded-lg bg-gray-700 text-white focus:ring-2 focus:ring-blue-500 focus:border-transparent"
          >
            <option value="">All Types</option>
            <option value="trail_recorded">Trail Recorded</option>
            <option value="mission_created">Mission Created</option>
            <option value="mission_started">Mission Started</option>
            <option value="mission_completed">Mission Completed</option>
            <option value="location_update">Location Update</option>
            <option value="speed_recorded">Speed Recorded</option>
            <option value="alert_triggered">Alert Triggered</option>
            <option value="breach_detected">Breach Detected</option>
            <option value="fuel_update">Fuel Update</option>
          </select>
        </div>
        <div className="flex items-end gap-2">
          <button
            onClick={handleExportCSV}
            className="flex-1 bg-green-600 hover:bg-green-700 text-white font-semibold py-2 px-4 rounded-lg transition"
          >
            📥 Export CSV
          </button>
        </div>
        <div className="flex items-end">
          <button
            onClick={() => setFilters({ days: 7, activity_type: '', activity_category: '', truck_id: '', driver_id: '' })}
            className="w-full bg-gray-400 hover:bg-gray-500 text-white font-semibold py-2 px-4 rounded-lg transition"
          >
            Reset
          </button>
        </div>
      </div>

      {/* Error Message */}
      {error && (
        <div className="mb-6 p-4 bg-red-900 border border-red-700 text-red-200 rounded-lg">
          {error}
        </div>
      )}

      {/* Loading State */}
      {loading && (
        <div className="text-center py-8">
          <div className="inline-block animate-spin rounded-full h-8 w-8 border-b-2 border-blue-500"></div>
          <p className="text-gray-400 mt-2">Loading activities...</p>
        </div>
      )}

      {/* Activities Table */}
      {!loading && activities.length > 0 && (
        <div className="overflow-x-auto border border-gray-700 rounded-lg">
          <table className="w-full text-sm">
            <thead className="bg-gradient-to-r from-gray-800 to-gray-700 border-b border-gray-700">
              <tr>
                <th className="px-4 py-3 text-left font-semibold text-gray-300">Truck</th>
                <th className="px-4 py-3 text-left font-semibold text-gray-300">Driver</th>
                <th className="px-4 py-3 text-left font-semibold text-gray-300">Activity Type</th>
                <th className="px-4 py-3 text-left font-semibold text-gray-300">Category</th>
                <th className="px-4 py-3 text-left font-semibold text-gray-300">Location</th>
                <th className="px-4 py-3 text-right font-semibold text-gray-300">Speed (km/h)</th>
                <th className="px-4 py-3 text-right font-semibold text-gray-300">Fuel %</th>
                <th className="px-4 py-3 text-center font-semibold text-gray-300">Alert</th>
                <th className="px-4 py-3 text-left font-semibold text-gray-300">Date/Time</th>
              </tr>
            </thead>
            <tbody>
              {activities.map((activity, index) => (
                <tr
                  key={activity.id}
                  className={`border-b border-gray-700 hover:bg-gray-700 transition ${
                    activity.is_critical ? 'bg-red-900 bg-opacity-20' : index % 2 === 0 ? 'bg-gray-800' : 'bg-gray-750'
                  }`}
                >
                  <td className="px-4 py-3 font-semibold text-gray-200">{activity.truck_identifier || '—'}</td>
                  <td className="px-4 py-3 text-gray-300">{activity.driver_name || '—'}</td>
                  <td className="px-4 py-3">
                    <span className={`inline-block px-2 py-1 rounded text-xs font-semibold ${getCategoryColor(activity.activity_category)}`}>
                      {activity.activity_type_display}
                    </span>
                  </td>
                  <td className="px-4 py-3">
                    <span className="inline-block px-2 py-1 rounded text-xs font-semibold capitalize bg-blue-900 text-blue-200">
                      {activity.activity_category}
                    </span>
                  </td>
                  <td className="px-4 py-3 text-gray-300 text-xs">{activity.location || '—'}</td>
                  <td className="px-4 py-3 text-right font-semibold text-gray-200">
                    {Number.isFinite(activity.speed_kmh) ? Number(activity.speed_kmh).toFixed(1) : '—'}
                  </td>
                  <td className="px-4 py-3 text-right font-semibold text-gray-200">
                    {Number.isFinite(activity.fuel_percentage) ? Number(activity.fuel_percentage).toFixed(1) : '—'}
                  </td>
                  <td className="px-4 py-3 text-center">
                    <div className="flex items-center justify-center gap-1">
                      {activity.is_critical && <span className="text-red-400 font-bold">🚨</span>}
                      {activity.alert_level && (
                        <span className={`text-xs font-semibold capitalize ${getAlertLevelColor(activity.alert_level)}`}>
                          {activity.alert_level}
                        </span>
                      )}
                    </div>
                  </td>
                  <td className="px-4 py-3 text-gray-300 text-xs">
                    {new Date(activity.timestamp).toLocaleString()}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}

      {/* Empty State */}
      {!loading && activities.length === 0 && (
        <div className="text-center py-12 bg-gray-800 rounded-lg border border-gray-700">
          <p className="text-gray-300 text-lg">No activities found for the selected filters</p>
          <p className="text-gray-500 text-sm mt-2">Adjust your filters or date range to find activities</p>
        </div>
      )}

      {/* Pagination Info */}
      {totalCount > 0 && (
        <div className="mt-4 p-4 bg-gray-800 rounded-lg border border-gray-700 text-center text-sm text-gray-400">
          Showing {activities.length} of {totalCount} activities • Last {filters.days} day(s)
        </div>
      )}
    </div>
  );
};

export default ActivityTable;
