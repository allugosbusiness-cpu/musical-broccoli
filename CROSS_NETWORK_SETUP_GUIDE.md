# PulseTrack Cross-Network Communication Setup Guide

## 🚀 What's New (May 12, 2026)

Your fleet management system now supports **cross-network communication**. Mobile apps and web dashboards can operate on **completely different WiFi networks** and still sync in real-time.

### Key Features ✅
- ✅ **Automatic Network Detection** - Picks fastest available connection
- ✅ **Intelligent Fallback** - Local network first, public backend as fallback
- ✅ **Real-Time Sync** - Location, speed, alerts across all networks
- ✅ **Automatic Retry** - Handles 404s and network errors gracefully
- ✅ **Zero Configuration** - Works out of the box

---

## 📋 Quick Start

### For Same Network (Fastest)
```bash
# 1. Start backend locally
cd server && python manage.py runserver

# 2. Start mobile app (same WiFi)
cd mobile && npm start

# 3. Open web dashboard
# http://localhost:5173 (dev) or https://pulsetrack-frontend-henna.vercel.app (prod)

# 4. Mobile app will auto-detect local network and use it
# ✓ Latency: 100-200ms (fast!)
```

### For Different Networks (Works Cross-Network)
```bash
# 1. Mobile on WiFi A, Web Dashboard on WiFi B
# 2. Mobile app automatically connects to Render backend
# 3. Web dashboard queries same Render backend
# 4. Real-time sync works across networks!
# ✓ Latency: 500-1500ms (acceptable for fleet ops)
```

---

## Overview

PulseTrack supports three deployment scenarios:
- **Same LAN**: All devices on same WiFi (fastest)
- **Cross-Network**: Different WiFi networks with Render backend
- **Mixed**: Some devices local, others cross-network

---

## 🔄 Network Selection Logic

The mobile app automatically chooses the best network:

```
App Starts
  ↓
Development Mode?
  ├─ YES → Try Local Network First
  │   ├─ Backend responding? → Use it (fast!)
  │   └─ Network error? → Fallback to Render
  │
  └─ NO (Production) → Use Render Backend Directly
```

### Local Network Detection
- **Android Emulator:** `http://10.0.2.2:8000/api/v1`
- **Physical Device:** `http://localhost:8000/api/v1`
- **Fallback:** `https://pulsetrack-back.onrender.com/api/v1`

---

## ⚡ Performance by Network

| Network Type | Latency | Best For | Status |
|-------------|---------|----------|--------|
| Same WiFi (Local) | 100-200ms | Office/Yard operations | ✅ Optimal |
| Different WiFi (Render) | 500-1500ms | Multi-location fleets | ✅ Working |
| Cellular (Render) | 1-3s | Individual drivers in field | ✅ Supported |

---

## Setup Instructions

### Step 1: Verify Backend Configuration

**For Local Development:**
```bash
# Check Django settings has correct ALLOWED_HOSTS
grep -n "pulsetrack-back.onrender.com" Logistics/settings.py
grep -n "CSRF_TRUSTED_ORIGINS" Logistics/settings.py

# Start backend
cd server && python manage.py runserver
# Output: Starting development server at http://127.0.0.1:8000/
```

**For Production (Render):**
- Backend already deployed to: `https://pulsetrack-back.onrender.com`
- No setup needed - mobile app will auto-detect and use it

### Step 2: Verify Mobile Configuration

**Check app.json:**
```bash
grep -A2 "extra" mobile/app.json | grep "API_BASE_URL"
# Should show: "https://pulsetrack-back.onrender.com/api/v1"
```

**Check apiConfig.ts:**
```bash
grep "FALLBACK_API_URL\|productionApiUrl" mobile/src/config/apiConfig.ts
# Should show: "https://pulsetrack-back.onrender.com/api/v1"
```

### Step 3: Start Your Apps

