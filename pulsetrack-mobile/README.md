# PulseTrack Mobile App

Fleet Management Driver Application built with **React Native (Expo)**.

## Overview

This mobile app works hand-in-hand with the **PulseTrack Fleet Management System** web app. Drivers use this app to:

1. **Register** - Enter name/phone, scan a QR code on their truck or enter a 6-digit PIN
2. **View Missions** - See assigned missions with origin/destination coordinates and cargo details
3. **Track in Real-Time** - GPS location, speed, and altitude are sent to the web app every 2 minutes
4. **Live Map** - View the route from origin to destination with real-time driver position
5. **Send Alerts** - Report mechanical issues, route problems, emergencies, and more
6. **Complete Missions** - Mark missions as completed with performance points awarded

## Tech Stack

- **Framework**: React Native (Expo SDK 50)
- **Navigation**: @react-navigation/native-stack
- **Maps**: react-native-maps (Google Maps)
- **Camera**: expo-camera (QR code scanning)
- **GPS**: expo-location (foreground + background tracking)
- **Sensors**: expo-sensors (speed monitoring)
- **Storage**: @react-native-async-storage/async-storage
- **Backend**: PulseTrack REST API at https://pulsetrack-back.onrender.com/api/v1

## Backend API Integration

The app communicates with the PulseTrack backend for:

| Endpoint | Method | Purpose |
|----------|--------|---------|
| `/mobile/driver-registration/` | POST | Register via QR code |
| `/mobile/validate-pin/` | POST | Register via 6-digit PIN |
| `/mobile/driver/{id}/available-missions/` | GET | List available missions |
| `/mobile/driver/{id}/current-mission/` | GET | Get active mission |
| `/mobile/mission/start-tracking/` | POST | Start a mission |
| `/mobile/mission/complete/{id}/` | POST | Complete a mission |
| `/mobile/driver/{id}/location/` | POST | Send GPS position & speed |
| `/mobile/alert/` | POST | Send driver alerts |
| `/mobile/driver/{id}/profile/` | GET | Get driver profile |

## Installation & Running

### Prerequisites

- **Node.js** v16+ (download from https://nodejs.org)
- **Expo CLI** (`npm install -g expo-cli`)
- **Expo Go** app on your phone (iOS/Android) for testing
- OR **Android Studio** for Android emulator
- OR **Xcode** for iOS simulator

### Setup

```bash
# Navigate to the mobile app directory
cd pulsetrack-mobile

# Install dependencies
npm install

# Start the Expo development server
npx expo start
```

### Running on a Device

1. Install **Expo Go** on your phone
2. Scan the QR code shown in terminal with Expo Go (Android) or Camera app (iOS)
3. The app will load and connect to the PulseTrack backend

### Building for Production

```bash
# Android APK
npm run build:android

# iOS IPA (requires Apple Developer account)
npm run build:ios
```

## App Flow

1. **Splash Screen** → App loads and checks for saved session
2. **Login Screen** → Driver enters name, phone number, and either:
   - **PIN Code**: 6-digit code from fleet manager
   - **QR Code**: Scan QR on the truck
3. **Home/Dashboard** → View current speed, GPS status, current mission, and available missions
4. **Missions** → List of assigned missions with start/complete buttons
5. **Tracking/Map** → Real-time Google Maps view showing:
   - Driver's current location with accuracy circle
   - Origin (green) and destination (red) markers
   - Route polyline
   - Current speed and GPS status
   - Start/Stop tracking and Complete mission buttons
6. **Alerts** → Send alerts to fleet manager:
   - Mechanical issue
   - Route deviation
   - Traffic
   - Emergency
   - Fuel issue
   - General report
7. **Profile** → View driver info, performance points, GPS toggle, and logout

## GPS Tracking Details

- **Foreground**: Continuous location watching (every ~60 seconds)
- **Background**: Location updates continue when app is minimized
- **Interval**: Location sent to server every 2 minutes (configurable)
- **Distance Filter**: Only sends if moved more than 50 meters
- **Speed**: Monitored in real-time, alerts if > 120 km/h
- **Accuracy**: GPS accuracy circle displayed on map

## Configuration

Edit `src/config/api.js` to change the backend URL:

```javascript
const API_BASE_URL = 'https://pulsetrack-back.onrender.com/api/v1';
```

Edit `app.json` → `"extra"` section for app-level config:

```json
{
  "apiBaseUrl": "https://pulsetrack-back.onrender.com/api/v1",
  "locationUpdateInterval": 120000,
  "locationDistanceFilter": 50
}
```

## Key Files

| File | Purpose |
|------|---------|
| `App.js` | Entry point, navigation setup |
| `src/config/api.js` | Backend API configuration |
| `src/config/theme.js` | Colors, fonts, spacing constants |
| `src/services/apiService.js` | HTTP API client |
| `src/services/locationService.js` | GPS tracking with background mode |
| `src/utils/storage.js` | AsyncStorage persistence |
| `src/screens/LoginScreen.js` | Registration with PIN or QR |
| `src/screens/QRScannerScreen.js` | Camera QR code scanner |
| `src/screens/HomeScreen.js` | Driver dashboard |
| `src/screens/MissionsScreen.js` | Mission list management |
| `src/screens/TrackingScreen.js` | Real-time map tracking |
| `src/screens/AlertsScreen.js` | Alert sending |
| `src/screens/ProfileScreen.js` | Driver profile & settings |
| `src/navigation/AppNavigator.js` | Screen routing |
| `app.json` | Expo configuration & permissions |

## Permissions Required

- **Camera**: QR code scanning for truck registration
- **Location (Foreground)**: Real-time tracking while app is open
- **Location (Background)**: Continue tracking when app is minimized
- Both iOS and Android permissions are configured in `app.json`

## Troubleshooting

1. **"Network request failed"** - Check internet connection and backend URL
2. **"Camera permission denied"** - Grant camera access in phone settings
3. **"Location permission denied"** - Grant location access in phone settings
4. **White screen on startup** - Run `npx expo start --clear` to clear cache
5. **Build errors** - Ensure all dependencies are installed: `npm install`

## Version

v2.0.0 - Full fleet management mobile solution

## Links

- **Backend API**: https://pulsetrack-back.onrender.com/api/v1
- **Web App**: https://pulsetrack-frontend-henna.vercel.app/
- **GitHub**: https://github.com/allugosbusiness-cpu/musical-broccoli