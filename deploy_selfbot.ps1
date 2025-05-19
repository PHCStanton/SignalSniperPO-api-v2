# Self Bot v1.0 Deployment Script for EC2
# This script deploys the Self Bot to an EC2 instance using the Telethon user account approach

param (
    [Parameter(Mandatory=$true)]
    [string]$HostIP,
    
    [Parameter(Mandatory=$true)]
    [string]$KeyPath,
    
    [string]$Username = "ubuntu",
    
    [string]$RemoteDir = "~/selfbot",
    
    [switch]$IncludeSessionFiles = $false
)

# Validate parameters
if (-not (Test-Path $KeyPath)) {
    Write-Error "SSH key file not found at: $KeyPath"
    exit 1
}

# Required files to deploy
$requiredFiles = @(
    "bot.py",
    "run_bot.py",
    "monitor_signals.py",
    "check_telegram_session.py",
    "simulate_test_signals.py",
    ".env",
    "requirements.txt",
    "test_po_websocket.py",
    "test_ssid_direct.py",
    "extract_po_trade_ssid.md",
    "get_fresh_ssid_guide.md",
    "run_telegram_monitor.sh",
    "Run-TelegramMonitor.ps1"
)

$requiredDirs = @(
    "config",
    "pocketoptionapi",
    "utils"
)

# Check if required files exist
foreach ($file in $requiredFiles) {
    if (-not (Test-Path $file)) {
        Write-Warning "Required file not found: $file"
    }
}

# Check if required directories exist
foreach ($dir in $requiredDirs) {
    if (-not (Test-Path $dir)) {
        Write-Warning "Required directory not found: $dir"
    }
}

# Create temporary directory for files to be transferred
$tempDir = Join-Path $env:TEMP "selfbot_deploy"
if (Test-Path $tempDir) {
    Remove-Item -Path $tempDir -Recurse -Force
}
New-Item -Path $tempDir -ItemType Directory | Out-Null

# Copy required files and directories
foreach ($file in $requiredFiles) {
    if (Test-Path $file) {
        Copy-Item -Path $file -Destination $tempDir
    }
}

foreach ($dir in $requiredDirs) {
    if (Test-Path $dir) {
        Copy-Item -Path $dir -Destination $tempDir -Recurse
    }
}

# Session files
if ($IncludeSessionFiles) {
    $sessionFiles = Get-ChildItem -Path "." -Filter "*.session" -File
    foreach ($file in $sessionFiles) {
        Copy-Item -Path $file.FullName -Destination $tempDir
    }
}

# Create systemd service file
$servicePath = Join-Path $tempDir "selfbot.service"
@"
[Unit]
Description=Self Bot Trading Service
After=network.target

[Service]
User=ubuntu
Group=ubuntu
WorkingDirectory=/home/ubuntu/selfbot
ExecStart=/home/ubuntu/selfbot/venv/bin/python /home/ubuntu/selfbot/bot.py
Restart=always
RestartSec=10
EnvironmentFile=/home/ubuntu/selfbot/.env

[Install]
WantedBy=multi-user.target
"@ | Out-File -FilePath $servicePath -Encoding utf8

# Create setup script
$setupPath = Join-Path $tempDir "setup.sh"
@"
#!/bin/bash
# Self Bot v1.0 Setup Script

# Update and install dependencies
sudo apt update
sudo apt install -y python3 python3-pip git ufw python3-venv

# Create and activate virtual environment
python3 -m venv venv
source venv/bin/activate

# Install requirements
pip install -r requirements.txt

# Set up systemd service
sudo cp selfbot.service /etc/systemd/system/
sudo systemctl daemon-reload
sudo systemctl enable selfbot.service

echo "Self Bot setup completed. You can now start the service with:"
echo "sudo systemctl start selfbot.service"
"@ | Out-File -FilePath $setupPath -Encoding utf8

# SSH setup
$sshOptions = "-i `"$KeyPath`" -o StrictHostKeyChecking=no"

# Create remote directory if it doesn't exist
Write-Host "Creating remote directory: $RemoteDir"
ssh $sshOptions $Username@$HostIP "mkdir -p $RemoteDir"

# Transfer files
Write-Host "Transferring files to EC2 instance..."
scp $sshOptions -r "$tempDir/*" "$Username@$HostIP`:$RemoteDir/"

# Make setup script executable
Write-Host "Making setup script executable..."
ssh $sshOptions $Username@$HostIP "chmod +x $RemoteDir/setup.sh"

# Run setup script
Write-Host "Running setup script..."
ssh $sshOptions $Username@$HostIP "cd $RemoteDir && ./setup.sh"

# Cleanup
Remove-Item -Path $tempDir -Recurse -Force

Write-Host "Deployment completed successfully!"
Write-Host "Remote directory: $RemoteDir"
Write-Host "To start the service: ssh $sshOptions $Username@$HostIP 'sudo systemctl start selfbot.service'"
Write-Host "To check service status: ssh $sshOptions $Username@$HostIP 'sudo systemctl status selfbot.service'"
Write-Host "To view logs: ssh $sshOptions $Username@$HostIP 'sudo journalctl -u selfbot.service -f'"
