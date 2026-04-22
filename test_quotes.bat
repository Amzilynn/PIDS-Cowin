@echo off
set "TEST_PATH=%CD%\test dir"
echo Testing with double double quotes:
echo cd /d ""%TEST_PATH%""
echo Testing with single quotes:
echo cd /d "%TEST_PATH%"
pause
