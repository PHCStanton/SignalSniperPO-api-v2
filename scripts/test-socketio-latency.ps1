# ------------------------------
# Test-SocketIO-Latency.ps1
# PocketOption Socket.io API Latency Testing
# ------------------------------

param(
    [string]$SessionId = "",
    [string]$ServerUrl = "https://pocketoption.com",
    [int]$TestDuration = 30
)

Write-Host "[INFO] PocketOption Socket.io Latency Testing" -ForegroundColor Cyan

if ([string]::IsNullOrEmpty($SessionId)) {
    Write-Host "[WARNING] No session_id provided. You can:" -ForegroundColor Yellow
    Write-Host "1. Run: .\test-socketio-latency.ps1 -SessionId 'your_session_id_here'" -ForegroundColor White
    Write-Host "2. Get session_id from browser DevTools → Network → Socket.io connection" -ForegroundColor White
    Write-Host "3. Continue with basic Socket.io connection test (limited functionality)" -ForegroundColor White
    Write-Host ""
    
    $choice = Read-Host "Continue with basic test? (y/n)"
    if ($choice -ne 'y') {
        Write-Host "[INFO] Exiting. Please provide session_id for full testing." -ForegroundColor Gray
        exit
    }
}

# Function to test Socket.io connection with Node.js
function Test-SocketIOLatency {
    param(
        [string]$Sid,
        [string]$Server,
        [int]$Duration
    )
    
    if (Get-Command "node" -ErrorAction SilentlyContinue) {
        Write-Host "`n[SOCKETIO TEST] Testing Socket.io connection..." -ForegroundColor Yellow
        
        $socketTestScript = @"
const io = require('socket.io-client');

const serverUrl = '$Server';
const sessionId = '$Sid';
const testDuration = $Duration * 1000; // Convert to milliseconds

console.log('Connecting to PocketOption Socket.io...');
console.log('Server: ' + serverUrl);
if (sessionId) {
    console.log('Session ID: ' + sessionId.substring(0, 10) + '...');
}

// Socket.io connection options
const options = {
    transports: ['websocket', 'polling'],
    upgrade: true,
    rememberUpgrade: true,
    timeout: 5000
};

// Add session_id if provided
if (sessionId) {
    options.query = { session_id: sessionId };
}

const socket = io(serverUrl, options);

let latencyTests = [];
let messageCount = 0;
let startTime = Date.now();

socket.on('connect', () => {
    console.log('Connected to Socket.io server');
    console.log('Socket ID: ' + socket.id);
    console.log('Transport: ' + socket.io.engine.transport.name);
    
    // Start latency testing
    console.log('\\nStarting latency tests for ' + ($Duration) + ' seconds...');
    
    const pingInterval = setInterval(() => {
        const pingStart = Date.now();
        
        // Send ping and measure response time
        socket.emit('ping', { timestamp: pingStart }, (response) => {
            const latency = Date.now() - pingStart;
            latencyTests.push(latency);
            console.log('Ping #' + (latencyTests.length) + ': ' + latency + 'ms');
        });
        
        // Also test with custom events that PocketOption might use
        socket.emit('time', {}, (response) => {
            // Handle time response if available
        });
        
    }, 1000); // Test every second
    
    // Stop testing after duration
    setTimeout(() => {
        clearInterval(pingInterval);
        
        if (latencyTests.length > 0) {
            const avg = latencyTests.reduce((a, b) => a + b, 0) / latencyTests.length;
            const min = Math.min(...latencyTests);
            const max = Math.max(...latencyTests);
            
            console.log('\\n=== LATENCY RESULTS ===');
            console.log('Tests completed: ' + latencyTests.length);
            console.log('Average latency: ' + avg.toFixed(2) + 'ms');
            console.log('Minimum latency: ' + min + 'ms');
            console.log('Maximum latency: ' + max + 'ms');
            console.log('Latency variance: ' + (max - min) + 'ms');
            
            // Performance assessment
            if (avg < 50) {
                console.log('Performance: EXCELLENT for trading');
            } else if (avg < 100) {
                console.log('Performance: GOOD for trading');
            } else if (avg < 200) {
                console.log('Performance: ACCEPTABLE for trading');
            } else {
                console.log('Performance: POOR - may affect trading');
            }
        } else {
            console.log('No successful ping responses received');
        }
        
        socket.disconnect();
        process.exit(0);
    }, testDuration);
});

// Listen for common PocketOption events
socket.on('quotes', (data) => {
    messageCount++;
    console.log('Received quotes update #' + messageCount);
});

socket.on('assets', (data) => {
    console.log('Received assets data');
});

socket.on('balance', (data) => {
    console.log('Received balance update');
});

socket.on('pong', (data) => {
    console.log('Received pong response');
});

socket.on('disconnect', (reason) => {
    console.log('Disconnected: ' + reason);
});

socket.on('connect_error', (error) => {
    console.log('Connection error: ' + error.message);
    process.exit(1);
});

// Handle process termination
process.on('SIGINT', () => {
    console.log('\\nTest interrupted by user');
    socket.disconnect();
    process.exit(0);
});
"@
        
        $tempPath = "$env:TEMP\socketio_test.js"
        $socketTestScript | Out-File -Encoding UTF8 -FilePath $tempPath
        
        Write-Host "Installing socket.io-client if needed..." -ForegroundColor Gray
        
        # Check if socket.io-client is installed
        $packageCheck = @"
try {
    require('socket.io-client');
    console.log('socket.io-client is available');
    process.exit(0);
} catch (e) {
    console.log('socket.io-client not found, please install it');
    console.log('Run: npm install socket.io-client');
    process.exit(1);
}
"@
        
        $checkPath = "$env:TEMP\check_socketio.js"
        $packageCheck | Out-File -Encoding UTF8 -FilePath $checkPath
        
        try {
            $checkResult = node $checkPath 2>&1
            if ($LASTEXITCODE -ne 0) {
                Write-Host "[ERROR] socket.io-client not installed" -ForegroundColor Red
                Write-Host "Please run: npm install socket.io-client" -ForegroundColor Yellow
                return
            }
            
            Write-Host "Running Socket.io latency test..." -ForegroundColor Green
            node $tempPath
            
        } catch {
            Write-Host "Socket.io test failed: $_" -ForegroundColor Red
        } finally {
            # Cleanup
            if (Test-Path $tempPath) { Remove-Item $tempPath -Force }
            if (Test-Path $checkPath) { Remove-Item $checkPath -Force }
        }
    } else {
        Write-Host "`n[ERROR] Node.js not available for Socket.io testing" -ForegroundColor Red
        Write-Host "Please install Node.js to test Socket.io latency" -ForegroundColor Yellow
    }
}

