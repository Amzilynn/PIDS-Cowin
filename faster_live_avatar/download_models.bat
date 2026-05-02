@echo off
echo ================================================================================
echo Downloading LivePortrait and Audio2Exp Weights via HuggingFace CLI
echo ================================================================================

REM Ensure huggingface_hub is installed
call venv\Scripts\python.exe -m pip install huggingface_hub

echo [1/2] Downloading Official LivePortrait Base Models...
call venv\Scripts\huggingface-cli download KwaiVGI/LivePortrait --local-dir weights --include "base_models/*"

echo [2/2] Downloading Audio-to-Expression Bridge Model...
call venv\Scripts\huggingface-cli download warmshao/FasterLivePortrait --local-dir weights --include "audio2exp.pth"

echo ================================================================================
echo Download Complete!
echo ================================================================================
