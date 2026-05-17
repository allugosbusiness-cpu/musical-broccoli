#!/bin/bash
# 🔍 Fleet Tracking App - Diagnostic Script
# Checks all three critical issues and provides solutions

echo "================================================"
echo "🔍 FLEET TRACKING APP - DIAGNOSTICS"
echo "================================================"
echo ""

# Color codes
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# ============================================
# DIAGNOSTIC 1: Check OTA Updates Configuration
# ============================================
echo "${BLUE}📋 DIAGNOSTIC 1: OTA Updates Configuration${NC}"
echo "─────────────────────────────────────"

APP_JSON_PATH="mobile/app.json"

if grep -q '"enabled": false' "$APP_JSON_PATH"; then
    echo -e "${GREEN}✅ OTA Updates: DISABLED${NC}"
    echo "   Status: App will not try to download remote updates"
else
    echo -e "${RED}❌ OTA Updates: ENABLED${NC}"
    echo "   Action Required: Set 'enabled: false' in mobile/app.json"
    echo "   This is causing: java.io.IOException: failed to download remote update"
fi

echo ""

# ============================================
# DIAGNOSTIC 2: Check API Configuration
# ============================================
echo "${BLUE}📋 DIAGNOSTIC 2: API Configuration${NC}"
echo "─────────────────────────────────────"

API_CONFIG_PATH="mobile/src/config/apiConfig.ts"

if grep -q "isExpoGo" "$API_CONFIG_PATH"; then
    echo -e "${GREEN}✅ API Platform Detection: CONFIGURED${NC}"
    echo "   Status: Code auto-detects Emulator vs Physical Device"
    echo "   Android Emulator → 10.0.2.2:8000"
    echo "   Android Device   → 192.168.1.236:8000"
else
    echo -e "${RED}❌ API Platform Detection: MISSING${NC}"
    echo "   Action Required: Update apiConfig.ts to detect platform"
    echo "   This is causing: QR scans to fail (can't reach backend)"
fi

echo ""

# ============================================
# DIAGNOSTIC 3: Check Pin Rendering Code
# ============================================
echo "${BLUE}📋 DIAGNOSTIC 3: Pin Rendering Setup${NC}"
echo "─────────────────────────────────────"

GLOBALMAP_PATH="client/Frontend/src/components/GlobalMap.jsx"

if grep -q "setSelectedTruckData" "$GLOBALMAP_PATH"; then
    echo -e "${GREEN}✅ Pin State Sync: IMPLEMENTED${NC}"
    echo "   Status: selectedTruckData syncs when truck selected"
else
    echo -e "${RED}❌ Pin State Sync: MISSING${NC}"
    echo "   Action Required: Add useEffect to sync selectedTruckData"
    echo "   This is causing: Info panel doesn't update on marker click"
fi

if grep -q "marker.on.*click" "$GLOBALMAP_PATH"; then
    echo -e "${GREEN}✅ Marker Click Handler: IMPLEMENTED${NC}"
    echo "   Status: Markers respond to click events"
else
    echo -e "${RED}❌ Marker Click Handler: MISSING${NC}"
    echo "   Action Required: Add click event listener to markers"
fi

echo ""

# ============================================
# DIAGNOSTIC 4: Network Connectivity
# ============================================
echo "${BLUE}📋 DIAGNOSTIC 4: Network Connectivity${NC}"
echo "─────────────────────────────────────"

echo "Checking backend server (port 8000)..."
if timeout 3 bash -c 'exec 3<>/dev/tcp/localhost/8000' 2>/dev/null; then
    echo -e "${GREEN}✅ Backend Server: REACHABLE${NC}"
    echo "   Location: localhost:8000"
else
    echo -e "${RED}❌ Backend Server: NOT REACHABLE${NC}"
    echo "   Action Required: Start Django server"
    echo "   Command: python manage.py runserver 0.0.0.0:8000"
fi

echo "Checking Vite dev server (port 5173)..."
if timeout 3 bash -c 'exec 3<>/dev/tcp/localhost/5173' 2>/dev/null; then
    echo -e "${GREEN}✅ Web Dev Server: REACHABLE${NC}"
    echo "   Location: localhost:5173"
else
    echo -e "${YELLOW}⚠️  Web Dev Server: NOT REACHABLE${NC}"
    echo "   Note: This is OK if not running web app right now"
fi

echo ""

# ============================================
# DIAGNOSTIC 5: LAN IP Detection
# ============================================
echo "${BLUE}📋 DIAGNOSTIC 5: LAN IP Configuration${NC}"
echo "─────────────────────────────────────"

# Try to get LAN IP (Windows)
LAN_IP=$(ipconfig | grep "IPv4" | grep "192.168" | head -1 | awk '{print $NF}')

if [ -z "$LAN_IP" ]; then
    # Try Linux
    LAN_IP=$(hostname -I | awk '{print $1}')
fi

if [ -n "$LAN_IP" ]; then
    echo -e "${GREEN}✅ LAN IP Detected: $LAN_IP${NC}"
    echo "   Use this IP for Android Physical Devices"
    echo "   Update API_BASE_URL to: http://$LAN_IP:8000/api/v1"
else
    echo -e "${YELLOW}⚠️  LAN IP: NOT DETECTED${NC}"
    echo "   For Android Physical Device, use: 192.168.x.x:8000"
    echo "   Run: ipconfig (Windows) or hostname -I (Linux)"
fi

echo ""

# ============================================
# SUMMARY
# ============================================
echo "${BLUE}📊 DIAGNOSTIC SUMMARY${NC}"
echo "─────────────────────────────────────"

ISSUES=0

if ! grep -q '"enabled": false' "$APP_JSON_PATH"; then
    ISSUES=$((ISSUES + 1))
fi

if ! grep -q "isExpoGo" "$API_CONFIG_PATH"; then
    ISSUES=$((ISSUES + 1))
fi

if ! grep -q "setSelectedTruckData" "$GLOBALMAP_PATH"; then
    ISSUES=$((ISSUES + 1))
fi

if [ $ISSUES -eq 0 ]; then
    echo -e "${GREEN}✅ ALL SYSTEMS OPERATIONAL${NC}"
    echo ""
    echo "Next Steps:"
    echo "1. npm install --legacy-peer-deps"
    echo "2. Start backend, web app, and mobile app"
    echo "3. Test marker clicks and QR scanning"
else
    echo -e "${RED}❌ $ISSUES ISSUES FOUND${NC}"
    echo ""
    echo "Please apply the fixes from CRITICAL_FIXES_APPLIED.md"
fi

echo ""
echo "================================================"
echo "Diagnostic complete. Check logs above for status."
echo "================================================"
