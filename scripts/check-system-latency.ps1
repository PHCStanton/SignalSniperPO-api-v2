# ------------------------------
# Test-SystemLatency.ps1
# ------------------------------
$targets = @("8.8.8.8", "1.1.1.1", "api.pocketoption.com")
$pingCount = 4

Write-Host "[INFO] Running latency diagnostics..." -ForegroundColor Cyan

# PING TEST
Write-Host "`n[PING TEST]" -ForegroundColor Yellow
foreach ($target in $targets) {
    Write-Host "`nPinging $target..."
    ping $target -n $pingCount
}

# DNS Resolution Test
Write-Host "`n[DNS RESOLUTION TEST]" -ForegroundColor Yellow
$dnsTarget = "api.pocketoption.com"
$startTime = Get-Date
[System.Net.Dns]::GetHostAddresses($dnsTarget) | Out-Null
$endTime = Get-Date
$duration = ($endTime - $startTime).TotalMilliseconds
Write-Host "Resolved $dnsTarget in $duration ms"

# WebSocket Latency Test (Optional)
# Requires Node.js + ws module
if (Get-Command "node" -ErrorAction SilentlyContinue) {
    $wsTestScript = @"
const WebSocket = require('ws');
const start = Date.now();
const ws = new WebSocket('wss://echo.websocket.org');

ws.on('open', function open() {
  ws.send('ping');
});

ws.on('message', function message(data) {
  const latency = Date.now() - start;
  console.log('WebSocket latency: ' + latency + ' ms');
  ws.close();
});
"@
    $scriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
    $wsTestJsPath = Join-Path $scriptDir "wstest_inline.js" # Create in scripts dir
    $wsTestScript | Out-File -Encoding ASCII -FilePath $wsTestJsPath
    Write-Host "`n[WEBSOCKET TEST] WebSocket latency test (Node.js + ws)..." -ForegroundColor Yellow
    try {
        # Execute node in the context of the scripts directory
        Push-Location $scriptDir
        node $wsTestJsPath
        Pop-Location
    } catch {
        Write-Host "WebSocket test failed: $_" -ForegroundColor Red
    } finally {
        # Clean up temporary file
        if (Test-Path $wsTestJsPath) {
            Remove-Item $wsTestJsPath -Force
        }
    }
} else {
    Write-Host "`n[INFO] Node.js not detected. Skipping WebSocket test." -ForegroundColor DarkGray
}

Write-Host "`n[SUCCESS] Done. Review the ping times and DNS resolution for insights." -ForegroundColor Green
