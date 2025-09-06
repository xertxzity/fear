@echo off
echo Fortnite Season 7 Emulator - Running as Administrator
echo ====================================================
echo.

REM Check if already running as admin
net session >nul 2>&1
if %errorLevel% == 0 (
    echo Running with administrator privileges
    echo.
    python main.py
) else (
    echo Requesting administrator privileges...
    powershell -Command "Start-Process '%~f0' -Verb RunAs"
    exit /b
)

echo.
echo Press any key to exit...
pause >nul
