#!/bin/bash
# deploy.sh - Deploys the Pocket Option trading bot to an EC2 instance.
#
# This script packages the necessary files, transfers them to the EC2 instance,
# sets up the environment, configures the bot to run as a service, and starts the bot.
#
# Usage: ./deploy.sh [options]
#
# Options:
#   -h, --host        EC2 instance hostname or IP address
#   -u, --user        SSH username (default: ec2-user)
#   -k, --key         Path to SSH private key
#   -p, --path        Remote deployment path (default: /home/ec2-user/pocket-option-bot)
#   -c, --config      Path to configuration file (default: deploy_config.json)
#   -s, --setup-only  Only set up the environment, don't deploy the bot
#   -r, --restart     Restart the bot service if it's already running
#   -v, --verbose     Enable verbose output
#   --help            Display this help message and exit

set -e  # Exit on error

# Default values
HOST=""
USER="ec2-user"
KEY=""
REMOTE_PATH="/home/ec2-user/pocket-option-bot"
CONFIG_FILE="deploy_config.json"
SETUP_ONLY=false
RESTART=false
VERBOSE=false

# ANSI color codes
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[0;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Function to display usage
function show_usage {
    echo "Usage: $0 [options]"
    echo ""
    echo "Options:"
    echo "  -h, --host        EC2 instance hostname or IP address"
    echo "  -u, --user        SSH username (default: ec2-user)"
    echo "  -k, --key         Path to SSH private key"
    echo "  -p, --path        Remote deployment path (default: /home/ec2-user/pocket-option-bot)"
    echo "  -c, --config      Path to configuration file (default: deploy_config.json)"
    echo "  -s, --setup-only  Only set up the environment, don't deploy the bot"
    echo "  -r, --restart     Restart the bot service if it's already running"
    echo "  -v, --verbose     Enable verbose output"
    echo "  --help            Display this help message and exit"
    exit 1
}

# Function to log messages
function log {
    local level=$1
    local message=$2
    local color=$NC
    
    case $level in
        "INFO")
            color=$GREEN
            ;;
        "WARN")
            color=$YELLOW
            ;;
        "ERROR")
            color=$RED
            ;;
        "DEBUG")
            color=$BLUE
            ;;
    esac
    
    if [[ "$level" != "DEBUG" || "$VERBOSE" == true ]]; then
        echo -e "${color}[$level] $message${NC}"
    fi
}

# Function to check if a command exists
function command_exists {
    command -v "$1" >/dev/null 2>&1
}

# Function to check if a file exists
function file_exists {
    [[ -f "$1" ]]
}

# Function to check if a directory exists
function dir_exists {
    [[ -d "$1" ]]
}

# Function to check if jq is installed
function check_jq {
    if ! command_exists jq; then
        log "ERROR" "jq is not installed. Please install it and try again."
        log "INFO" "On Ubuntu/Debian: sudo apt-get install jq"
        log "INFO" "On CentOS/RHEL: sudo yum install jq"
        log "INFO" "On macOS: brew install jq"
        exit 1
    fi
}

# Function to load configuration from file
function load_config {
    if file_exists "$CONFIG_FILE"; then
        log "INFO" "Loading configuration from $CONFIG_FILE"
        
        # Check if jq is installed
        check_jq
        
        # Load configuration
        if [[ -z "$HOST" ]]; then
            HOST=$(jq -r '.host // empty' "$CONFIG_FILE")
        fi
        
        if [[ "$USER" == "ec2-user" ]]; then
            USER=$(jq -r '.user // "ec2-user"' "$CONFIG_FILE")
        fi
        
        if [[ -z "$KEY" ]]; then
            KEY=$(jq -r '.key // empty' "$CONFIG_FILE")
        fi
        
        if [[ "$REMOTE_PATH" == "/home/ec2-user/pocket-option-bot" ]]; then
            REMOTE_PATH=$(jq -r '.remote_path // "/home/ec2-user/pocket-option-bot"' "$CONFIG_FILE")
        fi
        
        # Load additional configuration
        TELEGRAM_API_ID=$(jq -r '.telegram_api_id // empty' "$CONFIG_FILE")
        TELEGRAM_API_HASH=$(jq -r '.telegram_api_hash // empty' "$CONFIG_FILE")
        TELEGRAM_BOT_TOKEN=$(jq -r '.telegram_bot_token // empty' "$CONFIG_FILE")
        POCKET_OPTION_EMAIL=$(jq -r '.pocket_option_email // empty' "$CONFIG_FILE")
        POCKET_OPTION_PASSWORD=$(jq -r '.pocket_option_password // empty' "$CONFIG_FILE")
        
        log "DEBUG" "Configuration loaded:"
        log "DEBUG" "  Host: $HOST"
        log "DEBUG" "  User: $USER"
        log "DEBUG" "  Key: $KEY"
        log "DEBUG" "  Remote path: $REMOTE_PATH"
        log "DEBUG" "  Telegram API ID: ${TELEGRAM_API_ID:+set}"
        log "DEBUG" "  Telegram API hash: ${TELEGRAM_API_HASH:+set}"
        log "DEBUG" "  Telegram bot token: ${TELEGRAM_BOT_TOKEN:+set}"
        log "DEBUG" "  Pocket Option email: ${POCKET_OPTION_EMAIL:+set}"
        log "DEBUG" "  Pocket Option password: ${POCKET_OPTION_PASSWORD:+set}"
    else
        log "WARN" "Configuration file $CONFIG_FILE not found. Using command-line arguments."
    fi
}

