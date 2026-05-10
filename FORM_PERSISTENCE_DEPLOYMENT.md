# Form Persistence & Real-Time Integration Guide

## Overview
This deployment fixes the form-disappearing issue when adding new fleet items and implements full real-time propagation of new items to all dashboard components (map, tables, KPI cards, alerts, etc.).

## Architecture

### State Flow Diagram
```
App.jsx (Root State Management)
├── state: selectedTruck, selectedDriver, currentView, refreshTrigger
├── callbacks: handleSelectTruck, handleSelectDriver, triggerRefresh
└── passes props to all children

AdminDashboard (User Input)
├── receives: onDataChanged callback
├── actions: Add/Edit/Delete drivers, trucks, missions
├── onRefresh(): Reloads admin table
└── onDataChanged(): Calls parent triggerRefresh()
    └── increments refreshTrigger → triggers GlobalMap refetch

GlobalMap (Visual Display)
├── receives: refreshTrigger prop
├── watches: [previousTrucks, highlightedTruck, refreshTrigger]
├── on refreshTrigger change: getTrucks() → re-renders markers
└── trails/routes system updates automatically

KPICards, FleetTable, Alerts, etc.
├── receive: refreshTrigger prop  
├── watch: [selectedTruck, selectedDriver, refreshTrigger]
└── auto-update on any refresh signal
```

## Key Changes

### 1. App.jsx - Root Component
**File**: `client/Frontend/src/App.jsx`

**New Structure**:
```javascript
export default function App() {
  // Global state
  const [selectedTruck, setSelectedTruck] = useState(null);
  const [selectedDriver, setSelectedDriver] = useState(null);
  const [currentView, setCurrentView] = useState('dashboard');
  const [refreshTrigger, setRefreshTrigger] = useState(0);

  // Trigger refresh across all components
  const triggerRefresh = () => {
    setRefreshTrigger(prev => prev + 1);
  };

  // Selection callbacks
  const handleSelectTruck = (truck) => {
    setSelectedTruck(truck);
    setSelectedDriver(null);
    setCurrentView('dashboard');
    triggerRefresh(); // Refresh dashboard components
  };

  // Pass all state and callbacks as props to components
  return (
    <GlobalMap 
      refreshTrigger={refreshTrigger}
      highlightedTruck={selectedTruck}
      onTruckSelect={handleSelectTruck}
    />
    <AdminDashboard 
      onSelectTruck={handleSelectTruck}
      onSelectDriver={handleSelectDriver}
      onDataChanged={triggerRefresh}
    />
  );
}
```

**Impact**: All components now receive `refreshTrigger` prop, enabling coordinated updates.

### 2. AdminDashboard - Form Persistence
**File**: `client/Frontend/src/components/AdminDashboard.jsx`

**Changes**:
```javascript
// Accept onDataChanged callback from parent
export default function AdminDashboard({ 
  onSelectTruck, 
  onSelectDriver, 
  onDataChanged = () => {} 
}) {

  // In fetchData()
  const fetchData = async () => {
    try {
      // ... fetch logic ...
      setError(null);
      onDataChanged(); // ← Notify parent to refresh dashboard
    } finally {
      setLoading(false);
    }
  };

  // In each table's handleSubmit
  const handleSubmit = async (e) => {
    try {
      if (editingId) {
        await updateV1Truck(editingId, formData);
        setSuccess('Truck updated successfully');
        setEditingId(null);
      } else {
        await createV1Truck({ ...formData, fleet_id: 'default' });
        setSuccess('Truck created successfully');
        // ← Key: DON'T call setShowForm(false) - keep form open
        // ← Clear fields but leave modal visible
        setFormData({ truck_identifier: '', plate: '', ... });
      }
      onRefresh(); // Reload admin table
      // onDataChanged is called by onRefresh → fetchData() → onDataChanged()
      setTimeout(() => setSuccess(null), 3000);
    } catch (error) {
      // Show error message
    }
  };
}
```

**Form Persistence Logic**:
1. Remove `setShowForm(false)` from handleSubmit
2. Clear input fields with `setFormData({...initial})` 
3. Show success message for 3 seconds
4. Modal stays visible for next entry
5. Call onRefresh() which eventually calls onDataChanged()

**Visual Feedback**:
```javascript
{/* Inside form modal */}
{success && (
  <div className="mb-4 p-3 bg-green-900 border border-green-700 rounded text-green-200">
    <span>✓</span> {success}
  </div>
)}
{error && (
  <div className="mb-4 p-3 bg-red-900 border border-red-700 rounded text-red-200">
    <span>✕</span> {error}
  </div>
)}
```

### 3. GlobalMap - Refresh Trigger
**File**: `client/Frontend/src/components/GlobalMap.jsx`

**Changes**:
```javascript
export default function GlobalMap({ 
  onTruckSelect, 
  highlightedTruck = null,
  refreshTrigger = 0  // ← NEW: Listen for refresh signal
}) {

  useEffect(() => {
    const fetchTrucks = async () => {
      const trucksArray = await getTrucks();
      setTrucks(trucksArray);
      // Update markers, trails, etc.
    };

    fetchTrucks();
    const interval = setInterval(fetchTrucks, 10000);
    return () => clearInterval(interval);
  }, [previousTrucks, highlightedTruck, refreshTrigger]); // ← Added refreshTrigger
}
```

