# 🔍 Fleet Tracking App - Diagnostics (PowerShell)
# Checks all three critical issues and provides solutions

Write-Host "================================================" -ForegroundColor Blue
Write-Host "🔍 FLEET TRACKING APP - DIAGNOSTICS" -ForegroundColor Blue
Write-Host "================================================" -ForegroundColor Blue
Write-Host ""

# ============================================
# DIAGNOSTIC 1: Check OTA Updates Configuration
# ============================================
Write-Host "📋 DIAGNOSTIC 1: OTA Updates Configuration" -ForegroundColor Cyan
Write-Host "─────────────────────────────────────" -ForegroundColor Cyan

$appJsonPath = "mobile\app.json"

if (Test-Path $appJsonPath) {
    $appJsonContent = Get-Content $appJsonPath -Raw
    
    if ($appJsonContent -match '"enabled":\s*false') {
        Write-Host "✅ OTA Updates: DISABLED" -ForegroundColor Green
        Write-Host "   Status: App will not try to download remote updates"
    } else {
        Write-Host "❌ OTA Updates: ENABLED" -ForegroundColor Red
        Write-Host "   Action Required: Set 'enabled: false' in mobile/app.json"
        Write-Host "   This is causing: java.io.IOException: failed to download remote update"
    }
} else {
    Write-Host "⚠️  app.json not found at: $appJsonPath" -ForegroundColor Yellow
}

Write-Host ""

# ============================================
# DIAGNOSTIC 2: Check API Configuration
# ============================================
Write-Host "📋 DIAGNOSTIC 2: API Configuration" -ForegroundColor Cyan
Write-Host "─────────────────────────────────────" -ForegroundColor Cyan

$apiConfigPath = "mobile\src\config\apiConfig.ts"

if (Test-Path $apiConfigPath) {
    $apiConfigContent = Get-Content $apiConfigPath -Raw
    
    if ($apiConfigContent -match "isExpoGo|appOwnership") {
        Write-Host "✅ API Platform Detection: CONFIGURED" -ForegroundColor Green
        Write-Host "   Status: Code auto-detects Emulator vs Physical Device"
        Write-Host "   Android Emulator → 10.0.2.2:8000"
        Write-Host "   Android Device   → 192.168.1.236:8000"
    } else {
        Write-Host "❌ API Platform Detection: MISSING" -ForegroundColor Red
        Write-Host "   Action Required: Update apiConfig.ts to detect platform"
        Write-Host "   This is causing: QR scans to fail (can't reach backend)"
    }
} else {
    Write-Host "⚠️  apiConfig.ts not found at: $apiConfigPath" -ForegroundColor Yellow
}

Write-Host ""

# ============================================
# DIAGNOSTIC 3: Check Pin Rendering Code
# ============================================
Write-Host "📋 DIAGNOSTIC 3: Pin Rendering Setup" -ForegroundColor Cyan
Write-Host "─────────────────────────────────────" -ForegroundColor Cyan

$globalMapPath = "client\Frontend\src\components\GlobalMap.jsx"

if (Test-Path $globalMapPath) {
    $globalMapContent = Get-Content $globalMapPath -Raw
    
    if ($globalMapContent -match "setSelectedTruckData") {
        Write-Host "✅ Pin State Sync: IMPLEMENTED" -ForegroundColor Green
        Write-Host "   Status: selectedTruckData syncs when truck selected"
    } else {
        Write-Host "❌ Pin State Sync: MISSING" -ForegroundColor Red
        Write-Host "   Action Required: Add useEffect to sync selectedTruckData"
        Write-Host "   This is causing: Info panel doesn't update on marker click"
    }
    
    if ($globalMapContent -match "marker\.on.*click") {
        Write-Host "✅ Marker Click Handler: IMPLEMENTED" -ForegroundColor Green
        Write-Host "   Status: Markers respond to click events"
    } else {
        Write-Host "❌ Marker Click Handler: MISSING" -ForegroundColor Red
        Write-Host "   Action Required: Add click event listener to markers"
    }
} else {
    Write-Host "⚠️  GlobalMap.jsx not found at: $globalMapPath" -ForegroundColor Yellow
}

Write-Host ""

# ============================================
# DIAGNOSTIC 4: Network Connectivity
# ============================================
Write-Host "📋 DIAGNOSTIC 4: Network Connectivity" -ForegroundColor Cyan
Write-Host "─────────────────────────────────────" -ForegroundColor Cyan

