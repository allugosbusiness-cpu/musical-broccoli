import { useState } from 'react';
import Topbar from "./components/Topbar.jsx";
import KPICards from "./components/KPICards.jsx";
import GlobalMap from "./components/GlobalMap.jsx";
import FleetTable from "./components/FleetTable.jsx";
import Alerts from "./components/Alerts.jsx";
import AlertsTable from "./components/AlertsTable.jsx";
import FleetAlerts from "./components/FleetAlerts.jsx";
import FuelTracking from "./components/FuelTracking.jsx";
import AdminDashboard from "./components/AdminDashboard.jsx";
import QRCodeDisplay from "./components/QRCodeDisplay.jsx";
import DriverLinkingMethods from "./components/DriverLinkingMethods.jsx";
import AutoTrailActivation from "./components/AutoTrailActivation.jsx";
import MissionCreationForm from "./components/MissionCreationForm.jsx";
import TruckLocationSpeedWidget from "./components/TruckLocationSpeedWidget.jsx";
import ActivityTable from "./components/ActivityTable.jsx";
import { getDashboardTrucks, getDashboardDrivers } from "./services/api.js";

export default function App() {
  const [selectedTruck, setSelectedTruck] = useState(null);
  const [selectedDriver, setSelectedDriver] = useState(null);
  const [currentView, setCurrentView] = useState('dashboard');
  const [refreshTrigger, setRefreshTrigger] = useState(0);
  const [showMissionModal, setShowMissionModal] = useState(false);
  const [trucks, setTrucks] = useState([]);
  const [drivers, setDrivers] = useState([]);
  const [trailEvents, setTrailEvents] = useState([]);

  // Fetch trucks and drivers for mission creation form
  const loadFleetData = async () => {
    try {
      const trucksData = await getDashboardTrucks();
      const driversData = await getDashboardDrivers();
      setTrucks(trucksData || []);
      setDrivers(driversData || []);
    } catch (error) {
      console.error('Error loading fleet data:', error);
    }
  };

  const handleOpenMissionModal = async () => {
    await loadFleetData();
    setShowMissionModal(true);
  };

  const handleMissionCreated = (mission) => {
    console.log('✅ Mission created successfully:', mission);
    setShowMissionModal(false);
    triggerRefresh();
  };

  const handleTrailStatusChange = (event) => {
    console.log('🟢 Trail status changed:', event);
    setTrailEvents(prev => [...prev, event]);
  };

  const handleMissionEvent = (event) => {
    console.log('📌 Mission event:', event);
    setTrailEvents(prev => [...prev, event]);
  };

  // Trigger refresh across all dashboard components
  const triggerRefresh = () => {
    setRefreshTrigger(prev => prev + 1);
  };

  // Handle truck selection from Admin Dashboard
  const handleSelectTruck = (truck) => {
    setSelectedTruck(truck);
    setSelectedDriver(null);
    setCurrentView('dashboard');
    // Trigger refresh in dashboard components
    triggerRefresh();
  };

  // Handle driver selection from Admin Dashboard
  const handleSelectDriver = (driver) => {
    setSelectedDriver(driver);
    setSelectedTruck(null);
    setCurrentView('dashboard');
    // Trigger refresh in dashboard components
    triggerRefresh();
  };

  // Clear selection when switching to admin
  const handleViewChange = (view) => {
    setCurrentView(view);
    if (view === 'admin' || view === 'qr') {
      setSelectedTruck(null);
      setSelectedDriver(null);
    }
  };

  return (
    <div className="bg-slate-900 text-slate-100 min-h-screen">
      <Topbar 
        currentView={currentView} 
        onViewChange={handleViewChange}
        selectedTruck={selectedTruck}
        selectedDriver={selectedDriver}
      />

      {currentView === 'admin' ? (
        <AdminDashboard 
          onSelectTruck={handleSelectTruck}
          onSelectDriver={handleSelectDriver}
          onDataChanged={triggerRefresh}
        />
      ) : currentView === 'activity' ? (
        <div className="p-6 max-w-[1600px] mx-auto">
          <ActivityTable />
        </div>
      ) : currentView === 'qr' ? (
        <div className="p-6 max-w-[1600px] mx-auto">
          <h1 className="text-3xl font-bold text-slate-100 mb-2">🔗 PulseTrack Driver Linking</h1>
          <p className="text-slate-400 mb-6">Multiple methods to link drivers to trucks and assign missions</p>
          
          {/* Method Selection */}
          <div className="bg-slate-800 border border-slate-700 rounded-lg p-6 mb-6">
            <h2 className="text-xl font-semibold text-slate-100 mb-4">Choose a Linking Method</h2>
            
            {selectedTruck ? (
              <div className="space-y-6">
                {/* Truck-Specific Methods */}
                <div className="grid md:grid-cols-2 gap-6">
                  {/* QR Code Method */}
                  <div>
                    <h3 className="text-lg font-semibold text-slate-100 mb-4">📱 QR Code Method</h3>
                    <QRCodeDisplay 
                      truckId={selectedTruck.id}
                      truckData={selectedTruck}
                    />
                  </div>
                  
                  {/* Alternative Methods */}
                  <div>
                    <DriverLinkingMethods 
                      truckId={selectedTruck.id}
                      truckData={selectedTruck}
                    />
                  </div>
                </div>
              </div>
            ) : (
              <div className="bg-slate-700 rounded-lg p-6 text-center">
                <p className="text-slate-300 mb-4">Select a truck from the fleet list below to generate linking methods</p>
                <p className="text-slate-400 text-sm">↓ Scroll down to view your fleet</p>
              </div>
            )}
          </div>
          
          {/* Fleet Selection */}
          <div>
            <h2 className="text-2xl font-bold text-slate-100 mb-4">🚚 Fleet Vehicles</h2>
            <p className="text-slate-400 mb-4">Click a truck to generate linking codes and generate QR codes</p>
            <FleetTable 
              onTruckSelect={(truck) => {
                setSelectedTruck(truck);
              }}
              highlightedTruck={selectedTruck}
              refreshTrigger={refreshTrigger}
            />
          </div>
        </div>
      ) : (
        <>
          {/* Auto-Trail Activation Background Service */}
          <AutoTrailActivation 
            onTrailStatusChange={handleTrailStatusChange}
            onMissionEvent={handleMissionEvent}
          />

          {/* Mission Creation Modal */}
          {showMissionModal && (
            <MissionCreationForm 
              trucks={trucks}
              drivers={drivers}
              onMissionCreated={handleMissionCreated}
              onClose={() => setShowMissionModal(false)}
            />
          )}

          <div className="p-6 max-w-[1600px] mx-auto space-y-6">
            {/* Action Buttons Bar */}
            <div className="flex gap-3 mb-6">
              <button
                onClick={handleOpenMissionModal}
                className="px-6 py-2 bg-green-600 hover:bg-green-500 text-white rounded-lg font-semibold transition-colors flex items-center gap-2"
              >
                ➕ Create New Mission
              </button>
            </div>

            {/* Selection Context Banner */}
            {(selectedTruck || selectedDriver) && (
              <div className="bg-gradient-to-r from-blue-900/20 to-slate-800/20 border border-blue-700/30 rounded-lg p-4 flex items-center justify-between shadow-lg backdrop-blur-sm">
                <div className="flex items-center gap-3">
                  <span className="text-sm font-semibold text-slate-100">
                    {selectedTruck ? `📍 Truck: ${selectedTruck.truck_identifier || selectedTruck.plate}` : `👤 Driver: ${selectedDriver.first_name} ${selectedDriver.last_name}`}
                  </span>
                </div>
                <button
                  onClick={() => {
                    setSelectedTruck(null);
                    setSelectedDriver(null);
                  }}
                  className="text-sm text-blue-400 hover:text-blue-300 font-semibold transition-colors"
                >
                  ✕ Clear
                </button>
              </div>
            )}

          <KPICards selectedTruck={selectedTruck} selectedDriver={selectedDriver} refreshTrigger={refreshTrigger} />

          {/* TRUCK LOCATION & SPEED WIDGET - Real-time tracking */}
          <TruckLocationSpeedWidget />

          {/* MAIN GRID - Global Map Full Width */}
          <div className="w-full rounded-xl overflow-hidden shadow-xl border border-slate-700/50">
            <GlobalMap 
              onTruckSelect={handleSelectTruck}
              highlightedTruck={selectedTruck}
              refreshTrigger={refreshTrigger}
            />
          </div>

          {/* ALERTS TABLE - Real-time monitoring */}
          <AlertsTable 
            filterTruckId={selectedTruck?.id}
            onTruckAlert={handleSelectTruck}
            refreshTrigger={refreshTrigger}
          />

          <FleetTable 
            onTruckSelect={handleSelectTruck}
            highlightedTruck={selectedTruck}
            refreshTrigger={refreshTrigger}
          />

          {/* FUEL TRACKING */}
          <FuelTracking refreshTrigger={refreshTrigger} />

          {/* ACTIVITY AUDIT TRAIL */}
          <ActivityTable />

          {/* BOTTOM PANELS */}
          <div className="grid md:grid-cols-2 gap-6">
            <Alerts selectedTruck={selectedTruck} refreshTrigger={refreshTrigger} />
            <FleetAlerts selectedDriver={selectedDriver} refreshTrigger={refreshTrigger} />
          </div>
          </div>
        </>
      )}

      {/* Navigation Buttons */}
      <div className="fixed bottom-6 right-6 z-50">
        <button
          onClick={() => handleViewChange(currentView === 'admin' ? 'dashboard' : 'admin')}
          className={`px-5 py-3 rounded-lg font-semibold text-sm transition-all shadow-dark-lg hover:scale-105 ${
            currentView === 'admin'
              ? 'bg-slate-800 text-slate-100 border border-slate-700 hover:bg-slate-700'
              : 'bg-primary text-white hover:bg-primary-light'
          }`}
        >
          {currentView === 'admin' ? '← Dashboard' : 'Admin →'}
        </button>
      </div>
    </div>
  );
}
