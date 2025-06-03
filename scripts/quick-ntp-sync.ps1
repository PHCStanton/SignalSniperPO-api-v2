# ------------------------------
# quick-ntp-sync.ps1
# Quick NTP Synchronization for Trading Bot
# Phase 1 Implementation - Latency Optimization
# ------------------------------

param(
    [int]$ToleranceMs = 10,
    [switch]$Verbose = $false,
    [switch]$Force = $false
)

# Configure output based on verbose flag
if ($Verbose) {
    $VerbosePreference = "Continue"
}

Write-Host "[NTP-SYNC] Starting quick NTP synchronization..." -ForegroundColor Cyan

# Financial-grade NTP servers for trading applications
$NtpServers = @(
    "time.nist.gov",
    "pool.ntp.org", 
    "0.pool.ntp.org",
    "1.pool.ntp.org",
    "time.windows.com"
)

# Function to test NTP server responsiveness
function Test-NtpServer {
    param([string]$Server)
    
    try {
        Write-Verbose "[TEST] Testing NTP server: $Server"
        $result = w32tm /stripchart /computer:$Server /samples:1 /dataonly 2>&1
        
        if ($LASTEXITCODE -eq 0 -and $result -match "(\+|\-)[\d\.]+s") {
            Write-Verbose "[SUCCESS] $Server is responsive"
            return $true
        } else {
            Write-Verbose "[FAILED] $Server is not responsive"
            return $false
        }
    } catch {
        Write-Verbose "[ERROR] Error testing $Server`: $_"
        return $false
    }
}

# Function to force NTP sync with specific server
function Sync-WithServer {
    param([string]$Server)
    
    try {
        Write-Host "  [SYNC] Attempting sync with $Server..." -ForegroundColor Yellow
        
        # Configure NTP server temporarily
        $configResult = w32tm /config /manualpeerlist:"$Server,0x1" /syncfromflags:manual /reliable:yes /update 2>&1
        if ($LASTEXITCODE -ne 0) {
            Write-Verbose "[CONFIG-ERROR] Failed to configure server $Server"
            return $false
        }
        
        # Restart time service
        Restart-Service w32time -Force -ErrorAction SilentlyContinue
        Start-Sleep -Seconds 2
        
        # Force sync
        $syncResult = w32tm /resync /force 2>&1
        if ($LASTEXITCODE -eq 0) {
            Write-Host "  [SUCCESS] Synced with $Server" -ForegroundColor Green
            return $true
        } else {
            Write-Verbose "[SYNC-ERROR] Failed to sync with $Server`: $syncResult"
            return $false
        }
    } catch {
        Write-Verbose "[EXCEPTION] Error syncing with $Server`: $_"
        return $false
    }
}

# Function to check sync accuracy
function Test-SyncAccuracy {
    param([int]$ToleranceMs)
    
    try {
        Write-Host "  [CHECK] Verifying sync accuracy..." -ForegroundColor Yellow
        
        # Test accuracy with NIST
        $result = w32tm /stripchart /computer:time.nist.gov /samples:3 /dataonly 2>&1
        
        if ($LASTEXITCODE -eq 0) {
            # Parse offset values
            $offsets = @()
            foreach ($line in $result) {
                if ($line -match "(\+|\-)([\d\.]+)s") {
                    $offsetSeconds = [double]$matches[2]
                    if ($matches[1] -eq "-") { $offsetSeconds = -$offsetSeconds }
                    $offsets += ($offsetSeconds * 1000) # Convert to milliseconds
                }
            }
            
            if ($offsets.Count -gt 0) {
                $avgOffset = [Math]::Abs(($offsets | Measure-Object -Average).Average)
                Write-Host "  [ACCURACY] Average offset: $([Math]::Round($avgOffset, 2))ms" -ForegroundColor Cyan
                
                if ($avgOffset -le $ToleranceMs) {
                    Write-Host "  [SUCCESS] Sync accuracy within tolerance ($ToleranceMs ms)" -ForegroundColor Green
                    return $true, $avgOffset
                } else {
                    Write-Host "  [WARNING] Sync accuracy exceeds tolerance: $([Math]::Round($avgOffset, 2))ms > $ToleranceMs ms" -ForegroundColor Yellow
                    return $false, $avgOffset
                }
            }
        }
        
        Write-Host "  [ERROR] Could not verify sync accuracy" -ForegroundColor Red
        return $false, -1
    } catch {
        Write-Host "  [ERROR] Exception checking sync accuracy: $_" -ForegroundColor Red
        return $false, -1
    }
}

