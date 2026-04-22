@echo off
cd /d "%~dp0"
call venv\Scripts\activate.bat
python app.py --transport webrtc --model wav2lip --avatar_id sarah_static --batch_size 4 --listenport 8010
pause