**Trigger Flow**:
1. Admin form submitted → onDataChanged() called
2. Parent triggerRefresh() increments refreshTrigger
3. GlobalMap receives new refreshTrigger prop value
4. useEffect dependency [refreshTrigger] triggers
5. GlobalMap calls getTrucks() → fetches all trucks including newly created
6. New truck marker renders on map

### 4. API Enhancement
**File**: `client/Frontend/src/services/api.js`

**Enhancement**:
```javascript
export const createV1Truck = async (data) => {
  try {
    // Add default coordinates if not provided
    const enhancedData = {
      ...data,
      last_latitude: data.last_latitude || -17.8252,    // Harare center
      last_longitude: data.last_longitude || 31.0335
    };
    const response = await apiV1.post('/trucks/', enhancedData);
    return response.data;
  } catch (error) {
    console.error('Error creating v1 truck:', error);
    throw error;
  }
};
```

**Why**: New trucks need location data to render on map. Default Harare coordinates ensure visibility.

## Testing Workflow

### Test 1: Form Persistence
```
1. Click "Admin" button → navigate to Admin Dashboard
2. Click "Add Truck" button
3. Fill form: truck_identifier="TRUCK001", plate="ABC123", status="IDLE"
4. Click "Save Truck"
   ✓ Green success message appears: "Truck created successfully"
   ✓ Form modal STAYS OPEN (not dismissed)
   ✓ Input fields cleared
   ✓ Success message disappears after 3 seconds
5. Form ready for next entry
```

### Test 2: Map Update
```
1. Same as Test 1, but keep admin dashboard open
2. Click "Dashboard" button
3. Look at GlobalMap for new truck marker
   ✓ New truck appears with truck icon
   ✓ Marker positioned at Harare center (-17.8252, 31.0335)
   ✓ Truck name/identifier visible
4. Back to Admin, add another truck
5. Back to Dashboard → see both trucks on map
```

### Test 3: KPI Update
```
1. Add new truck via admin form
2. Stay in admin or switch to dashboard
3. Check KPICards.jsx
   ✓ "Active Trucks" count increases
   ✓ Truck list in KPI shows new truck
```

### Test 4: Full Integration
```
1. Add truck via admin form
2. Click "Dashboard"
3. Look for new truck on map ✓
4. Check KPI cards updated ✓
5. Check FleetTable row added ✓
6. Click truck on map → highlights blue ✓
7. Check Alerts panel for any truck actions ✓
8. Check FuelTracking can select new truck ✓
```

## Debugging

### Issue: Form closes after submit
**Solution**: Ensure handleSubmit doesn't call `setShowForm(false)`. Check AdminDashboard lines:
- DriversTable.handleSubmit (line ~185)
- TrucksTable.handleSubmit (line ~435)
- MissionsTable.handleSubmit (line ~680)

### Issue: New truck doesn't appear on map
**Troubleshoot**:
1. Check browser console: `console.log` in GlobalMap useEffect
2. Verify refreshTrigger changing: Add console.log in App.triggerRefresh()
3. Check getTrucks() returns new truck: API test in browser dev tools
4. Check GlobalMap useEffect dependencies include refreshTrigger

### Issue: Trails/routes not showing for new truck
**Expected**: Trails system picks up new truck in next cycle (10s interval)
- RoadMatchedTrailSystem component watches trucks array
- New truck triggers trail generation on next interval

### Issue: Alerts not triggering for new truck
**Expected**: Alert system generates based on truck location changes
- Backend DriverEventAlerts component watches truck telemetry
- New truck needs location updates to trigger alerts

## Performance Notes

- **Refetch Frequency**: GlobalMap fetches trucks every 10 seconds
- **Form Submit**: Instant POST, refresh visible in <1 second
- **Trail Generation**: Runs on separate 5-10 minute cycle
- **Alert Generation**: Runs when truck telemetry updates

## Production Readiness

**Before deployment**:
- [ ] Test all three form submissions (drivers, trucks, missions)
- [ ] Verify refreshTrigger flow with browser dev tools
- [ ] Check map updates within 10 seconds of form submission
- [ ] Verify KPI cards, FleetTable, Alerts all update
- [ ] Test with PostgreSQL database (not just SQLite)
- [ ] Test with authentication enabled (currently AllowAny)

**Post-deployment**:
- [ ] Monitor console for errors
- [ ] Check API response times during peak load
- [ ] Verify no memory leaks in component re-renders
- [ ] Monitor for duplicate markers/trails on map

## Rollback Plan

If issues occur:
1. Restore original AdminDashboard.jsx (before form persistence changes)
2. Restore original App.jsx (before state management)
3. Restore original GlobalMap.jsx (before refreshTrigger)

## Technical Debt

- [ ] Replace prop drilling with Context API (currentView, selectedTruck, etc.)
- [ ] Implement proper auth tokens (currently AllowAny for development)
- [ ] Add loading states during refreshTrigger updates
- [ ] Implement optimistic UI updates
- [ ] Add form validation error messages
- [ ] Implement undo/redo for admin operations
