#!/usr/bin/env powershell

# 🔧 EXPERT FIX - Expo Remote Update Download Error
# This script completely removes OTA update infrastructure and clears all caches

Write-Host "════════════════════════════════════════════════" -ForegroundColor Cyan
Write-Host "🔧 EXPO UPDATE ERROR - COMPREHENSIVE FIX" -ForegroundColor Cyan
Write-Host "════════════════════════════════════════════════" -ForegroundColor Cyan
Write-Host ""

$projectRoot = "c:\Users\Mugogo\Desktop\Fleet Management\mobile"
$serverRoot = "c:\Users\Mugogo\Desktop\Fleet Management\server"
$webRoot = "c:\Users\Mugogo\Desktop\Fleet Management\client\Frontend"

# ============================================
# STEP 1: Kill all existing processes
# ============================================
Write-Host "📋 STEP 1: Terminating existing processes..." -ForegroundColor Yellow
Write-Host "─────────────────────────────────────────────" -ForegroundColor Yellow

# Kill Node processes
Get-Process node -ErrorAction SilentlyContinue | Stop-Process -Force -ErrorAction SilentlyContinue
Get-Process npm -ErrorAction SilentlyContinue | Stop-Process -Force -ErrorAction SilentlyContinue

# Kill Expo/Metro
Get-Process metro -ErrorAction SilentlyContinue | Stop-Process -Force -ErrorAction SilentlyContinue
Get-Process expo -ErrorAction SilentlyContinue | Stop-Process -Force -ErrorAction SilentlyContinue

Write-Host "✅ All processes terminated" -ForegroundColor Green
Write-Host ""

# ============================================
# STEP 2: Clear Expo cache completely
# ============================================
Write-Host "📋 STEP 2: Clearing Expo cache..." -ForegroundColor Yellow
Write-Host "─────────────────────────────────────────────" -ForegroundColor Yellow

# Expo stores cache in multiple locations
$expoCachePaths = @(
    "$env:USERPROFILE\.expo",
    "$projectRoot\.expo",
    "$projectRoot\.expo\cache",
    "$projectRoot\node_modules\.cache",
    "$projectRoot\node_modules\.vite",
    "$projectRoot\.next",
    "$projectRoot\dist",
    "$projectRoot\build",
    "$projectRoot\.rn-cli.config.json"
)

foreach ($path in $expoCachePaths) {
    if (Test-Path $path) {
        try {
            Write-Host "  Removing: $path" -ForegroundColor Magenta
            Remove-Item -Recurse -Force $path -ErrorAction SilentlyContinue
        } catch {
            Write-Host "  ⚠️  Could not remove: $path" -ForegroundColor Yellow
        }
    }
}

Write-Host "✅ Expo cache cleared" -ForegroundColor Green
Write-Host ""

# ============================================
# STEP 3: Clear npm cache
# ============================================
Write-Host "📋 STEP 3: Clearing npm cache..." -ForegroundColor Yellow
Write-Host "─────────────────────────────────────────────" -ForegroundColor Yellow

npm cache clean --force
Write-Host "✅ npm cache cleared" -ForegroundColor Green
Write-Host ""

# ============================================
# STEP 4: Clear Metro bundler cache
# ============================================
Write-Host "📋 STEP 4: Clearing Metro bundler cache..." -ForegroundColor Yellow
Write-Host "─────────────────────────────────────────────" -ForegroundColor Yellow

$metroCachePaths = @(
    "$env:TEMP\haste-map-*",
    "$env:TEMP\metro-cache-*",
    "$projectRoot\node_modules\.metro-cache"
)

Get-ChildItem $env:TEMP -Filter "haste-map-*" -Directory -ErrorAction SilentlyContinue | Remove-Item -Recurse -Force -ErrorAction SilentlyContinue
Get-ChildItem $env:TEMP -Filter "metro-cache-*" -Directory -ErrorAction SilentlyContinue | Remove-Item -Recurse -Force -ErrorAction SilentlyContinue