# Function to test HTTP endpoints that might be used alongside Socket.io
function Test-PocketOptionHTTP {
    Write-Host "`n[HTTP TEST] Testing PocketOption HTTP endpoints..." -ForegroundColor Yellow
    
    $endpoints = @(
        "https://pocketoption.com/api/cabinet/demo-quick-high-low/",
        "https://pocketoption.com/api/v1/time",
        "https://pocketoption.com/en/"
    )
    
    foreach ($endpoint in $endpoints) {
        try {
            $startTime = Get-Date
            $response = Invoke-WebRequest -Uri $endpoint -TimeoutSec 5 -UseBasicParsing -ErrorAction Stop
            $endTime = Get-Date
            $latency = ($endTime - $startTime).TotalMilliseconds
            
            Write-Host "  $endpoint`: $([math]::Round($latency, 2))ms - Status: $($response.StatusCode)" -ForegroundColor Green
        } catch {
            Write-Host "  $endpoint`: FAILED - $($_.Exception.Message)" -ForegroundColor Red
        }
    }
}

# Main execution
Write-Host "`n=== POCKETOPTION SOCKET.IO LATENCY TEST ===" -ForegroundColor Magenta

if ($SessionId) {
    Write-Host "Using Session ID: $($SessionId.Substring(0, [Math]::Min(10, $SessionId.Length)))..." -ForegroundColor Cyan
}

Test-SocketIOLatency -Sid $SessionId -Server $ServerUrl -Duration $TestDuration
Test-PocketOptionHTTP

Write-Host "`n=== INSTRUCTIONS FOR GETTING SESSION_ID ===" -ForegroundColor Magenta
Write-Host "1. Open PocketOption in your browser" -ForegroundColor White
Write-Host "2. Press F12 to open Developer Tools" -ForegroundColor White
Write-Host "3. Go to Network tab" -ForegroundColor White
Write-Host "4. Look for Socket.io connections (usually contains 'socket.io')" -ForegroundColor White
Write-Host "5. Check the request URL or headers for session_id parameter" -ForegroundColor White
Write-Host "6. Copy the session_id value" -ForegroundColor White
Write-Host "7. Run: .\test-socketio-latency.ps1 -SessionId 'your_session_id_here'" -ForegroundColor Yellow

Write-Host "`n[SUCCESS] Socket.io latency testing complete!" -ForegroundColor Green
