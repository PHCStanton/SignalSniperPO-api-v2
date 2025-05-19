# deploy_to_ec2.ps1 - Deploys the Pocket Option trading bot to an EC2 instance from Windows.
#
# This script packages the necessary files, transfers them to the EC2 instance,
# sets up the environment, configures the bot to run as a service, and starts the bot.
#
# Usage: .\deploy_to_ec2.ps1 [options]
#
# Parameters:
#   -Host          EC2 instance hostname or IP address
#   -User          SSH username (default: ec2-user)
#   -KeyFile       Path to SSH private key (.pem file)
#   -RemotePath    Remote deployment path (default: /home/ec2-user/pocket-option-bot)
#   -ConfigFile    Path to configuration file (default: deploy_config.json)
#   -SetupOnly     Only set up the environment, don't deploy the bot
#   -Restart       Restart the bot service if it's already running
#   -Verbose       Enable verbose output

param (
    [Parameter(Mandatory=$false)]
    [string]$Host,
    
    [Parameter(Mandatory=$false)]
    [string]$User = "ec2-user",
    
    [Parameter(Mandatory=$false)]
    [string]$KeyFile,
    
    [Parameter(Mandatory=$false)]
    [string]$RemotePath = "/home/ec2-user/pocket-option-bot",
    
    [Parameter(Mandatory=$false)]
    [string]$ConfigFile = "deploy_config.json",
    
    [Parameter(Mandatory=$false)]
    [switch]$SetupOnly,
    
    [Parameter(Mandatory=$false)]
    [switch]$Restart,
    
    [Parameter(Mandatory=$false)]
    [switch]$Verbose
)

# Function to write colored output
function Write-ColorOutput {
    param (
        [Parameter(Mandatory=$true)]
        [string]$Level,
        
        [Parameter(Mandatory=$true)]
        [string]$Message
    )
    
    $color = "White"
    
    switch ($Level) {
        "INFO" { $color = "Green" }
        "WARN" { $color = "Yellow" }
        "ERROR" { $color = "Red" }
        "DEBUG" { $color = "Cyan" }
    }
    
    if ($Level -ne "DEBUG" -or $Verbose) {
        Write-Host "[$Level] $Message" -ForegroundColor $color
    }
}

# Function to check if a command exists
function Test-Command {
    param (
        [Parameter(Mandatory=$true)]
        [string]$Command
    )
    
    $exists = $null -ne (Get-Command $Command -ErrorAction SilentlyContinue)
    return $exists
}

# Function to check if a file exists
function Test-FileExists {
    param (
        [Parameter(Mandatory=$true)]
        [string]$Path
    )
    
    return Test-Path -Path $Path -PathType Leaf
}

# Function to check if a directory exists
function Test-DirectoryExists {
    param (
        [Parameter(Mandatory=$true)]
        [string]$Path
    )
    
    return Test-Path -Path $Path -PathType Container
}

# Function to load configuration from file
function Load-Config {
    if (Test-FileExists $ConfigFile) {
        Write-ColorOutput "INFO" "Loading configuration from $ConfigFile"
        
        try {
            $config = Get-Content -Path $ConfigFile -Raw | ConvertFrom-Json
            
            # Load configuration values if not provided as parameters
            if (-not $Host -and $config.host) {
                $script:Host = $config.host
            }
            
            if ($User -eq "ec2-user" -and $config.user) {
                $script:User = $config.user
            }
            
            if (-not $KeyFile -and $config.key) {
                $script:KeyFile = $config.key
            }
            
            if ($RemotePath -eq "/home/ec2-user/pocket-option-bot" -and $config.remote_path) {
                $script:RemotePath = $config.remote_path
            }
            
            # Load additional configuration
            $script:TelegramApiId = $config.telegram_api_id
            $script:TelegramApiHash = $config.telegram_api_hash
            $script:TelegramBotToken = $config.telegram_bot_token
            $script:PocketOptionEmail = $config.pocket_option_email
            $script:PocketOptionPassword = $config.pocket_option_password
            
            Write-ColorOutput "DEBUG" "Configuration loaded:"
            Write-ColorOutput "DEBUG" "  Host: $Host"
            Write-ColorOutput "DEBUG" "  User: $User"
            Write-ColorOutput "DEBUG" "  KeyFile: $KeyFile"
            Write-ColorOutput "DEBUG" "  RemotePath: $RemotePath"
            Write-ColorOutput "DEBUG" "  Telegram API ID: $(if ($TelegramApiId) { 'set' } else { 'not set' })"
            Write-ColorOutput "DEBUG" "  Telegram API hash: $(if ($TelegramApiHash) { 'set' } else { 'not set' })"
            Write-ColorOutput "DEBUG" "  Telegram bot token: $(if ($TelegramBotToken) { 'set' } else { 'not set' })"
            Write-ColorOutput "DEBUG" "  Pocket Option email: $(if ($PocketOptionEmail) { 'set' } else { 'not set' })"
            Write-ColorOutput "DEBUG" "  Pocket Option password: $(if ($PocketOptionPassword) { 'set' } else { 'not set' })"
        }
        catch {
            Write-ColorOutput "ERROR" "Error parsing configuration file: $_"
        }
    }
    else {
        Write-ColorOutput "WARN" "Configuration file $ConfigFile not found. Using command-line arguments."
    }
}

