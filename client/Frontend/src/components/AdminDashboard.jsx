import { useState, useEffect, useCallback, useMemo } from 'react';
import { Plus, Edit2, Trash2, X, Save, AlertCircle, RefreshCw, Eye, QrCode, MapPin, Route, Navigation } from 'lucide-react';
import DriverQRCodeModal from './DriverQRCodeModal';
import TrailAuditViewer from './TrailAuditViewer';
import { ZIMBABWE_LOCATIONS } from '../data/zimbabweLocations';
import { 
  getV1Trucks, getV1Drivers, getV1Missions,
  getDashboardDrivers, getDashboardTrucks, getDashboardMissions, getDashboardSummary,
  createV1Truck, updateV1Truck, deleteV1Truck,
  createV1Driver, updateV1Driver, deleteV1Driver,
  createV1Mission, updateV1Mission, deleteV1Mission,
  recalculatePerformance, syncTruckData, updateTruckLocationTracking
} from '../services/api';

export default function AdminDashboard({ onSelectTruck = () => {}, onSelectDriver = () => {}, onDataChanged = () => {} }) {
  const [activeTab, setActiveTab] = useState('drivers');
  const [showTrailViewer, setShowTrailViewer] = useState(false);
  const [trailViewerTruckId, setTrailViewerTruckId] = useState(null);
  const [drivers, setDrivers] = useState([]);
  const [trucks, setTrucks] = useState([]);
  const [missions, setMissions] = useState([]);
  const [dashboardSummary, setDashboardSummary] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  const [success, setSuccess] = useState(null);
  const [selectedDriverForQR, setSelectedDriverForQR] = useState(null);
  const [selectedTruckForQR, setSelectedTruckForQR] = useState(null);
  const [selectedMissionForQR, setSelectedMissionForQR] = useState(null);
  
  // Pagination states - limit items per table to 20 for performance
  const ITEMS_PER_PAGE = 20;
  const driverPage = useMemo(() => drivers.slice(0, ITEMS_PER_PAGE), [drivers]);
  const trucksPage = useMemo(() => trucks.slice(0, ITEMS_PER_PAGE), [trucks]);
  const missionsPage = useMemo(() => missions.slice(0, ITEMS_PER_PAGE), [missions]);

  // Fetch data on mount AND tab change
  useEffect(() => {
    fetchData();
  }, [activeTab]);

  // Also fetch on component mount
  useEffect(() => {
    if (trucks.length === 0 && drivers.length === 0 && missions.length === 0) {
      fetchData();
    }
  }, []);

  const fetchData = async () => {
    setLoading(true);
    try {
      if (activeTab === 'drivers') {
        // Use dashboard endpoint for drivers with calculated performance
        const dashboardData = await getDashboardDrivers();
        setDrivers(Array.isArray(dashboardData) ? dashboardData : []);
      } else if (activeTab === 'trucks') {
        // Use dashboard endpoint for trucks with synced mission data
        const dashboardData = await getDashboardTrucks();
        setTrucks(Array.isArray(dashboardData) ? dashboardData : []);
      } else if (activeTab === 'missions') {
        // Fetch all dashboard data for missions tab
        const missionsData = await getDashboardMissions();
        setMissions(Array.isArray(missionsData) ? missionsData : []);
      }
      
      // Also fetch summary for main dashboard
      const summary = await getDashboardSummary();
      setDashboardSummary(summary);
      
      setError(null);
      // Trigger refresh in dashboard components
      onDataChanged();
    } catch (err) {
      console.error('Error fetching data:', err);
      setError('Failed to load data');
    } finally {
      setLoading(false);
    }
  };

  const handleDeleteDriver = async (id) => {
    if (!confirm('Are you sure?')) return;
    try {
      await deleteV1Driver(id);
      setDrivers(drivers.filter(d => d.id !== id));
      setSuccess('Driver deleted successfully');
    } catch (err) {
      setError('Failed to delete driver');
    }
  };

  const handleDeleteTruck = async (id) => {
    if (!confirm('Are you sure?')) return;
    try {
      await deleteV1Truck(id);
      setTrucks(trucks.filter(t => t.id !== id));
      setSuccess('Truck deleted successfully');
    } catch (err) {
      setError('Failed to delete truck');
    }
  };

  const handleDeleteMission = async (id) => {
    if (!confirm('Are you sure?')) return;
    try {
      await deleteV1Mission(id);
      setMissions(missions.filter(m => m.id !== id));
      setSuccess('Mission deleted successfully');
    } catch (err) {
      setError('Failed to delete mission');
    }
  };

  return (
    <div className="min-h-screen bg-gradient-to-br from-slate-900 to-slate-800 p-6">
      <div className="max-w-7xl mx-auto">
        {/* Header */}
        <div className="flex justify-between items-center mb-8">
          <div className="flex items-center gap-3">
            <h1 className="text-4xl font-bold text-white">PulseTrack Admin</h1>
            <span className="px-3 py-1 text-sm font-bold bg-gradient-to-r from-blue-600 to-cyan-600 text-white rounded-lg">V2</span>
          </div>
          <button
            onClick={fetchData}
            className="flex items-center gap-2 px-4 py-2 bg-blue-600 hover:bg-blue-700 text-white rounded-lg transition"
          >
            <RefreshCw size={18} />
            Refresh
          </button>
        </div>

        {/* Alerts */}
        {error && (
          <div className="mb-4 p-4 bg-red-900/50 border border-red-700 rounded-lg flex items-center gap-2 text-red-200">
            <AlertCircle size={18} />
            {error}
          </div>
        )}
        {success && (
          <div className="mb-4 p-4 bg-green-900/50 border border-green-700 rounded-lg text-green-200">
            {success}
          </div>
        )}

        {/* Tabs */}
        <div className="flex gap-4 mb-6 border-b border-slate-700">
          {['drivers', 'trucks', 'missions', 'trails'].map(tab => (
            <button
              key={tab}
              onClick={() => setActiveTab(tab)}
              className={`px-4 py-3 font-semibold transition ${
                activeTab === tab
                  ? 'text-blue-400 border-b-2 border-blue-400'
                  : 'text-slate-400 hover:text-slate-300'
              }`}
            >
              {tab.charAt(0).toUpperCase() + tab.slice(1)}
              {activeTab === tab && (
                <span className="ml-2 inline-block bg-blue-600 text-white text-xs px-2 py-1 rounded">
                  {activeTab === 'drivers' ? drivers.length : activeTab === 'trucks' ? trucks.length : missions.length}
                </span>
              )}
            </button>
          ))}
        </div>

        {/* Content */}
        <div className="bg-slate-800 rounded-lg overflow-hidden shadow-2xl">
          {loading ? (
            <div className="p-8 text-center text-slate-400">
              <div className="inline-block animate-spin">⏳</div> Loading data...
            </div>
          ) : activeTab === 'drivers' ? (
            <DriversTable drivers={driverPage} totalCount={drivers.length} onDelete={handleDeleteDriver} onRefresh={fetchData} onSelectDriver={onSelectDriver} onSelectDriverForQR={setSelectedDriverForQR} onSelectTruckForQR={setSelectedTruckForQR} onSelectMissionForQR={setSelectedMissionForQR} />
          ) : activeTab === 'trucks' ? (
            <TrucksTable trucks={trucksPage} totalCount={trucks.length} onDelete={handleDeleteTruck} onRefresh={fetchData} onSelectTruck={onSelectTruck} />
          ) : activeTab === 'trails' ? (
            <div className="p-8 text-center">
              <Route size={48} className="mx-auto mb-4 text-blue-400" />
              <h2 className="text-2xl font-bold text-white mb-2">Trail & Audit Viewer</h2>
              <p className="text-slate-400 mb-6 max-w-lg mx-auto">
                View the full GPS trail of where each truck has been, including audit trail logs 
                recorded from the mobile app. See distance traveled, speed stats, and activity timeline.
              </p>
              <button
                onClick={() => setShowTrailViewer(true)}
                className="px-6 py-3 bg-blue-600 hover:bg-blue-700 text-white rounded-lg font-bold transition flex items-center gap-2 mx-auto"
              >
                <Route size={20} />
                Open Trail & Audit Viewer
              </button>
            </div>
          ) : (
            <MissionsTable missions={missionsPage} totalCount={missions.length} trucks={trucksPage} onDelete={handleDeleteMission} onRefresh={fetchData} />
          )}
        </div>
      </div>

      {/* Trail & Audit Viewer Modal */}
      {showTrailViewer && (
        <TrailAuditViewer 
          onClose={() => {
            setShowTrailViewer(false);
            setTrailViewerTruckId(null);
          }} 
          initialTruckId={trailViewerTruckId}
        />
      )}

      {/* Driver QR Code Modal */}
      {selectedDriverForQR && (
        <DriverQRCodeModal 
          driver={selectedDriverForQR}
          truck={selectedTruckForQR}
          mission={selectedMissionForQR}
          onClose={() => {
            setSelectedDriverForQR(null);
            setSelectedTruckForQR(null);
            setSelectedMissionForQR(null);
          }}
        />
      )}
    </div>
  );
}

// ============================================================
// DRIVERS TABLE
// ============================================================

