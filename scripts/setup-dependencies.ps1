# ------------------------------
# Setup-Dependencies.ps1
# Install required dependencies for PocketOption latency testing
# ------------------------------

Write-Host "[INFO] Setting up dependencies for PocketOption latency testing..." -ForegroundColor Cyan

# Check if Node.js is installed
Write-Host "`n[CHECK] Verifying Node.js installation..." -ForegroundColor Yellow
if (Get-Command "node" -ErrorAction SilentlyContinue) {
    $nodeVersion = node --version
    Write-Host "[SUCCESS] Node.js found: $nodeVersion" -ForegroundColor Green
    
    $npmVersion = npm --version
    Write-Host "[SUCCESS] npm found: v$npmVersion" -ForegroundColor Green
} else {
    Write-Host "[ERROR] Node.js not found!" -ForegroundColor Red
    Write-Host "Please install Node.js from: https://nodejs.org/" -ForegroundColor Yellow
    Write-Host "After installation, restart PowerShell and run this script again." -ForegroundColor Yellow
    exit 1
}

# Check current directory
Write-Host "`n[INFO] Current directory: $PWD" -ForegroundColor Cyan

# Initialize npm project if package.json doesn't exist
if (-not (Test-Path "package.json")) {
    Write-Host "`n[SETUP] Initializing npm project..." -ForegroundColor Yellow
    
    $packageJson = @{
        name = "pocketoption-latency-testing"
        version = "1.0.0"
        description = "PocketOption trading latency testing tools"
        main = "index.js"
        scripts = @{
            test = "echo `"Error: no test specified`" && exit 1"
        }
        keywords = @("trading", "latency", "pocketoption", "socketio")
        author = "Trading Optimizer"
        license = "MIT"
        dependencies = @{}
    } | ConvertTo-Json -Depth 3
    
    $packageJson | Out-File -FilePath "package.json" -Encoding UTF8
    Write-Host "[SUCCESS] Created package.json" -ForegroundColor Green
}

# Install socket.io-client
Write-Host "`n[INSTALL] Installing socket.io-client..." -ForegroundColor Yellow
try {
    npm install socket.io-client
    if ($LASTEXITCODE -eq 0) {
        Write-Host "[SUCCESS] socket.io-client installed successfully!" -ForegroundColor Green
    } else {
        Write-Host "[ERROR] Failed to install socket.io-client" -ForegroundColor Red
        exit 1
    }
} catch {
    Write-Host "[ERROR] Error installing socket.io-client: $_" -ForegroundColor Red
    exit 1
}

# Verify installation
Write-Host "`n[VERIFY] Testing socket.io-client installation..." -ForegroundColor Yellow
$testScript = @"
try {
    const io = require('socket.io-client');
    console.log('[SUCCESS] socket.io-client is working correctly');
    console.log('Version:', require('socket.io-client/package.json').version);
} catch (error) {
    console.log('[ERROR] socket.io-client test failed:', error.message);
    process.exit(1);
}
"@

$scriptDir = Split-Path -Parent $MyInvocation.MyCommand.Definition
$testPath = Join-Path $scriptDir "test_socketio_install_inline.js"
$testScript | Out-File -Encoding UTF8 -FilePath $testPath

try {
    Push-Location $scriptDir
    node $testPath
    if ($LASTEXITCODE -eq 0) {
        Write-Host "[SUCCESS] Installation verified successfully!" -ForegroundColor Green
    }
    Pop-Location
} catch {
    Pop-Location # Ensure we pop location even on error
    Write-Host "[ERROR] Installation verification failed" -ForegroundColor Red
} finally {
    if (Test-Path $testPath) {
        Remove-Item $testPath -Force
    }
}

# Show what was installed
Write-Host "`n[INFO] Installation summary:" -ForegroundColor Cyan
if (Test-Path "node_modules") {
    $nodeModulesSize = (Get-ChildItem "node_modules" -Recurse | Measure-Object -Property Length -Sum).Sum / 1MB
    Write-Host "node_modules created ($([math]::Round($nodeModulesSize, 1)) MB)" -ForegroundColor White
}

if (Test-Path "package-lock.json") {
    Write-Host "package-lock.json created" -ForegroundColor White
}

Write-Host "`n=== READY TO TEST ===" -ForegroundColor Magenta
Write-Host "You can now run the latency tests:" -ForegroundColor Green
Write-Host "  .\test-pocketoption-live.ps1" -ForegroundColor White
Write-Host "  .\test-socketio-latency.ps1" -ForegroundColor White
Write-Host "  .\check-system-latency.ps1" -ForegroundColor White

Write-Host "`n[SUCCESS] Setup complete!" -ForegroundColor Green
