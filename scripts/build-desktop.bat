@echo off
echo ============================================
echo  Premier Cost Engine - Desktop Build
echo ============================================
echo.

cd /d "%~dp0\.."

echo [1/4] Building frontend static export...
cd frontend
call npx next build
if errorlevel 1 (
    echo ERROR: Frontend build failed!
    pause
    exit /b 1
)
cd ..
echo       Frontend built to frontend/out/
echo.

echo [2/4] Bundling Python backend with PyInstaller...
cd backend
pip install pyinstaller >nul 2>&1
python -m PyInstaller run_server.spec --noconfirm
if errorlevel 1 (
    echo ERROR: PyInstaller build failed!
    pause
    exit /b 1
)
cd ..
echo       Backend built to backend/dist/run_server/
echo.

echo [3/4] Installing Electron dependencies...
cd electron
call npm install
if errorlevel 1 (
    echo ERROR: npm install failed!
    pause
    exit /b 1
)
echo.

echo [4/4] Building Electron installer...
call npm run build
if errorlevel 1 (
    echo ERROR: Electron build failed!
    pause
    exit /b 1
)
cd ..
echo.

echo ============================================
echo  BUILD COMPLETE!
echo  Installer: dist-electron/
echo ============================================
pause
