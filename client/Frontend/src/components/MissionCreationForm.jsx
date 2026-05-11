import { useState } from 'react';
import axios from 'axios';

const getApiV1Base = () => {
  if (import.meta.env.MODE === 'development') return 'http://localhost:8000/api/v1';
  return 'https://musical-broccoli-production.up.railway.app/api/v1';
};

/**
 * MissionCreationForm Component
 * 
 * Allows users to create new missions for trucks and drivers
 */
export default function MissionCreationForm({ trucks, drivers, onMissionCreated, onClose }) {
  const [formData, setFormData] = useState({
    identifier: '',
    truck_id: '',
    driver_id: '',
    origin: { lat: '', lon: '' },
    destination: { lat: '', lon: '' },
    planned_distance_km: '',
    planned_duration_minutes: '',
    notes: '',
  });

  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  const [success, setSuccess] = useState(false);

  const handleInputChange = (e) => {
    const { name, value } = e.target;
    
    if (name.startsWith('origin_')) {
      const key = name.replace('origin_', '');
      setFormData(prev => ({
        ...prev,
        origin: {
          ...prev.origin,
          [key]: parseFloat(value) || '',
        }
      }));
    } else if (name.startsWith('destination_')) {
      const key = name.replace('destination_', '');
      setFormData(prev => ({
        ...prev,
        destination: {
          ...prev.destination,
          [key]: parseFloat(value) || '',
        }
      }));
    } else {
      setFormData(prev => ({
        ...prev,
        [name]: value,
      }));
    }
  };

  const validateForm = () => {
    if (!formData.truck_id) return 'Please select a truck';
    if (!formData.driver_id) return 'Please select a driver';
    if (!formData.origin.lat || !formData.origin.lon) return 'Please enter origin coordinates';
    if (!formData.destination.lat || !formData.destination.lon) return 'Please enter destination coordinates';
    if (!formData.planned_distance_km) return 'Please enter planned distance';
    if (!formData.planned_duration_minutes) return 'Please enter planned duration';
    return null;
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    
    const validationError = validateForm();
    if (validationError) {
      setError(validationError);
      return;
    }

    setLoading(true);
    setError(null);

    try {
      const apiUrl = `${getApiV1Base()}/api-missions/create/`;
      console.log('📝 Creating mission at:', apiUrl);
      console.log('📦 Mission data:', formData);

      const response = await axios.post(apiUrl, {
        identifier: formData.identifier || `MIS-${Date.now()}`,
        truck_id: formData.truck_id,
        driver_id: formData.driver_id,
        status: 'pending',
        origin: {
          lat: formData.origin.lat,
          lon: formData.origin.lon,
        },
        destination: {
          lat: formData.destination.lat,
          lon: formData.destination.lon,
        },
        planned_distance_km: parseFloat(formData.planned_distance_km),
        planned_duration_minutes: parseInt(formData.planned_duration_minutes),
        notes: formData.notes,
      });

      console.log('✅ Mission created successfully:', response.data);
      setSuccess(true);

      if (onMissionCreated) {
        onMissionCreated(response.data);
      }

      // Reset form
      setFormData({
        identifier: '',
        truck_id: '',
        driver_id: '',
        origin: { lat: '', lon: '' },
        destination: { lat: '', lon: '' },
        planned_distance_km: '',
        planned_duration_minutes: '',
        notes: '',
      });

      // Close after 2 seconds
      setTimeout(() => {
        if (onClose) onClose();
      }, 2000);
    } catch (err) {
      console.error('❌ Mission creation error:', err.response?.data || err.message);
      setError(err.response?.data?.error || err.message || 'Failed to create mission');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="fixed inset-0 bg-black/50 backdrop-blur-sm z-50 flex items-center justify-center p-4">
      <div className="bg-slate-900 border border-slate-700 rounded-lg shadow-xl max-w-2xl w-full max-h-[90vh] overflow-y-auto">
        {/* Header */}
        <div className="sticky top-0 bg-slate-900 border-b border-slate-700 px-6 py-4 flex justify-between items-center">
          <h2 className="text-xl font-bold text-white">Create New Mission</h2>
          <button
            onClick={onClose}
            className="text-slate-400 hover:text-white transition"
          >
            ✕
          </button>
        </div>

        {/* Form */}
        <form onSubmit={handleSubmit} className="p-6 space-y-5">
          {/* Success Message */}
          {success && (
            <div className="bg-green-900/30 border border-green-600 rounded p-4 text-green-300">
              ✅ Mission created successfully!
            </div>
          )}

          {/* Error Message */}
          {error && (
            <div className="bg-red-900/30 border border-red-600 rounded p-4 text-red-300">
              ❌ {error}
            </div>
          )}

          {/* Truck Selection */}
          <div>
            <label className="block text-sm font-semibold text-slate-300 mb-2">
              Truck <span className="text-red-400">*</span>
            </label>
            <select
              name="truck_id"
              value={formData.truck_id}
              onChange={handleInputChange}
              className="w-full bg-slate-800 border border-slate-600 text-white px-4 py-2 rounded focus:outline-none focus:border-blue-500"
            >
              <option value="">Select a truck...</option>
              {trucks?.map(truck => (
                <option key={truck.id} value={truck.id}>
                  {truck.truck_identifier} ({truck.plate})
                </option>
              ))}
            </select>
          </div>

          {/* Driver Selection */}
          <div>
            <label className="block text-sm font-semibold text-slate-300 mb-2">
              Driver <span className="text-red-400">*</span>
            </label>
            <select
              name="driver_id"
              value={formData.driver_id}
              onChange={handleInputChange}
              className="w-full bg-slate-800 border border-slate-600 text-white px-4 py-2 rounded focus:outline-none focus:border-blue-500"
            >
              <option value="">Select a driver...</option>
              {drivers?.map(driver => (
                <option key={driver.id} value={driver.id}>
                  {driver.first_name} {driver.last_name} ({driver.phone_number})
                </option>
              ))}
            </select>
          </div>

          {/* Mission Identifier */}
          <div>
            <label className="block text-sm font-semibold text-slate-300 mb-2">
              Mission ID (Optional)
            </label>
            <input
              type="text"
              name="identifier"
              placeholder="e.g., MIS-001"
              value={formData.identifier}
              onChange={handleInputChange}
              className="w-full bg-slate-800 border border-slate-600 text-white px-4 py-2 rounded focus:outline-none focus:border-blue-500 placeholder-slate-500"
            />
          </div>

          {/* Origin Coordinates */}
          <div className="grid grid-cols-2 gap-3">
            <div>
              <label className="block text-sm font-semibold text-slate-300 mb-2">
                Origin Latitude <span className="text-red-400">*</span>
              </label>
              <input
                type="number"
                name="origin_lat"
                step="0.0001"
                placeholder="-17.8"
                value={formData.origin.lat}
                onChange={handleInputChange}
                className="w-full bg-slate-800 border border-slate-600 text-white px-4 py-2 rounded focus:outline-none focus:border-blue-500 placeholder-slate-500"
              />
            </div>
            <div>
              <label className="block text-sm font-semibold text-slate-300 mb-2">
                Origin Longitude <span className="text-red-400">*</span>
              </label>
              <input
                type="number"
                name="origin_lon"
                step="0.0001"
                placeholder="31.0"
                value={formData.origin.lon}
                onChange={handleInputChange}
                className="w-full bg-slate-800 border border-slate-600 text-white px-4 py-2 rounded focus:outline-none focus:border-blue-500 placeholder-slate-500"
              />
            </div>
          </div>

          {/* Destination Coordinates */}
          <div className="grid grid-cols-2 gap-3">
            <div>
              <label className="block text-sm font-semibold text-slate-300 mb-2">
                Destination Latitude <span className="text-red-400">*</span>
              </label>
              <input
                type="number"
                name="destination_lat"
                step="0.0001"
                placeholder="-17.9"
                value={formData.destination.lat}
                onChange={handleInputChange}
                className="w-full bg-slate-800 border border-slate-600 text-white px-4 py-2 rounded focus:outline-none focus:border-blue-500 placeholder-slate-500"
              />
            </div>
            <div>
              <label className="block text-sm font-semibold text-slate-300 mb-2">
                Destination Longitude <span className="text-red-400">*</span>
              </label>
              <input
                type="number"
                name="destination_lon"
                step="0.0001"
                placeholder="31.1"
                value={formData.destination.lon}
                onChange={handleInputChange}
                className="w-full bg-slate-800 border border-slate-600 text-white px-4 py-2 rounded focus:outline-none focus:border-blue-500 placeholder-slate-500"
              />
            </div>
          </div>

          {/* Distance and Duration */}
          <div className="grid grid-cols-2 gap-3">
            <div>
              <label className="block text-sm font-semibold text-slate-300 mb-2">
                Planned Distance (km) <span className="text-red-400">*</span>
              </label>
              <input
                type="number"
                name="planned_distance_km"
                min="0"
                step="0.1"
                placeholder="50"
                value={formData.planned_distance_km}
                onChange={handleInputChange}
                className="w-full bg-slate-800 border border-slate-600 text-white px-4 py-2 rounded focus:outline-none focus:border-blue-500 placeholder-slate-500"
              />
            </div>
            <div>
              <label className="block text-sm font-semibold text-slate-300 mb-2">
                Planned Duration (minutes) <span className="text-red-400">*</span>
              </label>
              <input
                type="number"
                name="planned_duration_minutes"
                min="0"
                step="1"
                placeholder="120"
                value={formData.planned_duration_minutes}
                onChange={handleInputChange}
                className="w-full bg-slate-800 border border-slate-600 text-white px-4 py-2 rounded focus:outline-none focus:border-blue-500 placeholder-slate-500"
              />
            </div>
          </div>

          {/* Notes */}
          <div>
            <label className="block text-sm font-semibold text-slate-300 mb-2">
              Notes (Optional)
            </label>
            <textarea
              name="notes"
              rows="3"
              placeholder="Add any additional mission notes..."
              value={formData.notes}
              onChange={handleInputChange}
              className="w-full bg-slate-800 border border-slate-600 text-white px-4 py-2 rounded focus:outline-none focus:border-blue-500 placeholder-slate-500"
            />
          </div>

          {/* Action Buttons */}
          <div className="flex gap-3 pt-4 border-t border-slate-700">
            <button
              type="button"
              onClick={onClose}
              className="flex-1 px-4 py-2 bg-slate-700 hover:bg-slate-600 text-white rounded transition font-semibold"
            >
              Cancel
            </button>
            <button
              type="submit"
              disabled={loading}
              className="flex-1 px-4 py-2 bg-blue-600 hover:bg-blue-500 disabled:bg-blue-800 text-white rounded transition font-semibold"
            >
              {loading ? 'Creating...' : 'Create Mission'}
            </button>
          </div>
        </form>
      </div>
    </div>
  );
}
