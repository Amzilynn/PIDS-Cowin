@echo off
TITLE VITAL AI SYSTEM - FULL MULTI-SERVER ORCHESTRATOR
COLOR 0A

echo ======================================================
echo   VITAL AI - MULTI-SERVER LAUNCHER (DSO 1, 2, 3, 4)
echo ======================================================
echo.

:: 0. Clean up existing processes
echo [0/6] Cleaning up existing processes...
taskkill /F /IM python.exe /T 2>nul
taskkill /F /IM node.exe /T 2>nul
timeout /t 2 /nobreak >nul

:: 1. Start Faster Live Avatar Engine (Port 8027)
echo [1/6] Starting Avatar Engine (8027)...
start "AVATAR ENGINE" cmd /k "cd faster_live_avatar && ..\dso_avatar\venv\Scripts\python.exe run.py"
timeout /t 3

:: 2. Start DSO1 Training (Port 8001)
echo [2/6] Starting DSO1 Training (8001)...
start "DSO1 TRAINING" cmd /k "cd dso1 && ..\dso_avatar\venv\Scripts\python.exe -m uvicorn src.api.main:app --host 0.0.0.0 --port 8001"
timeout /t 3

:: 3. Start DSO2 Sales Chat (Port 8000)
echo [3/6] Starting DSO2 Sales Chat (8000)...
start "DSO2 CHAT" cmd /k "cd dso2 && ..\dso_avatar\venv\Scripts\python.exe -m uvicorn src.api.main:app --host 0.0.0.0 --port 8000"
timeout /t 3

:: 4. Start DSO3 Expertise/Auth (Port 8003)
echo [4/6] Starting DSO3 Expertise (8003)...
start "DSO3 EXPERTISE" cmd /k "dso_avatar\venv\Scripts\python.exe dso3_server.py"
timeout /t 3

:: 5. Start DSO4 Visit Strategy (Port 8004)
echo [5/6] Starting DSO4 Visit Strategy (8004)...
start "DSO4 VISITS" cmd /k "dso_avatar\venv\Scripts\python.exe dso4_server.py"
timeout /t 3

:: 6. Start Frontend Dashboard (Port 5173)
echo [6/6] Starting Frontend Dashboard (5173)...
start "FRONTEND" cmd /k "cd front && npm run dev"

echo.
echo ======================================================
echo   ALL SERVERS STARTING IN SEPARATE WINDOWS
echo.
echo   - PORT 8027: Avatar Renderer
echo   - PORT 8001: DSO1 (Training)
echo   - PORT 8000: DSO2 (Chat)
echo   - PORT 8003: DSO3 (Auth/Products)
echo   - PORT 8004: DSO4 (Visit Strategy)
echo   - PORT 5173: Frontend UI
echo ======================================================
echo.
pause
