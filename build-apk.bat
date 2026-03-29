@echo off
echo ========================================
echo    Admin Panel - APK Build Script
echo ========================================
echo.

REM Check if Node.js is installed
where node >nul 2>nul
if %ERRORLEVEL% NEQ 0 (
    echo ERROR: Node.js not found!
    echo Please install Node.js from: https://nodejs.org/
    pause
    exit /b 1
)

echo [1/4] Installing EAS CLI...
call npm install -g eas-cli

echo.
echo [2/4] Please login to Expo:
echo Username: IT_Infotec
echo Password: HPVerma@1999
echo.
call eas login

echo.
echo [3/4] Navigating to project directory...
cd /d "%~dp0"

echo.
echo [4/4] Starting APK build...
echo This will take 15-20 minutes...
echo.
call eas build --platform android --profile preview

echo.
echo ========================================
echo    Build Complete!
echo ========================================
echo.
echo Download your APK from the link shown above!
echo.
pause