# Function to validate required parameters
function Validate-Params {
    $valid = $true
    
    if (-not $Host) {
        Write-ColorOutput "ERROR" "Host is required. Use -Host to specify the EC2 instance hostname or IP address."
        $valid = $false
    }
    
    if (-not $KeyFile) {
        Write-ColorOutput "ERROR" "SSH private key is required. Use -KeyFile to specify the path to the SSH private key."
        $valid = $false
    }
    elseif (-not (Test-FileExists $KeyFile)) {
        Write-ColorOutput "ERROR" "SSH private key file $KeyFile not found."
        $valid = $false
    }
    
    # Check if required tools are installed
    if (-not (Test-Command "ssh")) {
        Write-ColorOutput "ERROR" "SSH client is not installed or not in PATH. Please install OpenSSH or ensure it's in your PATH."
        $valid = $false
    }
    
    if (-not (Test-Command "scp")) {
        Write-ColorOutput "ERROR" "SCP client is not installed or not in PATH. Please install OpenSSH or ensure it's in your PATH."
        $valid = $false
    }
    
    return $valid
}

# Function to create a temporary directory for packaging
function Create-TempDir {
    $tempDir = Join-Path -Path $env:TEMP -ChildPath "pocket-option-bot-$(Get-Random)"
    New-Item -ItemType Directory -Path $tempDir | Out-Null
    Write-ColorOutput "DEBUG" "Created temporary directory: $tempDir"
    return $tempDir
}