function DriversTable({ drivers, onDelete, onRefresh, onSelectDriver, onSelectDriverForQR, onSelectTruckForQR, onSelectMissionForQR }) {
  const [showForm, setShowForm] = useState(false);
  const [editingId, setEditingId] = useState(null);
  const [success, setSuccess] = useState(null);
  const [error, setError] = useState(null);
  const [formData, setFormData] = useState({
    first_name: '',
    last_name: '',
    email: '',
    phone: '',
    license_number: '',
    license_state: 'ZW',
    hire_date: new Date().toISOString().split('T')[0],
    status: 'active'
  });

  const statusOptions = ['active', 'suspended', 'terminated', 'on_leave'];

  const handleEdit = (driver) => {
    setFormData({
      first_name: driver.first_name || '',
      last_name: driver.last_name || '',
      email: driver.email || '',
      phone: driver.phone || '',
      license_number: driver.license_number || '',
      license_state: driver.license_state || 'ZW',
      hire_date: driver.hire_date || new Date().toISOString().split('T')[0],
      status: driver.status || 'active'
    });
    setEditingId(driver.id);
    setShowForm(true);
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    try {
      // Validate required fields
      if (!formData.first_name || !formData.last_name || !formData.phone || !formData.email) {
        setError('First name, last name, email, and phone are required');
        return;
      }
      if (!formData.license_number || !formData.license_state) {
        setError('License number and state are required');
        return;
      }

      if (editingId) {
        await updateV1Driver(editingId, formData);
        setSuccess(`✅ Driver ${formData.first_name} ${formData.last_name} updated successfully`);
        setEditingId(null);
      } else {
        // Don't send fleet_id - let backend handle it
        // Only send the required fields
        const driverData = {
          first_name: formData.first_name,
          last_name: formData.last_name,
          email: formData.email,
          phone: formData.phone,
          license_number: formData.license_number,
          license_state: formData.license_state,
          hire_date: formData.hire_date,
          status: formData.status || 'active'
        };
        console.log('📝 Creating driver with data:', driverData);
        const newDriver = await createV1Driver(driverData);
        console.log('✅ Driver created:', newDriver);
        setSuccess(`✅ Driver ${formData.first_name} ${formData.last_name} created successfully`);
        // Keep form open but clear fields for next entry
        setFormData({
          first_name: '',
          last_name: '',
          email: '',
          phone: '',
          license_number: '',
          license_state: 'ZW',
          hire_date: new Date().toISOString().split('T')[0],
          status: 'active'
        });
      }
      // Refresh data without closing form
      onRefresh();
      // Clear success message after 5 seconds (longer to see it)
      setTimeout(() => setSuccess(null), 5000);
    } catch (error) {
      console.error('❌ Error saving driver:', error);
      console.error('   Response Status:', error.response?.status);
      console.error('   Response Data:', error.response?.data);
      console.error('   Response Headers:', error.response?.headers);
      
      let errorMsg = 'Failed to save driver';
      if (error.response?.data?.error) {
        errorMsg = error.response.data.error;
      } else if (error.response?.data?.detail) {
        errorMsg = error.response.data.detail;
      } else if (error.response?.data) {
        // Log all field errors
        const fieldErrors = Object.entries(error.response.data)
          .map(([field, msg]) => `${field}: ${Array.isArray(msg) ? msg.join(', ') : msg}`)
          .join('; ');
        errorMsg = fieldErrors || error.message;
      } else {
        errorMsg = error.message;
      }
      
      console.error('   Parsed error message:', errorMsg);
      setError(`⚠️ Failed to save driver: ${errorMsg}`);
      // Keep error visible longer (10 seconds)
      setTimeout(() => setError(null), 10000);
    }
  };

  return (
    <div>
      {/* Add Button */}
      <div className="p-4 border-b border-slate-700 flex justify-end">
        <button
          onClick={() => {
            setFormData({
              first_name: '',
              last_name: '',
              email: '',
              phone: '',
              license_number: '',
              license_state: 'ZW',
              hire_date: new Date().toISOString().split('T')[0],
              status: 'active'
            });
            setEditingId(null);
            setShowForm(true);
          }}
          className="flex items-center gap-2 px-4 py-2 bg-green-600 hover:bg-green-700 text-white rounded-lg transition"
        >
          <Plus size={18} />
          Add Driver
        </button>
      </div>

      {/* Table */}
      <div className="overflow-x-auto">
        <table className="w-full text-sm">
          <thead className="bg-slate-700 text-slate-300">
            <tr>
              <th className="px-6 py-3 text-left">Name</th>
              <th className="px-6 py-3 text-left">Email</th>
              <th className="px-6 py-3 text-left">Phone</th>
              <th className="px-6 py-3 text-left">License</th>
              <th className="px-6 py-3 text-left">Status</th>
              <th className="px-6 py-3 text-left">Performance Points</th>
              <th className="px-6 py-3 text-left">Deliveries</th>
              <th className="px-6 py-3 text-center">Actions</th>
            </tr>
          </thead>
          <tbody>
            {drivers.length === 0 ? (
              <tr>
                <td colSpan={7} className="px-6 py-8 text-center text-slate-400">
                  No drivers found. {!showForm && <span>Create one to get started.</span>}
                </td>
              </tr>
            ) : (
              drivers.map(driver => (
                <tr key={driver.id} className="border-b border-slate-700 hover:bg-slate-700/50">
                  <td className="px-6 py-4 text-slate-200">
                    {driver.name || `${driver.first_name || ''} ${driver.last_name || ''}`.trim()}
                  </td>
                  <td className="px-6 py-4 text-slate-400">{driver.email}</td>
                  <td className="px-6 py-4 text-slate-400">{driver.phone}</td>
                  <td className="px-6 py-4 text-slate-400">{driver.license_number}</td>
                  <td className="px-6 py-4">
                    <span className={`px-3 py-1 rounded-full text-xs font-semibold ${
                      driver.status === 'active' ? 'bg-green-900/50 text-green-300' :
                      driver.status === 'suspended' ? 'bg-red-900/50 text-red-300' :
                      driver.status === 'on_leave' ? 'bg-yellow-900/50 text-yellow-300' :
                      'bg-slate-700 text-slate-300'
                    }`}>
                      {driver.status?.toUpperCase()}
                    </span>
                  </td>
                  <td className="px-6 py-4">
                    <span className="px-3 py-1 bg-blue-900/50 text-blue-300 rounded-full text-sm font-semibold">
                      {driver.performance_points || 0} pts
                    </span>
                  </td>
                  <td className="px-6 py-4 text-slate-300">
                    {driver.deliveries_count || 0}
                  </td>
                  <td className="px-6 py-4 text-center flex justify-center gap-2">
                    <button
                      onClick={() => onSelectDriver(driver)}
                      className="p-2 text-green-400 hover:bg-green-900/30 rounded transition"
                      title="View in Dashboard"
                    >
                      <Eye size={16} />
                    </button>
                    <button
                      onClick={() => {
                        onSelectDriverForQR(driver);
                        onSelectTruckForQR(null);
                        onSelectMissionForQR(null);
                      }}
                      className="p-2 text-purple-400 hover:bg-purple-900/30 rounded transition"
                      title="Generate QR Code"
                    >
                      <QrCode size={16} />
                    </button>
                    <button
                      onClick={() => handleEdit(driver)}
                      className="p-2 text-blue-400 hover:bg-blue-900/30 rounded transition"
                    >
                      <Edit2 size={16} />
                    </button>
                    <button
                      onClick={() => onDelete(driver.id)}
                      className="p-2 text-red-400 hover:bg-red-900/30 rounded transition"
                    >
                      <Trash2 size={16} />
                    </button>
                  </td>
                </tr>
              ))
            )}
          </tbody>
        </table>
      </div>

      {/* Form Modal */}
      {showForm && (
        <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50">
          <div className="bg-slate-800 rounded-lg p-6 max-w-md w-full">
            <div className="flex justify-between items-center mb-4">
              <h2 className="text-xl font-bold text-white">
                {editingId ? 'Edit Driver' : 'Add Driver'}
              </h2>
              <button onClick={() => setShowForm(false)} className="text-slate-400 hover:text-white">
                <X size={20} />
              </button>
            </div>

            {/* Success Message */}
            {success && (
              <div className="mb-4 p-3 bg-green-900 border border-green-700 rounded text-green-200 text-sm flex items-center gap-2">
                <span>✓</span>
                {success}
              </div>
            )}
            
            {/* Error Message */}
            {error && (
              <div className="mb-4 p-3 bg-red-900 border border-red-700 rounded text-red-200 text-sm flex items-center gap-2">
                <span>✕</span>
                {error}
              </div>
            )}

            <form onSubmit={handleSubmit} className="space-y-4">
              <input
                type="text"
                placeholder="First Name"
                value={formData.first_name}
                onChange={(e) => setFormData({ ...formData, first_name: e.target.value })}
                className="w-full px-3 py-2 bg-slate-700 text-white rounded border border-slate-600 focus:border-blue-500 outline-none"
                required
              />
              <input
                type="text"
                placeholder="Last Name"
                value={formData.last_name}
                onChange={(e) => setFormData({ ...formData, last_name: e.target.value })}
                className="w-full px-3 py-2 bg-slate-700 text-white rounded border border-slate-600 focus:border-blue-500 outline-none"
                required
              />
              <input
                type="email"
                placeholder="Email"
                value={formData.email}
                onChange={(e) => setFormData({ ...formData, email: e.target.value })}
                className="w-full px-3 py-2 bg-slate-700 text-white rounded border border-slate-600 focus:border-blue-500 outline-none"
              />
              <input
                type="tel"
                placeholder="Phone"
                value={formData.phone}
                onChange={(e) => setFormData({ ...formData, phone: e.target.value })}
                className="w-full px-3 py-2 bg-slate-700 text-white rounded border border-slate-600 focus:border-blue-500 outline-none"
              />
              <input
                type="text"
                placeholder="License Number"
                value={formData.license_number}
                onChange={(e) => setFormData({ ...formData, license_number: e.target.value })}
                className="w-full px-3 py-2 bg-slate-700 text-white rounded border border-slate-600 focus:border-blue-500 outline-none"
                required
              />
              <select
                value={formData.license_state}
                onChange={(e) => setFormData({ ...formData, license_state: e.target.value })}
                className="w-full px-3 py-2 bg-slate-700 text-white rounded border border-slate-600 focus:border-blue-500 outline-none"
                required
              >
                <option value="ZW">Zimbabwe (ZW)</option>
                <option value="SA">South Africa (SA)</option>
                <option value="BW">Botswana (BW)</option>
                <option value="ZA">Other</option>
              </select>
              <input
                type="date"
                placeholder="Hire Date"
                value={formData.hire_date}
                onChange={(e) => setFormData({ ...formData, hire_date: e.target.value })}
                className="w-full px-3 py-2 bg-slate-700 text-white rounded border border-slate-600 focus:border-blue-500 outline-none"
                required
              />
              <select
                value={formData.status}
                onChange={(e) => setFormData({ ...formData, status: e.target.value })}
                className="w-full px-3 py-2 bg-slate-700 text-white rounded border border-slate-600 focus:border-blue-500 outline-none"
              >
                {statusOptions.map(status => (
                  <option key={status} value={status}>{status.toUpperCase()}</option>
                ))}
              </select>
              <button
                type="submit"
                className="w-full px-4 py-2 bg-blue-600 hover:bg-blue-700 text-white rounded transition flex items-center justify-center gap-2"
              >
                <Save size={18} />
                Save Driver
              </button>
            </form>
          </div>
        </div>
      )}
    </div>
  );
}

