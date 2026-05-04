@echo off
echo ================================================================================
echo                    Stopping Co_Win Platform
echo ================================================================================
echo.

echo [INFO] Stopping SRS Docker container...
docker stop srs-platform >nul 2>&1
docker rm srs-platform >nul 2>&1

echo [INFO] Stopping processes on port 5500 (TTS)...
for /f "tokens=5" %%a in ('netstat -aon ^| findstr ":5500 "') do (
    echo     Killing PID %%a
    taskkill /f /pid %%a >nul 2>&1
)

echo [INFO] Stopping processes on port 8010 (Avatar)...
for /f "tokens=5" %%a in ('netstat -aon ^| findstr ":8010 "') do (
    echo     Killing PID %%a
    taskkill /f /pid %%a >nul 2>&1
)

echo [INFO] Stopping processes on port 8000 (DSO2 API)...
for /f "tokens=5" %%a in ('netstat -aon ^| findstr ":8000 "') do (
    echo     Killing PID %%a
    taskkill /f /pid %%a >nul 2>&1
)

echo [INFO] Stopping processes on port 5173 (Frontend)...
for /f "tokens=5" %%a in ('netstat -aon ^| findstr ":5173 "') do (
    echo     Killing PID %%a
    taskkill /f /pid %%a >nul 2>&1
)

echo.
echo ================================================================================
echo All servers stopped!
echo ================================================================================
pause
