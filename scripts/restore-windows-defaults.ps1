# ------------------------------
# Restore-Windows-Defaults.ps1
# Reverse the optimizations made by optimize-windows-latency.ps1
# ------------------------------

# Ensure admin privileges
if (-NOT ([Security.Principal.WindowsPrincipal] [Security.Principal.WindowsIdentity]::GetCurrent()).IsInRole("Administrator")) {
    Write-Warning "Run PowerShell as Administrator to restore settings."
    exit
}

Write-Host "[INFO] Restoring Windows default settings..." -ForegroundColor Cyan
Write-Host "This will reverse the optimizations made by optimize-windows-latency.ps1" -ForegroundColor Yellow

# Restore power scheme to Balanced
Write-Host "`n[RESTORE] Setting power scheme back to Balanced..." -ForegroundColor Green
powercfg -setactive SCHEME_BALANCED

# Re-enable Nagle's Algorithm (restore default TCP behavior)
Write-Host "[RESTORE] Re-enabling Nagle's Algorithm (removing custom TCP settings)..." -ForegroundColor Green
$interfaces = Get-ChildItem "HKLM:\SYSTEM\CurrentControlSet\Services\Tcpip\Parameters\Interfaces\"
foreach ($iface in $interfaces) {
    try {
        Remove-ItemProperty -Path $iface.PSPath -Name "TcpAckFrequency" -ErrorAction SilentlyContinue
        Remove-ItemProperty -Path $iface.PSPath -Name "TCPNoDelay" -ErrorAction SilentlyContinue
        Write-Host "  Restored interface: $($iface.PSChildName)" -ForegroundColor Gray
    } catch {
        # Ignore errors for interfaces that don't have these properties
    }
}

# Restore TCP Settings to defaults
Write-Host "[RESTORE] Restoring TCP stack to default settings..." -ForegroundColor Green
try {
    netsh int tcp set global rss=default
    netsh int tcp set global autotuninglevel=normal
    netsh int tcp set global chimney=default
    netsh int tcp set global congestionprovider=default
    Write-Host "  TCP settings restored to defaults" -ForegroundColor Gray
} catch {
    Write-Host "  Some TCP settings may require manual restoration" -ForegroundColor Yellow
}

# Re-enable services that were disabled
Write-Host "[RESTORE] Re-enabling previously disabled services..." -ForegroundColor Green
$services = @(
    @{Name="DiagTrack"; DisplayName="Connected User Experiences and Telemetry"; DefaultStartup="Automatic"},
    @{Name="SysMain"; DisplayName="SysMain (Superfetch)"; DefaultStartup="Automatic"},
    @{Name="WSearch"; DisplayName="Windows Search"; DefaultStartup="Automatic (Delayed Start)"},
    @{Name="DeliveryOptimization"; DisplayName="Delivery Optimization"; DefaultStartup="Automatic (Delayed Start)"}
)

foreach ($svc in $services) {
    try {
        Write-Host "  Enabling service: $($svc.DisplayName)" -ForegroundColor Gray
        Set-Service -Name $svc.Name -StartupType Automatic -ErrorAction SilentlyContinue
        Start-Service -Name $svc.Name -ErrorAction SilentlyContinue
    } catch {
        Write-Host "    Warning: Could not restore $($svc.Name) - may need manual intervention" -ForegroundColor Yellow
    }
}

# Re-enable Windows Defender real-time protection
Write-Host "[RESTORE] Re-enabling Windows Defender real-time monitoring..." -ForegroundColor Green
try {
    Set-MpPreference -DisableRealtimeMonitoring $false
    Write-Host "  Windows Defender real-time protection enabled" -ForegroundColor Gray
} catch {
    Write-Host "  Warning: Could not re-enable Defender - may need manual intervention" -ForegroundColor Yellow
}

# Restore CPU power management to default
Write-Host "[RESTORE] Restoring CPU power management to defaults..." -ForegroundColor Green
try {
    # Restore monitor timeout (15 minutes on AC power)
    powercfg -change -monitor-timeout-ac 15
    
    # Restore CPU throttling to default values (typically 5% min, 100% max)
    powercfg -setacvalueindex SCHEME_BALANCED SUB_PROCESSOR PROCTHROTTLEMIN 5
    powercfg -setacvalueindex SCHEME_BALANCED SUB_PROCESSOR PROCTHROTTLEMAX 100
    
    # Apply the changes
    powercfg -setactive SCHEME_BALANCED
    
    Write-Host "  CPU power management restored to balanced profile" -ForegroundColor Gray
} catch {
    Write-Host "  Warning: Some CPU settings may need manual restoration" -ForegroundColor Yellow
}

# Additional cleanup - restore Windows Update service if it was affected
Write-Host "[RESTORE] Ensuring Windows Update service is enabled..." -ForegroundColor Green
try {
    Set-Service -Name "wuauserv" -StartupType Automatic -ErrorAction SilentlyContinue
    Write-Host "  Windows Update service restored" -ForegroundColor Gray
} catch {
    Write-Host "  Windows Update service was not affected" -ForegroundColor Gray
}

# Show current power scheme
Write-Host "`n[INFO] Current power scheme:" -ForegroundColor Cyan
$currentScheme = powercfg -getactivescheme
Write-Host "  $currentScheme" -ForegroundColor White

# Show service status
Write-Host "`n[INFO] Service status check:" -ForegroundColor Cyan
foreach ($svc in $services) {
    try {
        $serviceStatus = Get-Service -Name $svc.Name -ErrorAction SilentlyContinue
        if ($serviceStatus) {
            $status = $serviceStatus.Status
            $startup = (Get-WmiObject -Class Win32_Service -Filter "Name='$($svc.Name)'").StartMode
            Write-Host "  $($svc.DisplayName): $status ($startup)" -ForegroundColor White
        }
    } catch {
        Write-Host "  $($svc.Name): Status unknown" -ForegroundColor Yellow
    }
}

Write-Host "`n=== RESTORATION COMPLETE ===" -ForegroundColor Magenta
Write-Host "✅ Power scheme restored to Balanced" -ForegroundColor Green
Write-Host "✅ Nagle's Algorithm re-enabled (TCP optimized for general use)" -ForegroundColor Green
Write-Host "✅ TCP stack restored to default settings" -ForegroundColor Green
Write-Host "✅ System services re-enabled" -ForegroundColor Green
Write-Host "✅ Windows Defender real-time protection re-enabled" -ForegroundColor Green
Write-Host "✅ CPU power management restored to balanced" -ForegroundColor Green

Write-Host "`n[RECOMMENDATION] Please reboot your system to ensure all changes take effect." -ForegroundColor Yellow
Write-Host "[INFO] Your system is now restored to Windows default settings." -ForegroundColor Cyan

# Optional: Ask if user wants to reboot now
$reboot = Read-Host "`nWould you like to reboot now? (y/N)"
if ($reboot -eq 'y' -or $reboot -eq 'Y') {
    Write-Host "[INFO] Rebooting system in 10 seconds..." -ForegroundColor Yellow
    Write-Host "Press Ctrl+C to cancel" -ForegroundColor Gray
    Start-Sleep -Seconds 10
    Restart-Computer -Force
}
