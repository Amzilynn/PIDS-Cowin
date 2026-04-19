@echo off
cd /d "%~dp0"
call venv\Scripts\activate.bat
python app.py --transport webrtc --model wav2lip --avatar_id wav2lip_eya_vertical --batch_size 1
pause
