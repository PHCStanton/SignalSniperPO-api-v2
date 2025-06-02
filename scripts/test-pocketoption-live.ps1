# ------------------------------
# Test-PocketOption-Live.ps1
# Real PocketOption Socket.io Trading Latency Test
# ------------------------------

param(
    [string]$SessionId = "2666465456adc00252df90dd2da488d1",
    [string]$UserId = "101002476",
    [int]$TestDuration = 30,
    [switch]$IsDemo = $false
)

Write-Host "[INFO] PocketOption Live Trading API Latency Test" -ForegroundColor Cyan
Write-Host "Session ID: $($SessionId.Substring(0, 8))..." -ForegroundColor Gray
Write-Host "User ID: $UserId" -ForegroundColor Gray
Write-Host "Demo Mode: $IsDemo" -ForegroundColor Gray

# Function to test PocketOption Socket.io with real authentication
function Test-PocketOptionLive {
    param(
        [string]$Sid,
        [string]$Uid,
        [int]$Duration,
        [string]$Demo
    )
    
    if (Get-Command "node" -ErrorAction SilentlyContinue) {
        Write-Host "`n[LIVE TEST] Testing PocketOption Socket.io with authentication..." -ForegroundColor Yellow
        
        $liveTestScript = @"
const io = require('socket.io-client');

const sessionId = '$Sid';
const userId = '$Uid';
const isDemo = $Demo;
const testDuration = $Duration * 1000;

console.log('Connecting to PocketOption with real session...');
console.log('Session ID: ' + sessionId.substring(0, 8) + '...');
console.log('User ID: ' + userId);
console.log('Demo Mode: ' + isDemo);

// PocketOption Socket.io connection
const socket = io('https://pocketoption.com', {
    transports: ['websocket', 'polling'],
    upgrade: true,
    timeout: 10000,
    forceNew: true
});

let latencyTests = [];
let messageCount = 0;
let quotesReceived = 0;
let balanceUpdates = 0;
let connectionTime = 0;

const startTime = Date.now();

socket.on('connect', () => {
    connectionTime = Date.now() - startTime;
    console.log('Connected in ' + connectionTime + 'ms');
    console.log('Socket ID: ' + socket.id);
    console.log('Transport: ' + socket.io.engine.transport.name);
    
    // Authenticate with PocketOption
    console.log('\\nAuthenticating...');
    const authData = {
        session: 'a:4:{s:10:"session_id";s:32:"' + sessionId + '";s:10:"ip_address";s:14:"63.178.193.220";s:10:"user_agent";s:111:"Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/137.0.0.0 Safari/537.36";s:13:"last_activity";i:' + Math.floor(Date.now() / 1000) + ';}49178e83020b72682666eadb310670ec',
        isDemo: isDemo ? 1 : 0,
        uid: parseInt(userId),
        platform: 2,
        isFastHistory: true
    };
    
    socket.emit('auth', authData);
    
    // Start latency testing after authentication
    setTimeout(() => {
        console.log('\\nStarting trading latency tests...');
        
        const testInterval = setInterval(() => {
            const pingStart = Date.now();
            
            // Test 1: Time synchronization (critical for trading)
            socket.emit('time', {}, (response) => {
                const latency = Date.now() - pingStart;
                latencyTests.push({ type: 'time', latency: latency });
                console.log('Time sync: ' + latency + 'ms');
            });
            
            // Test 2: Asset quotes request
            socket.emit('quotes', { assets: [1, 2, 3] }, (response) => {
                const latency = Date.now() - pingStart;
                latencyTests.push({ type: 'quotes', latency: latency });
                console.log('Quotes request: ' + latency + 'ms');
            });
            
            // Test 3: Balance check
            socket.emit('balance', {}, (response) => {
                const latency = Date.now() - pingStart;
                latencyTests.push({ type: 'balance', latency: latency });
                console.log('Balance check: ' + latency + 'ms');
            });
            
        }, 2000); // Test every 2 seconds
        
        // Stop testing after duration
        setTimeout(() => {
            clearInterval(testInterval);
            
            console.log('\\n=== TRADING LATENCY RESULTS ===');
            console.log('Connection time: ' + connectionTime + 'ms');
            console.log('Total tests: ' + latencyTests.length);
            console.log('Quotes received: ' + quotesReceived);
            console.log('Balance updates: ' + balanceUpdates);
            
            if (latencyTests.length > 0) {
                // Calculate averages by type
                const timeTests = latencyTests.filter(t => t.type === 'time');
                const quotesTests = latencyTests.filter(t => t.type === 'quotes');
                const balanceTests = latencyTests.filter(t => t.type === 'balance');
                
                if (timeTests.length > 0) {
                    const avgTime = timeTests.reduce((a, b) => a + b.latency, 0) / timeTests.length;
                    console.log('Average time sync latency: ' + avgTime.toFixed(2) + 'ms');
                }
                
                if (quotesTests.length > 0) {
                    const avgQuotes = quotesTests.reduce((a, b) => a + b.latency, 0) / quotesTests.length;
                    console.log('Average quotes latency: ' + avgQuotes.toFixed(2) + 'ms');
                }
                
                if (balanceTests.length > 0) {
                    const avgBalance = balanceTests.reduce((a, b) => a + b.latency, 0) / balanceTests.length;
                    console.log('Average balance latency: ' + avgBalance.toFixed(2) + 'ms');
                }
                
                const allLatencies = latencyTests.map(t => t.latency);
                const overallAvg = allLatencies.reduce((a, b) => a + b, 0) / allLatencies.length;
                const minLatency = Math.min(...allLatencies);
                const maxLatency = Math.max(...allLatencies);
                
                console.log('\\nOverall average: ' + overallAvg.toFixed(2) + 'ms');
                console.log('Min latency: ' + minLatency + 'ms');
                console.log('Max latency: ' + maxLatency + 'ms');
                console.log('Latency variance: ' + (maxLatency - minLatency) + 'ms');
                
                // Trading performance assessment
                console.log('\\n=== TRADING PERFORMANCE ASSESSMENT ===');
                if (overallAvg < 30) {
                    console.log('🟢 EXCELLENT - Perfect for high-frequency trading');
                } else if (overallAvg < 50) {
                    console.log('🟢 VERY GOOD - Excellent for active trading');
                } else if (overallAvg < 100) {
                    console.log('🟡 GOOD - Suitable for most trading strategies');
                } else if (overallAvg < 200) {
                    console.log('🟡 ACCEPTABLE - May notice slight delays');
                } else {
                    console.log('🔴 POOR - May significantly affect trading performance');
                }
                
                if (maxLatency - minLatency > 100) {
                    console.log('⚠️  WARNING: High latency variance detected');
                }
            }
            
            socket.disconnect();
            process.exit(0);
        }, testDuration);
        
    }, 2000); // Wait 2 seconds after connection for auth
});

// Listen for PocketOption-specific events
socket.on('auth_success', (data) => {
    console.log('✅ Authentication successful');
    console.log('Account data received');
});

socket.on('auth_error', (data) => {
    console.log('❌ Authentication failed: ' + JSON.stringify(data));
});

socket.on('quotes_update', (data) => {
    quotesReceived++;
    if (quotesReceived <= 5) {
        console.log('📈 Live quotes update #' + quotesReceived);
    }
});

socket.on('balance_update', (data) => {
    balanceUpdates++;
    console.log('💰 Balance update #' + balanceUpdates);
});

socket.on('asset_data', (data) => {
    console.log('📊 Asset data received');
});

socket.on('trade_result', (data) => {
    console.log('🎯 Trade result received');
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
        
        $scriptDir = Split-Path -Parent $PSCommandPath # Corrected way to get script path
        $tempPath = Join-Path $scriptDir "pocketoption_live_test_inline.js"
        $liveTestScript | Out-File -Encoding UTF8 -FilePath $tempPath
        
        # Check for socket.io-client
        $packageCheck = @"
try {
    require('socket.io-client');
    console.log('socket.io-client is available');
} catch (e) {
    console.log('ERROR: socket.io-client not found');
    console.log('Please run: npm install socket.io-client');
    process.exit(1);
}
"@
        
        $checkPath = Join-Path $scriptDir "check_socketio_inline.js"
        $packageCheck | Out-File -Encoding UTF8 -FilePath $checkPath
        
        try {
            Push-Location $scriptDir
            node $checkPath
            if ($LASTEXITCODE -ne 0) {
                Pop-Location
                Write-Host "[ERROR] Please install socket.io-client first:" -ForegroundColor Red
                Write-Host "npm install socket.io-client" -ForegroundColor Yellow
                return
            }
            
            Write-Host "Running live PocketOption latency test..." -ForegroundColor Green
            Write-Host "This will test actual trading API calls with your session" -ForegroundColor Cyan
            Write-Host "Press Ctrl+C to stop early`n" -ForegroundColor Gray
            
            node $tempPath
            Pop-Location
            
        } catch {
            Pop-Location # Ensure we pop location even on error
            Write-Host "Live test failed: $_" -ForegroundColor Red
        } finally {
            # Cleanup
            if (Test-Path $tempPath) { Remove-Item $tempPath -Force }
            if (Test-Path $checkPath) { Remove-Item $checkPath -Force }
        }
    } else {
        Write-Host "`n[ERROR] Node.js required for Socket.io testing" -ForegroundColor Red
        Write-Host "Please install Node.js from https://nodejs.org/" -ForegroundColor Yellow
    }
}

# Main execution
Write-Host "`n=== LIVE POCKETOPTION TRADING LATENCY TEST ===" -ForegroundColor Magenta

# Convert demo switch to boolean for JavaScript
$demoMode = if ($IsDemo) { "true" } else { "false" }

Test-PocketOptionLive -Sid $SessionId -Uid $UserId -Duration $TestDuration -Demo $demoMode

Write-Host "`n=== WHAT THIS TEST MEASURES ===" -ForegroundColor Magenta
Write-Host "✅ Real authentication with your session" -ForegroundColor Green
Write-Host "✅ Time synchronization latency (critical for trading)" -ForegroundColor Green
Write-Host "✅ Live quotes request/response times" -ForegroundColor Green
Write-Host "✅ Balance check latency" -ForegroundColor Green
Write-Host "✅ Real-time data feed reception" -ForegroundColor Green
Write-Host "✅ Overall trading API performance" -ForegroundColor Green

Write-Host "`n[SUCCESS] Live trading latency test complete!" -ForegroundColor Green