**Backend (if local development):**
```bash
cd server
python manage.py runserver
```

**Mobile App:**
```bash
cd mobile
npm start
# Press 'a' for Android, 'i' for iOS, 'w' for web

# Watch logs for:
# 📡 Development mode
# 🌐 WiFi network detected (or Cross-network detected)
# ✅ Request succeeded
```

**Web Dashboard:**
```bash
# Local dev
cd client/Frontend && npm run dev

# Or open production
# https://pulsetrack-frontend-henna.vercel.app
```

### Step 4: Test Cross-Network Communication

**Test 1: Same Network**
1. Mobile and backend on same WiFi
2. Open web dashboard on same network
3. Start mission from mobile
4. Watch truck on map update in real-time
5. ✅ Should see updates every 5-10 seconds

**Test 2: Different Networks**
1. Mobile on WiFi A
2. Web dashboard on WiFi B (or different internet connection)
3. Start mission from mobile
4. Truck still appears on map and updates in real-time
5. ✅ Slightly delayed (500-1500ms) but working!

**Test 3: Network Switching**
1. Mobile app actively tracking mission
2. Switch from WiFi A to WiFi B mid-mission
3. Mobile app continues tracking seamlessly
4. Updates continue to web dashboard
5. ✅ No errors, no manual reconnection needed

---

## Quick Reference

### Finding Backend IP (for same-network scenarios)

**Windows:**
```powershell
ipconfig
# Look for "IPv4 Address" under your network adapter
# Example: 192.168.1.100
```

**macOS/Linux:**
```bash
ifconfig
# Look for "inet" under your active network interface
# Example: 192.168.1.100

2. **Edit `.env.local`**:

For local development:
```env
VITE_API_BASE_URL=http://localhost:8000/api
```

For same network testing:
```env
VITE_API_BASE_URL=http://192.168.1.100:8000/api
```

For remote server:
```env
VITE_API_BASE_URL=https://api.pulsetrack.example.com/api
```

3. **Restart frontend**:
```bash
cd client/Frontend
npm run dev
```

### Step 3: Configure Mobile App (React Native)

1. **Create `.env.local` file** in `mobile/`:
```bash
cp mobile/.env.example mobile/.env.local
```

2. **Edit `.env.local`** based on your deployment:

**Android Emulator** (Backend on same machine):
```env
EXPO_PUBLIC_API_BASE_URL=http://10.0.2.2:8000/api/v1
```

**Android Physical Device** (Same network):
```env
EXPO_PUBLIC_API_BASE_URL=http://192.168.1.100:8000/api/v1
```

**iOS Simulator** (Backend on same machine):
```env
EXPO_PUBLIC_API_BASE_URL=http://localhost:8000/api/v1
```

**iOS Physical Device** (Same network):
```env
EXPO_PUBLIC_API_BASE_URL=http://192.168.1.100:8000/api/v1
```

**Different Network** (Remote/VPN):
```env
EXPO_PUBLIC_API_BASE_URL=https://api.pulsetrack.example.com/api/v1
```

3. **Restart mobile app**:
```bash
cd mobile
npm start
# Then press 'a' for Android or 'i' for iOS
```

### Step 4: Verify Backend Configuration

The backend (`server/Logistics/settings.py`) is already configured to accept cross-network requests:

- ✅ `ALLOWED_HOSTS = ['*']` - Accepts requests from any host
- ✅ `CORS_ALLOW_ALL_ORIGINS = True` (in DEBUG mode) - Allows cross-origin requests
- ✅ Retry logic built into both frontend and mobile APIs

No backend configuration changes needed for same-network setup.

---

## Testing Cross-Network Communication

### Test 1: Frontend to Backend

1. Open frontend in browser: `http://localhost:5173`
2. Check browser console (F12 → Console)
3. Should see: `🔗 Frontend API Base: http://YOUR_IP:8000/api`
4. Navigate to any page that loads data (Drivers, Trucks, Missions)
5. Verify data loads without errors

