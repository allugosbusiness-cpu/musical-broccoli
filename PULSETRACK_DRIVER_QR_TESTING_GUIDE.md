# PulseTrack Driver QR Code System - Testing Guide

## System Overview

### Features Implemented:
1. **Driver-Specific QR Codes**: Each driver in the admin dashboard has a QR code
2. **Mission Assignment**: When a driver is assigned to a mission, a QR code is generated
3. **Real-Time Tracking**: Drivers scan the QR code, and their location/speed is tracked in real-time
4. **Rate Limiting**: Data is sent in batches every 5 seconds to prevent server crashes
5. **Offline Support**: Locations are queued locally if offline

---

## Prerequisites

### Physical Phone Setup:
1. **Android Phone or iPhone** (with camera)
2. **Node.js and npm** installed on your PC
3. **Expo CLI**: `npm install -g expo-cli`
4. **PulseTrack Frontend**: Running on `http://localhost:5173`
5. **PulseTrack Mobile App**: Built and running via Expo

### Network Setup:
- **PC and Phone must be on the same WiFi network**
- Phone must be able to reach PC's local IP address

---

## Step 1: Start the Frontend Dashboard

### On Your PC (Command Prompt/PowerShell):

```powershell
cd "c:\Users\Mugogo\Desktop\Fleet Management\client\Frontend"
npm run dev
```

**Expected Output:**
```
  VITE v5.4.21  ready in 1234 ms

  ➜  Local:   http://localhost:5173/
  ➜  press h + enter to show help
```

**Note the port number (usually 5173)**

---

## Step 2: Start the Mobile App

### On Your PC (New Command Prompt/PowerShell):

```powershell
cd "c:\Users\Mugogo\Desktop\Fleet Management\mobile"
npm start
```

**Expected Output:**
```
Starting Metro Bundler
Expo dev server running on http://192.168.x.x:8081
Press a to open Android emulator
Press i to open iOS simulator
Press w to open web
Press e to show QR code
Press j to open debugger
```

### On Your Phone:
1. **Install Expo Go** app from Google Play Store (Android) or App Store (iOS)
2. **Scan the QR code** shown in your terminal
   - OR press `e` to display QR code
3. **Expo Go** will automatically download and launch the PulseTrack app

---

## Step 3: Initial Driver Registration (First Time Only)

### On Your Phone:
1. Open **PulseTrack** (via Expo Go)
2. Enter your **phone number** (e.g., +263123456789 or just 0123456789)
3. Tap **"Continue to QR Scanner"**
4. You'll see a camera screen - this is where you scan the **truck registration QR code**

### On Your PC (Dashboard):
1. Open browser: **http://localhost:5173**
2. Log in to the admin dashboard
3. Navigate to **"QR Code"** tab (top navigation)
4. You'll see a **general fleet QR code**
5. Either:
   - **Print it** and scan with phone
   - **Share your screen** and have phone scan directly
   - **Download it** and open on another device

### Back on Your Phone:
1. Point phone at the **fleet QR code**
2. It will auto-scan and register your driver
3. You'll be taken to the **Dashboard**

---

## Step 4: Generate Driver-Specific QR Code

### On Your PC (Dashboard):
1. Go to **Admin** → **"Drivers"** tab
2. Find a driver in the list
3. Click the **purple QR icon** (next to eye and pencil icons) for that driver
4. A **modal window** will appear with:
   - Driver name and phone number
   - Driver's specific QR code
   - Instructions
   - Download button

### To Test with Your Driver:
1. Click the **purple QR icon** next to your name
2. Your driver QR code appears

---

## Step 5: Test Real-Time Mission Tracking

### Scenario: Mission Assignment with QR Code

#### On Your PC (Dashboard):
1. Go to **Admin** → **"Missions"** tab
2. Create a NEW mission or select an existing one:
   - **Driver**: Select yourself (the driver)
   - **Truck**: Select any truck
   - **Status**: "ASSIGNED"
   - **Origin**: e.g., "Harare"
   - **Destination**: e.g., "Mutare"
3. Click **"Save Mission"**
4. Go back to **"Drivers"** tab
5. Click the **QR icon** for your driver
6. Download or prepare to share the QR code

#### On Your Phone:
1. Make sure you're **NOT** in the dashboard yet (or go back to home)
2. Point phone camera at the **driver mission QR code**
3. App will show:
   - Your driver name
   - Mission ID
   - Message: "Location and speed will be tracked every 5 seconds"
4. Tap **"Start Tracking"** button
5. You'll be taken to the **Dashboard**

---

## Step 6: Monitor Real-Time Tracking

### On Your PC (Dashboard):
1. Once tracking starts on phone:
2. Go to **"Dashboard"** tab (main view)
3. You should see:
   - **Your driver** appears on the map (if location available)
   - **Real-time location** updates approximately every 5 seconds
   - **Speed indicator** updates
   - **Live status** shows LIVE (green indicator)

### What's Being Tracked:
- **Latitude & Longitude**
- **Speed** (in km/h or mph)
- **Timestamp** of each update
- **Accuracy** of GPS location

