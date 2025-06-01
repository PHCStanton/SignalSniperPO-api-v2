# ------------------------------
# Test-Node-Modules.ps1
# Diagnose Node.js module loading issues
# ------------------------------

Write-Host "[INFO] Diagnosing Node.js module loading..." -ForegroundColor Cyan

# Check current directory
Write-Host "`nCurrent directory: $PWD" -ForegroundColor Yellow

# Check if node_modules exists
if (Test-Path "node_modules") {
    Write-Host "[SUCCESS] node_modules directory found" -ForegroundColor Green
    
    if (Test-Path "node_modules/socket.io-client") {
        Write-Host "[SUCCESS] socket.io-client directory found" -ForegroundColor Green
    } else {
        Write-Host "[ERROR] socket.io-client directory not found" -ForegroundColor Red
    }
} else {
    Write-Host "[ERROR] node_modules directory not found" -ForegroundColor Red
}

# Test Node.js module resolution
Write-Host "`n[TEST] Testing Node.js module resolution..." -ForegroundColor Yellow

$testScript = @"
console.log('Current working directory:', process.cwd());
console.log('Node.js module paths:');
console.log(require.resolve.paths('socket.io-client'));

try {
    const io = require('socket.io-client');
    console.log('[SUCCESS] socket.io-client loaded successfully');
    console.log('Version:', require('socket.io-client/package.json').version);
} catch (error) {
    console.log('[ERROR] Failed to load socket.io-client:', error.message);
    console.log('Error code:', error.code);
    
    // Try to find the module manually
    try {
        const path = require('path');
        const fs = require('fs');
        const modulePath = path.join(process.cwd(), 'node_modules', 'socket.io-client');
        console.log('Looking for module at:', modulePath);
        
        if (fs.existsSync(modulePath)) {
            console.log('[INFO] Module directory exists');
            const packagePath = path.join(modulePath, 'package.json');
            if (fs.existsSync(packagePath)) {
                console.log('[INFO] package.json exists');
                const pkg = JSON.parse(fs.readFileSync(packagePath, 'utf8'));
                console.log('[INFO] Package version:', pkg.version);
            }
        } else {
            console.log('[ERROR] Module directory does not exist');
        }
    } catch (e) {
        console.log('[ERROR] Manual check failed:', e.message);
    }
}
"@

$testPath = "test_modules.js"
$testScript | Out-File -Encoding UTF8 -FilePath $testPath

try {
    Write-Host "Running Node.js test..." -ForegroundColor Gray
    node $testPath
} catch {
    Write-Host "[ERROR] Node.js test failed: $_" -ForegroundColor Red
} finally {
    if (Test-Path $testPath) {
        Remove-Item $testPath -Force
    }
}

Write-Host "`n[INFO] Diagnosis complete" -ForegroundColor Cyan