# Function to validate required parameters
function validate_params {
    if [[ -z "$HOST" ]]; then
        log "ERROR" "Host is required. Use -h or --host to specify the EC2 instance hostname or IP address."
        show_usage
    fi
    
    if [[ -z "$KEY" ]]; then
        log "ERROR" "SSH private key is required. Use -k or --key to specify the path to the SSH private key."
        show_usage
    fi
    
    if ! file_exists "$KEY"; then
        log "ERROR" "SSH private key file $KEY not found."
        exit 1
    fi
}

# Function to create a temporary directory for packaging
function create_temp_dir {
    TEMP_DIR=$(mktemp -d)
    log "DEBUG" "Created temporary directory: $TEMP_DIR"
    trap 'rm -rf "$TEMP_DIR"' EXIT
}

# Function to package the necessary files
function package_files {
    log "INFO" "Packaging files for deployment..."
    
    # Create directories
    mkdir -p "$TEMP_DIR/pocketoptionapi"
    mkdir -p "$TEMP_DIR/utils"
    mkdir -p "$TEMP_DIR/docs"
    mkdir -p "$TEMP_DIR/config"
    
    # Copy files
    cp -r ../pocketoptionapi/* "$TEMP_DIR/pocketoptionapi/"
    cp -r ../utils/* "$TEMP_DIR/utils/"
    cp -r ../docs/* "$TEMP_DIR/docs/"
    cp ../README.md "$TEMP_DIR/"
    
    # Create config files
    if [[ -n "$TELEGRAM_API_ID" && -n "$TELEGRAM_API_HASH" ]]; then
        cat > "$TEMP_DIR/config/telegram_config.json" << EOF
{
    "channel_name": "BINARY TRADING CLUB",
    "channel_username": null,
    "channel_id": null,
    "signal_parser": {
        "first_message_pattern": "Trading Pair: (\\w+/\\w+)(?:\\s*\\(OTC\\))?",
        "second_message_timer_pattern": "SET THE TIMER TO (\\d{2}:\\d{2}:\\d{2})",
        "second_message_pair_pattern": "Currency pair (\\w+/\\w+)",
        "second_message_direction_pattern": "(HIGHER|LOWER)",
        "second_message_expiry_pattern": "Trade time: (\\d+) MIN",
        "max_time_between_messages": 60
    },
    "monitoring": {
        "enabled": true,
        "log_all_messages": false
    }
}
EOF
    fi
    
    if [[ -n "$POCKET_OPTION_EMAIL" && -n "$POCKET_OPTION_PASSWORD" ]]; then
        cat > "$TEMP_DIR/config/pocket_option_config.json" << EOF
{
    "api": {
        "websocket_url": null,
        "connection_timeout": 30,
        "ping_interval": 30
    },
    "trading": {
        "default_asset": "EUR/USD",
        "default_amount": 1,
        "default_expiry": 60,
        "test_mode": true
    },
    "tests": {
        "assets_to_check": ["EUR/USD", "GBP/USD", "USD/JPY", "EUR/JPY", "AUD/USD"],
        "run_balance_check": true,
        "run_asset_check": true,
        "run_trade_test": false
    }
}
EOF
    fi
    
    # Create environment file
    cat > "$TEMP_DIR/config/.env" << EOF
# Telegram API credentials
TELEGRAM_API_ID=${TELEGRAM_API_ID}
TELEGRAM_API_HASH=${TELEGRAM_API_HASH}
TELEGRAM_BOT_TOKEN=${TELEGRAM_BOT_TOKEN}

# Pocket Option credentials
POCKET_OPTION_EMAIL=${POCKET_OPTION_EMAIL}
POCKET_OPTION_PASSWORD=${POCKET_OPTION_PASSWORD}
EOF
    
    # Create requirements.txt
    cat > "$TEMP_DIR/requirements.txt" << EOF
telethon>=1.24.0
websockets>=10.3
asyncio>=3.4.3
aiohttp>=3.8.1
python-dotenv>=0.20.0
pytz>=2022.1
SQLite3>=3.36.0
EOF
    
    # Create setup script
    cat > "$TEMP_DIR/setup.sh" << EOF
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
EOF
    
    # Create service file
    cat > "$TEMP_DIR/pocket-option-bot.service" << EOF
[Unit]
Description=Pocket Option Trading Bot
After=network.target

[Service]
Type=simple
User=${USER}
WorkingDirectory=${REMOTE_PATH}
ExecStart=${REMOTE_PATH}/venv/bin/python3 ${REMOTE_PATH}/bot.py
Restart=on-failure
RestartSec=5
StandardOutput=syslog
StandardError=syslog
SyslogIdentifier=pocket-option-bot
Environment="PYTHONPATH=${REMOTE_PATH}"
EnvironmentFile=${REMOTE_PATH}/config/.env

[Install]
WantedBy=multi-user.target
EOF
    
    # Create bot.py (placeholder)
    cat > "$TEMP_DIR/bot.py" << EOF
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
EOF
    
    # Make scripts executable
    chmod +x "$TEMP_DIR/setup.sh"
    chmod +x "$TEMP_DIR/bot.py"
    
    log "INFO" "Files packaged successfully."
}

# Function to transfer files to the EC2 instance
function transfer_files {
    log "INFO" "Transferring files to $HOST..."
    
    # Create SSH options
    SSH_OPTS="-i $KEY -o StrictHostKeyChecking=no -o UserKnownHostsFile=/dev/null"
    
    # Create remote directory
    ssh $SSH_OPTS $USER@$HOST "mkdir -p $REMOTE_PATH"
    
    # Transfer files
    rsync -avz --progress -e "ssh $SSH_OPTS" "$TEMP_DIR/" $USER@$HOST:$REMOTE_PATH/
    
    log "INFO" "Files transferred successfully."
}

# Function to set up the environment on the EC2 instance
function setup_environment {
    log "INFO" "Setting up environment on $HOST..."
    
    # Create SSH options
    SSH_OPTS="-i $KEY -o StrictHostKeyChecking=no -o UserKnownHostsFile=/dev/null"
    
    # Run setup script
    ssh $SSH_OPTS $USER@$HOST "cd $REMOTE_PATH && chmod +x setup.sh && ./setup.sh"
    
    log "INFO" "Environment set up successfully."
}

# Function to configure the bot to run as a service
function configure_service {
    log "INFO" "Configuring bot to run as a service..."
    
    # Create SSH options
    SSH_OPTS="-i $KEY -o StrictHostKeyChecking=no -o UserKnownHostsFile=/dev/null"
    
    # Copy service file to systemd directory
    ssh $SSH_OPTS $USER@$HOST "sudo cp $REMOTE_PATH/pocket-option-bot.service /etc/systemd/system/ && sudo systemctl daemon-reload"
    
    log "INFO" "Service configured successfully."
}

# Function to start the bot
function start_bot {
    log "INFO" "Starting the bot..."
    
    # Create SSH options
    SSH_OPTS="-i $KEY -o StrictHostKeyChecking=no -o UserKnownHostsFile=/dev/null"
    
    # Enable and start the service
    if [[ "$RESTART" == true ]]; then
        ssh $SSH_OPTS $USER@$HOST "sudo systemctl enable pocket-option-bot && sudo systemctl restart pocket-option-bot"
    else
        ssh $SSH_OPTS $USER@$HOST "sudo systemctl enable pocket-option-bot && sudo systemctl start pocket-option-bot"
    fi
    
    # Check service status
    ssh $SSH_OPTS $USER@$HOST "sudo systemctl status pocket-option-bot"
    
    log "INFO" "Bot started successfully."
}

# Parse command-line arguments
while [[ $# -gt 0 ]]; do
    case $1 in
        -h|--host)
            HOST="$2"
            shift 2
            ;;
        -u|--user)
            USER="$2"
            shift 2
            ;;
        -k|--key)
            KEY="$2"
            shift 2
            ;;
        -p|--path)
            REMOTE_PATH="$2"
            shift 2
            ;;
        -c|--config)
            CONFIG_FILE="$2"
            shift 2
            ;;
        -s|--setup-only)
            SETUP_ONLY=true
            shift
            ;;
        -r|--restart)
            RESTART=true
            shift
            ;;
        -v|--verbose)
            VERBOSE=true
            shift
            ;;
        --help)
            show_usage
            ;;
        *)
            log "ERROR" "Unknown option: $1"
            show_usage
            ;;
    esac
done

# Main script execution
log "INFO" "Starting deployment process..."

# Load configuration
load_config

# Validate parameters
validate_params

# Create temporary directory
create_temp_dir

# Package files
package_files

# Transfer files
transfer_files

# Set up environment
setup_environment

# If setup only, exit
if [[ "$SETUP_ONLY" == true ]]; then
    log "INFO" "Setup completed successfully. Exiting without deploying the bot."
    exit 0
fi

# Configure service
configure_service

# Start bot
start_bot

log "INFO" "Deployment completed successfully."