// ============================================================
// TRUCKS TABLE
// ============================================================

function TrucksTable({ trucks, onDelete, onRefresh, onSelectTruck }) {
  const [showForm, setShowForm] = useState(false);
  const [editingId, setEditingId] = useState(null);
  const [success, setSuccess] = useState(null);
  const [error, setError] = useState(null);
  const [showLocationModal, setShowLocationModal] = useState(false);
  const [selectedTruckForLocation, setSelectedTruckForLocation] = useState(null);
  const [locationUpdateData, setLocationUpdateData] = useState({
    latitude: '',
    longitude: '',
    speed_kmh: 0
  });
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
    status: 'idle'
  });

  const statusOptions = ['idle', 'enroute', 'maintenance', 'decommissioned'];

  const handleUpdateLocation = (truck) => {
    // ✅ NEW: Allow updating truck location in real-time
    setSelectedTruckForLocation(truck);
    setLocationUpdateData({
      latitude: truck.last_latitude || '',
      longitude: truck.last_longitude || '',
      speed_kmh: truck.speed_kmh || 0
    });
    setShowLocationModal(true);
  };

  const handleSubmitLocationUpdate = async (e) => {
    e.preventDefault();
    try {
      if (!locationUpdateData.latitude || !locationUpdateData.longitude) {
        setError('Latitude and longitude are required');
        return;
      }

      const lat = parseFloat(locationUpdateData.latitude);
      const lon = parseFloat(locationUpdateData.longitude);

      if (lat < -90 || lat > 90 || lon < -180 || lon > 180) {
        setError('Invalid coordinates. Lat: -90 to 90, Lon: -180 to 180');
        return;
      }

      await updateTruckLocationTracking(
        selectedTruckForLocation.id,
        lat,
        lon,
        parseFloat(locationUpdateData.speed_kmh) || 0
      );

      setSuccess(`✅ Location updated for ${selectedTruckForLocation.truck_identifier}`);
      setShowLocationModal(false);
      onRefresh();
      
      const timer = setTimeout(() => setSuccess(null), 3000);
      return () => clearTimeout(timer);
    } catch (err) {
      console.error('Error updating location:', err);
      setError('Failed to update truck location');
    }
  };

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

  const handleSubmit = async (e) => {
    e.preventDefault();
    console.log('📋 [FORM] Truck save clicked - form data:', JSON.stringify(formData, null, 2));
    try {
      // Validate required fields
      if (!formData.truck_identifier || !formData.plate) {
        console.error('❌ [FORM] Validation failed - missing truck_identifier or plate');
        setError('Truck identifier and plate are required');
        return;
      }

      console.log('✅ [FORM] Validation passed');

      if (editingId) {
        console.log('📝 [FORM] Updating existing truck:', editingId);
        await updateV1Truck(editingId, formData);
        console.log('✅ [FORM] Truck updated successfully');
        setSuccess('✅ Truck updated successfully');
        setEditingId(null);
      } else {
        // Generate a UUIDv4 for fleet_id
        const fleetId = 'xxxxxxxx-xxxx-4xxx-yxxx-xxxxxxxxxxxx'.replace(/[xy]/g, function(c) {
          const r = Math.random() * 16 | 0, v = c === 'x' ? r : (r & 0x3 | 0x8);
          return v.toString(16);
        });
        console.log('📝 [FORM] Creating NEW truck with fleetId:', fleetId);
        console.log('📝 [FORM] Truck data to send:', JSON.stringify({ ...formData, fleet_id: fleetId }, null, 2));
        const response = await createV1Truck({ ...formData, fleet_id: fleetId });
        console.log('✅ [FORM] Truck created successfully, response:', response);
        setSuccess(`✅ Truck ${formData.truck_identifier} created successfully`);
        // Show alert immediately so user knows it worked
        alert(`✅ SUCCESS!\n\nTruck "${formData.truck_identifier}" created successfully!\n\nPlate: ${formData.plate}`);
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
          status: 'idle'
        });
      }
      // Refresh data without closing form
      console.log('🔄 [FORM] Calling onRefresh to reload trucks');
      onRefresh();
      // Clear success message after 5 seconds (longer to see it)
      setTimeout(() => setSuccess(null), 5000);
    } catch (error) {
      console.error('❌ [FORM ERROR] Error saving truck:', error);
      console.error('   Error name:', error.name);
      console.error('   Error message:', error.message);
      console.error('   Response status:', error.response?.status);
      console.error('   Response data:', error.response?.data);
      console.error('   Response headers:', error.response?.headers);
      console.error('   Full error:', error);
      
      // Extract error message from various possible locations
      let errorMsg = 'Failed to save truck';
      if (error.response?.data?.error) {
        errorMsg = error.response.data.error;
      } else if (error.response?.data?.detail) {
        errorMsg = error.response.data.detail;
      } else if (error.response?.data?.non_field_errors) {
        errorMsg = Array.isArray(error.response.data.non_field_errors) 
          ? error.response.data.non_field_errors.join(', ')
          : error.response.data.non_field_errors;
      } else if (typeof error.response?.data === 'string') {
        errorMsg = error.response.data;
      } else if (error.response?.data) {
        // Show all validation errors
        errorMsg = Object.entries(error.response.data)
          .map(([key, value]) => `${key}: ${Array.isArray(value) ? value.join(', ') : value}`)
          .join(' | ');
      } else {
        errorMsg = error.message || 'Failed to save truck';
      }
      
      console.error('   Parsed error message:', errorMsg);
      setError(`⚠️ Failed to save truck: ${errorMsg}`);
      // Show alert immediately so user sees the error
      alert(`❌ Truck Creation Failed!\n\n${errorMsg}`);
      // Keep error visible longer (10 seconds)
      setTimeout(() => setError(null), 10000);
    }
  };

  return (
    <div>
      {/* Add Button */}
      <div className="p-4 border-b border-slate-700 flex justify-end">
        <button
          onClick={() => {
            setFormData({
              truck_identifier: '',
              plate: '',
              make: '',
              model: '',
              status: 'idle'
            });
            setEditingId(null);
            setShowForm(true);
          }}
          className="flex items-center gap-2 px-4 py-2 bg-green-600 hover:bg-green-700 text-white rounded-lg transition"
        >
          <Plus size={18} />
          Add Truck
        </button>
      </div>

      {/* Table */}
      <div className="overflow-x-auto">
        <table className="w-full text-sm">
          <thead className="bg-slate-700 text-slate-300">
            <tr>
              <th className="px-6 py-3 text-left">Identifier</th>
              <th className="px-6 py-3 text-left">Plate</th>
              <th className="px-6 py-3 text-left">Make / Model</th>
              <th className="px-6 py-3 text-left">Status</th>
              <th className="px-6 py-3 text-left">Location</th>
              <th className="px-6 py-3 text-left">Distance (km)</th>
              <th className="px-6 py-3 text-left">Fuel Used</th>
              <th className="px-6 py-3 text-center">Actions</th>
            </tr>
          </thead>
          <tbody>
            {trucks.length === 0 ? (
              <tr>
                <td colSpan={8} className="px-6 py-8 text-center text-slate-400">
                  No trucks found. Create one to get started.
                </td>
              </tr>
            ) : (
              trucks.map(truck => (
                <tr key={truck.id} className="border-b border-slate-700 hover:bg-slate-700/50">
                  <td className="px-6 py-4 text-slate-200 font-semibold">{truck.truck_identifier}</td>
                  <td className="px-6 py-4 text-slate-400">{truck.plate}</td>
                  <td className="px-6 py-4 text-slate-400">{truck.make} {truck.model}</td>
                  <td className="px-6 py-4">
                    <span className={`px-3 py-1 rounded-full text-xs font-semibold ${
                      truck.status === 'IDLE' ? 'bg-blue-900/50 text-blue-300' :
                      truck.status === 'ENROUTE' ? 'bg-green-900/50 text-green-300' :
                      truck.status === 'MAINTENANCE' ? 'bg-yellow-900/50 text-yellow-300' :
                      'bg-red-900/50 text-red-300'
                    }`}>
                      {truck.status}
                    </span>
                  </td>
                  <td className="px-6 py-4 text-slate-400">
                    {Number.isFinite(truck.location?.lat) && Number.isFinite(truck.location?.lon)
                      ? `${Number(truck.location.lat).toFixed(3)}, ${Number(truck.location.lon).toFixed(3)}`
                      : (Number.isFinite(truck.latitude) && Number.isFinite(truck.longitude)
                          ? `${Number(truck.latitude).toFixed(3)}, ${Number(truck.longitude).toFixed(3)}`
                          : 'No data')}
                  </td>
                  <td className="px-6 py-4 text-slate-300">
                    {Number.isFinite(truck.distance_travelled_km) ? `${Number(truck.distance_travelled_km).toFixed(1)} km` : '0 km'}
                  </td>
                  <td className="px-6 py-4">
                    <div className="flex flex-col gap-1">
                      <span className="text-slate-300">{Number.isFinite(truck.fuel_consumed_liters) ? `${Number(truck.fuel_consumed_liters).toFixed(1)} L` : '0 L'}</span>
                      <div className="w-24 bg-slate-700 rounded-full h-2">
                        <div 
                          className="bg-yellow-500 h-2 rounded-full"
                          style={{ width: `${Number.isFinite(truck.fuel_percent) ? truck.fuel_percent : 0}%` }}
                        />
                      </div>
                      <span className="text-slate-500 text-xs">{Number.isFinite(truck.fuel_percent) ? `${Number(truck.fuel_percent).toFixed(0)}%` : '0%'}</span>
                    </div>
                  </td>
                  <td className="px-6 py-4 text-center flex justify-center gap-2">
                    <button
                      onClick={() => onSelectTruck(truck)}
                      className="p-2 text-green-400 hover:bg-green-900/30 rounded transition"
                      title="View in Dashboard"
                    >
                      <Eye size={16} />
                    </button>
                    <button
                      onClick={() => handleUpdateLocation(truck)}
                      className="p-2 text-purple-400 hover:bg-purple-900/30 rounded transition"
                      title="Update Location"
                    >
                      <MapPin size={16} />
                    </button>
                    <button
                      onClick={() => handleEdit(truck)}
                      className="p-2 text-blue-400 hover:bg-blue-900/30 rounded transition"
                    >
                      <Edit2 size={16} />
                    </button>
                    <button
                      onClick={() => onDelete(truck.id)}
                      className="p-2 text-red-400 hover:bg-red-900/30 rounded transition"
                    >
                      <Trash2 size={16} />
                    </button>
                  </td>
                </tr>
              ))
            )}
          </tbody>
        </table>
      </div>

      {/* Location Update Modal */}
      {showLocationModal && selectedTruckForLocation && (
        <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50">
          <div className="bg-slate-800 rounded-lg p-6 max-w-md w-full">
            <div className="flex justify-between items-center mb-4">
              <h2 className="text-xl font-bold text-white flex items-center gap-2">
                <MapPin size={20} />
                Update Location
              </h2>
              <button onClick={() => setShowLocationModal(false)} className="text-slate-400 hover:text-white">
                <X size={20} />
              </button>
            </div>
            
            {error && (
              <div className="mb-4 p-3 bg-red-900/50 border border-red-700 text-red-300 rounded text-sm">
                {error}
              </div>
            )}

            <form onSubmit={handleSubmitLocationUpdate} className="space-y-3">
              <div>
                <label className="block text-slate-300 text-sm font-medium mb-1">
                  Truck: {selectedTruckForLocation.truck_identifier}
                </label>
              </div>

              <div>
                <label className="block text-slate-300 text-sm font-medium mb-1">Latitude</label>
                <input
                  type="number"
                  step="0.0001"
                  min="-90"
                  max="90"
                  placeholder="-17.8 to 17.8"
                  value={locationUpdateData.latitude}
                  onChange={(e) => setLocationUpdateData({ ...locationUpdateData, latitude: e.target.value })}
                  className="w-full px-3 py-2 bg-slate-700 text-white rounded border border-slate-600 focus:border-purple-500 outline-none"
                  required
                />
              </div>

              <div>
                <label className="block text-slate-300 text-sm font-medium mb-1">Longitude</label>
                <input
                  type="number"
                  step="0.0001"
                  min="-180"
                  max="180"
                  placeholder="31.0 to 32.8"
                  value={locationUpdateData.longitude}
                  onChange={(e) => setLocationUpdateData({ ...locationUpdateData, longitude: e.target.value })}
                  className="w-full px-3 py-2 bg-slate-700 text-white rounded border border-slate-600 focus:border-purple-500 outline-none"
                  required
                />
              </div>

              <div>
                <label className="block text-slate-300 text-sm font-medium mb-1">Speed (km/h) - Optional</label>
                <input
                  type="number"
                  step="0.1"
                  min="0"
                  placeholder="0"
                  value={locationUpdateData.speed_kmh}
                  onChange={(e) => setLocationUpdateData({ ...locationUpdateData, speed_kmh: e.target.value })}
                  className="w-full px-3 py-2 bg-slate-700 text-white rounded border border-slate-600 focus:border-purple-500 outline-none"
                />
              </div>

              <div className="text-xs text-slate-400 bg-slate-700/50 p-2 rounded">
                💡 Enter coordinates or use format: lat,lon (e.g., -17.8,31.0)
              </div>

              <div className="flex gap-3 pt-4">
                <button
                  type="submit"
                  className="flex-1 px-4 py-2 bg-purple-600 hover:bg-purple-700 text-white rounded transition flex items-center justify-center gap-2"
                >
                  <Save size={16} />
                  Update Location
                </button>
                <button
                  type="button"
                  onClick={() => setShowLocationModal(false)}
                  className="flex-1 px-4 py-2 bg-slate-700 hover:bg-slate-600 text-white rounded transition"
                >
                  Cancel
                </button>
              </div>
            </form>
          </div>
        </div>
      )}

      {/* Form Modal */}
      {showForm && (
        <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50">
          <div className="bg-slate-800 rounded-lg p-6 max-w-md w-full">
            <div className="flex justify-between items-center mb-4">
              <h2 className="text-xl font-bold text-white">
                {editingId ? 'Edit Truck' : 'Add Truck'}
              </h2>
              <button onClick={() => setShowForm(false)} className="text-slate-400 hover:text-white">
                <X size={20} />
              </button>
            </div>

            {/* Success Message */}
            {success && (
              <div className="mb-4 p-3 bg-green-900 border border-green-700 rounded text-green-200 text-sm flex items-center gap-2">
                <span>✓</span>
                {success}
              </div>
            )}
            
            {/* Error Message */}
            {error && (
              <div className="mb-4 p-3 bg-red-900 border border-red-700 rounded text-red-200 text-sm flex items-center gap-2">
                <span>✕</span>
                {error}
              </div>
            )}

            <form onSubmit={(e) => { console.log('🔴 [FORM EVENT] Submit event fired'); handleSubmit(e); }} className="space-y-3 max-h-96 overflow-y-auto">
              <div className="grid grid-cols-2 gap-3">
                <input
                  type="text"
                  placeholder="Truck Identifier"
                  value={formData.truck_identifier}
                  onChange={(e) => setFormData({ ...formData, truck_identifier: e.target.value })}
                  className="col-span-2 px-3 py-2 bg-slate-700 text-white rounded border border-slate-600 focus:border-blue-500 outline-none"
                  required
                />
                <input
                  type="text"
                  placeholder="License Plate"
                  value={formData.plate}
                  onChange={(e) => setFormData({ ...formData, plate: e.target.value })}
                  className="col-span-2 px-3 py-2 bg-slate-700 text-white rounded border border-slate-600 focus:border-blue-500 outline-none"
                  required
                />
                <input
                  type="text"
                  placeholder="Make"
                  value={formData.make}
                  onChange={(e) => setFormData({ ...formData, make: e.target.value })}
                  className="px-3 py-2 bg-slate-700 text-white rounded border border-slate-600 focus:border-blue-500 outline-none"
                />
                <input
                  type="text"
                  placeholder="Model"
                  value={formData.model}
                  onChange={(e) => setFormData({ ...formData, model: e.target.value })}
                  className="px-3 py-2 bg-slate-700 text-white rounded border border-slate-600 focus:border-blue-500 outline-none"
                />
                <input
                  type="number"
                  placeholder="Year"
                  value={formData.year}
                  onChange={(e) => setFormData({ ...formData, year: parseInt(e.target.value) })}
                  className="px-3 py-2 bg-slate-700 text-white rounded border border-slate-600 focus:border-blue-500 outline-none"
                  min="1990"
                />
                <input
                  type="text"
                  placeholder="VIN"
                  value={formData.vin}
                  onChange={(e) => setFormData({ ...formData, vin: e.target.value })}
                  className="px-3 py-2 bg-slate-700 text-white rounded border border-slate-600 focus:border-blue-500 outline-none"
                />
                <input
                  type="text"
                  placeholder="Telematics ID"
                  value={formData.telematics_id}
                  onChange={(e) => setFormData({ ...formData, telematics_id: e.target.value })}
                  className="col-span-2 px-3 py-2 bg-slate-700 text-white rounded border border-slate-600 focus:border-blue-500 outline-none"
                />
                <input
                  type="number"
                  placeholder="Fuel Capacity (L)"
                  value={formData.fuel_capacity_liters}
                  onChange={(e) => setFormData({ ...formData, fuel_capacity_liters: parseFloat(e.target.value) })}
                  className="col-span-2 px-3 py-2 bg-slate-700 text-white rounded border border-slate-600 focus:border-blue-500 outline-none"
                  min="10"
                  step="0.1"
                />
                <input
                  type="date"
                  placeholder="Maintenance Due"
                  value={formData.maintenance_due_date}
                  onChange={(e) => setFormData({ ...formData, maintenance_due_date: e.target.value })}
                  className="col-span-2 px-3 py-2 bg-slate-700 text-white rounded border border-slate-600 focus:border-blue-500 outline-none"
                />
                <select
                  value={formData.status}
                  onChange={(e) => setFormData({ ...formData, status: e.target.value })}
                  className="col-span-2 px-3 py-2 bg-slate-700 text-white rounded border border-slate-600 focus:border-blue-500 outline-none"
                >
                  {statusOptions.map(status => (
                    <option key={status} value={status}>{status}</option>
                  ))}
                </select>
              </div>
              <button
                type="submit"
                onClick={(e) => {
                  console.log('🔴 [BUTTON CLICK] Save button clicked directly');
                  // Don't prevent default - let form submission work
                }}
                className="w-full px-4 py-2 bg-blue-600 hover:bg-blue-700 text-white rounded transition flex items-center justify-center gap-2"
              >
                <Save size={18} />
                Save Truck
              </button>
            </form>
          </div>
        </div>
      )}
    </div>
  );
}

