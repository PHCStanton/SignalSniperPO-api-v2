# SignalSniper Bot Runner for PowerShell
# Handles virtual environment setup and bot execution with low latency optimization
# Works both inside and outside VS Code, with or without Administrator privileges

param(
    [switch]$Force,
    [switch]$SkipVenvCheck,
    [switch]$Debug,
    [switch]$CreateNewVenv
)

# Set strict mode for better error handling
Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

# Colors for output
function Write-ColorOutput {
    param(
        [string]$Message,
        [string]$Color = "White"
    )
    Write-Host $Message -ForegroundColor $Color
}

# Banner
Write-ColorOutput "================================================================================" "Cyan"
Write-ColorOutput "                    SignalSniper Bot Runner v2.0                                " "Cyan"
Write-ColorOutput "                       Low Latency Trading Edition                              " "Cyan"
Write-ColorOutput "================================================================================" "Cyan"
Write-ColorOutput ""

# Check if running as Administrator
$currentPrincipal = New-Object Security.Principal.WindowsPrincipal([Security.Principal.WindowsIdentity]::GetCurrent())
$isAdmin = $currentPrincipal.IsInRole([Security.Principal.WindowsBuiltInRole]::Administrator)

if ($isAdmin) {
    Write-ColorOutput "[WARNING] Running as Administrator detected" "Yellow"
    Write-ColorOutput "   This may cause permission issues with virtual environments." "Yellow"
    Write-ColorOutput "   The script will handle this automatically." "Yellow"
    Write-ColorOutput ""
}

# Set execution policy for current user if needed
try {
    $currentPolicy = Get-ExecutionPolicy -Scope CurrentUser
    if ($currentPolicy -eq "Restricted" -or $currentPolicy -eq "Undefined") {
        Write-ColorOutput "[POLICY] Setting PowerShell execution policy..." "Yellow"
        Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser -Force
        Write-ColorOutput "[OK] Execution policy set to RemoteSigned for current user" "Green"
    }
} catch {
    Write-ColorOutput "[WARNING] Could not set execution policy: $($_.Exception.Message)" "Yellow"
    Write-ColorOutput "   You may need to run: Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser" "Yellow"
}

# Navigate to project directory
$projectPath = "C:\projects\SignalSniper"
if (-not (Test-Path $projectPath)) {
    Write-ColorOutput "[ERROR] Project directory not found: $projectPath" "Red"
    exit 1
}

Set-Location $projectPath
Write-ColorOutput "[DIR] Working directory: $(Get-Location)" "Blue"

# Function to create virtual environment with proper permissions
function New-VirtualEnvironment {
    param([string]$VenvPath)
    
    Write-ColorOutput "[BUILD] Creating new virtual environment..." "Blue"
    
    # Remove existing venv if it exists
    if (Test-Path $VenvPath) {
        Write-ColorOutput "[CLEAN] Removing existing venv directory..." "Yellow"
        try {
            Remove-Item -Path $VenvPath -Recurse -Force -ErrorAction Stop
            Write-ColorOutput "[OK] Old venv removed successfully" "Green"
        } catch {
            Write-ColorOutput "[WARNING] Could not remove old venv, trying with permissions fix..." "Yellow"
            try {
                & takeown /f $VenvPath /r /d y 2>$null | Out-Null
                & icacls $VenvPath /grant "${env:USERNAME}:(OI)(CI)F" /T /Q 2>$null | Out-Null
                Remove-Item -Path $VenvPath -Recurse -Force -ErrorAction Stop
                Write-ColorOutput "[OK] Old venv removed with permission fix" "Green"
            } catch {
                Write-ColorOutput "[ERROR] Failed to remove old venv: $($_.Exception.Message)" "Red"
                return $false
            }
        }
    }
    
    # Create new venv
    try {
        if ($isAdmin) {
            # If running as admin, create venv with explicit permissions
            python -m venv $VenvPath
            & icacls $VenvPath /grant "${env:USERNAME}:(OI)(CI)F" /T /Q 2>$null | Out-Null
            Write-ColorOutput "[OK] Virtual environment created with proper permissions" "Green"
        } else {
            python -m venv $VenvPath
            Write-ColorOutput "[OK] Virtual environment created successfully" "Green"
        }
        return $true
    } catch {
        Write-ColorOutput "[ERROR] Failed to create virtual environment: $($_.Exception.Message)" "Red"
        return $false
    }
}

