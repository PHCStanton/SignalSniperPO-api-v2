# Run-TelegramMonitor.ps1 - Script to run the Telegram signal monitoring test suite
#
# This script runs the check_telegram_session.py script to verify that we have a valid
# Telegram session and can access the BINARY TRADING CLUB channel, and then runs the
# monitor_signals.py script to monitor for signals.
#
# Usage:
#   .\Run-TelegramMonitor.ps1 [-Duration <seconds>] [-Verbose]

param (
    [int]$Duration,
    [switch]$Verbose
)

Write-Host "Telegram Signal Monitoring Test Suite" -ForegroundColor Cyan
Write-Host "------------------------------------" -ForegroundColor Cyan
Write-Host ""

# Check if Python is installed
try {
    $pythonVersion = python --version
    Write-Host "Using $pythonVersion"
} catch {
    Write-Host "Error: Python is not installed or not in PATH" -ForegroundColor Red
    exit 1
}

# Check if required scripts exist
if (-not (Test-Path "check_telegram_session.py")) {
    Write-Host "Error: check_telegram_session.py not found" -ForegroundColor Red
    exit 1
}

if (-not (Test-Path "monitor_signals.py")) {
    Write-Host "Error: monitor_signals.py not found" -ForegroundColor Red
    exit 1
}

# Create data directory if it doesn't exist
if (-not (Test-Path "data")) {
    New-Item -ItemType Directory -Path "data" | Out-Null
    Write-Host "Created data directory"
}

# Build command arguments
$verboseArg = if ($Verbose) { "--verbose" } else { "" }
$durationArg = if ($Duration) { "--duration $Duration" } else { "" }

# Step 1: Check Telegram session
Write-Host "Step 1: Checking Telegram session..." -ForegroundColor Green
$checkCommand = "python check_telegram_session.py $verboseArg"
Write-Host "Running: $checkCommand" -ForegroundColor Gray
try {
    Invoke-Expression $checkCommand
    if ($LASTEXITCODE -ne 0) {
        Write-Host "Error: Telegram session check failed" -ForegroundColor Red
        Write-Host "Please fix the session issues before continuing" -ForegroundColor Yellow
        exit 1
    }
} catch {
    Write-Host "Error executing check_telegram_session.py: $_" -ForegroundColor Red
    exit 1
}

Write-Host ""
Write-Host "Step 2: Starting signal monitor..." -ForegroundColor Green
Write-Host "Press Ctrl+C to stop monitoring" -ForegroundColor Yellow
Write-Host ""

# Step 2: Run signal monitor
$monitorCommand = "python monitor_signals.py $durationArg $verboseArg"
Write-Host "Running: $monitorCommand" -ForegroundColor Gray
try {
    Invoke-Expression $monitorCommand
    if ($LASTEXITCODE -ne 0) {
        Write-Host ""
        Write-Host "Error: Signal monitor exited with an error" -ForegroundColor Red
        exit 1
    }
} catch {
    Write-Host ""
    Write-Host "Signal monitor stopped: $_" -ForegroundColor Yellow
    exit 0
}

Write-Host ""
Write-Host "Signal monitoring completed successfully" -ForegroundColor Green