# Function to package the necessary files
function Package-Files {
    param (
        [Parameter(Mandatory=$true)]
        [string]$TempDir
    )
    
    Write-ColorOutput "INFO" "Packaging files for deployment..."
    
    # Create directories
    New-Item -ItemType Directory -Path "$TempDir\pocketoptionapi" -Force | Out-Null
    New-Item -ItemType Directory -Path "$TempDir\utils" -Force | Out-Null
    New-Item -ItemType Directory -Path "$TempDir\docs" -Force | Out-Null
    New-Item -ItemType Directory -Path "$TempDir\config" -Force | Out-Null
    
    # Get the project root directory (parent of utils)
    $projectRoot = Split-Path -Parent (Split-Path -Parent $PSCommandPath)
    
    # Copy files
    Copy-Item -Path "$projectRoot\pocketoptionapi\*" -Destination "$TempDir\pocketoptionapi\" -Recurse
    Copy-Item -Path "$projectRoot\utils\*" -Destination "$TempDir\utils\" -Recurse
    Copy-Item -Path "$projectRoot\docs\*" -Destination "$TempDir\docs\" -Recurse
    
    if (Test-FileExists "$projectRoot\README.md") {
        Copy-Item -Path "$projectRoot\README.md" -Destination "$TempDir\"
    }
    
    # Create config files
    if ($TelegramApiId -and $TelegramApiHash) {
        $telegramConfig = @{
            channel_name = "BINARY TRADING CLUB"
            channel_username = $null
            channel_id = $null
            signal_parser = @{
                first_message_pattern = "Trading Pair: (\w+/\w+)(?:\s*\(OTC\))?"
                second_message_timer_pattern = "SET THE TIMER TO (\d{2}:\d{2}:\d{2})"
                second_message_pair_pattern = "Currency pair (\w+/\w+)"
                second_message_direction_pattern = "(HIGHER|LOWER)"
                second_message_expiry_pattern = "Trade time: (\d+) MIN"
                max_time_between_messages = 60
            }
            monitoring = @{
                enabled = $true
                log_all_messages = $false
            }
        }
        
        $telegramConfig | ConvertTo-Json -Depth 10 | Set-Content -Path "$TempDir\config\telegram_config.json"
    }
    
    if ($PocketOptionEmail -and $PocketOptionPassword) {
        $pocketOptionConfig = @{
            api = @{
                websocket_url = $null
                connection_timeout = 30
                ping_interval = 30
            }
            trading = @{
                default_asset = "EUR/USD"
                default_amount = 1
                default_expiry = 60
                test_mode = $true
            }
            tests = @{
                assets_to_check = @("EUR/USD", "GBP/USD", "USD/JPY", "EUR/JPY", "AUD/USD")
                run_balance_check = $true
                run_asset_check = $true
                run_trade_test = $false
            }
        }
        
        $pocketOptionConfig | ConvertTo-Json -Depth 10 | Set-Content -Path "$TempDir\config\pocket_option_config.json"
    }
    
    # Create environment file
    @"
# Telegram API credentials
TELEGRAM_API_ID=$TelegramApiId
TELEGRAM_API_HASH=$TelegramApiHash
TELEGRAM_BOT_TOKEN=$TelegramBotToken

# Pocket Option credentials
POCKET_OPTION_EMAIL=$PocketOptionEmail
POCKET_OPTION_PASSWORD=$PocketOptionPassword
"@ | Set-Content -Path "$TempDir\config\.env"
    
    # Create requirements.txt
    @"
telethon>=1.24.0
websockets>=10.3
asyncio>=3.4.3
aiohttp>=3.8.1
python-dotenv>=0.20.0
pytz>=2022.1
SQLite3>=3.36.0
"@ | Set-Content -Path "$TempDir\requirements.txt"
    
    # Create setup script
    @"
#!/bin/bash
# setup.sh - Sets up the environment for the Pocket Option trading bot.

set -e  # Exit on error

# Install dependencies
echo "Installing dependencies..."
sudo apt-get update
sudo apt-get install -y python3 python3-pip python3-venv

# Create virtual environment
echo "Creating virtual environment..."
python3 -m venv venv
source venv/bin/activate

# Install Python dependencies
echo "Installing Python dependencies..."
pip install --upgrade pip
pip install -r requirements.txt

# Set up configuration
echo "Setting up configuration..."
mkdir -p ~/.pocket-option-bot
cp -r config/* ~/.pocket-option-bot/

echo "Setup complete!"
"@ | Set-Content -Path "$TempDir\setup.sh"
    
    # Create service file
    @"
[Unit]
Description=Pocket Option Trading Bot
After=network.target

[Service]
Type=simple
User=$User
WorkingDirectory=$RemotePath
ExecStart=$RemotePath/venv/bin/python3 $RemotePath/bot.py
Restart=on-failure
RestartSec=5
StandardOutput=syslog
StandardError=syslog
SyslogIdentifier=pocket-option-bot
Environment="PYTHONPATH=$RemotePath"
EnvironmentFile=$RemotePath/config/.env

[Install]
WantedBy=multi-user.target
"@ | Set-Content -Path "$TempDir\pocket-option-bot.service"
    
    # Create bot.py (placeholder)
    @"
#!/usr/bin/env python3
"""
bot.py - Main entry point for the Pocket Option trading bot.

This script initializes the trading bot, connects to the Telegram channel,
authenticates with the Pocket Option API, and starts monitoring for signals.
"""

import os
import sys
import json
import asyncio
import logging
import signal
from datetime import datetime
import dotenv

# Load environment variables
dotenv.load_dotenv(os.path.expanduser("~/.pocket-option-bot/.env"))

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler("bot.log")
    ]
)
logger = logging.getLogger(__name__)

# Placeholder for the main bot functionality
async def main():
    logger.info("Starting Pocket Option Trading Bot...")
    logger.info("This is a placeholder. Implement the actual bot functionality here.")
    
    # Keep the bot running
    while True:
        await asyncio.sleep(60)
        logger.info(f"Bot is running... {datetime.now().isoformat()}")

if __name__ == "__main__":
    logger.info("Initializing bot...")
    
    # Handle graceful shutdown
    loop = asyncio.get_event_loop()
    
    def signal_handler():
        logger.info("Shutting down...")
        loop.stop()
    
    for sig in (signal.SIGINT, signal.SIGTERM):
        loop.add_signal_handler(sig, signal_handler)
    
    try:
        loop.run_until_complete(main())
    except KeyboardInterrupt:
        logger.info("Bot interrupted by user")
    except Exception as e:
        logger.error(f"Error in bot: {str(e)}")
    finally:
        logger.info("Bot stopped")
"@ | Set-Content -Path "$TempDir\bot.py"
    
    Write-ColorOutput "INFO" "Files packaged successfully."
}

# Function to transfer files to the EC2 instance
function Transfer-Files {
    param (
        [Parameter(Mandatory=$true)]
        [string]$TempDir
    )
    
    Write-ColorOutput "INFO" "Transferring files to $Host..."
    
    # Create SSH options
    $sshOptions = "-i `"$KeyFile`" -o StrictHostKeyChecking=no -o UserKnownHostsFile=/dev/null"
    
    # Create remote directory
    $createDirCommand = "ssh $sshOptions $User@$Host `"mkdir -p $RemotePath`""
    Write-ColorOutput "DEBUG" "Executing: $createDirCommand"
    Invoke-Expression $createDirCommand
    
    # Transfer files using SCP
    $transferCommand = "scp $sshOptions -r `"$TempDir\*`" $User@$Host`:$RemotePath/"
    Write-ColorOutput "DEBUG" "Executing: $transferCommand"
    Invoke-Expression $transferCommand
    
    Write-ColorOutput "INFO" "Files transferred successfully."
}

# Function to set up the environment on the EC2 instance
function Setup-Environment {
    Write-ColorOutput "INFO" "Setting up environment on $Host..."
    
    # Create SSH options
    $sshOptions = "-i `"$KeyFile`" -o StrictHostKeyChecking=no -o UserKnownHostsFile=/dev/null"
    
    # Run setup script
    $setupCommand = "ssh $sshOptions $User@$Host `"cd $RemotePath && chmod +x setup.sh && ./setup.sh`""
    Write-ColorOutput "DEBUG" "Executing: $setupCommand"
    Invoke-Expression $setupCommand
    
    Write-ColorOutput "INFO" "Environment set up successfully."
}

# Function to configure the bot to run as a service
function Configure-Service {
    Write-ColorOutput "INFO" "Configuring bot to run as a service..."
    
    # Create SSH options
    $sshOptions = "-i `"$KeyFile`" -o StrictHostKeyChecking=no -o UserKnownHostsFile=/dev/null"
    
    # Copy service file to systemd directory
    $serviceCommand = "ssh $sshOptions $User@$Host `"sudo cp $RemotePath/pocket-option-bot.service /etc/systemd/system/ && sudo systemctl daemon-reload`""
    Write-ColorOutput "DEBUG" "Executing: $serviceCommand"
    Invoke-Expression $serviceCommand
    
    Write-ColorOutput "INFO" "Service configured successfully."
}

# Function to start the bot
function Start-Bot {
    Write-ColorOutput "INFO" "Starting the bot..."
    
    # Create SSH options
    $sshOptions = "-i `"$KeyFile`" -o StrictHostKeyChecking=no -o UserKnownHostsFile=/dev/null"
    
    # Enable and start the service
    if ($Restart) {
        $startCommand = "ssh $sshOptions $User@$Host `"sudo systemctl enable pocket-option-bot && sudo systemctl restart pocket-option-bot`""
    }
    else {
        $startCommand = "ssh $sshOptions $User@$Host `"sudo systemctl enable pocket-option-bot && sudo systemctl start pocket-option-bot`""
    }
    
    Write-ColorOutput "DEBUG" "Executing: $startCommand"
    Invoke-Expression $startCommand
    
    # Check service status
    $statusCommand = "ssh $sshOptions $User@$Host `"sudo systemctl status pocket-option-bot`""
    Write-ColorOutput "DEBUG" "Executing: $statusCommand"
    Invoke-Expression $statusCommand
    
    Write-ColorOutput "INFO" "Bot started successfully."
}

# Function to clean up temporary directory
function Cleanup-TempDir {
    param (
        [Parameter(Mandatory=$true)]
        [string]$TempDir
    )
    
    if (Test-DirectoryExists $TempDir) {
        Remove-Item -Path $TempDir -Recurse -Force
        Write-ColorOutput "DEBUG" "Removed temporary directory: $TempDir"
    }
}

# Main script execution
Write-Host "Pocket Option Trading Bot - EC2 Deployment Script" -ForegroundColor Cyan
Write-Host "------------------------------------------------" -ForegroundColor Cyan
Write-Host ""

# Load configuration
Load-Config

# Validate parameters
$valid = Validate-Params
if (-not $valid) {
    Write-ColorOutput "ERROR" "Parameter validation failed. Please check the errors above and try again."
    exit 1
}

# Create temporary directory
$tempDir = Create-TempDir

try {
    # Package files
    Package-Files -TempDir $tempDir
    
    # Transfer files
    Transfer-Files -TempDir $tempDir
    
    # Set up environment
    Setup-Environment
    
    # If setup only, exit
    if ($SetupOnly) {
        Write-ColorOutput "INFO" "Setup completed successfully. Exiting without deploying the bot."
        exit 0
    }
    
    # Configure service
    Configure-Service
    
    # Start bot
    Start-Bot
    
    Write-ColorOutput "INFO" "Deployment completed successfully."
}
catch {
    Write-ColorOutput "ERROR" "Deployment failed: $_"
    exit 1
}
finally {
    # Clean up temporary directory
    Cleanup-TempDir -TempDir $tempDir
}