# Check Python installation
Write-ColorOutput "[PYTHON] Checking Python installation..." "Blue"
try {
    $pythonVersion = python --version 2>&1
    Write-ColorOutput "[OK] Python found: $pythonVersion" "Green"
} catch {
    Write-ColorOutput "[ERROR] Python not found in PATH" "Red"
    Write-ColorOutput "   Please install Python from https://python.org" "Yellow"
    Write-ColorOutput "   Make sure to check 'Add Python to PATH' during installation" "Yellow"
    Read-Host "Press Enter to exit"
    exit 1
}

# Virtual environment handling
$venvPath = Join-Path $projectPath "venv"
$activateScript = Join-Path $venvPath "Scripts\Activate.ps1"
$pythonExe = Join-Path $venvPath "Scripts\python.exe"
$pipExe = Join-Path $venvPath "Scripts\pip.exe"

# Check if we need to create a new venv
if ($CreateNewVenv -or -not (Test-Path $activateScript)) {
    if (-not (Test-Path $activateScript)) {
        Write-ColorOutput "[WARNING] Virtual environment not found" "Yellow"
    }
    
    if (-not (New-VirtualEnvironment -VenvPath $venvPath)) {
        Write-ColorOutput "[ERROR] Failed to set up virtual environment" "Red"
        Read-Host "Press Enter to exit"
        exit 1
    }
}

# Activate virtual environment
Write-ColorOutput "[VENV] Activating virtual environment..." "Blue"
try {
    # Method 1: Try standard activation
    & $activateScript -ErrorAction Stop
    Write-ColorOutput "[OK] Virtual environment activated (standard method)" "Green"
} catch {
    # Method 2: Manual environment variable setup
    Write-ColorOutput "[WARNING] Standard activation failed, using alternative method..." "Yellow"
    $env:VIRTUAL_ENV = $venvPath
    $env:PATH = "$venvPath\Scripts;$env:PATH"
    $env:PYTHON_HOME = $venvPath
    
    # Verify activation
    if (Test-Path $pythonExe) {
        Write-ColorOutput "[OK] Virtual environment activated (alternative method)" "Green"
    } else {
        Write-ColorOutput "[ERROR] Failed to activate virtual environment" "Red"
        exit 1
    }
}

# Install/upgrade dependencies
if (-not $SkipVenvCheck) {
    Write-ColorOutput "[DEPS] Checking and installing dependencies..." "Blue"
    
    # Upgrade pip first
    try {
        & $pythonExe -m pip install --upgrade pip --quiet
        Write-ColorOutput "[OK] Pip upgraded successfully" "Green"
    } catch {
        Write-ColorOutput "[WARNING] Pip upgrade failed: $($_.Exception.Message)" "Yellow"
    }
    
    # Install requirements
    $requirementsFile = Join-Path $projectPath "requirements.txt"
    if (Test-Path $requirementsFile) {
        try {
            Write-ColorOutput "[DEPS] Installing from requirements.txt..." "Blue"
            & $pipExe install -r $requirementsFile --quiet
            Write-ColorOutput "[OK] All dependencies installed successfully" "Green"
        } catch {
            Write-ColorOutput "[WARNING] Some dependencies failed to install" "Yellow"
            Write-ColorOutput "   Installing essential packages individually..." "Yellow"
            
            # Install essential packages one by one
            $essentialPackages = @("telethon", "python-dotenv", "pytz", "asyncio", "aiohttp", "websockets")
            foreach ($package in $essentialPackages) {
                try {
                    & $pipExe install $package --quiet
                    Write-ColorOutput "   [OK] $package installed" "Green"
                } catch {
                    Write-ColorOutput "   [ERROR] Failed to install $package" "Red"
                }
            }
        }
    } else {
        Write-ColorOutput "[WARNING] requirements.txt not found" "Yellow"
        Write-ColorOutput "   Installing essential packages..." "Yellow"
        & $pipExe install telethon python-dotenv pytz asyncio aiohttp websockets --quiet
    }
}