// ============================================================
// MISSIONS TABLE
// ============================================================

function MissionsTable({ missions, trucks = [], drivers = [], onDelete, onRefresh }) {
  const [showForm, setShowForm] = useState(false);
  const [editingId, setEditingId] = useState(null);
  const [success, setSuccess] = useState(null);
  const [error, setError] = useState(null);
  const [localDrivers, setLocalDrivers] = useState(drivers);
  const [locationSuggestions, setLocationSuggestions] = useState({ origin: [], destination: [], current_location: [] });
  const [locationSearch, setLocationSearch] = useState({ origin: '', destination: '', current_location: '' });
  const [formData, setFormData] = useState({
    mission_number: '',
    truck_id: '',
    driver_id: '',
    status: 'PLANNED',
    distance_total_m: 0,
    est_time_minutes: '',
    cargo: '',
    weight_kg: '',
    progress: 0,
    destination: '',
    current_location: '',
    origin: '',
    mission_date: ''
  });

  const statusOptions = ['PLANNED', 'ASSIGNED', 'ENROUTE', 'PAUSED', 'COMPLETED', 'CANCELLED'];

  // Update local drivers when props change
  useEffect(() => {
    if (drivers && Array.isArray(drivers) && drivers.length > 0) {
      setLocalDrivers(drivers);
    } else {
      // Fallback: fetch drivers if not provided
      const fetchDrivers = async () => {
        try {
          const response = await getV1Drivers();
          setLocalDrivers(Array.isArray(response) ? response : (response.data || []));
        } catch (err) {
          console.error('Failed to load drivers:', err);
          setLocalDrivers([]);
        }
      };
      fetchDrivers();
    }
  }, [drivers]);

  // Get API base URL for v1 endpoints (works in both dev and prod)
  const getApiV1Base = () => {
    if (import.meta.env.MODE === 'development') return 'http://localhost:8000/api/v1';
    return 'https://pulsetrack-back.onrender.com/api/v1';
  };

  /**
   * Geocode a text address to {lat, lon, name} using the backend proxy
   * Falls back to direct Nominatim if backend is unreachable
   */
  const geocodeAddress = async (addressText) => {
    if (!addressText || addressText.length < 2) return null;
    
    // Check if it's already coordinates
    const coordMatch = addressText.trim().match(/^(-?\d+\.?\d*)\s*,\s*(-?\d+\.?\d*)$/);
    if (coordMatch) {
      const lat = parseFloat(coordMatch[1]);
      const lon = parseFloat(coordMatch[2]);
      if (lat >= -90 && lat <= 90 && lon >= -180 && lon <= 180) {
        return { lat, lon, name: addressText, source: 'coordinate' };
      }
    }
    
    // Check Zimbabwe locations first
    const exact = ZIMBABWE_LOCATIONS.find(l => 
      l.name.toLowerCase() === addressText.toLowerCase()
    );
    if (exact) return { ...exact, source: 'local' };
    
    const partial = ZIMBABWE_LOCATIONS.filter(l =>
      l.name.toLowerCase().includes(addressText.toLowerCase())
    );
    if (partial.length === 1) return { ...partial[0], source: 'local' };
    
    // Try backend autocomplete proxy (avoids CORS)
    try {
      const resp = await fetch(
        `${getApiV1Base()}/locations/autocomplete/?q=${encodeURIComponent(addressText)}&source=auto`,
        { method: 'GET', headers: { 'Content-Type': 'application/json' } }
      );
      if (resp.ok) {
        const data = await resp.json();
        const results = data.results || [];
        if (results.length > 0) {
          return { lat: results[0].lat, lon: results[0].lon, name: results[0].name, source: 'nominatim' };
        }
      }
    } catch (e) {
      console.warn('Backend geocoding failed:', e.message);
    }
    
    // Fallback: direct Nominatim call
    try {
      const resp = await fetch(
        `https://nominatim.openstreetmap.org/search?format=json&q=${encodeURIComponent(addressText)}&limit=3&countrycodes=zw`,
        { headers: { 'User-Agent': 'PulseTrack App' } }
      );
      if (resp.ok) {
        const data = await resp.json();
        if (data && data.length > 0) {
          return {
            lat: parseFloat(data[0].lat),
            lon: parseFloat(data[0].lon),
            name: data[0].display_name || addressText,
            source: 'nominatim'
          };
        }
      }
    } catch (e) {
      console.warn('Direct Nominatim failed:', e.message);
    }
    
    return null;
  };

  // Handle location search - accepts name search, direct coordinate input, and OSM Nominatim geocoding
  const handleLocationSearch = async (type, searchTerm) => {
    setLocationSearch(prev => ({ ...prev, [type]: searchTerm }));
    
    if (!searchTerm || searchTerm.length < 2) {
      setLocationSuggestions(prev => ({ ...prev, [type]: [] }));
      return;
    }

    // Check if input is coordinate format: "lat,lon" or "lat, lon"
    const coordMatch = searchTerm.trim().match(/^(-?\d+\.?\d*)\s*,\s*(-?\d+\.?\d*)$/);
    if (coordMatch) {
      const lat = parseFloat(coordMatch[1]);
      const lon = parseFloat(coordMatch[2]);
      if (lat >= -90 && lat <= 90 && lon >= -180 && lon <= 180) {
        setLocationSuggestions(prev => ({ 
          ...prev, 
          [type]: [{ lat, lon, name: `Custom Location (${lat.toFixed(4)}, ${lon.toFixed(4)})` }]
        }));
        return;
      }
    }

    // Search from ZIMBABWE_LOCATIONS + backend autocomplete proxy
    const localFiltered = ZIMBABWE_LOCATIONS.filter(loc =>
      loc.name.toLowerCase().includes(searchTerm.toLowerCase())
    );
    
    try {
      const resp = await fetch(
        `${getApiV1Base()}/locations/autocomplete/?q=${encodeURIComponent(searchTerm)}&source=auto`,
        { method: 'GET', headers: { 'Content-Type': 'application/json' } }
      );
      if (resp.ok) {
        const data = await resp.json();
        const apiResults = (data.results || []).map(r => ({
          lat: r.lat, lon: r.lon, name: r.name || r.display_name || searchTerm, source: 'nominatim'
        }));
        // Merge with local results, deduplicate
        const merged = [...localFiltered];
        for (const r of apiResults) {
          if (!merged.some(m => Math.abs(m.lat - r.lat) < 0.001 && Math.abs(m.lon - r.lon) < 0.001)) {
            merged.push(r);
          }
        }
        setLocationSuggestions(prev => ({ ...prev, [type]: merged }));
        return;
      }
    } catch (e) {
      console.warn('Backend autocomplete failed:', e.message);
    }
    
    setLocationSuggestions(prev => ({ ...prev, [type]: localFiltered }));
  };

  // Select location suggestion
  const selectLocation = (type, location) => {
    // Store as JSON object with lat/lon
    const locationObj = { lat: location.lat, lon: location.lon, name: location.name };
    
    setFormData(prev => {
      const updated = {
        ...prev,
        [type]: locationObj
      };
      
      // Auto-calculate distance if both origin and destination are set
      if (type === 'origin' && updated.destination && updated.destination.lat) {
        calculateDistanceViOSRM(locationObj, updated.destination).then(dist => {
          setFormData(f => ({ ...f, distance_total_m: dist }));
        });
      } else if (type === 'destination' && updated.origin && updated.origin.lat) {
        calculateDistanceViOSRM(updated.origin, locationObj).then(dist => {
          setFormData(f => ({ ...f, distance_total_m: dist }));
        });
      }
      
      // Auto-calculate progress if current_location is set and mission is ENROUTE
      if (type === 'current_location' && updated.origin && updated.distance_total_m > 0) {
        if (updated.status && updated.status.toLowerCase() === 'enroute') {
          calculateProgressFromDistanceOSRM(updated.origin, locationObj, updated.distance_total_m).then(progress => {
            setFormData(f => ({ ...f, progress }));
          });
        }
      }
      
      return updated;
    });
    setLocationSearch(prev => ({ ...prev, [type]: location.name }));
    setLocationSuggestions(prev => ({ ...prev, [type]: [] }));
  };

  // Calculate distance in meters from two coordinates (Haversine formula)
  const calculateDistance = (coord1, coord2) => {
    try {
      // Parse coordinates - support formats: "lat, lon" or just numbers
      const parseCoord = (str) => {
        if (!str) return null;
        const parts = str.split(',').map(s => parseFloat(s.trim()));
        if (parts.length >= 2 && !isNaN(parts[0]) && !isNaN(parts[1])) {
          return { lat: parts[0], lon: parts[1] };
        }
        return null;
      };

      const p1 = parseCoord(coord1);
      const p2 = parseCoord(coord2);

      if (!p1 || !p2) return 0;

      const toRad = (deg) => (deg * Math.PI) / 180;
      const R = 6371000; // Earth's radius in meters
      const dLat = toRad(p2.lat - p1.lat);
      const dLon = toRad(p2.lon - p1.lon);
      const a =
        Math.sin(dLat / 2) * Math.sin(dLat / 2) +
        Math.cos(toRad(p1.lat)) * Math.cos(toRad(p2.lat)) *
        Math.sin(dLon / 2) * Math.sin(dLon / 2);
      const c = 2 * Math.atan2(Math.sqrt(a), Math.sqrt(1 - a));
      return Math.round(R * c); // Distance in meters
    } catch (err) {
      console.error('Error calculating distance:', err);
      return 0;
    }
  };

  // Updated: Now uses OSRM API
  const calculateDistanceViOSRM = async (origin, destination) => {
    try {
      const parseLocation = (loc) => {
        if (typeof loc === 'object' && loc.lat !== undefined && loc.lon !== undefined) {
          return { lat: loc.lat, lon: loc.lon };
        } else if (typeof loc === 'string') {
          const parts = loc.split(',').map(s => parseFloat(s.trim()));
          if (parts.length >= 2 && !isNaN(parts[0]) && !isNaN(parts[1])) {
            return { lat: parts[0], lon: parts[1] };
          }
        }
        return null;
      };

      const orig = parseLocation(origin);
      const dest = parseLocation(destination);

      if (!orig || !dest) return 0;

      // Use the backend API URL (works in both dev and production)
      const backendUrl = window.location.hostname === 'localhost' 
        ? 'http://localhost:8000/api/v1/calculate-distance/'
        : 'https://pulsetrack-back.onrender.com/api/v1/calculate-distance/';

      const response = await fetch(backendUrl, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          origin: { lat: orig.lat, lon: orig.lon },
          destination: { lat: dest.lat, lon: dest.lon }
        })
      });

      if (!response.ok) {
        console.error('Distance API error:', response.status);
        return 0;
      }

      const data = await response.json();
      console.log('Distance API response:', data);
      return data.distance_meters || data.distance_m || 0;
    } catch (err) {
      console.error('Distance calculation error:', err);
      return 0;
    }
  };

  // Calculate progress based on distance traveled
  const calculateProgressFromDistance = (originCoords, currentLocationCoords, totalDistanceM) => {
    if (!originCoords || !currentLocationCoords || !totalDistanceM) return 0;
    
    try {
      const distanceTraveled = calculateDistance(
        `${originCoords.lat},${originCoords.lon}`,
        `${currentLocationCoords.lat},${currentLocationCoords.lon}`
      );
      
      const progress = Math.min(100, Math.round((distanceTraveled / totalDistanceM) * 100));
      return progress;
    } catch (err) {
      console.error('Error calculating progress:', err);
      return 0;
    }
  };

  // Async version using OSRM API
  const calculateProgressFromDistanceOSRM = async (originCoords, currentLocationCoords, totalDistanceM) => {
    if (!originCoords || !currentLocationCoords) return 0;
    
    try {
      // Get distance traveled from origin to current location
      const distanceTraveled = await calculateDistanceViOSRM(
        originCoords,
        currentLocationCoords
      );
      
      // If totalDistanceM not provided, calculate it
      let totalDist = totalDistanceM || 0;
      if (!totalDist) {
        // We'll need destination to calculate total - this shouldn't happen normally
        totalDist = distanceTraveled;
      }
      
      if (totalDist === 0) return 0;
      
      const progress = Math.min(100, Math.round((distanceTraveled / totalDist) * 100));
      console.log('Progress calculation:', { distanceTraveled, totalDist, progress });
      return progress;
    } catch (err) {
      console.error('Error calculating progress via OSRM:', err);
      return 0;
    }
  };

  // Enhanced progress calculation that recalculates distance if needed
  const calculateEnrouteProgress = async (origin, currentLoc, destination) => {
    if (!origin || !currentLoc) return 0;
    
    try {
      // Calculate total distance (origin → destination)
      const totalDist = await calculateDistanceViOSRM(origin, destination);
      
      // Calculate distance traveled (origin → current_location)
      const distanceTraveled = await calculateDistanceViOSRM(origin, currentLoc);
      
      if (totalDist === 0) return 0;
      
      const progress = Math.min(100, Math.round((distanceTraveled / totalDist) * 100));
      console.log('Enroute progress:', { distanceTraveled, totalDist, progress });
      return progress;
    } catch (err) {
      console.error('Error calculating enroute progress:', err);
      return 0;
    }
  };

  // Auto-calculate distance when origin or destination changes
  const handleOriginDestinationChange = (updates) => {
    const newFormData = { ...formData, ...updates };
    
    // Auto-calculate if both origin and destination are provided
    if (newFormData.origin && newFormData.destination) {
      const calculatedDistance = calculateDistance(newFormData.origin, newFormData.destination);
      newFormData.distance_total_m = calculatedDistance;
    }
    
    setFormData(newFormData);
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    setError(null);
    setSuccess(null);
    
    // AUTO-GEOCODE: If origin/destination/current_location are still text strings
    // (user typed an address but didn't click a suggestion), geocode them now
    try {
      for (const field of ['origin', 'destination', 'current_location']) {
        if (formData[field] && typeof formData[field] === 'string' && formData[field].trim()) {
          console.log(`🔍 Auto-geocoding ${field}: "${formData[field]}"`);
          const geocoded = await geocodeAddress(formData[field]);
          if (geocoded) {
            formData[field] = geocoded;
            setLocationSearch(prev => ({ ...prev, [field]: geocoded.name }));
            console.log(`✅ Geocoded ${field}:`, geocoded);
          } else {
            console.warn(`⚠️ Could not geocode ${field}: "${formData[field]}"`);
          }
        }
      }
    } catch (geoErr) {
      console.warn('Auto-geocoding error:', geoErr);
    }
    
    try {
      if (editingId) {
        // For update, normalize status and auto-calculate progress with OSRM
        const statusValue = formData.status.toLowerCase();
        let progressValue = parseInt(formData.progress) || 0;
        
        if (statusValue === 'planned' || statusValue === 'assigned') {
          progressValue = 0;
        } else if (statusValue === 'enroute') {
          // For ENROUTE: use OSRM-based calculation if origin, destination and current_location available
          if (formData.origin && formData.current_location && formData.destination) {
            progressValue = await calculateEnrouteProgress(formData.origin, formData.current_location, formData.destination);
          }
        } else if (statusValue === 'completed') {
          progressValue = 100;
        }
        
        const updateData = {
          ...formData,
          truck: formData.truck_id || null,  // API expects 'truck' not 'truck_id'
          driver: formData.driver_id || null,  // API expects 'driver' not 'driver_id'
          status: statusValue,
          distance_total_m: parseInt(formData.distance_total_m) || 0,
          est_time_minutes: parseInt(formData.est_time_minutes) || 0,
          weight_kg: parseFloat(formData.weight_kg) || 0,
          progress_pct: progressValue
        };
        // Remove the old field names to avoid conflicts
        delete updateData.truck_id;
        delete updateData.driver_id;
        await updateV1Mission(editingId, updateData);
        setSuccess('Mission updated successfully');
        setEditingId(null);
      } else {
        // For create, send all fields that backend expects
        const fleetId = 'xxxxxxxx-xxxx-4xxx-yxxx-xxxxxxxxxxxx'.replace(/[xy]/g, function(c) {
          const r = Math.random() * 16 | 0, v = c === 'x' ? r : (r & 0x3 | 0x8);
          return v.toString(16);
        });
        
        // Handle origin/destination - can be string coords or objects
        const parseLocation = (loc) => {
          if (!loc) return { lat: 0, lon: 0 };
          if (typeof loc === 'object') return loc;
          // If it's a string like "lat,lon", parse it
          const parts = loc.split(',').map(p => parseFloat(p.trim()));
          return { lat: parts[0] || 0, lon: parts[1] || 0 };
        };
        
        // Normalize status to lowercase
        const statusValue = formData.status.toLowerCase();
        
        // Auto-calculate progress based on status and distance using OSRM
        let progressValue = parseInt(formData.progress) || 0;
        if (statusValue === 'planned' || statusValue === 'assigned') {
          progressValue = 0;
        } else if (statusValue === 'enroute') {
          // For ENROUTE: use OSRM-based calculation if origin, destination and current_location available
          if (formData.origin && formData.current_location && formData.destination) {
            progressValue = await calculateEnrouteProgress(formData.origin, formData.current_location, formData.destination);
          }
        } else if (statusValue === 'completed') {
          progressValue = 100;
        }
        // For 'paused' and 'cancelled', keep current progress
        
        const createData = {
          mission_number: formData.mission_number,
          truck: formData.truck_id || null,  // API expects 'truck' not 'truck_id'
          driver: formData.driver_id || null,  // API expects 'driver' not 'driver_id'
          status: statusValue,
          distance_total_m: parseInt(formData.distance_total_m) || 0,
          progress_pct: progressValue,
          origin: parseLocation(formData.origin),
          destination: parseLocation(formData.destination),
          current_location: formData.current_location ? parseLocation(formData.current_location) : null,
          cargo: formData.cargo ? { description: formData.cargo, weight_kg: parseFloat(formData.weight_kg) || 0 } : null,
          mission_date: formData.mission_date || new Date().toISOString().split('T')[0],
          fleet_id: fleetId
        };
        
        // Validate required fields
        if (!createData.mission_number) {
          setError('Mission number is required');
          return;
        }
        if (!createData.truck) {
          setError('Truck selection is required');
          return;
        }
        if (!createData.origin || (createData.origin.lat === 0 && createData.origin.lon === 0)) {
          setError('Valid origin location is required');
          return;
        }
        if (!createData.destination || (createData.destination.lat === 0 && createData.destination.lon === 0)) {
          setError('Valid destination location is required');
          return;
        }
        
        console.log('Sending mission data:', createData);
        await createV1Mission(createData);
        setSuccess('Mission created successfully');
        // Keep form open but clear fields
        setFormData({
          mission_number: '',
          truck_id: '',
          driver_id: '',
          status: 'PLANNED',
          distance_total_m: 0,
          est_time_minutes: '',
          cargo: '',
          weight_kg: '',
          progress: 0,
          destination: '',
          current_location: '',
          origin: '',
          mission_date: ''
        });
      }
      onRefresh(); // Refresh admin table
      const timer = setTimeout(() => setSuccess(null), 3000);
      return () => clearTimeout(timer);
    } catch (error) {
      console.error('Error saving mission:', error);
      setError(error?.response?.data?.detail || 'Failed to save mission');
      const timer = setTimeout(() => setError(null), 3000);
      return () => clearTimeout(timer);
    }
  };

  return (
    <div>
      <div className="p-4 border-b border-slate-700 flex justify-between items-center">
        <h3 className="font-semibold text-white">Missions</h3>
        <button
          onClick={() => {
            setFormData({
              mission_number: '',
              truck_id: '',
              driver_id: '',
              status: 'PLANNED',
              distance_total_m: 0,
              est_time_minutes: '',
              cargo: '',
              weight_kg: '',
              progress: 0,
              destination: '',
              current_location: '',
              origin: '',
              mission_date: ''
            });
            setEditingId(null);
            setShowForm(true);
          }}
          className="flex items-center gap-2 px-4 py-2 bg-green-600 hover:bg-green-700 text-white rounded-lg transition"
        >
          <Plus size={18} />
          Add Mission
        </button>
      </div>

      {/* Table */}
      <div className="overflow-x-auto">
        <table className="w-full text-sm">
          <thead className="bg-slate-700 text-slate-300">
            <tr>
              <th className="px-6 py-3 text-left">Mission #</th>
              <th className="px-6 py-3 text-left">Truck</th>
              <th className="px-6 py-3 text-left">Driver</th>
              <th className="px-6 py-3 text-left">Status</th>
              <th className="px-6 py-3 text-left">Progress</th>
              <th className="px-6 py-3 text-left">Distance</th>
              <th className="px-6 py-3 text-left">Stops</th>
              <th className="px-6 py-3 text-center">Actions</th>
            </tr>
          </thead>
          <tbody>
            {missions.length === 0 ? (
              <tr>
                <td colSpan={8} className="px-6 py-8 text-center text-slate-400">
                  No missions found.
                </td>
              </tr>
            ) : (
              missions.map(mission => (
                <tr key={mission.id} className="border-b border-slate-700 hover:bg-slate-700/50">
                  <td className="px-6 py-4 text-slate-200 font-semibold">{mission.mission_number}</td>
                  <td className="px-6 py-4 text-slate-400">
                    {mission.truck_name || 'Unassigned'}
                  </td>
                  <td className="px-6 py-4 text-slate-400">
                    {mission.driver_name || 'Unassigned'}
                  </td>
                  <td className="px-6 py-4">
                    <span className={`px-3 py-1 rounded-full text-xs font-semibold ${
                      mission.status === 'ENROUTE' ? 'bg-green-900/50 text-green-300' :
                      mission.status === 'COMPLETED' ? 'bg-blue-900/50 text-blue-300' :
                      mission.status === 'PLANNED' ? 'bg-yellow-900/50 text-yellow-300' :
                      mission.status === 'CANCELLED' ? 'bg-red-900/50 text-red-300' :
                      'bg-slate-700 text-slate-300'
                    }`}>
                      {mission.status}
                    </span>
                  </td>
                  <td className="px-6 py-4">
                    <div className="flex items-center gap-2">
                      <div className="w-16 bg-slate-700 rounded-full h-2">
                        <div 
                          className="bg-green-500 h-2 rounded-full" 
                          style={{ width: `${mission.progress_pct || 0}%` }}
                        />
                      </div>
                      <span className="text-slate-300 text-xs">{mission.progress_pct || 0}%</span>
                    </div>
                  </td>
                  <td className="px-6 py-4 text-slate-400">
                    {mission.distance_total_m != null && Number.isFinite(Number(mission.distance_total_m)) ? `${(Number(mission.distance_total_m) / 1000).toFixed(1)}km` : 'N/A'}
                  </td>
                  <td className="px-6 py-4 text-slate-400">
                    {mission.stops_detail?.length || 0}
                  </td>
                  <td className="px-6 py-4 text-center flex justify-center gap-2">
                    <button
                      onClick={() => onDelete(mission.id)}
                      className="p-2 text-red-400 hover:bg-red-900/30 rounded transition"
                    >
                      <Trash2 size={16} />
                    </button>
                  </td>
                </tr>
              ))
            )}
          </tbody>
        </table>
      </div>

      {/* Form Modal */}
      {showForm && (
        <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50 p-4">
          <div className="bg-slate-800 rounded-lg p-6 max-w-lg w-full max-h-screen overflow-y-auto">
            <div className="flex justify-between items-center mb-4 sticky top-0 bg-slate-800 pb-4">
              <h2 className="text-xl font-bold text-white">
                {editingId ? 'Edit Mission' : 'Add Mission'}
              </h2>
              <button onClick={() => setShowForm(false)} className="text-slate-400 hover:text-white">
                <X size={20} />
              </button>
            </div>

            {/* Success Message */}
            {success && (
              <div className="mb-4 p-3 bg-green-900 border border-green-700 rounded text-green-200 text-sm flex items-center gap-2">
                <span>✓</span>
                {success}
              </div>
            )}
            
            {/* Error Message */}
            {error && (
              <div className="mb-4 p-3 bg-red-900 border border-red-700 rounded text-red-200 text-sm flex items-center gap-2">
                <span>✕</span>
                {error}
              </div>
            )}

            <form onSubmit={handleSubmit} className="space-y-4">
              <input
                type="text"
                placeholder="Mission Number"
                value={formData.mission_number}
                onChange={(e) => setFormData({ ...formData, mission_number: e.target.value })}
                className="w-full px-3 py-2 bg-slate-700 text-white rounded border border-slate-600 focus:border-blue-500 outline-none"
                required
              />
              <input
                type="date"
                placeholder="Mission Date"
                value={formData.mission_date}
                onChange={(e) => setFormData({ ...formData, mission_date: e.target.value })}
                className="w-full px-3 py-2 bg-slate-700 text-white rounded border border-slate-600 focus:border-blue-500 outline-none"
              />
              <select
                value={formData.truck_id}
                onChange={(e) => setFormData({ ...formData, truck_id: e.target.value })}
                className="w-full px-3 py-2 bg-slate-700 text-white rounded border border-slate-600 focus:border-blue-500 outline-none"
              >
                <option value="">Select Truck</option>
                {trucks.map(truck => (
                  <option key={truck.id} value={truck.id}>{truck.truck_identifier}</option>
                ))}
              </select>
              <div className="text-xs text-slate-500 px-3 py-2 bg-slate-700/30 rounded">
                Distance will auto-calculate from coordinates (leave blank or enter manually)
              </div>
              <input
                type="number"
                placeholder="Distance (meters) - Auto-calculated"
                value={formData.distance_total_m}
                onChange={(e) => setFormData({ ...formData, distance_total_m: e.target.value })}
                className="w-full px-3 py-2 bg-slate-700 text-white rounded border border-slate-600 focus:border-blue-500 outline-none"
              />
              <input
                type="number"
                placeholder="Est. Time (minutes) - Optional"
                value={formData.est_time_minutes}
                onChange={(e) => setFormData({ ...formData, est_time_minutes: e.target.value })}
                className="w-full px-3 py-2 bg-slate-700 text-white rounded border border-slate-600 focus:border-blue-500 outline-none"
              />
              <select
                value={formData.status}
                onChange={(e) => {
                  const newStatus = e.target.value;
                  // Auto-calculate progress based on status
                  let newProgress = formData.progress;
                  const status = newStatus.toLowerCase();
                  if (status === 'planned' || status === 'assigned') {
                    newProgress = 0;
                  } else if (status === 'enroute') {
                    // For ENROUTE: calculate based on current_location distance
                    if (formData.origin && formData.current_location && formData.distance_total_m) {
                      newProgress = calculateProgressFromDistance(formData.origin, formData.current_location, formData.distance_total_m);
                    } else {
                      // Default to 25% if location data not available
                      newProgress = newProgress === 0 ? 25 : newProgress;
                    }
                  } else if (status === 'completed') {
                    newProgress = 100;
                  }
                  setFormData({ ...formData, status: newStatus, progress: newProgress });
                }}
                className="w-full px-3 py-2 bg-slate-700 text-white rounded border border-slate-600 focus:border-blue-500 outline-none"
              >
                {statusOptions.map(status => (
                  <option key={status} value={status}>{status}</option>
                ))}
              </select>
              <div className="text-xs text-slate-400 px-3 py-1">
                Auto-progress: PLANNED/ASSIGNED→0%, ENROUTE→distance-based%, COMPLETED→100%
              </div>

              {/* Driver Selection - Always visible */}
              <select
                value={formData.driver_id}
                onChange={(e) => setFormData({ ...formData, driver_id: e.target.value })}
                className="w-full px-3 py-2 bg-slate-700 text-white rounded border border-slate-600 focus:border-blue-500 outline-none"
              >
                <option value="">Select Driver</option>
                {localDrivers && localDrivers.map(driver => (
                  <option key={driver.id} value={driver.id}>
                    {driver.first_name} {driver.last_name} ({driver.license_number || 'N/A'})
                  </option>
                ))}
              </select>

              <input
                type="text"
                placeholder="Cargo Description"
                value={formData.cargo}
                onChange={(e) => setFormData({ ...formData, cargo: e.target.value })}
                className="w-full px-3 py-2 bg-slate-700 text-white rounded border border-slate-600 focus:border-blue-500 outline-none"
              />
              <input
                type="number"
                placeholder="Weight (kg)"
                value={formData.weight_kg}
                onChange={(e) => setFormData({ ...formData, weight_kg: e.target.value })}
                className="w-full px-3 py-2 bg-slate-700 text-white rounded border border-slate-600 focus:border-blue-500 outline-none"
              />
              <input
                type="number"
                placeholder="Progress (%)"
                min="0"
                max="100"
                value={formData.progress}
                onChange={(e) => setFormData({ ...formData, progress: parseInt(e.target.value) || 0 })}
                className="w-full px-3 py-2 bg-slate-700 text-white rounded border border-slate-600 focus:border-blue-500 outline-none text-sm"
              />
              <div className="text-xs text-slate-400 px-3 py-1">
                Auto-calculated: PLANNED/ASSIGNED=0%, ENROUTE=(distance traveled / total distance)%, COMPLETED=100%
              </div>

              {/* Origin Location Search */}
              <div className="relative">
                <input
                  type="text"
                  placeholder="Origin (search location or enter coords: -17.8,31.0)"
                  value={locationSearch.origin}
                  onChange={(e) => handleLocationSearch('origin', e.target.value)}
                  className="w-full px-3 py-2 bg-slate-700 text-white rounded border border-slate-600 focus:border-blue-500 outline-none"
                />
                {locationSuggestions.origin && locationSuggestions.origin.length > 0 && (
                  <div className="absolute top-full left-0 right-0 bg-slate-700 border border-slate-600 rounded mt-1 z-10 max-h-48 overflow-y-auto shadow-lg">
                    {locationSuggestions.origin.map((location, idx) => (
                      <button
                        key={idx}
                        type="button"
                        onClick={() => selectLocation('origin', location)}
                        className="w-full text-left px-3 py-2 text-slate-300 hover:bg-blue-600/50 border-b border-slate-600 last:border-b-0 transition"
                      >
                        <div className="font-medium text-white">{location.name}</div>
                        <div className="text-xs text-slate-400">{Number.isFinite(location.lat) && Number.isFinite(location.lon) ? `${Number(location.lat).toFixed(4)}, ${Number(location.lon).toFixed(4)}` : 'No coordinates'}</div>
                      </button>
                    ))}
                  </div>
                )}
              </div>

              {/* Current Location Search */}
              <div className="relative">
                <input
                  type="text"
                  placeholder="Current Location (search location or enter coords: -17.85,31.05)"
                  value={locationSearch.current_location}
                  onChange={(e) => handleLocationSearch('current_location', e.target.value)}
                  className="w-full px-3 py-2 bg-slate-700 text-white rounded border border-slate-600 focus:border-blue-500 outline-none"
                />
                {locationSuggestions.current_location && locationSuggestions.current_location.length > 0 && (
                  <div className="absolute top-full left-0 right-0 bg-slate-700 border border-slate-600 rounded mt-1 z-10 max-h-48 overflow-y-auto shadow-lg">
                    {locationSuggestions.current_location.map((location, idx) => (
                      <button
                        key={idx}
                        type="button"
                        onClick={() => selectLocation('current_location', location)}
                        className="w-full text-left px-3 py-2 text-slate-300 hover:bg-blue-600/50 border-b border-slate-600 last:border-b-0 transition"
                      >
                        <div className="font-medium text-white">{location.name}</div>
                        <div className="text-xs text-slate-400">{Number.isFinite(location.lat) && Number.isFinite(location.lon) ? `${Number(location.lat).toFixed(4)}, ${Number(location.lon).toFixed(4)}` : 'No coordinates'}</div>
                      </button>
                    ))}
                  </div>
                )}
              </div>

              {/* Destination Location Search */}
              <div className="relative">
                <input
                  type="text"
                  placeholder="Destination (search location or enter coords: -18.0,31.1)"
                  value={locationSearch.destination}
                  onChange={(e) => handleLocationSearch('destination', e.target.value)}
                  className="w-full px-3 py-2 bg-slate-700 text-white rounded border border-slate-600 focus:border-blue-500 outline-none"
                />
                {locationSuggestions.destination && locationSuggestions.destination.length > 0 && (
                  <div className="absolute top-full left-0 right-0 bg-slate-700 border border-slate-600 rounded mt-1 z-10 max-h-48 overflow-y-auto shadow-lg">
                    {locationSuggestions.destination.map((location, idx) => (
                      <button
                        key={idx}
                        type="button"
                        onClick={() => selectLocation('destination', location)}
                        className="w-full text-left px-3 py-2 text-slate-300 hover:bg-blue-600/50 border-b border-slate-600 last:border-b-0 transition"
                      >
                        <div className="font-medium text-white">{location.name}</div>
                        <div className="text-xs text-slate-400">{Number.isFinite(location.lat) && Number.isFinite(location.lon) ? `${Number(location.lat).toFixed(4)}, ${Number(location.lon).toFixed(4)}` : 'No coordinates'}</div>
                      </button>
                    ))}
                  </div>
                )}
              </div>
              <div className="text-xs text-slate-500 px-3 py-2 bg-slate-700/30 rounded">
                {typeof formData.destination === 'object' && formData.destination?.lat ? 
                  `Distance will auto-calculate from origin to destination coordinates. Current: ${(Math.round((formData.distance_total_m || 0) / 1000 * 10) / 10)}km`
                  : 'Distance will auto-calculate from origin to destination coordinates'}
              </div>
              <button
                type="submit"
                className="w-full px-4 py-2 bg-blue-600 hover:bg-blue-700 text-white rounded transition flex items-center justify-center gap-2"
              >
                <Save size={18} />
                Save Mission
              </button>
            </form>
          </div>
        </div>
      )}
    </div>
  );
}

