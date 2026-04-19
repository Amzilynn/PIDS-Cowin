@echo off
setlocal
echo ==========================================
3: echo   MuseTalk - High Performance Launcher
echo ==========================================
echo.
echo Starting MuseTalk (HD Engine)...
echo.

:: Jump to the dso_avatar folder
cd /d "%~dp0\dso_avatar"

:: Activate venv and run MuseTalk
call venv\Scripts\activate.bat
python app.py --transport webrtc --model musetalk --avatar_id musetalk_avatar1 --batch_size 1

if %ERRORLEVEL% neq 0 (
    echo.
    echo [ERROR] MuseTalk failed to start.
    pause
)

endlocal
