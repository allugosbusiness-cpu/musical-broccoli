import { useState } from 'react';
import axios from 'axios';
import { getCachedResults, setCachedResults } from '../data/locationCache';

const getApiV1Base = () => {
  if (import.meta.env.MODE === 'development') return 'http://localhost:8000/api/v1';
  return 'https://pulsetrack-back.onrender.com/api/v1';
};

/**
 * LocationAutocomplete Component
 * Provides dropdown suggestions for location selection
 */
function LocationAutocomplete({ label, value, searchQuery, suggestions, onSearch, onSelectLocation, type = 'origin' }) {
  return (
    <div className="relative">
      <label className="block text-sm font-semibold text-slate-300 mb-2">
        {label} <span className="text-red-400">*</span>
      </label>
      <input
        type="text"
        placeholder="Search for location (e.g., Mutare, school, butchery)..."
        value={searchQuery}
        onChange={(e) => onSearch(e.target.value, type)}
        className="w-full bg-slate-800 border border-slate-600 text-white px-4 py-2 rounded focus:outline-none focus:border-blue-500 placeholder-slate-500"
      />
      
      {/* Suggestions Dropdown */}
      {searchQuery.length > 1 && suggestions.length > 0 && (
        <div className="absolute top-full left-0 right-0 mt-1 bg-slate-800 border border-slate-600 rounded shadow-lg z-40">
          <div className="max-h-48 overflow-y-auto">
            {suggestions.map((loc, idx) => (
              <button
                key={idx}
                type="button"
                onClick={() => onSelectLocation(loc, type)}
                className="w-full px-4 py-2 hover:bg-slate-700 text-left text-white hover:text-blue-300 transition flex justify-between items-start"
              >
                <div>
                  <div className="font-semibold">{loc.name}</div>
                  <div className="text-xs text-slate-400">{loc.type} • {Number.isFinite(loc.lat) && Number.isFinite(loc.lon) ? `${Number(loc.lat).toFixed(4)}, ${Number(loc.lon).toFixed(4)}` : 'No coords'}</div>
                </div>
              </button>
            ))}
          </div>
        </div>
      )}
      
      {/* Selected Location Display */}
      {Number.isFinite(value?.lat) && Number.isFinite(value?.lon) && (
        <div className="mt-2 p-2 bg-slate-800 border border-slate-600 rounded text-sm text-slate-300">
          📍 {Number(value.lat).toFixed(4)}, {Number(value.lon).toFixed(4)}
        </div>
      )}
    </div>
  );
}