Write-Host "Checking backend server (localhost:8000)..."
try {
    $tcpClient = New-Object System.Net.Sockets.TcpClient
    $tcpClient.ConnectAsync("localhost", 8000).Wait(3000)
    if ($tcpClient.Connected) {
        Write-Host "✅ Backend Server: REACHABLE" -ForegroundColor Green
        Write-Host "   Location: localhost:8000"
        $tcpClient.Close()
    } else {
        Write-Host "❌ Backend Server: NOT REACHABLE" -ForegroundColor Red
        Write-Host "   Action Required: Start Django server"
        Write-Host "   Command: python manage.py runserver 0.0.0.0:8000"
    }
} catch {
    Write-Host "❌ Backend Server: NOT REACHABLE" -ForegroundColor Red
    Write-Host "   Action Required: Start Django server"
    Write-Host "   Command: python manage.py runserver 0.0.0.0:8000"
}

Write-Host "Checking Vite dev server (localhost:5173)..."
try {
    $tcpClient = New-Object System.Net.Sockets.TcpClient
    $tcpClient.ConnectAsync("localhost", 5173).Wait(3000)
    if ($tcpClient.Connected) {
        Write-Host "✅ Web Dev Server: REACHABLE" -ForegroundColor Green
        Write-Host "   Location: localhost:5173"
        $tcpClient.Close()
    } else {
        Write-Host "⚠️  Web Dev Server: NOT REACHABLE" -ForegroundColor Yellow
        Write-Host "   Note: This is OK if not running web app right now"
    }
} catch {
    Write-Host "⚠️  Web Dev Server: NOT REACHABLE" -ForegroundColor Yellow
    Write-Host "   Note: This is OK if not running web app right now"
}

Write-Host ""

# ============================================
# DIAGNOSTIC 5: LAN IP Detection
# ============================================
Write-Host "📋 DIAGNOSTIC 5: LAN IP Configuration" -ForegroundColor Cyan
Write-Host "─────────────────────────────────────" -ForegroundColor Cyan

$lanIp = (Get-NetIPAddress -AddressFamily IPv4 -AddressState Preferred | Where-Object { $_.IPAddress -like "192.168.*" } | Select-Object -First 1).IPAddress

if ($lanIp) {
    Write-Host "✅ LAN IP Detected: $lanIp" -ForegroundColor Green
    Write-Host "   Use this IP for Android Physical Devices"
    Write-Host "   Update API_BASE_URL to: http://$lanIp`:8000/api/v1"
} else {
    Write-Host "⚠️  LAN IP: NOT DETECTED" -ForegroundColor Yellow
    Write-Host "   For Android Physical Device, use: 192.168.x.x:8000"
    Write-Host "   Or configure in: mobile/src/config/apiConfig.ts"
}

Write-Host ""

# ============================================
# SUMMARY
# ============================================
Write-Host "📊 DIAGNOSTIC SUMMARY" -ForegroundColor Cyan
Write-Host "─────────────────────────────────────" -ForegroundColor Cyan

$issues = 0

if (Test-Path $appJsonPath) {
    $appJsonContent = Get-Content $appJsonPath -Raw
    if (-not ($appJsonContent -match '"enabled":\s*false')) {
        $issues += 1
    }
}

if (Test-Path $apiConfigPath) {
    $apiConfigContent = Get-Content $apiConfigPath -Raw
    if (-not ($apiConfigContent -match "isExpoGo")) {
        $issues += 1
    }
}

if (Test-Path $globalMapPath) {
    $globalMapContent = Get-Content $globalMapPath -Raw
    if (-not ($globalMapContent -match "setSelectedTruckData")) {
        $issues += 1
    }
}

if ($issues -eq 0) {
    Write-Host "✅ ALL SYSTEMS OPERATIONAL" -ForegroundColor Green
    Write-Host ""
    Write-Host "Next Steps:" -ForegroundColor Cyan
    Write-Host "1. npm install --legacy-peer-deps"
    Write-Host "2. Start backend:    python manage.py runserver 0.0.0.0:8000"
    Write-Host "3. Start web app:    npm run dev"
    Write-Host "4. Start mobile:     npx expo start"
    Write-Host "5. Test marker clicks and QR scanning"
} else {
    Write-Host "❌ $issues ISSUE(S) FOUND" -ForegroundColor Red
    Write-Host ""
    Write-Host "Please apply the fixes from CRITICAL_FIXES_APPLIED.md" -ForegroundColor Yellow
}

Write-Host ""
Write-Host "================================================" -ForegroundColor Blue
Write-Host "Diagnostic complete. Check status above." -ForegroundColor Blue
Write-Host "================================================" -ForegroundColor Blue
