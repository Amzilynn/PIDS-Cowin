@echo off
setlocal enabledelayedexpansion

echo ================================================================================
echo                    Co_Win Platform - Real-time Wav2Lip
echo                     [Modern Architecture - PowerShell]
echo ================================================================================
echo.

cd /d "%~dp0"

REM 1. Clean up stale processes
echo [INFO] Cleaning up ports 5500, 8010, 8011, 8000, 5173, 1985...
powershell -Command "Get-NetTCPConnection -LocalPort 5500, 8010, 8011, 8000, 5173, 1985 -ErrorAction SilentlyContinue | Where-Object { $_.OwningProcess -ne 0 } | Select-Object -ExpandProperty OwningProcess | Get-Unique | ForEach-Object { Stop-Process -Id $_ -Force -ErrorAction SilentlyContinue }"
timeout /t 2 /nobreak >nul

echo ================================================================================
echo Starting Servers (Direct Mode - NO DOCKER)...
echo ================================================================================

REM 2. Start Wav2Lip Engine (Direct WebRTC Mode)
echo [1/4] Starting Wav2Lip Avatar Engine...
start "WAV2LIP-ENGINE" /D "%CD%\dso_avatar" powershell -NoExit -Command "venv\Scripts\python.exe app.py --transport webrtc --model wav2lip --avatar_id sarah_static --listenport 8010 --batch_size 4 --modelres 256 -l 10 -r 3"
start "AVATAR-SERVICE" /D "%CD%\dso_avatar" powershell -NoExit -Command "venv\Scripts\python.exe avatar_service.py"

REM 2.5 Start TTS Server
echo [3/5] Starting TTS Server...
start "TTS-SERVER" /D "%CD%\dso2\frontend" powershell -NoExit -Command "python tts_server.py"

timeout /t 5 /nobreak >nul

REM 3. Start DSO2 API
echo [2/4] Starting DSO2 API...
start "DSO2-API" powershell -NoExit -Command "Set-Location dso2; if (Test-Path venv/Scripts/python.exe) { venv/Scripts/python.exe -m uvicorn src.api.main:app --host 0.0.0.0 --port 8000 } else { uvicorn src.api.main:app --host 0.0.0.0 --port 8000 }"

timeout /t 2 /nobreak >nul

REM 7. Start Frontend
echo [5/5] Starting Frontend...
start "FRONTEND-VITE" powershell -NoExit -Command "Set-Location front; npm run dev"

echo.
echo ================================================================================
echo All servers initialized!
echo ================================================================================
echo.
echo   - SRS WebRTC:   http://localhost:1985
echo   - Avatar Engine: http://localhost:8010
echo   - Frontend:     http://localhost:5173
echo.
echo Please REFRESH your browser (Ctrl+F5) to ensure the latest WebRTC fix is loaded.
echo ================================================================================
pause