# ------------------------------
# Test-PocketOption-API.ps1
# Run PocketOption latency test using official Python API
# ------------------------------

param(
    [string]$SessionId = "2666465456adc00252df90dd2da488d1",
    [string]$UserId = "101002476",
    [int]$TestDuration = 30,
    [switch]$IsDemo = $false
)

Write-Host "[INFO] PocketOption Official API Latency Test" -ForegroundColor Cyan
Write-Host "Session ID: $($SessionId.Substring(0, 8))..." -ForegroundColor Gray
Write-Host "User ID: $UserId" -ForegroundColor Gray
Write-Host "Demo Mode: $IsDemo" -ForegroundColor Gray
Write-Host "Test Duration: $TestDuration seconds" -ForegroundColor Gray

# Check if Python is available
if (-not (Get-Command "python" -ErrorAction SilentlyContinue)) {
    Write-Host "`n[ERROR] Python not found!" -ForegroundColor Red
    Write-Host "Please install Python from: https://python.org/" -ForegroundColor Yellow
    exit 1
}

# Check if PocketOption API is installed
Write-Host "`n[CHECK] Verifying PocketOption API installation..." -ForegroundColor Yellow
try {
    $result = python -c "import pocketoptionapi; print('PocketOption API found')" 2>&1
    if ($LASTEXITCODE -eq 0) {
        Write-Host "[SUCCESS] PocketOption API is installed" -ForegroundColor Green
    } else {
        Write-Host "[ERROR] PocketOption API not found!" -ForegroundColor Red
        Write-Host "Please run the setup first:" -ForegroundColor Yellow
        Write-Host "  cd PocketOptionAPI-v2" -ForegroundColor White
        Write-Host "  pip install -e ." -ForegroundColor White
        exit 1
    }
} catch {
    Write-Host "[ERROR] Failed to check PocketOption API: $_" -ForegroundColor Red
    exit 1
}

# Update the Python script with current parameters
Write-Host "`n[SETUP] Configuring test parameters..." -ForegroundColor Yellow

$pythonScript = Get-Content "test-pocketoption-python.py" -Raw

# Update session ID
$pythonScript = $pythonScript -replace 'session_id\\";s:32:\\"[^"]*\\"', "session_id\\`";s:32:\\`"$SessionId\\`""

# Update user ID
$pythonScript = $pythonScript -replace '"uid":\d+', "`"uid`":$UserId"

# Update demo mode
$demoValue = if ($IsDemo) { "True" } else { "False" }
$pythonScript = $pythonScript -replace 'DEMO = (True|False)', "DEMO = $demoValue"

# Update test duration
$pythonScript = $pythonScript -replace 'self\.test_duration = \d+', "self.test_duration = $TestDuration"

# Save updated script
$pythonScript | Out-File -Encoding UTF8 -FilePath "test-pocketoption-configured.py"

Write-Host "[SUCCESS] Test configured successfully" -ForegroundColor Green

# Run the Python latency test
Write-Host "`n=== STARTING POCKETOPTION API LATENCY TEST ===" -ForegroundColor Magenta
Write-Host "Using official PocketOption API v2" -ForegroundColor Cyan
Write-Host "This will test real trading API calls with proper authentication" -ForegroundColor Cyan
Write-Host "Press Ctrl+C to stop early`n" -ForegroundColor Gray

try {
    python "test-pocketoption-configured.py"
    
    if ($LASTEXITCODE -eq 0) {
        Write-Host "`n[SUCCESS] Latency test completed successfully!" -ForegroundColor Green
    } else {
        Write-Host "`n[ERROR] Test failed with exit code: $LASTEXITCODE" -ForegroundColor Red
    }
} catch {
    Write-Host "`n[ERROR] Failed to run Python test: $_" -ForegroundColor Red
} finally {
    # Cleanup
    if (Test-Path "test-pocketoption-configured.py") {
        Remove-Item "test-pocketoption-configured.py" -Force
    }
}

Write-Host "`n=== WHAT THIS TEST MEASURES ===" -ForegroundColor Magenta
Write-Host "✅ Real PocketOption API connection latency" -ForegroundColor Green
Write-Host "✅ Balance retrieval response times" -ForegroundColor Green
Write-Host "✅ Market data (candles) request latency" -ForegroundColor Green
Write-Host "✅ Payout information access speed" -ForegroundColor Green
Write-Host "✅ Trade execution latency (demo mode only)" -ForegroundColor Green
Write-Host "✅ Overall trading API performance analysis" -ForegroundColor Green

Write-Host "`n[INFO] Test complete! Check results above for latency analysis." -ForegroundColor Cyan
