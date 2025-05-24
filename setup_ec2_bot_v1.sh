#!/bin/bash
# setup_ec2_bot_v1.sh - Comprehensive setup script for Self Bot v1.0 on EC2
# Run this script on your EC2 instance in the self_bot_v1 directory

# Exit on error
set -e

echo "=========================================================="
echo "Setting up Self Bot v1.0 on EC2 instance"
echo "=========================================================="

# Check if we're in the right directory
if [ ! -f "requirements.txt" ]; then
    echo "Error: requirements.txt not found. Make sure you're in the self_bot_v1 directory."
    exit 1
fi

# Step 1: Install system dependencies
echo -e "\n[1/7] Installing system dependencies..."
sudo apt-get update
sudo apt-get install -y python3-pip python3-venv sqlite3 libsqlite3-dev

# Step 2: Set up Python virtual environment
echo -e "\n[2/7] Setting up Python virtual environment..."
if [ ! -d "venv" ]; then
    python3 -m venv venv
    echo "Virtual environment created."
else
    echo "Virtual environment already exists."
fi

# Step 3: Activate virtual environment and install dependencies
echo -e "\n[3/7] Installing Python dependencies..."
source venv/bin/activate
pip install --upgrade pip
pip install -r requirements.txt

# Step 4: Check configuration files
echo -e "\n[4/7] Checking configuration files..."
mkdir -p config
mkdir -p data
mkdir -p logs

# Check for telegram_config.json
if [ ! -f "config/telegram_config.json" ]; then
    echo "Warning: telegram_config.json not found. Creating a template..."
    cat > config/telegram_config.json << 'EOL'
{
  "channel_name": "BINARY TRADING CLUB",
  "channel_id": -1002412213735,
  "first_message_regex": "Trading Pair: (\\w+/\\w+)(?:\\s*\\(OTC\\))?",
  "second_message_regex": {
    "timer": "SET THE TIMER TO (\\d{2}:\\d{2}:\\d{2})",
    "pair": "Currency pair (\\w+/\\w+)",
    "direction": "(HIGHER|LOWER)",
    "expiry": "Trade time: (\\d+) MIN"
  },
  "pair_match_window": 60,
  "api_id": 28529262,
  "api_hash": "6e3dde953198895cddbd7396631a1da5",
  "session_name": "pocket_option_userbot"
}
EOL
    echo "Please update config/telegram_config.json with your settings."
else
    echo "telegram_config.json found."
fi

# Check for pocket_option_config.json
if [ ! -f "config/pocket_option_config.json" ]; then
    echo "Warning: pocket_option_config.json not found. Creating a template..."
    cat > config/pocket_option_config.json << 'EOL'
{
  "ssid": "YOUR_ACTUAL_SSID_HERE",
  "is_demo": true,
  "api": {
    "websocket_url": "wss://po.trade/socket.io/?EIO=3&transport=websocket",
    "connection_timeout": 30,
    "ping_interval": 30
  },
  "trading": {
    "default_asset": "EUR/USD",
    "default_amount": 1,
    "default_expiry": 60,
    "test_mode": true
  }
}
EOL
    echo "Please update config/pocket_option_config.json with your SSID."
else
    echo "pocket_option_config.json found."
fi

# Check for .env file
if [ ! -f ".env" ]; then
    echo "Warning: .env file not found. Creating a template..."
    cat > .env << 'EOL'
TELEGRAM_API_ID=28529262
TELEGRAM_API_HASH=6e3dde953198895cddbd7396631a1da5
EOL
    echo ".env file created."
else
    echo ".env file found."
fi

# Step 5: Create systemd service file
echo -e "\n[5/7] Creating systemd service file..."
cat > selfbot.service << 'EOL'
[Unit]
Description=Self Bot Trading Service
After=network.target

[Service]
User=ubuntu
Group=ubuntu
WorkingDirectory=/home/ubuntu/self_bot_v1
ExecStart=/home/ubuntu/self_bot_v1/venv/bin/python /home/ubuntu/self_bot_v1/bot.py
Restart=always
RestartSec=10
EnvironmentFile=/home/ubuntu/self_bot_v1/.env

[Install]
WantedBy=multi-user.target
EOL

echo "Systemd service file created."

# Step 6: Install systemd service
echo -e "\n[6/7] Installing systemd service..."
sudo mv selfbot.service /etc/systemd/system/
sudo systemctl daemon-reload
sudo systemctl enable selfbot.service

# Step 7: Verify SQLite is working
echo -e "\n[7/7] Verifying SQLite installation..."
python -c "import sqlite3; print('SQLite version:', sqlite3.sqlite_version)"

# Setup complete
echo -e "\n=========================================================="
echo "Setup complete! Here are the next steps:"
echo "=========================================================="
echo "1. Update your configuration files if needed:"
echo "   - config/telegram_config.json"
echo "   - config/pocket_option_config.json"
echo ""
echo "2. Test your Telegram session:"
echo "   source venv/bin/activate"
echo "   python check_telegram_session.py --verbose"
echo ""
echo "3. Test your Pocket Option SSID:"
echo "   source venv/bin/activate"
echo "   python test_ssid_direct.py"
echo ""
echo "4. Monitor for signals (test for 5 minutes):"
echo "   source venv/bin/activate"
echo "   python monitor_signals.py --duration 300 --verbose"
echo ""
echo "5. Start the bot service:"
echo "   sudo systemctl start selfbot.service"
echo ""
echo "6. Check service status and logs:"
echo "   sudo systemctl status selfbot.service"
echo "   sudo journalctl -u selfbot.service -f"
echo "=========================================================="
