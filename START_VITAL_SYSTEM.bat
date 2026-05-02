@echo off
TITLE VITAL AI SYSTEM - ALL SERVERS
COLOR 0A

echo ======================================================
echo   VITAL AI - FULL SYSTEM LAUNCHER (DSO2 + AVATAR)
echo ======================================================
echo.

:: 1. Start Faster Live Avatar Engine (Port 8027)
echo [1/3] Starting Faster Live Avatar Engine...
start "AVATAR ENGINE" cmd /k "cd faster_live_avatar && ..\dso_avatar\venv\Scripts\python.exe main.py"
timeout /t 5

:: 2. Start DSO2 Backend (Port 8000)
echo [2/3] Starting DSO2 Backend...
start "DSO2 BACKEND" cmd /k "cd dso2 && venv\Scripts\python.exe -m uvicorn src.api.main:app --host 0.0.0.0 --port 8000 --reload"
timeout /t 3

:: 3. Start Frontend Dashboard (Port 5173)
echo [3/3] Starting Frontend Dashboard...
start "FRONTEND" cmd /k "cd front && npm run dev"

echo.
echo ======================================================
echo   SYSTEM READY! 
echo   - Backend: http://localhost:8000
echo   - Frontend: http://localhost:5173
echo   - Avatar: http://localhost:8027 (Socket.io)
echo ======================================================
pause
