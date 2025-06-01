# Ensure admin privileges
if (-NOT ([Security.Principal.WindowsPrincipal] [Security.Principal.WindowsIdentity]::GetCurrent()).IsInRole("Administrator")) {
    Write-Warning "Run PowerShell as Administrator."
    exit
}

Write-Output "[INFO] Setting power scheme to High Performance..."
powercfg -setactive SCHEME_MIN

# Disable Nagle's Algorithm (for all interfaces)
Write-Output "[INFO] Disabling Nagle's Algorithm..."
$interfaces = Get-ChildItem "HKLM:\SYSTEM\CurrentControlSet\Services\Tcpip\Parameters\Interfaces\"
foreach ($iface in $interfaces) {
    New-ItemProperty -Path $iface.PSPath -Name "TcpAckFrequency" -Value 1 -PropertyType DWord -Force
    New-ItemProperty -Path $iface.PSPath -Name "TCPNoDelay" -Value 1 -PropertyType DWord -Force
}

# Optimize TCP Settings
Write-Output "[INFO] Optimizing TCP stack..."
netsh int tcp set global rss=enabled
netsh int tcp set global autotuninglevel=normal
netsh int tcp set global chimney=enabled
netsh int tcp set global congestionprovider=ctcp

# Disable unnecessary services
$services = @(
    "DiagTrack",         # Telemetry
    "SysMain",           # Superfetch
    "WSearch",           # Windows Search
    "DeliveryOptimization"
)
foreach ($svc in $services) {
    Write-Output "[INFO] Disabling service: $svc"
    Stop-Service -Name $svc -Force -ErrorAction SilentlyContinue
    Set-Service -Name $svc -StartupType Disabled
}

# Optional: Disable Windows Defender real-time protection
Write-Output "[WARNING] Attempting to disable Defender real-time monitoring..."
Set-MpPreference -DisableRealtimeMonitoring $true

# CPU to run full power
Write-Output "[INFO] Locking CPU to 100% performance..."
powercfg -change -monitor-timeout-ac 0
powercfg -setacvalueindex SCHEME_MIN SUB_PROCESSOR PROCTHROTTLEMAX 100
powercfg -setacvalueindex SCHEME_MIN SUB_PROCESSOR PROCTHROTTLEMIN 100

# Done
Write-Output "[SUCCESS] Latency optimizations complete. Please reboot to apply all changes."