/**
 * MissionCreationForm Component
 * 
 * Allows users to create new missions for trucks and drivers
 * Includes location autocomplete for origin and destination
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
  
  // Location autocomplete state
  const [originSearch, setOriginSearch] = useState('');
  const [destinationSearch, setDestinationSearch] = useState('');
  const [originSuggestions, setOriginSuggestions] = useState([]);
  const [destinationSuggestions, setDestinationSuggestions] = useState([]);

  // Fetch location suggestions with client-side caching
  const fetchLocationSuggestions = async (query, type) => {
    if (query.length < 2) {
      if (type === 'origin') setOriginSuggestions([]);
      else setDestinationSuggestions([]);
      return;
    }

    // Check client cache first
    const cached = getCachedResults(query);
    if (cached) {
      console.log(`📍 Using cached results for "${query}"`);
      if (type === 'origin') {
        setOriginSuggestions(cached);
      } else {
        setDestinationSuggestions(cached);
      }
      return;
    }

    try {
      const response = await axios.get(`${getApiV1Base()}/locations/autocomplete/`, {
        params: { q: query, source: 'auto' }
      });
      
      const results = response.data.results || [];
      
      // Cache results client-side (reduce backend calls)
      if (results.length > 0) {
        setCachedResults(query, results);
      }
      
      if (type === 'origin') {
        setOriginSuggestions(results);
      } else {
        setDestinationSuggestions(results);
      }
    } catch (err) {
      console.error(`Location search error (${type}):`, err);
    }
  };

  const handleLocationSearch = (query, type) => {
    if (type === 'origin') {
      setOriginSearch(query);
    } else {
      setDestinationSearch(query);
    }
    fetchLocationSuggestions(query, type);
  };

  const handleSelectLocation = (location, type) => {
    setFormData(prev => ({
      ...prev,
      [type]: {
        lat: location.lat,
        lon: location.lon,
      }
    }));

    if (type === 'origin') {
      setOriginSearch(location.name);
      setOriginSuggestions([]);
    } else {
      setDestinationSearch(location.name);
      setDestinationSuggestions([]);
    }

    console.log(`📍 Selected ${type}:`, location);
  };

  const handleInputChange = (e) => {
    const { name, value } = e.target;
    
    if (name.startsWith('origin_')) {
      const key = name.replace('origin_', '');
      setFormData(prev => ({
        ...prev,
        origin: {
          ...prev.origin,
          [key]: value, // Store raw string value from input (will be parsed later)
        }
      }));
    } else if (name.startsWith('destination_')) {
      const key = name.replace('destination_', '');
      setFormData(prev => ({
        ...prev,
        destination: {
          ...prev.destination,
          [key]: value,
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
    if (formData.origin.lat === '' || formData.origin.lon === '') return 'Please enter origin coordinates';
    if (formData.destination.lat === '' || formData.destination.lon === '') return 'Please enter destination coordinates';
    if (formData.planned_distance_km === '') return 'Please enter planned distance';
    if (formData.planned_duration_minutes === '') return 'Please enter planned duration';
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
      const apiUrl = `${getApiV1Base()}/missions/`;
      
      // 🔑 CRITICAL: LOG THE ACTUAL PAYLOAD BEFORE SENDING
      // Payload matches what backend MissionSerializer.create() expects
      const payload = {
        mission_number: formData.identifier || `MIS-${Date.now()}`,
        truck: formData.truck_id,
        driver: formData.driver_id,
        status: 'planned',
        origin: {
          lat: parseFloat(formData.origin.lat),
          lon: parseFloat(formData.origin.lon),
        },
        destination: {
          lat: parseFloat(formData.destination.lat),
          lon: parseFloat(formData.destination.lon),
        },
        priority: 'normal',
      };
      
      console.log('📤 Sending mission payload:', payload);
      console.log('🔗 API URL:', apiUrl);

      const response = await axios.post(apiUrl, payload);

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
      setOriginSearch('');
      setDestinationSearch('');

      // Close after 2 seconds
      setTimeout(() => {
        if (onClose) onClose();
      }, 2000);
    } catch (err) {
      console.error('❌ Mission creation error:', err);
      // Log full error response for debugging
      if (err.response) {
        console.error('Error response data:', err.response.data);
        console.error('Error response status:', err.response.status);
        console.error('Error response headers:', err.response.headers);
      }
      setError(err.response?.data?.detail || err.response?.data?.error || err.message || 'Failed to create mission');
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

          {/* Origin Location with Autocomplete */}
          <LocationAutocomplete
            label="📍 Origin Location"
            value={formData.origin}
            searchQuery={originSearch}
            suggestions={originSuggestions}
            onSearch={handleLocationSearch}
            onSelectLocation={handleSelectLocation}
            type="origin"
          />

          {/* Manual Origin Coordinates (optional override) */}
          <div className="grid grid-cols-2 gap-3">
            <div>
              <label className="block text-xs font-semibold text-slate-400 mb-2">
                Origin Latitude (Manual)
              </label>
              <input
                type="number"
                name="origin_lat"
                step="0.0001"
                placeholder="-17.8"
                value={formData.origin.lat}
                onChange={handleInputChange}
                className="w-full bg-slate-800 border border-slate-600 text-white px-3 py-1.5 rounded text-sm focus:outline-none focus:border-blue-500 placeholder-slate-500"
              />
            </div>
            <div>
              <label className="block text-xs font-semibold text-slate-400 mb-2">
                Origin Longitude (Manual)
              </label>
              <input
                type="number"
                name="origin_lon"
                step="0.0001"
                placeholder="31.0"
                value={formData.origin.lon}
                onChange={handleInputChange}
                className="w-full bg-slate-800 border border-slate-600 text-white px-3 py-1.5 rounded text-sm focus:outline-none focus:border-blue-500 placeholder-slate-500"
              />
            </div>
          </div>

          {/* Destination Location with Autocomplete */}
          <LocationAutocomplete
            label="📍 Destination Location"
            value={formData.destination}
            searchQuery={destinationSearch}
            suggestions={destinationSuggestions}
            onSearch={handleLocationSearch}
            onSelectLocation={handleSelectLocation}
            type="destination"
          />

          {/* Manual Destination Coordinates (optional override) */}
          <div className="grid grid-cols-2 gap-3">
            <div>
              <label className="block text-xs font-semibold text-slate-400 mb-2">
                Destination Latitude (Manual)
              </label>
              <input
                type="number"
                name="destination_lat"
                step="0.0001"
                placeholder="-17.9"
                value={formData.destination.lat}
                onChange={handleInputChange}
                className="w-full bg-slate-800 border border-slate-600 text-white px-3 py-1.5 rounded text-sm focus:outline-none focus:border-blue-500 placeholder-slate-500"
              />
            </div>
            <div>
              <label className="block text-xs font-semibold text-slate-400 mb-2">
                Destination Longitude (Manual)
              </label>
              <input
                type="number"
                name="destination_lon"
                step="0.0001"
                placeholder="31.1"
                value={formData.destination.lon}
                onChange={handleInputChange}
                className="w-full bg-slate-800 border border-slate-600 text-white px-3 py-1.5 rounded text-sm focus:outline-none focus:border-blue-500 placeholder-slate-500"
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