# Main sync process
try {
    # Check if we need admin privileges
    $isAdmin = ([Security.Principal.WindowsPrincipal] [Security.Principal.WindowsIdentity]::GetCurrent()).IsInRole("Administrator")
    if (-not $isAdmin) {
        Write-Host "[ERROR] Administrator privileges required for NTP sync" -ForegroundColor Red
        Write-Host "Please run PowerShell as Administrator" -ForegroundColor Yellow
        exit 1
    }
    
    # Get current sync status
    Write-Host "[INFO] Checking current time sync status..." -ForegroundColor Cyan
    $statusResult = w32tm /query /status 2>&1
    
    if ($statusResult -match "Last Successful Sync Time: (.+)") {
        $lastSync = $matches[1]
        Write-Host "  Last successful sync: $lastSync" -ForegroundColor Gray
    }
    
    # Check if force sync is needed
    $needsSync = $Force
    if (-not $needsSync) {
        # Check current accuracy
        $accurate, $currentOffset = Test-SyncAccuracy -ToleranceMs $ToleranceMs
        if (-not $accurate -and $currentOffset -gt 0) {
            Write-Host "[INFO] Current sync exceeds tolerance, forcing resync..." -ForegroundColor Yellow
            $needsSync = $true
        } elseif ($accurate) {
            Write-Host "[SUCCESS] Time is already synchronized within tolerance" -ForegroundColor Green
            exit 0
        }
    }
    
    if ($needsSync) {
        Write-Host "[SYNC] Starting NTP synchronization process..." -ForegroundColor Cyan
        
        # Test servers and find responsive ones
        $responsiveServers = @()
        foreach ($server in $NtpServers) {
            if (Test-NtpServer -Server $server) {
                $responsiveServers += $server
            }
        }
        
        if ($responsiveServers.Count -eq 0) {
            Write-Host "[ERROR] No responsive NTP servers found" -ForegroundColor Red
            exit 1
        }
        
        Write-Host "[INFO] Found $($responsiveServers.Count) responsive NTP servers" -ForegroundColor Green
        
        # Try to sync with each responsive server
        $syncSuccess = $false
        foreach ($server in $responsiveServers) {
            if (Sync-WithServer -Server $server) {
                $syncSuccess = $true
                break
            }
        }
        
        if (-not $syncSuccess) {
            Write-Host "[ERROR] Failed to sync with any NTP server" -ForegroundColor Red
            exit 1
        }
        
        # Wait a moment for sync to settle
        Start-Sleep -Seconds 3
    }
    
    # Final accuracy check
    Write-Host "[VERIFY] Performing final accuracy verification..." -ForegroundColor Cyan
    $finalAccurate, $finalOffset = Test-SyncAccuracy -ToleranceMs $ToleranceMs
    
    if ($finalAccurate) {
        Write-Host "[SUCCESS] NTP synchronization completed successfully!" -ForegroundColor Green
        Write-Host "  Final accuracy: $([Math]::Round($finalOffset, 2))ms (tolerance: $ToleranceMs ms)" -ForegroundColor Green
        
        # Log success for bot integration
        $logEntry = @{
            timestamp = (Get-Date).ToString("yyyy-MM-dd HH:mm:ss")
            status = "success"
            offset_ms = [Math]::Round($finalOffset, 2)
            tolerance_ms = $ToleranceMs
        }
        
        # Save to log file for bot monitoring
        $logPath = Join-Path $PSScriptRoot "ntp_sync.log"
        $logEntry | ConvertTo-Json -Compress | Out-File -FilePath $logPath -Append -Encoding UTF8
        
        exit 0
    } else {
        Write-Host "[WARNING] Sync completed but accuracy still exceeds tolerance" -ForegroundColor Yellow
        Write-Host "  Current offset: $([Math]::Round($finalOffset, 2))ms (tolerance: $ToleranceMs ms)" -ForegroundColor Yellow
        
        # Log warning for bot integration
        $logEntry = @{
            timestamp = (Get-Date).ToString("yyyy-MM-dd HH:mm:ss")
            status = "warning"
            offset_ms = [Math]::Round($finalOffset, 2)
            tolerance_ms = $ToleranceMs
        }
        
        $logPath = Join-Path $PSScriptRoot "ntp_sync.log"
        $logEntry | ConvertTo-Json -Compress | Out-File -FilePath $logPath -Append -Encoding UTF8
        
        exit 2
    }
    
} catch {
    Write-Host "[ERROR] Exception during NTP sync: $_" -ForegroundColor Red
    
    # Log error for bot integration
    $logEntry = @{
        timestamp = (Get-Date).ToString("yyyy-MM-dd HH:mm:ss")
        status = "error"
        error = $_.Exception.Message
        tolerance_ms = $ToleranceMs
    }
    
    $logPath = Join-Path $PSScriptRoot "ntp_sync.log"
    $logEntry | ConvertTo-Json -Compress | Out-File -FilePath $logPath -Append -Encoding UTF8
    
    exit 1
}
