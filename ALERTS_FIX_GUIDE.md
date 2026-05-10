# Alert System Fixes - Complete Debugging Guide

## Summary of Changes

Three critical issues were fixed to resolve alert duplication, popup display, and notification delivery:

### 1. ✅ Duplicate Alerts (Alerts.jsx)

**Problem:** Same alert appearing 4+ times with different timestamps

**Root Cause:** 
- Backend creating multiple alert records for single off-route event
- Frontend deduplication not grouping alerts properly

**Fix Applied:**
- **Step 1:** Deduplicate by ID - filters out exact duplicates
- **Step 2:** Group by `truck-alert_type` - keeps only most recent of each type per truck
- **Step 3:** Limit to 10 total alerts and sort by recency

**Code Location:** [client/Frontend/src/components/Alerts.jsx](client/Frontend/src/components/Alerts.jsx#L10-L60)

**What Changed:**
```javascript
// Before: Simple Set-based dedup (ineffective for grouping)
const seen = new Set();
data.forEach(alert => {
  if (!seen.has(alert.id)) {
    seen.add(alert.id);
    uniqueAlerts.push(alert);
  }
});

// After: Three-tier deduplication
// 1. By ID
const byId = {};
data.forEach(alert => {
  if (!byId[alert.id] || newer) byId[alert.id] = alert;
});

// 2. By truck + type
const grouped = {};
Object.values(byId).forEach(alert => {
  const key = `${alert.truck}-${alert.alert_type}`;
  if (!grouped[key] || newer) grouped[key] = alert;
});

// 3. Sort & limit
Object.values(grouped)
  .sort((a, b) => new Date(b.created_at) - new Date(a.created_at))
  .slice(0, 10)
```

---

### 2. ✅ Invalid Date Error (Alerts.jsx + FleetAlerts.jsx)

**Problem:** Timestamp display showing "Invalid Date" error

**Root Cause:** 
- `formatTime()` function not handling malformed timestamps gracefully
- Backend returning timestamps in unexpected format

**Fix Applied:**
- Added `isNaN()` check to validate date before formatting
- Added try-catch error handling with fallback
- Logs invalid timestamps for debugging

**Code Location:** 
- [client/Frontend/src/components/Alerts.jsx](client/Frontend/src/components/Alerts.jsx#L84-L103)
- [client/Frontend/src/components/FleetAlerts.jsx](client/Frontend/src/components/FleetAlerts.jsx#L92-L111)

**What Changed:**
```javascript
// Before: No error handling
const formatTime = (timestamp) => {
  const time = new Date(timestamp);
  const diff = Math.floor((now - time) / 1000);
  // If timestamp malformed, produces NaN
};

// After: Robust error handling
const formatTime = (timestamp) => {
  if (!timestamp) return 'unknown time';
  try {
    const time = new Date(timestamp);
    if (isNaN(time.getTime())) {
      console.warn('Invalid timestamp:', timestamp);
      return 'unknown time';
    }
    const diff = Math.floor((now - time) / 1000);
    // ...
  } catch (error) {
    console.error('Error formatting time:', error, timestamp);
    return 'unknown time';
  }
};
```

---

### 3. ✅ Native Notifications Not Working (DriverEventAlerts.jsx)

**Problem:** 
- No permission request appeared
- Notifications never sent to device
- Unknown modal popup still rendering

**Root Causes:**
- Permission request not being triggered properly
- Event listeners not attached
- No logging to debug execution flow

**Fix Applied:**
- **Immediate permission request** on component mount
- **Enhanced logging** to track execution at each step
- **Event listener registration** with verification
- **Null-safe notification sending** with permission checks
- **5-minute cooldown** per truck+event to prevent spam
- **Try-catch wrapper** around notification creation

**Code Location:** [client/Frontend/src/components/DriverEventAlerts.jsx](client/Frontend/src/components/DriverEventAlerts.jsx)

**What Changed:**
```javascript
// First effect: Permission request on mount
useEffect(() => {
  if (!permissionRequestedRef.current) {
    permissionRequestedRef.current = true;
    
    if ('Notification' in window) {
      console.log('🔔 Notification API available');
      console.log('🔔 Current permission:', Notification.permission);
      
      if (Notification.permission === 'default') {
        console.log('🔔 Requesting notification permission...');
        Notification.requestPermission().then(permission => {
          console.log('🔔 Permission result:', permission);
        });
      }
    }
  }
}, []);

// Second effect: Event handling with extensive logging
const handleEvent = (eventType, data) => {
  const truckId = data?.truckId || 'unknown';
  const notifyKey = `${truckId}-${eventType}`;
  
  if (notifiedRef.current.has(notifyKey)) {
    console.log(`⏭️ Skipping duplicate notification: ${notifyKey}`);
    return;
  }
  
  console.log(`📢 Processing event: ${eventType} for ${truckId}`);
  notifiedRef.current.add(notifyKey);
  
  sendNotification('🚨 Off-Route Alert', {
    body: `Truck ${truckId} is off-route...`,
    tag: `off-route-${truckId}`
  });
};

// Register all event listeners
const events = ['off-route-detected', 'back-on-route', 'truck-delayed', 'speed-drop', 'driver-stopped'];
events.forEach(evt => {
  tracker.on(evt, (data) => {
    console.log(`📨 Event received: ${evt}`, data);
    handleEvent(evt, data);
  });
});

console.log('✅ Event listeners registered for:', events.join(', '));
```

---

## How to Test

### Test 1: Check for Duplicate Alerts

1. **Open Browser DevTools** - Press `F12` or Right-click → Inspect
2. **Go to Console tab**
3. **Start the dev server:** `cd client/Frontend && npm run dev`
4. **Open app:** Navigate to `http://localhost:5173`
5. **Check the Alerts KPI card** (bottom right)
6. **Expected:** Each truck+alert_type combination appears only once
7. **Look for:** "Off-route detected: 617m" should appear 1x per truck, not 4x

**Debug Output:**
```javascript
// In console, you should see:
// Raw API data showing 4 records with same truck/message
// After dedup, should show only 1 per truck+type
```

---

### Test 2: Check Timestamp Formatting

1. **Open DevTools Console**
2. **Trigger an off-route alert** (or wait for existing ones)
3. **Look at timestamps** in Alerts.jsx display
4. **Expected:** Shows "just now", "5m ago", "2h ago", or time like "14:30"
5. **NOT Expected:** "Invalid Date" errors

**Debug Output:**
```javascript
// Should NOT see:
// Uncaught TypeError: Cannot read property of undefined

// Should see timestamps like:
// "just now"
// "5m ago"
// "23:30:04"
```

---

### Test 3: Verify Notification Permission Request

1. **Open DevTools Console**
2. **Reload page** (hard refresh: `Ctrl+Shift+R`)
3. **Look for browser notification permission popup** (top-center of browser)
4. **Expected outputs in console:**
   ```
   🔔 Notification API available
   🔔 Current permission: default
   🔔 Requesting notification permission...
   🔔 Permission result: granted (or denied)
   ```

**If permission already granted:**
   ```
   🔔 Notification API available
   🔔 Current permission: granted
   🔔 Notifications already permitted
   ```

**Troubleshooting:**
- If no permission popup: Check browser settings (Notifications might be disabled)
- If permission stays 'denied': Check browser URL (Notification API requires HTTPS or localhost)
- If permission is 'default': Browser might not support Notification API (use recent Chrome/Firefox)

---

### Test 4: Verify Notifications Fire on Events

1. **Open DevTools Console**
2. **Grant notification permission when prompted**
3. **Trigger off-route alert** (move a truck off its route in real-time, or manually create alert)
4. **Look for console output:**
   ```
   📢 Processing event: off-route-detected for ZW-AWE-5379
   ✅ Notification sent: 🚨 Off-Route Alert
   ```
5. **Look for system notification** (should appear as OS-level notification)

**Event Types That Trigger:**
- `off-route-detected` → "🚨 Off-Route Alert"
- `back-on-route` → "✅ Back on Route"
- `truck-delayed` → "⏰ Truck Delayed"
- `speed-drop` → "📉 Speed Drop"
- `driver-stopped` → "🛑 Driver Stopped"

---

### Test 5: Check Backend Alert Creation

1. **Terminal:** Run backend `python manage.py runserver`
2. **DB query:** Check if multiple records created for same truck/event

```bash
# In Django shell:
python manage.py shell

# Check alert records:
from api.models import Alert
Alert.objects.filter(truck='ZW-AWE-5379', alert_type='off-route-detected').values('id', 'truck', 'message', 'created_at')
# Should see 4 separate records with different created_at times if duplicates are being created at backend level
```

**If you see 4+ records with milliseconds difference:**
- Problem is at backend (RoadMatchedTrailSystem calling createAlert multiple times)
- Solution: Add backend-level deduplication check before creating record

---

## Console Log Reference

### Healthy Startup (No Duplicates, Notifications Working)

```
✅ Event listeners registered for: off-route-detected, back-on-route, truck-delayed, speed-drop, driver-stopped
🔔 Notification API available
🔔 Current permission: granted
🔔 Notifications already permitted
📨 Event received: off-route-detected {truckId: 'ZW-AWE-5379', distance: '617m', ...}
📢 Processing event: off-route-detected for ZW-AWE-5379
✅ Notification sent: 🚨 Off-Route Alert
```

### Problem Indicators

**Duplicate Alerts:**
```
❌ Four identical alerts in UI for same truck+type
❌ Different created_at timestamps (23:30:04, 23:29:40, 23:28:30, ...)
```

**Invalid Date:**
```
❌ "Invalid Date" text in timestamp display
⚠️ Invalid timestamp: undefined
```

**Notifications Not Working:**
```
❌ No permission popup
❌ No "Processing event" logs
❌ Notification.permission stays 'default' or 'denied'
```

---

## File Changes Summary

| File | Changes | Status |
|------|---------|--------|
| `Alerts.jsx` | Stricter deduplication (3-tier), formatTime error handling | ✅ Applied |
| `DriverEventAlerts.jsx` | Permission request on mount, event logging, sendNotification wrapper | ✅ Applied |
| `FleetAlerts.jsx` | formatTime error handling | ✅ Applied |

---

## Next Steps If Issues Persist

### If Duplicates Still Appear:

1. **Check backend database:**
   ```bash
   python manage.py shell
   from api.models import Alert
   Alert.objects.filter(is_resolved=False).values('id', 'truck', 'alert_type', 'created_at').count()
   ```
   - If 10+ records for 2 trucks, duplicates being created at backend
   - If ≤2 records per truck, frontend dedup is failing

2. **Add debug logging to RoadMatchedTrailSystem.jsx:**
   ```javascript
   // Before createAlert:
   console.log('About to create alert for:', truckId, alertData);
   
   // Verify alertManager.emitIfNew() is returning true:
   if (alertManager.emitIfNew(truckId, 'off-route-detected', alertData)) {
     console.log('✅ Alert allowed by manager');
     createAlert(...);
   } else {
     console.log('⏭️ Alert blocked by manager (cooldown)');
   }
   ```

### If Notifications Don't Work:

1. **Check permission:**
   ```javascript
   console.log('Permission status:', Notification.permission);
   ```
   - Should be `'granted'`
   - If `'denied'`: User rejected or browser blocked
   - If `'default'`: Permission prompt never appeared

2. **Check HTTPS requirement:**
   - Notification API works on:
     - ✅ `http://localhost:*` (local dev)
     - ✅ `https://yourdomain.com` (production)
   - ❌ `http://yourdomain.com` (HTTP without localhost)

3. **Check browser support:**
   - Chrome/Chromium: ✅ Full support
   - Firefox: ✅ Full support  
   - Safari: ⚠️ Partial support (macOS 14+)
   - Edge: ✅ Full support

---

## Production Deployment Notes

When deploying to production:

1. **Ensure HTTPS** - Notification API requires secure context
2. **Set notification icons** - Replace `/truck-icon.png` with actual path
3. **Test notification permission** - Users must grant permission first time
4. **Monitor notification failures** - Add error tracking to catch permission denials

---

## Quick Checklist

- [ ] No "Invalid Date" errors in alert display
- [ ] Each truck+alert_type shows only once (no duplicates)
- [ ] Notification permission popup appears on first load
- [ ] Console shows "Notification sent:" when alerts trigger
- [ ] System notifications appear as OS-level popups
- [ ] Timestamps display correctly (e.g., "5m ago", "just now")
- [ ] Duplicate alerts don't pile up after 1 minute
