import { useState, useEffect } from "react";
import { Plus, Edit2, Trash2, X, Save, AlertCircle } from "lucide-react";
import { getV1Trucks, updateV1Truck, createV1Truck, deleteV1Truck } from '../services/api';

export default function TruckAdmin() {
  const [trucks, setTrucks] = useState([]);
  const [showForm, setShowForm] = useState(false);
  const [editingId, setEditingId] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  const [success, setSuccess] = useState(null);

  // ✅ UPDATED: Form data matches FleetTruck model fields
  const [formData, setFormData] = useState({
    truck_identifier: '',
    plate: '',
    make: '',
    model: '',
    year: new Date().getFullYear(),
    vin: '',
    telematics_id: '',
    fuel_capacity_liters: 100,
    maintenance_due_date: '',
    status: 'IDLE'
  });

  const statusOptions = ['IDLE', 'ENROUTE', 'MAINTENANCE', 'DECOMMISSIONED'];

  // ✅ UPDATED: Fetch trucks on mount AND when data changes
  useEffect(() => {
    fetchTrucks();
  }, []);

  const fetchTrucks = async () => {
    try {
      console.log('📥 [API] Fetching trucks from v1 API...');
      const data = await getV1Trucks();
      console.log('✅ [API] Trucks fetched:', data);
      setTrucks(Array.isArray(data) ? data : []);
    } catch (error) {
      console.error('❌ [API] Error fetching trucks:', error);
      setError('Failed to load trucks');
    }
  };

  const handleInputChange = (e) => {
    const { name, value } = e.target;
    setFormData(prev => ({
      ...prev,
      [name]: name === 'year' ? parseInt(value) : value
    }));
  };

  // ✅ UPDATED: Load truck data matching FleetTruck model
  const handleEdit = (truck) => {
    setFormData({
      truck_identifier: truck.truck_identifier || '',
      plate: truck.plate || '',
      make: truck.make || '',
      model: truck.model || '',
      year: truck.year || new Date().getFullYear(),
      vin: truck.vin || '',
      telematics_id: truck.telematics_id || '',
      fuel_capacity_liters: truck.fuel_capacity_liters || 100,
      maintenance_due_date: truck.maintenance_due_date || '',
      status: truck.status || 'IDLE'
    });
    setEditingId(truck.id);
    setShowForm(true);
  };

  const handleAddNew = () => {
    setFormData({
      truck_identifier: '',
      plate: '',
      make: '',
      model: '',
      year: new Date().getFullYear(),
      vin: '',
      telematics_id: '',
      fuel_capacity_liters: 100,
      maintenance_due_date: '',
      status: 'IDLE'
    });
    setEditingId(null);
    setShowForm(true);
  };

  // ✅ UPDATED: Submit handler with proper validation and v2 API
  const handleSubmit = async (e) => {
    e.preventDefault();
    console.log('📋 [FORM] Submit triggered');
    setLoading(true);
    setError(null);
    setSuccess(null);

    try {
      // ✅ VALIDATE: Check required fields
      if (!formData.truck_identifier || !formData.plate) {
        console.error('❌ [FORM] Validation failed - missing required fields');
        setError('Truck identifier and plate are required');
        setLoading(false);
        return;
      }

      console.log('✅ [FORM] Validation passed, formData:', JSON.stringify(formData, null, 2));

      if (editingId) {
        // Update existing truck
        console.log('📝 [FORM] Updating truck:', editingId);
        await updateV1Truck(editingId, formData);
        setSuccess(`✅ Truck ${formData.truck_identifier} updated successfully!`);
        setEditingId(null);
      } else {
        // ✅ NEW: Create with auto-generated UUID fleet_id
        const fleetId = 'xxxxxxxx-xxxx-4xxx-yxxx-xxxxxxxxxxxx'.replace(/[xy]/g, function(c) {
          const r = Math.random() * 16 | 0, v = c === 'x' ? r : (r & 0x3 | 0x8);
          return v.toString(16);
        });
        console.log('📝 [FORM] Creating new truck with fleetId:', fleetId);
        console.log('📝 [FORM] Truck data:', JSON.stringify({ ...formData, fleet_id: fleetId }, null, 2));
        const result = await createV1Truck({ ...formData, fleet_id: fleetId });
        console.log('✅ [FORM] Truck created, result:', result);
        setSuccess(`✅ Truck ${formData.truck_identifier} created successfully!`);
        // Keep form open but clear fields for next entry
        setFormData({
          truck_identifier: '',
          plate: '',
          make: '',
          model: '',
          year: new Date().getFullYear(),
          vin: '',
          telematics_id: '',
          fuel_capacity_liters: 100,
          maintenance_due_date: '',
          status: 'IDLE'
        });
      }

      await fetchTrucks();
      setTimeout(() => {
        setSuccess(null);
        if (editingId) setShowForm(false);
      }, 5000);
    } catch (err) {
      console.error('❌ [FORM ERROR] Error saving truck:', err);
      console.error('   Error type:', err.name);
      console.error('   Error message:', err.message);
      console.error('   Full error response:', err.response?.data);
      console.error('   Response status:', err.response?.status);
      console.error('   Response headers:', err.response?.headers);
      
      // Extract detailed error message
      let errorMsg = 'Failed to save truck';
      if (err.response?.data?.error) {
        errorMsg = err.response.data.error;
      } else if (err.response?.data?.detail) {
        errorMsg = err.response.data.detail;
      } else if (err.response?.data) {
        errorMsg = Object.entries(err.response.data)
          .map(([key, value]) => `${key}: ${Array.isArray(value) ? value.join(', ') : value}`)
          .join(' | ');
      } else if (err.message) {
        errorMsg = err.message;
      }
      
      console.error('   Extracted error message:', errorMsg);
      setError(`⚠️ Failed to save truck: ${errorMsg}`);
      setTimeout(() => setError(null), 10000);
    } finally {
      setLoading(false);
    }
  };

  const handleCancel = () => {
    setShowForm(false);
    setEditingId(null);
    setError(null);
  };

  const handleDelete = async (truckId, identifier) => {
    if (window.confirm(`Are you sure you want to delete truck ${identifier}?`)) {
      try {
        setLoading(true);
        await deleteV1Truck(truckId);
        setSuccess(`✅ Truck ${identifier} deleted successfully!`);
        await fetchTrucks();
        setTimeout(() => setSuccess(null), 3000);
      } catch (err) {
        setError(`Failed to delete truck: ${err.message}`);
        console.error('Error deleting truck:', err);
      } finally {
        setLoading(false);
      }
    }
  };

  return (
    <div className="bg-bg text-text min-h-screen p-6">
      <div className="max-w-6xl mx-auto space-y-6">
        {/* Header */}
        <div className="flex items-center justify-between mb-8">
          <div>
            <h1 className="text-3xl font-heading font-bold text-text1">Fleet Trucks</h1>
            <p className="text-text3 mt-2">Add and manage trucks in your fleet</p>
          </div>
          <button
            onClick={handleAddNew}
            disabled={showForm}
            className="flex items-center gap-2 px-4 py-2 bg-blue/20 border border-blue/40 text-blue rounded-lg hover:bg-blue/30 transition-all disabled:opacity-50"
          >
            <Plus className="w-4 h-4" />
            Add Truck
          </button>
        </div>

        {/* Success/Error Messages */}
        {success && (
          <div className="p-4 bg-green/10 border border-green/40 rounded-lg flex items-center gap-3 text-green">
            <AlertCircle className="w-5 h-5" />
            <span>{success}</span>
          </div>
        )}
        {error && (
          <div className="p-4 bg-red/10 border border-red/40 rounded-lg flex items-center gap-3 text-red">
            <AlertCircle className="w-5 h-5" />
            <span>{error}</span>
          </div>
        )}

        {/* Form Modal */}
        {showForm && (
          <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50 p-4">
            <div className="bg-bg2 border border-border rounded-xl max-w-2xl w-full max-h-[90vh] overflow-y-auto glass">
              <div className="sticky top-0 px-6 py-4 border-b border-border flex items-center justify-between bg-bg2/95">
                <h2 className="text-xl font-heading font-bold text-text1">
                  {editingId ? 'Edit Truck' : 'Add New Truck'}
                </h2>
                <button
                  onClick={handleCancel}
                  className="text-text3 hover:text-text2"
                >
                  <X className="w-5 h-5" />
                </button>
              </div>

              {/* Form Content */}
              <form onSubmit={handleSubmit} className="p-6 space-y-4">
                {/* 2-Column Grid Layout */}
                <div className="grid grid-cols-2 gap-4">
                  {/* Truck Identifier */}
                  <div>
                    <label className="block text-sm font-mono text-text3 mb-2">Truck Identifier *</label>
                    <input
                      type="text"
                      name="truck_identifier"
                      value={formData.truck_identifier}
                      onChange={handleInputChange}
                      placeholder="TRK-001"
                      required
                      className="w-full px-3 py-2 bg-bg3 border border-border2 rounded-lg text-text1 placeholder-text3 focus:outline-none focus:border-blue"
                    />
                  </div>

                  {/* License Plate */}
                  <div>
                    <label className="block text-sm font-mono text-text3 mb-2">License Plate *</label>
                    <input
                      type="text"
                      name="plate"
                      value={formData.plate}
                      onChange={handleInputChange}
                      placeholder="ZW-ABC-123"
                      required
                      className="w-full px-3 py-2 bg-bg3 border border-border2 rounded-lg text-text1 placeholder-text3 focus:outline-none focus:border-blue"
                    />
                  </div>

                  {/* Make */}
                  <div>
                    <label className="block text-sm font-mono text-text3 mb-2">Make</label>
                    <input
                      type="text"
                      name="make"
                      value={formData.make}
                      onChange={handleInputChange}
                      placeholder="Volvo"
                      className="w-full px-3 py-2 bg-bg3 border border-border2 rounded-lg text-text1 placeholder-text3 focus:outline-none focus:border-blue"
                    />
                  </div>

                  {/* Model */}
                  <div>
                    <label className="block text-sm font-mono text-text3 mb-2">Model</label>
                    <input
                      type="text"
                      name="model"
                      value={formData.model}
                      onChange={handleInputChange}
                      placeholder="FH16"
                      className="w-full px-3 py-2 bg-bg3 border border-border2 rounded-lg text-text1 placeholder-text3 focus:outline-none focus:border-blue"
                    />
                  </div>

                  {/* Year */}
                  <div>
                    <label className="block text-sm font-mono text-text3 mb-2">Year</label>
                    <input
                      type="number"
                      name="year"
                      value={formData.year}
                      onChange={handleInputChange}
                      placeholder="2024"
                      className="w-full px-3 py-2 bg-bg3 border border-border2 rounded-lg text-text1 placeholder-text3 focus:outline-none focus:border-blue"
                    />
                  </div>

                  {/* VIN */}
                  <div>
                    <label className="block text-sm font-mono text-text3 mb-2">VIN</label>
                    <input
                      type="text"
                      name="vin"
                      value={formData.vin}
                      onChange={handleInputChange}
                      placeholder="VIN123456789"
                      className="w-full px-3 py-2 bg-bg3 border border-border2 rounded-lg text-text1 placeholder-text3 focus:outline-none focus:border-blue"
                    />
                  </div>

                  {/* Telematics ID */}
                  <div>
                    <label className="block text-sm font-mono text-text3 mb-2">Telematics ID</label>
                    <input
                      type="text"
                      name="telematics_id"
                      value={formData.telematics_id}
                      onChange={handleInputChange}
                      placeholder="TEL-001"
                      className="w-full px-3 py-2 bg-bg3 border border-border2 rounded-lg text-text1 placeholder-text3 focus:outline-none focus:border-blue"
                    />
                  </div>

                  {/* Fuel Capacity */}
                  <div>
                    <label className="block text-sm font-mono text-text3 mb-2">Fuel Capacity (L)</label>
                    <input
                      type="number"
                      name="fuel_capacity_liters"
                      value={formData.fuel_capacity_liters}
                      onChange={handleInputChange}
                      placeholder="100"
                      className="w-full px-3 py-2 bg-bg3 border border-border2 rounded-lg text-text1 placeholder-text3 focus:outline-none focus:border-blue"
                    />
                  </div>

                  {/* Status */}
                  <div>
                    <label className="block text-sm font-mono text-text3 mb-2">Status</label>
                    <select
                      name="status"
                      value={formData.status}
                      onChange={handleInputChange}
                      className="w-full px-3 py-2 bg-bg3 border border-border2 rounded-lg text-text1 focus:outline-none focus:border-blue appearance-none cursor-pointer"
                    >
                      {statusOptions.map(status => (
                        <option key={status} value={status}>
                          {status}
                        </option>
                      ))}
                    </select>
                  </div>

                  {/* Maintenance Due Date */}
                  <div className="col-span-2">
                    <label className="block text-sm font-mono text-text3 mb-2">Maintenance Due Date</label>
                    <input
                      type="date"
                      name="maintenance_due_date"
                      value={formData.maintenance_due_date}
                      onChange={handleInputChange}
                      className="w-full px-3 py-2 bg-bg3 border border-border2 rounded-lg text-text1 placeholder-text3 focus:outline-none focus:border-blue"
                    />
                  </div>
                </div>

                {/* Form Actions */}
                <div className="flex gap-3 pt-4 border-t border-border">
                  <button
                    type="submit"
                    disabled={loading}
                    className="flex-1 flex items-center justify-center gap-2 px-4 py-2 bg-blue/20 border border-blue/40 text-blue rounded-lg hover:bg-blue/30 transition-all disabled:opacity-50"
                  >
                    <Save className="w-4 h-4" />
                    {loading ? 'Saving...' : 'Save Truck'}
                  </button>
                  <button
                    type="button"
                    onClick={handleCancel}
                    className="flex-1 px-4 py-2 bg-bg3 border border-border2 text-text2 rounded-lg hover:bg-bg3/80 transition-all"
                  >
                    Cancel
                  </button>
                </div>
              </form>
            </div>
          </div>
        )}

        {/* Trucks Table */}
        <div className="border border-border rounded-lg overflow-hidden">
          <div className="overflow-x-auto">
            <table className="w-full text-sm">
              <thead className="bg-bg3 border-b border-border">
                <tr>
                  <th className="px-6 py-3 text-left font-mono text-text3">Identifier</th>
                  <th className="px-6 py-3 text-left font-mono text-text3">Plate</th>
                  <th className="px-6 py-3 text-left font-mono text-text3">Make / Model</th>
                  <th className="px-6 py-3 text-left font-mono text-text3">Status</th>
                  <th className="px-6 py-3 text-left font-mono text-text3">Fuel Capacity</th>
                  <th className="px-6 py-3 text-center font-mono text-text3">Actions</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-border">
                {trucks.length === 0 ? (
                  <tr>
                    <td colSpan="6" className="px-6 py-8 text-center text-text3">
                      No trucks found. Create your first truck!
                    </td>
                  </tr>
                ) : (
                  trucks.map(truck => (
                    <tr key={truck.id} className="hover:bg-bg3/50 transition-colors">
                      <td className="px-6 py-3 font-mono text-text1">{truck.truck_identifier}</td>
                      <td className="px-6 py-3 font-mono text-text1">{truck.plate}</td>
                      <td className="px-6 py-3 text-text2">
                        {truck.make} {truck.model}
                      </td>
                      <td className="px-6 py-3">
                        <span className="px-2 py-1 rounded text-xs font-mono bg-bg3 text-text2">
                          {truck.status}
                        </span>
                      </td>
                      <td className="px-6 py-3 font-mono text-text2">{truck.fuel_capacity_liters}L</td>
                      <td className="px-6 py-3 flex items-center justify-center gap-2">
                        <button
                          onClick={() => handleEdit(truck)}
                          className="p-2 hover:bg-bg3 rounded transition-colors text-blue"
                          title="Edit"
                        >
                          <Edit2 className="w-4 h-4" />
                        </button>
                        <button
                          onClick={() => handleDelete(truck.id, truck.truck_identifier)}
                          className="p-2 hover:bg-bg3 rounded transition-colors text-red"
                          title="Delete"
                        >
                          <Trash2 className="w-4 h-4" />
                        </button>
                      </td>
                    </tr>
                  ))
                )}
              </tbody>
            </table>
          </div>
        </div>
      </div>
    </div>
  );
}
        setSuccess(`Truck ${formData.plate} updated successfully!`);
      } else {
        // Create new truck with auto-generated ID if not provided
        const truckId = formData.id.trim() || `TRUCK-${Date.now()}-${Math.random().toString(36).substr(2, 9)}`;
        await createTruck({
          id: truckId,
          plate: formData.plate,
          driver: formData.driver,
          status: formData.status,
          location: formData.location,
          speed: parseInt(formData.speed),
          eta: formData.eta,
          progress: parseInt(formData.progress),
          cargo: formData.cargo,
          weight: formData.weight,
          coordinates: coordinates,
          origin_coordinates: originCoordinates,
          destination_coordinates: destinationCoordinates,
          origin: formData.origin,
          destination: formData.destination,
        });
        setSuccess(`Truck ${formData.plate} created successfully!`);
      }

      await fetchTrucks();
      setShowForm(false);
      setTimeout(() => setSuccess(null), 3000);
    } catch (err) {
      setError(err.message || 'Failed to save truck');
      console.error('Error saving truck:', err);
    } finally {
      setLoading(false);
    }
  };

  const handleCancel = () => {
    setShowForm(false);
    setEditingId(null);
    setError(null);
  };

  const handleDelete = async (truckId, plate) => {
    if (window.confirm(`Are you sure you want to delete truck ${plate}?`)) {
      try {
        setLoading(true);
        await deleteTruck(truckId);
        setSuccess(`Truck ${plate} deleted successfully!`);
        await fetchTrucks();
        setTimeout(() => setSuccess(null), 3000);
      } catch (err) {
        setError(`Failed to delete truck: ${err.message}`);
        console.error('Error deleting truck:', err);
      } finally {
        setLoading(false);
      }
    }
  };

  return (
    <div className="bg-bg text-text min-h-screen p-6">
      <div className="max-w-6xl mx-auto space-y-6">
        {/* Header */}
        <div className="flex items-center justify-between mb-8">
          <div>
            <h1 className="text-3xl font-heading font-bold text-text1">PulseTrack Management</h1>
            <p className="text-text3 mt-2">Add and manage trucks in your fleet</p>
          </div>
          <button
            onClick={handleAddNew}
            disabled={showForm}
            className="flex items-center gap-2 px-4 py-2 bg-blue/20 border border-blue/40 text-blue rounded-lg hover:bg-blue/30 transition-all disabled:opacity-50"
          >
            <Plus className="w-4 h-4" />
            Add Truck
          </button>
        </div>

        {/* Success/Error Messages */}
        {success && (
          <div className="p-4 bg-green/10 border border-green/40 rounded-lg flex items-center gap-3 text-green">
            <AlertCircle className="w-5 h-5" />
            <span>{success}</span>
          </div>
        )}
        {error && (
          <div className="p-4 bg-red/10 border border-red/40 rounded-lg flex items-center gap-3 text-red">
            <AlertCircle className="w-5 h-5" />
            <span>{error}</span>
          </div>
        )}

        {/* Form Modal */}
        {showForm && (
          <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50 p-4">
            <div className="bg-bg2 border border-border rounded-xl max-w-2xl w-full max-h-96 overflow-y-auto glass">
              <div className="sticky top-0 px-6 py-4 border-b border-border flex items-center justify-between bg-bg2/95">
                <h2 className="text-xl font-heading font-bold text-text1">
                  {editingId ? 'Edit Truck' : 'Add New Truck'}
                </h2>
                <button
                  onClick={handleCancel}
                  className="text-text3 hover:text-text2"
                >
                  <X className="w-5 h-5" />
                </button>
              </div>

              <form onSubmit={handleSubmit} className="p-6 space-y-4">
                <div className="grid grid-cols-2 gap-4">
                  {/* Truck ID */}
                  <div>
                    <label className="block text-sm font-mono text-text3 mb-2">Truck ID</label>
                    <input
                      type="text"
                      name="id"
                      value={formData.id}
                      onChange={handleInputChange}
                      disabled={editingId}
                      placeholder="TRK001"
                      required
                      className="w-full px-3 py-2 bg-bg3 border border-border2 rounded-lg text-text1 placeholder-text3 focus:outline-none focus:border-blue disabled:opacity-50"
                    />
                  </div>

                  {/* Plate */}
                  <div>
                    <label className="block text-sm font-mono text-text3 mb-2">License Plate</label>
                    <input
                      type="text"
                      name="plate"
                      value={formData.plate}
                      onChange={handleInputChange}
                      placeholder="ZW-ABC-123"
                      required
                      className="w-full px-3 py-2 bg-bg3 border border-border2 rounded-lg text-text1 placeholder-text3 focus:outline-none focus:border-blue"
                    />
                  </div>

                  {/* Driver */}
                  <div>
                    <label className="block text-sm font-mono text-text3 mb-2">Driver Name</label>
                    <input
                      type="text"
                      name="driver"
                      value={formData.driver}
                      onChange={handleInputChange}
                      placeholder="John Doe"
                      required
                      className="w-full px-3 py-2 bg-bg3 border border-border2 rounded-lg text-text1 placeholder-text3 focus:outline-none focus:border-blue"
                    />
                  </div>

                  {/* Status */}
                  <div>
                    <label className="block text-sm font-mono text-text3 mb-2">Status</label>
                    <select
                      name="status"
                      value={formData.status}
                      onChange={handleInputChange}
                      className="w-full px-3 py-2 bg-bg3 border border-border2 rounded-lg text-text1 focus:outline-none focus:border-blue appearance-none cursor-pointer"
                      style={{ colorScheme: 'dark' }}
                    >
                      {statusOptions.map(status => (
                        <option key={status} value={status}>
                          {status.charAt(0).toUpperCase() + status.slice(1)}
                        </option>
                      ))}
                    </select>
                  </div>

                  {/* Location */}
                  <div>
                    <label className="block text-sm font-mono text-text3 mb-2">Location</label>
                    <select
                      name="location"
                      value={formData.location}
                      onChange={handleInputChange}
                      className="w-full px-3 py-2 bg-slate-600 border border-border2 rounded-lg text-text1 focus:outline-none focus:border-blue appearance-none cursor-pointer"
                      style={{ colorScheme: 'light' }}
                    >
                      {locationList.map(loc => (
                        <option key={loc} value={loc}>{loc}</option>
                      ))}
                    </select>
                  </div>

                  {/* Origin */}
                  <div>
                    <label className="block text-sm font-mono text-text3 mb-2">Route Origin</label>
                    <select
                      name="origin"
                      value={formData.origin}
                      onChange={handleInputChange}
                      className="w-full px-3 py-2 bg-slate-600 border border-border2 rounded-lg text-text1 focus:outline-none focus:border-blue appearance-none cursor-pointer"
                      style={{ colorScheme: 'dark' }}
                    >
                      {locationList.map(loc => (
                        <option key={loc} value={loc}>{loc}</option>
                      ))}
                    </select>
                  </div>

                  {/* Destination */}
                  <div>
                    <label className="block text-sm font-mono text-text3 mb-2">Route Destination</label>
                    <select
                      name="destination"
                      value={formData.destination}
                      onChange={handleInputChange}
                      className="w-full px-3 py-2 bg-slate-600 border border-border2 rounded-lg text-text1 focus:outline-none focus:border-blue appearance-none cursor-pointer"
                      style={{ colorScheme: 'dark' }}
                    >
                      {locationList.map(loc => (
                        <option key={loc} value={loc}>{loc}</option>
                      ))}
                    </select>
                  </div>

                  {/* Speed */}
                  <div>
                    <label className="block text-sm font-mono text-text3 mb-2">Speed (km/h)</label>
                    <input
                      type="number"
                      name="speed"
                      value={formData.speed}
                      onChange={handleInputChange}
                      min="0"
                      max="200"
                      className="w-full px-3 py-2 bg-bg3 border border-border2 rounded-lg text-text1 focus:outline-none focus:border-blue"
                    />
                  </div>

                  {/* ETA */}
                  <div>
                    <label className="block text-sm font-mono text-text3 mb-2">ETA</label>
                    <input
                      type="date"
                      name="eta"
                      value={formData.eta}
                      onChange={handleInputChange}
                      className="w-full px-3 py-2 bg-bg3 border border-border2 rounded-lg text-text1 focus:outline-none focus:border-blue"
                    />
                  </div>

                  {/* Progress */}
                  <div>
                    <label className="block text-sm font-mono text-text3 mb-2">Progress (%)</label>
                    <input
                      type="number"
                      name="progress"
                      value={formData.progress}
                      onChange={handleInputChange}
                      min="0"
                      max="100"
                      className="w-full px-3 py-2 bg-bg3 border border-border2 rounded-lg text-text1 focus:outline-none focus:border-blue"
                    />
                  </div>

                  {/* Cargo */}
                  <div className="col-span-2">
                    <label className="block text-sm font-mono text-text3 mb-2">Cargo Type</label>
                    <input
                      type="text"
                      name="cargo"
                      value={formData.cargo}
                      onChange={handleInputChange}
                      placeholder="Electronics, Food, etc."
                      className="w-full px-3 py-2 bg-bg3 border border-border2 rounded-lg text-text1 placeholder-text3 focus:outline-none focus:border-blue"
                    />
                  </div>

                  {/* Weight */}
                  <div className="col-span-2">
                    <label className="block text-sm font-mono text-text3 mb-2">Weight</label>
                    <input
                      type="text"
                      name="weight"
                      value={formData.weight}
                      onChange={handleInputChange}
                      placeholder="5000kg"
                      className="w-full px-3 py-2 bg-bg3 border border-border2 rounded-lg text-text1 placeholder-text3 focus:outline-none focus:border-blue"
                    />
                  </div>
                </div>

                {/* Form Buttons */}
                <div className="flex gap-3 pt-4 border-t border-border">
                  <button
                    type="submit"
                    disabled={loading}
                    className="flex-1 flex items-center justify-center gap-2 px-4 py-2 bg-blue/20 border border-blue/40 text-blue rounded-lg hover:bg-blue/30 transition-all disabled:opacity-50"
                  >
                    <Save className="w-4 h-4" />
                    {loading ? 'Saving...' : 'Save'}
                  </button>
                  <button
                    type="button"
                    onClick={handleCancel}
                    className="flex-1 px-4 py-2 bg-bg3 border border-border2 text-text2 rounded-lg hover:bg-border/20 transition-all"
                  >
                    Cancel
                  </button>
                </div>
              </form>
            </div>
          </div>
        )}

        {/* Trucks Table */}
        <div className="bg-bg2/80 backdrop-blur-sm border border-border rounded-xl overflow-hidden glass">
          <div className="px-6 py-4 border-b border-border">
            <h2 className="text-lg font-heading font-semibold text-text1">All Trucks ({trucks.length})</h2>
          </div>
          
          <div className="overflow-x-auto">
            <table className="w-full">
              <thead>
                <tr className="border-b border-border/50 bg-bg3/50">
                  <th className="px-6 py-3 text-left text-xs font-mono text-text3 uppercase">ID</th>
                  <th className="px-6 py-3 text-left text-xs font-mono text-text3 uppercase">Plate</th>
                  <th className="px-6 py-3 text-left text-xs font-mono text-text3 uppercase">Driver</th>
                  <th className="px-6 py-3 text-left text-xs font-mono text-text3 uppercase">Status</th>
                  <th className="px-6 py-3 text-left text-xs font-mono text-text3 uppercase">Location</th>
                  <th className="px-6 py-3 text-left text-xs font-mono text-text3 uppercase">Speed</th>
                  <th className="px-6 py-3 text-left text-xs font-mono text-text3 uppercase">Progress</th>
                  <th className="px-6 py-3 text-left text-xs font-mono text-text3 uppercase">Actions</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-border/30">
                {trucks.length > 0 ? (
                  trucks.map(truck => (
                    <tr key={truck.id} className="hover:bg-bg3/50 transition-colors">
                      <td className="px-6 py-4 text-sm font-mono text-text2">{truck.id}</td>
                      <td className="px-6 py-4 text-sm text-text1 font-semibold">{truck.plate}</td>
                      <td className="px-6 py-4 text-sm text-text1">{truck.driver}</td>
                      <td className="px-6 py-4 text-sm">
                        <span className={`px-2 py-1 rounded text-xs font-semibold capitalize ${
                          truck.status === 'moving' ? 'bg-blue/20 text-blue' :
                          truck.status === 'delayed' ? 'bg-amber/20 text-amber' :
                          truck.status === 'stopped' ? 'bg-red/20 text-red' :
                          truck.status === 'delivered' ? 'bg-green/20 text-green' :
                          'bg-text3/20 text-text3'
                        }`}>
                          {truck.status}
                        </span>
                      </td>
                      <td className="px-6 py-4 text-sm text-text1">{truck.location}</td>
                      <td className="px-6 py-4 text-sm text-text2 font-mono">{truck.speed} km/h</td>
                      <td className="px-6 py-4 text-sm text-text2 font-mono">{truck.progress}%</td>
                      <td className="px-6 py-4 text-sm">
                        <div className="flex items-center gap-2">
                          <button
                            onClick={() => handleEdit(truck)}
                            disabled={showForm}
                            className="inline-flex items-center gap-1 px-3 py-1 text-blue/70 hover:text-blue disabled:opacity-50 transition-colors"
                            title="Edit"
                          >
                            <Edit2 className="w-4 h-4" />
                          </button>
                          <button
                            onClick={() => handleDelete(truck.id, truck.plate)}
                            disabled={showForm || loading}
                            className="inline-flex items-center gap-1 px-3 py-1 text-red/70 hover:text-red disabled:opacity-50 transition-colors"
                            title="Delete"
                          >
                            <Trash2 className="w-4 h-4" />
                          </button>
                        </div>
                      </td>
                    </tr>
                  ))
                ) : (
                  <tr>
                    <td colSpan="8" className="px-6 py-8 text-center text-text3">
                      No trucks found. Create one to get started.
                    </td>
                  </tr>
                )}
              </tbody>
            </table>
          </div>
        </div>
      </div>
    </div>
  );
}
