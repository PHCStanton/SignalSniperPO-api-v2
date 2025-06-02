@echo off
:: SignalSniper Bot Launcher
:: Double-click this file to run the bot

echo ===============================================
echo         SignalSniper Bot Launcher
echo ===============================================
echo.

:: Check if PowerShell is available
where powershell >nul 2>nul
if %errorlevel% neq 0 (
    echo ERROR: PowerShell not found!
    echo Please install PowerShell to run this bot.
    pause
    exit /b 1
)

:: Run the PowerShell script
echo Starting bot...
echo.

:: Run without admin privileges by default
powershell.exe -NoProfile -ExecutionPolicy Bypass -File "%~dp0run_bot_powershell.ps1"

:: If you need to create a new virtual environment, uncomment the line below:
:: powershell.exe -NoProfile -ExecutionPolicy Bypass -File "%~dp0run_bot_powershell.ps1" -CreateNewVenv

:: If you want to run with debug information, uncomment the line below:
:: powershell.exe -NoProfile -ExecutionPolicy Bypass -File "%~dp0run_bot_powershell.ps1" -Debug

pause
