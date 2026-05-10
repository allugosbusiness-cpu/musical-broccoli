# PulseTrack Physical Device Testing Guide

Quick reference for testing PulseTrack on physical devices across different networks.

## Find Your Backend IP (Windows)

Open Command Prompt and run:
```powershell
ipconfig
```

Look for IPv4 Address - it will be something like `192.168.1.100` or `10.0.0.5`

Example output:
```
Ethernet adapter Ethernet:
   IPv4 Address. . . . . . . . . : 192.168.1.100
   Subnet Mask . . . . . . . . . : 255.255.255.0
```

## Backend Network Access Checklist

- [ ] Backend is running: `npm run dev` or `python manage.py runserver 0.0.0.0:8000`
- [ ] Port 8000 is accessible
- [ ] Windows Firewall allows port 8000 (or disable for testing)
- [ ] Device is on same network OR connected via VPN
- [ ] Backend IP is correct and static

## Desktop Browser Testing

Test that your backend IP works from the browser:

```
http://192.168.1.100:8000/api/
```

Should see JSON response. If not, the device can't reach backend.

## Android Physical Device Testing

### Same Network (WiFi)

1. Find backend IP: `192.168.1.100` (example)

2. Mobile `.env.local`:
```env
EXPO_PUBLIC_API_BASE_URL=http://192.168.1.100:8000/api/v1
```

3. Start Expo:
```bash
cd mobile
npm start
```

4. On Android device, scan QR code OR press Espresso to open

5. Watch Expo console - should see:
```
📱 Android (Physical): http://192.168.1.100:8000/api/v1
🔗 Backend API Base: http://192.168.1.100:8000/api/v1
```

### Different Network (Cellular/Different WiFi)

Options:
1. **Use VPN** - Connect device to VPN, then use VPN IP/domain
2. **Use public IP** - Set backend domain in DNS
3. **Use ngrok** - Expose localhost publicly:
   ```bash
   ngrok http 8000
   # Copy provided URL and use in EXPO_PUBLIC_API_BASE_URL
   ```

## iOS Physical Device Testing

### Same Network (WiFi)

1. Find backend IP: `192.168.1.100` (example)

2. Mobile `.env.local`:
```env
EXPO_PUBLIC_API_BASE_URL=http://192.168.1.100:8000/api/v1
```

3. Start Expo:
```bash
cd mobile
npm start
```

4. On iOS device, scan QR code or use Expo app

5. Should see same console output as Android

### Common iOS Issues

- **SSL/TLS errors**: iOS requires HTTPS for non-localhost
- **Solution**: Use domain with valid HTTPS certificate
- **For local testing**: Use device hotspot from PC with static IP

## Frontend Web Testing on Physical Device

1. Start frontend:
```bash
cd client/Frontend
npm run dev
```

Vite shows URL like: `http://localhost:5174/`

2. Find your PC IP and navigate from phone:
```
http://192.168.1.100:5174/
```

3. Frontend should load and sync with backend

## Quick Diagnostic Commands

```bash
# Test backend is accessible
curl http://192.168.1.100:8000/api/

# Test from specific port (if changed)
curl http://192.168.1.100:8000/

# Check firewall (Windows)
netstat -an | findstr :8000

# Kill process using port 8000 (if stuck)
netstat -ano | findstr :8000
taskkill /PID <PID> /F

# Monitor backend requests in real-time
# (in server directory)
tail -f debug.log
```

## Device Network Settings

### Android
- Settings → WiFi → Connect to same network as backend
- Verify IP: Settings → About phone → IP address

### iOS
- Settings → WiFi → Connect to same network as backend
- Verify IP: Settings → General → About → IP Address

## Firewall Configuration

If app can't connect, firewall may be blocking:

### Windows Firewall
1. Windows Defender Firewall → Allow an app through firewall
2. Find Python/Node.js
3. Check "Private" if on home network
4. Check "Public" if need external access

### macOS Firewall
1. System Preferences → Security & Privacy → Firewall
2. Firewall Options → Allow incoming connections for Python/Node

### Linux
```bash
sudo ufw allow 8000
```

## Testing Checklist

- [ ] Backend running on `0.0.0.0:8000`
- [ ] PC/Mac IP verified (not localhost)
- [ ] Device on same network (WiFi connected)
- [ ] `.env` files configured with correct IP
- [ ] Expo restarted after `.env` changes
- [ ] Browser can reach `http://IP:8000/api/`
- [ ] Device can reach same IP:8000
- [ ] No firewall blocks access
- [ ] App QR scan completes
- [ ] Driver registration succeeds
- [ ] Location data appears in backend

## Troubleshooting Matrix

| Issue | Cause | Fix |
|-------|-------|-----|
| Can't find backend | Wrong IP or port | Re-check `ipconfig`, port 8000 open |
| Connection timeout | Firewall blocking | Allow port 8000 in firewall |
| DNS error | Network issue | Switch to IP instead of domain |
| SSL error (iOS) | Not HTTPS | Use domain with cert or different network |
| Retrying failed requests | Server slow | Check backend CPU/memory, reduce data |
| "Processing..." stuck | Timeout | Check network latency: `ping IP` |

## Performance Tips

- **Reduce data**: Check fewer drivers/trucks in admin
- **Check network**: Should have < 100ms latency for same network
- **Monitor backend**: Use `htop` or Task Manager while testing
- **Use wired**: Ethernet often faster/more reliable than WiFi
- **Reduce refresh**: Lower dashboard update frequency during test

## Success Indicators

✅ Mobile app loads QR scanner screen  
✅ QR scan triggers registration  
✅ Driver appears in backend list  
✅ Location updates visible in real-time  
✅ No error logs in console  
✅ Backend responds quickly (< 1 second)

## Next Steps

1. Successfully test on same network
2. Test on different network (if needed)
3. Verify all features work (QR, location, alerts)
4. Load test with multiple devices
5. Deploy to production

---

**Still having issues?** Check CROSS_NETWORK_SETUP_GUIDE.md for detailed troubleshooting.
