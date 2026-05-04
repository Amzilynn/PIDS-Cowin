@echo off
setlocal
echo ==========================================
echo   Wav2Lip - Fast Platform Launcher
echo ==========================================
echo.
echo Starting Wav2Lip (Speed Optimized)...
echo.

:: Jump to the dso_avatar folder
cd /d "%~dp0\dso_avatar"

:: Activate venv and run Wav2Lip
call venv\Scripts\activate.bat
python app.py --transport webrtc --model wav2lip --avatar_id wav2lip_eya_vertical --batch_size 1

if %ERRORLEVEL% neq 0 (
    echo.
    echo [ERROR] Wav2Lip failed to start.
    pause
)

endlocal
