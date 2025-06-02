# ------------------------------
# Test-API-Latency.ps1
# PocketOption API Latency Testing
# ------------------------------

Write-Host "[INFO] Testing PocketOption API latency..." -ForegroundColor Cyan

# API endpoints to test
$apiEndpoints = @(
    "https://api.pocketoption.com/api/v1/time",
    "https://api.pocketoption.com/api/v1/assets",
    "https://api.pocketoption.com/api/v1/quotes",
    "https://pocketoption.com/api/cabinet/demo-quick-high-low/"
)

# Function to test HTTP latency
function Test-HttpLatency {
    param(
        [string]$Url,
        [int]$Iterations = 5
    )
    
    Write-Host "`n[TESTING] $Url" -ForegroundColor Yellow
    $latencies = @()
    
    for ($i = 1; $i -le $Iterations; $i++) {
        try {
            $startTime = Get-Date
            
            # Make HTTP request with timeout
            $response = Invoke-WebRequest -Uri $Url -TimeoutSec 10 -UseBasicParsing -ErrorAction Stop
            
            $endTime = Get-Date
            $latency = ($endTime - $startTime).TotalMilliseconds
            $latencies += $latency
            
            Write-Host "  Attempt $i`: $([math]::Round($latency, 2))ms - Status: $($response.StatusCode)" -ForegroundColor Green
            
            # Small delay between requests
            Start-Sleep -Milliseconds 100
            
        } catch {
            Write-Host "  Attempt $i`: FAILED - $($_.Exception.Message)" -ForegroundColor Red
        }
    }
    
    if ($latencies.Count -gt 0) {
        $avgLatency = ($latencies | Measure-Object -Average).Average
        $minLatency = ($latencies | Measure-Object -Minimum).Minimum
        $maxLatency = ($latencies | Measure-Object -Maximum).Maximum
        
        Write-Host "  Summary: Avg=$([math]::Round($avgLatency, 2))ms, Min=$([math]::Round($minLatency, 2))ms, Max=$([math]::Round($maxLatency, 2))ms" -ForegroundColor Cyan
        
        return @{
            Url = $Url
            Average = $avgLatency
            Minimum = $minLatency
            Maximum = $maxLatency
            SuccessCount = $latencies.Count
            TotalAttempts = $Iterations
        }
    } else {
        Write-Host "  Summary: All requests failed" -ForegroundColor Red
        return $null
    }
}

# Function to test WebSocket latency (if available)
function Test-WebSocketLatency {
    if (Get-Command "node" -ErrorAction SilentlyContinue) {
        Write-Host "`n[WEBSOCKET TEST] Testing WebSocket connection..." -ForegroundColor Yellow
        
        $wsTestScript = @"
const WebSocket = require('ws');

// Test multiple WebSocket endpoints
const endpoints = [
    'wss://api.pocketoption.com/ws',
    'wss://pocketoption.com/ws',
    'wss://echo.websocket.org'  // Fallback test
];

async function testWebSocket(url) {
    return new Promise((resolve, reject) => {
        const start = Date.now();
        const ws = new WebSocket(url);
        
        const timeout = setTimeout(() => {
            ws.close();
            reject(new Error('Connection timeout'));
        }, 5000);
        
        ws.on('open', function open() {
            const connectLatency = Date.now() - start;
            console.log('Connected to ' + url + ' in ' + connectLatency + 'ms');
            
            // Test ping-pong latency
            const pingStart = Date.now();
            ws.send('ping');
            
            ws.on('message', function message(data) {
                const pongLatency = Date.now() - pingStart;
                console.log('Ping-pong latency: ' + pongLatency + 'ms');
                clearTimeout(timeout);
                ws.close();
                resolve({ connectLatency, pongLatency });
            });
        });
        
        ws.on('error', function error(err) {
            clearTimeout(timeout);
            reject(err);
        });
    });
}

// Test each endpoint
(async () => {
  for (const endpoint of endpoints) {
      try {
          await testWebSocket(endpoint);
          break; // If successful, stop testing
      } catch (error) {
          console.log('Failed to connect to ' + endpoint + ': ' + error.message);
      }
  }
})();
"@
        
        $scriptDir = Split-Path -Parent $PSCommandPath # Corrected way to get script path
        $wsTestJsPath = Join-Path $scriptDir "api_ws_test_inline.js" # Create in scripts dir
        $wsTestScript | Out-File -Encoding UTF8 -FilePath $wsTestJsPath
        
        try {
            Push-Location $scriptDir
            node $wsTestJsPath
            Pop-Location
        } catch {
            Write-Host "WebSocket test failed: $_" -ForegroundColor Red
        } finally {
            if (Test-Path $wsTestJsPath) {
                Remove-Item $wsTestJsPath -Force
            }
        }
    } else {
        Write-Host "`n[INFO] Node.js not available for WebSocket testing" -ForegroundColor DarkGray
    }
}

# Test TCP connection latency
function Test-TcpLatency {
    param(
        [string]$Hostname,
        [int]$Port = 443
    )
    
    Write-Host "`n[TCP TEST] Testing TCP connection to $Hostname`:$Port" -ForegroundColor Yellow
    
    try {
        $startTime = Get-Date
        $tcpClient = New-Object System.Net.Sockets.TcpClient
        $tcpClient.Connect($Hostname, $Port)
        $endTime = Get-Date
        $latency = ($endTime - $startTime).TotalMilliseconds
        
        Write-Host "  TCP connection established in $([math]::Round($latency, 2))ms" -ForegroundColor Green
        $tcpClient.Close()
        
        return $latency
    } catch {
        Write-Host "  TCP connection failed: $($_.Exception.Message)" -ForegroundColor Red
        return $null
    }
}

# Main testing sequence
Write-Host "`n=== HTTP API LATENCY TESTS ===" -ForegroundColor Magenta

$results = @()
foreach ($endpoint in $apiEndpoints) {
    $result = Test-HttpLatency -Url $endpoint -Iterations 3
    if ($result) {
        $results += $result
    }
}

# TCP connection test
Write-Host "`n=== TCP CONNECTION TESTS ===" -ForegroundColor Magenta
$tcpLatency = Test-TcpLatency -Hostname "api.pocketoption.com" -Port 443

# WebSocket test
Write-Host "`n=== WEBSOCKET TESTS ===" -ForegroundColor Magenta
Test-WebSocketLatency

# Summary
Write-Host "`n=== SUMMARY ===" -ForegroundColor Magenta
if ($results.Count -gt 0) {
    Write-Host "Successful API endpoints:" -ForegroundColor Green
    foreach ($result in $results) {
        Write-Host "  $($result.Url): Avg $([math]::Round($result.Average, 2))ms" -ForegroundColor White
    }
    
    $overallAvg = ($results | ForEach-Object { $_.Average } | Measure-Object -Average).Average
    Write-Host "`nOverall average API latency: $([math]::Round($overallAvg, 2))ms" -ForegroundColor Cyan
} else {
    Write-Host "No successful API connections" -ForegroundColor Red
}

if ($tcpLatency) {
    Write-Host "TCP connection latency: $([math]::Round($tcpLatency, 2))ms" -ForegroundColor Cyan
}

Write-Host "`n[SUCCESS] API latency testing complete!" -ForegroundColor Green
