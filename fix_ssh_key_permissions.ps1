# fix_ssh_key_permissions.ps1
# This script fixes permissions on an SSH private key file for Windows
# Run this script as Administrator for best results

param (
    [Parameter(Mandatory=$true)]
    [string]$KeyFile = "EC2\whoami-in-Frankfurt.pem"
)

Write-Host "Fixing permissions for SSH key file: $KeyFile" -ForegroundColor Cyan
Write-Host "================================================" -ForegroundColor Cyan

# Check if file exists
if (-not (Test-Path $KeyFile)) {
    Write-Host "Error: Key file not found: $KeyFile" -ForegroundColor Red
    exit 1
}

try {
    # 1. Reset permissions to a clean state
    Write-Host "1. Resetting permissions..." -ForegroundColor Yellow
    icacls.exe $KeyFile /reset /T /C /Q
    
    # 2. Remove inheritance
    Write-Host "2. Removing inheritance..." -ForegroundColor Yellow
    icacls.exe $KeyFile /inheritance:r /T /C /Q
    
    # 3. Grant current user Full Control
    Write-Host "3. Granting current user Full Control..." -ForegroundColor Yellow
    icacls.exe $KeyFile /grant:r "$($env:USERNAME):(F)" /T /C /Q
    
    # 4. Remove common problematic groups
    Write-Host "4. Removing other users and groups..." -ForegroundColor Yellow
    icacls.exe $KeyFile /remove "Authenticated Users" "BUILTIN\Users" "Everyone" /T /C /Q
    
    Write-Host "`nPermissions fixed successfully!" -ForegroundColor Green
    Write-Host "You can now try your SSH connection again:" -ForegroundColor Green
    Write-Host "ssh -i EC2/whoami-in-Frankfurt.pem ubuntu@3.126.128.227" -ForegroundColor Cyan
}
catch {
    Write-Host "Error fixing permissions: $_" -ForegroundColor Red
    exit 1
}
