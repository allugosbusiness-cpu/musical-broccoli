@echo off
REM EXPO REMOTE UPDATE ERROR - COMPLETE RESET

echo ===============================================
echo STEP 1: Killing all processes
echo ===============================================

taskkill /F /IM node.exe >nul 2>&1
taskkill /F /IM npm.cmd >nul 2>&1
taskkill /F /IM metro.exe >nul 2>&1

echo Done.
echo.

echo ===============================================
echo STEP 2: Clearing caches
echo ===============================================

REM Expo cache
rmdir /S /Q "%USERPROFILE%\.expo" >nul 2>&1
rmdir /S /Q "mobile\.expo" >nul 2>&1

REM npm cache
call npm cache clean --force

echo Done.
echo.

echo ===============================================
echo STEP 3: Clearing node_modules
echo ===============================================

cd mobile
rmdir /S /Q node_modules >nul 2>&1
del package-lock.json >nul 2>&1

echo Done.
echo.

echo ===============================================
echo STEP 4: Fresh install
echo ===============================================

call npm install --legacy-peer-deps --prefer-offline --no-audit --ignore-scripts

echo.
echo Done.
echo.

echo ===============================================
echo READY TO START EXPO
echo ===============================================
echo.
echo Run this command:
echo   npx expo start --clear --localhost
echo.
echo Then in Expo Go on your phone/emulator, scan the QR code.
echo.
pause