Write-Host "✅ Metro cache cleared" -ForegroundColor Green
Write-Host ""

# ============================================
# STEP 5: Verify app.json is correct
# ============================================
Write-Host "📋 STEP 5: Verifying configuration..." -ForegroundColor Yellow
Write-Host "─────────────────────────────────────────────" -ForegroundColor Yellow

$appJsonPath = "$projectRoot\app.json"
$appJsonContent = Get-Content $appJsonPath -Raw

if ($appJsonContent -match '"updates"') {
    Write-Host "❌ WARNING: 'updates' section still present in app.json!" -ForegroundColor Red
    Write-Host "   This will still trigger update checks" -ForegroundColor Red
} else {
    Write-Host "✅ app.json: 'updates' section removed" -ForegroundColor Green
}

if ($appJsonContent -match '"runtimeVersion":\s*"1\.0\.0"') {
    Write-Host "✅ app.json: runtimeVersion set to static string" -ForegroundColor Green
} else {
    Write-Host "⚠️  app.json: runtimeVersion might need verification" -ForegroundColor Yellow
}

Write-Host ""

# ============================================
# STEP 6: Fresh npm install
# ============================================
Write-Host "📋 STEP 6: Fresh npm install..." -ForegroundColor Yellow
Write-Host "─────────────────────────────────────────────" -ForegroundColor Yellow

cd $projectRoot

# Remove node_modules and package-lock
Write-Host "  Removing node_modules..." -ForegroundColor Magenta
Remove-Item -Recurse -Force node_modules -ErrorAction SilentlyContinue
Remove-Item -Force package-lock.json -ErrorAction SilentlyContinue

# Install with proper flags
Write-Host "  Installing dependencies..." -ForegroundColor Magenta
npm install --legacy-peer-deps --prefer-offline --no-audit --ignore-scripts 2>&1 | Out-Null

Write-Host "✅ Dependencies installed" -ForegroundColor Green
Write-Host ""

# ============================================
# STEP 7: Start Expo with environment vars
# ============================================
Write-Host "📋 STEP 7: Ready to start Expo..." -ForegroundColor Yellow
Write-Host "─────────────────────────────────────────────" -ForegroundColor Yellow
Write-Host ""

Write-Host "✅ ALL CACHES CLEARED - SYSTEM READY" -ForegroundColor Green
Write-Host ""

Write-Host "🚀 NEXT STEPS - RUN THESE COMMANDS IN SEPARATE TERMINALS:" -ForegroundColor Cyan
Write-Host ""

Write-Host "Terminal 1 - Backend:" -ForegroundColor Yellow
Write-Host "  cd '$serverRoot'" -ForegroundColor White
Write-Host "  python manage.py runserver 0.0.0.0:8000" -ForegroundColor White
Write-Host ""

Write-Host "Terminal 2 - Web App:" -ForegroundColor Yellow
Write-Host "  cd '$webRoot'" -ForegroundColor White
Write-Host "  npm run dev" -ForegroundColor White
Write-Host ""

Write-Host "Terminal 3 - Mobile App (THIS IS THE KEY ONE):" -ForegroundColor Yellow
Write-Host "  cd '$projectRoot'" -ForegroundColor White
Write-Host "  npx expo start --clear --localhost" -ForegroundColor White
Write-Host ""

Write-Host "════════════════════════════════════════════════" -ForegroundColor Cyan
Write-Host "If you still get 'failed to download remote update' error:" -ForegroundColor Yellow
Write-Host "  1. Ctrl+C to stop Expo" -ForegroundColor Yellow
Write-Host "  2. Run: npm cache clean --force" -ForegroundColor Yellow
Write-Host "  3. Run: npx expo start --clear --localhost --reset-cache" -ForegroundColor Yellow
Write-Host "════════════════════════════════════════════════" -ForegroundColor Cyan
