import React, { useState, useEffect } from 'react';
import axios from 'axios';
import { getApiV1Base } from '../utils/helpers';

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
      const params = {
        limit: ITEMS_PER_PAGE,
        days: filters.days,
      };

      if (filters.activity_type) params.activity_type = filters.activity_type;
      if (filters.activity_category) params.activity_category = filters.activity_category;
      if (filters.truck_id) params.truck_id = filters.truck_id;
      if (filters.driver_id) params.driver_id = filters.driver_id;

      const response = await axios.get(`${API_BASE}/v1/activities/`, { params });
      setActivities(response.data.activities || []);
      setTotalCount(response.data.total_count || 0);
    } catch (err) {
      console.error('Error fetching activities:', err);
      setError('Failed to load activities');
    } finally {
      setLoading(false);
    }
  };

  const fetchSummary = async () => {
    try {
      const response = await axios.get(`${API_BASE}/v1/activities/summary/`, {
        params: { days: filters.days },
      });
      setSummary(response.data);
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
      mission: 'bg-blue-100 text-blue-800',
      location: 'bg-green-100 text-green-800',
      speed: 'bg-yellow-100 text-yellow-800',
      fuel: 'bg-orange-100 text-orange-800',
      alert: 'bg-red-100 text-red-800',
      breach: 'bg-purple-100 text-purple-800',
      driver: 'bg-indigo-100 text-indigo-800',
      maintenance: 'bg-gray-100 text-gray-800',
      trail: 'bg-teal-100 text-teal-800',
      cargo: 'bg-pink-100 text-pink-800',
    };
    return colors[category] || 'bg-gray-100 text-gray-800';
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
    <div className="w-full max-w-7xl mx-auto p-4 bg-white rounded-lg shadow-lg">
      <h2 className="text-3xl font-bold mb-6 text-gray-800">📊 Activity Audit Trail</h2>

      {/* Summary Cards */}
      {summary && (
        <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mb-6">
          <div className="bg-gradient-to-br from-blue-50 to-blue-100 p-4 rounded-lg border border-blue-200">
            <div className="text-sm text-blue-600 font-semibold">Total Activities</div>
            <div className="text-3xl font-bold text-blue-800">{summary.total_activities}</div>
          </div>
          <div className="bg-gradient-to-br from-red-50 to-red-100 p-4 rounded-lg border border-red-200">
            <div className="text-sm text-red-600 font-semibold">Critical Events</div>
            <div className="text-3xl font-bold text-red-800">{summary.critical_count}</div>
          </div>
          <div className="bg-gradient-to-br from-green-50 to-green-100 p-4 rounded-lg border border-green-200">
            <div className="text-sm text-green-600 font-semibold">Trucks Active</div>
            <div className="text-3xl font-bold text-green-800">{Object.keys(summary.by_truck || {}).length}</div>
          </div>
          <div className="bg-gradient-to-br from-purple-50 to-purple-100 p-4 rounded-lg border border-purple-200">
            <div className="text-sm text-purple-600 font-semibold">Drivers Active</div>
            <div className="text-3xl font-bold text-purple-800">{Object.keys(summary.by_driver || {}).length}</div>
          </div>
        </div>
      )}

      {/* Filters */}
      <div className="grid grid-cols-1 md:grid-cols-5 gap-4 mb-6 p-4 bg-gray-50 rounded-lg border border-gray-200">
        <div>
          <label className="block text-sm font-semibold text-gray-700 mb-1">Days Range</label>
          <select
            name="days"
            value={filters.days}
            onChange={handleFilterChange}
            className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
          >
            <option value={1}>Last 24 Hours</option>
            <option value={7}>Last 7 Days</option>
            <option value={14}>Last 14 Days</option>
            <option value={30}>Last 30 Days</option>
            <option value={60}>Last 60 Days</option>
          </select>
        </div>
        <div>
          <label className="block text-sm font-semibold text-gray-700 mb-1">Category</label>
          <select
            name="activity_category"
            value={filters.activity_category}
            onChange={handleFilterChange}
            className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
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
          <label className="block text-sm font-semibold text-gray-700 mb-1">Activity Type</label>
          <select
            name="activity_type"
            value={filters.activity_type}
            onChange={handleFilterChange}
            className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
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
        <div className="mb-6 p-4 bg-red-100 border border-red-400 text-red-700 rounded-lg">
          {error}
        </div>
      )}

      {/* Loading State */}
      {loading && (
        <div className="text-center py-8">
          <div className="inline-block animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600"></div>
          <p className="text-gray-600 mt-2">Loading activities...</p>
        </div>
      )}

      {/* Activities Table */}
      {!loading && activities.length > 0 && (
        <div className="overflow-x-auto border border-gray-200 rounded-lg">
          <table className="w-full text-sm">
            <thead className="bg-gradient-to-r from-gray-100 to-gray-50 border-b border-gray-200">
              <tr>
                <th className="px-4 py-3 text-left font-semibold text-gray-700">Truck</th>
                <th className="px-4 py-3 text-left font-semibold text-gray-700">Driver</th>
                <th className="px-4 py-3 text-left font-semibold text-gray-700">Activity Type</th>
                <th className="px-4 py-3 text-left font-semibold text-gray-700">Category</th>
                <th className="px-4 py-3 text-left font-semibold text-gray-700">Location</th>
                <th className="px-4 py-3 text-right font-semibold text-gray-700">Speed (km/h)</th>
                <th className="px-4 py-3 text-right font-semibold text-gray-700">Fuel %</th>
                <th className="px-4 py-3 text-center font-semibold text-gray-700">Alert</th>
                <th className="px-4 py-3 text-left font-semibold text-gray-700">Date/Time</th>
              </tr>
            </thead>
            <tbody>
              {activities.map((activity, index) => (
                <tr
                  key={activity.id}
                  className={`border-b border-gray-200 hover:bg-blue-50 transition ${
                    activity.is_critical ? 'bg-red-50' : index % 2 === 0 ? 'bg-white' : 'bg-gray-50'
                  }`}
                >
                  <td className="px-4 py-3 font-semibold text-gray-800">{activity.truck_identifier || '—'}</td>
                  <td className="px-4 py-3 text-gray-700">{activity.driver_name || '—'}</td>
                  <td className="px-4 py-3">
                    <span className={`inline-block px-2 py-1 rounded text-xs font-semibold ${getCategoryColor(activity.activity_category)}`}>
                      {activity.activity_type_display}
                    </span>
                  </td>
                  <td className="px-4 py-3">
                    <span className="inline-block px-2 py-1 rounded text-xs font-semibold capitalize bg-blue-100 text-blue-800">
                      {activity.activity_category}
                    </span>
                  </td>
                  <td className="px-4 py-3 text-gray-700 text-xs">{activity.location || '—'}</td>
                  <td className="px-4 py-3 text-right font-semibold text-gray-800">
                    {activity.speed_kmh ? activity.speed_kmh.toFixed(1) : '—'}
                  </td>
                  <td className="px-4 py-3 text-right font-semibold text-gray-800">
                    {activity.fuel_percentage ? activity.fuel_percentage.toFixed(1) : '—'}
                  </td>
                  <td className="px-4 py-3 text-center">
                    <div className="flex items-center justify-center gap-1">
                      {activity.is_critical && <span className="text-red-600 font-bold">🚨</span>}
                      {activity.alert_level && (
                        <span className={`text-xs font-semibold capitalize ${getAlertLevelColor(activity.alert_level)}`}>
                          {activity.alert_level}
                        </span>
                      )}
                    </div>
                  </td>
                  <td className="px-4 py-3 text-gray-700 text-xs">
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
        <div className="text-center py-12 bg-gray-50 rounded-lg border border-gray-200">
          <p className="text-gray-600 text-lg">No activities found for the selected filters</p>
          <p className="text-gray-500 text-sm mt-2">Adjust your filters or date range to find activities</p>
        </div>
      )}

      {/* Pagination Info */}
      {totalCount > 0 && (
        <div className="mt-4 p-4 bg-gray-50 rounded-lg border border-gray-200 text-center text-sm text-gray-600">
          Showing {activities.length} of {totalCount} activities • Last {filters.days} day(s)
        </div>
      )}
    </div>
  );
};

export default ActivityTable;