### Test 2: Mobile to Backend

1. Start mobile app
2. Open Expo DevTools console
3. Should see:
   ```
   📱 [Platform]: [Config URL]
   🔗 Backend API Base: [Your configured URL]
   ```
4. Complete QR registration flow
5. Verify driver data appears in backend

### Test 3: Real-time Sync

1. Start mission tracking on mobile app
2. Check backend admin dashboard
3. Verify location/speed updates appear in real-time
4. Check mobile logs for successful API calls

---

## Network Scenarios

### Scenario 1: Local Development

**Setup:**
- Backend running on `localhost:8000`
- Frontend running on `localhost:5173`
- Mobile running on Android Emulator

**Configuration:**
```env
# Frontend
VITE_API_BASE_URL=http://localhost:8000/api

# Mobile (Android Emulator)
EXPO_PUBLIC_API_BASE_URL=http://10.0.2.2:8000/api/v1
```

**Testing:**
- Frontend: `http://localhost:5173`
- Mobile: Start emulator, scan QR codes

---

### Scenario 2: Same Local Network (LAN)

**Setup:**
- Backend on machine with IP `192.168.1.100` (example)
- Frontend accessed from laptop on same WiFi
- Mobile device on same WiFi

**Configuration:**
```env
# Frontend (.env.local)
VITE_API_BASE_URL=http://192.168.1.100:8000/api

# Mobile (.env.local)
EXPO_PUBLIC_API_BASE_URL=http://192.168.1.100:8000/api/v1
```

**Testing:**
- Frontend: Navigate to `http://192.168.1.100:5173`
- Mobile: Should sync data automatically

**Troubleshooting:**
- Verify all devices on same network: `ping 192.168.1.100`
- Check firewall allows port 8000
- Disable VPN/proxy on test devices

---

### Scenario 3: Remote Network (VPN/Public Domain)

**Setup:**
- Backend behind VPN or on public domain
- Frontend/Mobile access from anywhere