# Verify environment
Write-ColorOutput ""
Write-ColorOutput "[TEST] Verifying environment setup..." "Blue"
try {
    $testResult = & $pythonExe -c "import telethon, dotenv, pytz; print('OK')" 2>&1
    if ($testResult -eq "OK") {
        Write-ColorOutput "[OK] All essential modules verified" "Green"
    } else {
        throw "Module import test failed"
    }
} catch {
    Write-ColorOutput "[ERROR] Environment verification failed: $($_.Exception.Message)" "Red"
    Write-ColorOutput "   The bot may not run properly" "Yellow"
}

# Display environment info
if ($Debug) {
    Write-ColorOutput ""
    Write-ColorOutput "[INFO] Environment Information:" "Cyan"
    Write-ColorOutput "   Python: $(& $pythonExe --version)" "White"
    Write-ColorOutput "   Pip: $(& $pipExe --version)" "White"
    Write-ColorOutput "   Virtual Env: $venvPath" "White"
    Write-ColorOutput "   Working Dir: $(Get-Location)" "White"
    Write-ColorOutput ""
}

# Check if main bot file exists
$botFile = "SignalSniper.py"
if (-not (Test-Path $botFile)) {
    Write-ColorOutput "[ERROR] Bot file not found: $botFile" "Red"
    exit 1
}

# Performance optimizations for Windows
Write-ColorOutput ""
Write-ColorOutput "[PERF] Applying performance optimizations..." "Blue"

# Set process priority
try {
    $currentProcess = Get-Process -Id $PID
    $currentProcess.PriorityClass = [System.Diagnostics.ProcessPriorityClass]::High
    Write-ColorOutput "[OK] Process priority set to High" "Green"
} catch {
    Write-ColorOutput "[WARNING] Could not set process priority" "Yellow"
}

# Disable Windows Defender real-time scanning for the project folder (requires admin)
if ($isAdmin) {
    try {
        Add-MpPreference -ExclusionPath $projectPath -ErrorAction SilentlyContinue
        Write-ColorOutput "[OK] Added Windows Defender exclusion for project folder" "Green"
    } catch {
        Write-ColorOutput "[WARNING] Could not add Windows Defender exclusion" "Yellow"
    }
}

# Clear screen before starting bot
Clear-Host

# Final banner
Write-ColorOutput "================================================================================" "Green"
Write-ColorOutput "                    STARTING SIGNALSNIPER BOT v3.0                              " "Green"
Write-ColorOutput "                         LOW LATENCY TRADING MODE                               " "Green"
Write-ColorOutput "================================================================================" "Green"
Write-ColorOutput ""
Write-ColorOutput "[SIGNAL] Monitoring Telegram signals..." "Cyan"
Write-ColorOutput "[TRADE] Ready for low-latency trading..." "Cyan"
Write-ColorOutput ""

# Run the bot
try {
    & $pythonExe $botFile
} catch {
    Write-ColorOutput ""
    Write-ColorOutput "[ERROR] Bot crashed with error: $($_.Exception.Message)" "Red"
    Write-ColorOutput ""
    Write-ColorOutput "Troubleshooting tips:" "Yellow"
    Write-ColorOutput "1. Check if all dependencies are installed correctly" "White"
    Write-ColorOutput "2. Verify your .env file contains valid credentials" "White"
    Write-ColorOutput "3. Ensure Telegram session is properly configured" "White"
    Write-ColorOutput "4. Check the bot logs for more details" "White"
    Write-ColorOutput ""
}

# Cleanup on exit
Write-ColorOutput ""
Write-ColorOutput "[STOPPED] Bot stopped" "Yellow"
Write-ColorOutput ""
Read-Host "Press Enter to exit"