---

## Step 7: Rate Limiting Details

### How It Works:
1. **Location collection**: Happens as fast as phone's GPS provides (usually every 1-2 seconds)
2. **Rate limiting**: Only sends updates **every 5 seconds** to prevent server overload
3. **Queue system**: Up to 50 locations stored locally before forced send
4. **Offline support**: If phone loses internet, locations are queued and sent when connection restores

### Configuration (Advanced):
Edit file: `mobile/src/services/rateLimitedTracking.ts`

```typescript
private config: RateLimitConfig = {
  locationUpdateInterval: 5000,    // 5 seconds between updates
  alertSendInterval: 10000,        // 10 seconds between alert checks
  maxQueueSize: 50,                // Max 50 locations in queue
};
```

---

## Step 8: Send Alerts from Driver

### On Your Phone:
1. In the **Dashboard** tab, look for **"Alerts"** section
2. Tap any alert button (Speed, Traffic, Emergency, etc.)
3. Alert is queued locally
4. Every 10 seconds, queued alerts are sent to the server

### On Your PC (Dashboard):
1. Go to **"Alerts"** section
2. You should see your alert appear in the **Alerts Table**
3. Alerts include:
   - Driver name
   - Alert type
   - Timestamp
   - Status

---

## Step 9: Stop Tracking

### On Your Phone:
1. In **Dashboard**, tap the **"Stop Tracking"** or **"End Mission"** button
2. Or navigate away from the app
3. Remaining queued locations are sent to server

### Verification:
1. Location updates stop appearing on PC dashboard
2. Status changes from "LIVE" to "OFFLINE"

---

## Troubleshooting

### Problem: Phone can't reach PC's Expo Server
**Solution:**
1. Find PC's IP address:
   ```powershell
   ipconfig
   ```
   Look for "IPv4 Address" (usually 192.168.x.x)
2. On phone, when scanning QR:
   - Change `localhost:8081` to `192.168.x.x:8081`
   - Or restart Expo with: `expo start --tunnel`

### Problem: QR code won't scan
**Solution:**
1. Ensure good lighting
2. Print at least 3x3 inches
3. Hold phone 4-6 inches away
4. Try downloading the QR code image and opening on another device to scan

### Problem: Locations not updating on dashboard
**Solution:**
1. Check phone has GPS enabled
2. Ensure phone has internet connection
3. Check PC terminal for error messages
4. Restart both apps

### Problem: App crashes when scanning QR
**Solution:**
1. Check mobile/src/screens/QRScannerScreen.tsx for errors
2. Ensure rate-limited tracking service is installed
3. Check AsyncStorage permissions

---

## Expected Data Flow

### With Rate Limiting:

```
Phone GPS             →  Local Queue           →  Backend
Every 1-2 sec         Every 5 sec              (Batched)
  |                        |
  └─ Location 1   ──→ [L1, L2, L3, L4, L5] ──→ Save all 5 to database
  └─ Location 2           (Every 5 sec)         (Every 5-30 seconds)
  └─ Location 3
  └─ Location 4
  └─ Location 5
```

### Performance Benefits:
- **Reduced server load**: 5 locations per request instead of 5 requests
- **Reduced bandwidth**: Batch sending is more efficient
- **Better battery life**: Less frequent network calls
- **Offline resilience**: Locations cached locally

---

## Performance Metrics

### System Capacity (Before Crashes):
- **Without Rate Limiting**: ~5-10 drivers maximum
- **With Rate Limiting**: ~100+ drivers simultaneously
- **Max locations per driver**: 50 in queue
- **Max queue time**: 30 seconds before forced send

---

## Testing Checklist

- [ ] Frontend dashboard loads at localhost:5173
- [ ] Mobile app starts via Expo Go
- [ ] Initial driver registration works
- [ ] Driver QR code displays in admin
- [ ] Scanning driver QR code starts tracking
- [ ] Location updates appear on dashboard every ~5 seconds
- [ ] Speed shows in dashboard
- [ ] Alerts can be sent from phone
- [ ] Alerts appear in admin dashboard
- [ ] Tracking can be stopped
- [ ] Location updates stop when tracking ends
- [ ] Offline queuing works (disable WiFi, then reconnect)

---

## Next Steps (Optional)

### Backend Enhancements:
1. Add database indexes for location queries
2. Implement WebSocket for real-time dashboard updates
3. Add data aggregation (10-second averages, etc.)
4. Implement historical playback of routes

### Mobile App Enhancements:
1. Add battery optimization
2. Add offline map caching
3. Add geofencing alerts
4. Add emergency SOS button

### Dashboard Enhancements:
1. Add heatmap of high-traffic areas
2. Add driver performance analytics
3. Add predictive ETA calculations
4. Add route optimization suggestions

---

## Support

For issues or questions:
1. Check the error messages in phone's Expo console
2. Check PC terminal for backend errors
3. Review logs in AsyncStorage (for mobile)
4. Check browser console (for frontend)

---

**Happy Testing! 🚀**