**Prerequisites:**
- HTTPS certificate (get free one from Let's Encrypt)
- Public domain or VPN connection
- SSL/TLS certificate installed on server

**Configuration:**
```env
# Frontend
VITE_API_BASE_URL=https://api.pulsetrack.example.com/api

# Mobile
EXPO_PUBLIC_API_BASE_URL=https://api.pulsetrack.example.com/api/v1
```

**Backend changes** (in `server/Logistics/settings.py`):
```python
# Disable DEBUG mode
DEBUG = False

# Set allowed hosts
ALLOWED_HOSTS = ['api.pulsetrack.example.com', 'www.pulsetrack.example.com']

# Update CORS to only allow your domains
CORS_ALLOWED_ORIGINS = [
    'https://pulsetrack.example.com',
    'https://app.pulsetrack.example.com',
]

# Enforce HTTPS
SECURE_SSL_REDIRECT = True
SESSION_COOKIE_SECURE = True
CSRF_COOKIE_SECURE = True
```

---

## Built-in Retry & Resilience

Both frontend and mobile apps include automatic retry logic:

**Retry Configuration:**
- Max retries: 3
- Initial delay: 1000ms
- Backoff multiplier: 2x (exponential)
- Request timeout: 30 seconds

**Retryable Errors:**
- HTTP 408, 429, 500, 502, 503, 504
- Network timeouts
- Connection refused

**Example Flow:**
```
Request fails with timeout
→ Wait 1000ms
→ Retry (attempt 2/3)
→ Fails again
→ Wait 2000ms (1000 * 2)
→ Retry (attempt 3/3)
→ Success or final failure
```

---

## Troubleshooting

### Frontend Can't Connect to Backend

**Symptoms:**
- Console error: `Failed to load data`
- Network tab shows failed requests

**Solutions:**
1. Verify backend is running:
   ```bash
   curl http://YOUR_IP:8000/api/
   ```

2. Check CORS headers:
   ```bash
   curl -i http://YOUR_IP:8000/api/
   ```
   Should see `Access-Control-Allow-Origin: *`

3. Verify API_BASE_URL in `.env.local`:
   ```bash
   cat client/Frontend/.env.local | grep VITE_API_BASE_URL
   ```

4. Check browser console for actual error message

---

### Mobile App Can't Connect

**Symptoms:**
- Expo console shows network errors
- Data won't sync

**Android Emulator:**
- Verify using `http://10.0.2.2:8000/api/v1`
- Not `http://localhost:8000/api/v1`

**Physical Device:**
- Verify device on same WiFi as backend
- Verify firewall allows port 8000
- Test: `ping YOUR_BACKEND_IP` from device

**Different Network:**
- Verify VPN is connected
- Verify domain DNS resolves
- Test: `curl https://api.pulsetrack.example.com/api/v1/`

---

### API Requests Timing Out

**Symptoms:**
- Requests fail after 30 seconds
- Mobile shows "Processing..." then fails

**Solutions:**
1. Check backend performance:
   ```bash
   # Monitor CPU/Memory while making requests
   ```

2. Check network latency:
   ```bash
   ping YOUR_BACKEND_IP
   # Should be < 100ms for same network
   ```

3. Check backend logs for errors:
   ```bash
   cd server
   tail -f logs/debug.log
   ```

4. Increase timeout (advanced):
   - Frontend: Edit `src/config/apiConfig.js` → `timeout`
   - Mobile: Edit `src/config/apiConfig.ts` → `requestTimeout`

---

## Environment Variables Reference

### Frontend (`client/Frontend/.env.local`)

| Variable | Default | Example |
|----------|---------|---------|
| `VITE_API_BASE_URL` | `http://localhost:8000/api` | `http://192.168.1.100:8000/api` |
| `VITE_ENVIRONMENT` | `development` | `production` |
| `VITE_DEBUG` | `true` | `false` |

### Mobile (`mobile/.env.local`)

| Variable | Default | Example |
|----------|---------|---------|
| `EXPO_PUBLIC_API_BASE_URL` | `http://10.0.2.2:8000/api/v1` | `http://192.168.1.100:8000/api/v1` |
| `EXPO_PUBLIC_DEBUG` | `true` | `false` |
| `EXPO_PUBLIC_REQUEST_TIMEOUT` | `30000` | `45000` |
| `EXPO_PUBLIC_MAX_RETRIES` | `3` | `5` |

---

## Performance Tips

1. **Use same network when possible** - Lower latency = faster syncing
2. **Monitor backend logs** - Check for bottlenecks
3. **Rate limit configuration** - Mobile app limits to 20 requests/sec by default
4. **Use HTTPS in production** - Adds minimal overhead with caching

---

## Security Best Practices

1. **Never expose backend without HTTPS** in production
2. **Use firewall** to restrict port 8000 access
3. **Use strong passwords** for admin dashboard
4. **Rotate tokens** periodically
5. **Keep dependencies updated** - Run `npm audit fix`

---

## Support & Debug

For debugging, enable verbose logging:

**Frontend:**
```javascript
// In browser console
localStorage.setItem('debug', '*');
location.reload();
```

**Mobile:**
```bash
# Run with debug output
npm start -- --verbose
```

**Backend:**
```python
# In settings.py
LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'handlers': {
        'console': {
            'class': 'logging.StreamHandler',
        },
    },
    'root': {
        'handlers': ['console'],
        'level': 'DEBUG',
    },
}
```

---

## Next Steps

1. ✅ Configure `.env` files for your network
2. ✅ Restart frontend and mobile apps
3. ✅ Test data syncing
4. ✅ Monitor logs for any errors
5. ✅ Deploy to production when ready

For questions or issues, check the project README or GitHub issues.
