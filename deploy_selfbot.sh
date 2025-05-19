#!/bin/bash
# Self Bot v1.0 Deployment Script for EC2
# This script deploys the Self Bot to an EC2 instance using the Telethon user account approach

# Default values
USERNAME="ubuntu"
REMOTE_DIR="~/selfbot"
INCLUDE_SESSION_FILES=false

# Function to display usage information
usage() {
    echo "Usage: $0 -h HOST_IP -k KEY_PATH [-u USERNAME] [-d REMOTE_DIR] [-s]"
    echo "  -h HOST_IP        EC2 instance IP address"
    echo "  -k KEY_PATH       Path to SSH private key file (.pem)"
    echo "  -u USERNAME       SSH username (default: ubuntu)"
    echo "  -d REMOTE_DIR     Remote directory (default: ~/selfbot)"
    echo "  -s                Include session files"
    exit 1
}

# Parse command line arguments
while getopts "h:k:u:d:s" opt; do
    case $opt in
        h) HOST_IP="$OPTARG" ;;
        k) KEY_PATH="$OPTARG" ;;
        u) USERNAME="$OPTARG" ;;
        d) REMOTE_DIR="$OPTARG" ;;
        s) INCLUDE_SESSION_FILES=true ;;
        *) usage ;;
    esac
done

# Check required arguments
if [ -z "$HOST_IP" ] || [ -z "$KEY_PATH" ]; then
    echo "Error: Missing required arguments."
    usage
fi

# Validate key file
if [ ! -f "$KEY_PATH" ]; then
    echo "Error: SSH key file not found at: $KEY_PATH"
    exit 1
fi

# Set proper permissions for key file (required for SSH)
chmod 400 "$KEY_PATH"

# Required files to deploy
REQUIRED_FILES=(
    "bot.py"
    "run_bot.py"
    "monitor_signals.py"
    "check_telegram_session.py"
    "simulate_test_signals.py"
    ".env"
    "requirements.txt"
    "test_po_websocket.py"
    "test_ssid_direct.py"
    "extract_po_trade_ssid.md"
    "get_fresh_ssid_guide.md"
    "run_telegram_monitor.sh"
)

REQUIRED_DIRS=(
    "config"
    "pocketoptionapi"
    "utils"
)

# Check if required files exist
for file in "${REQUIRED_FILES[@]}"; do
    if [ ! -f "$file" ]; then
        echo "Warning: Required file not found: $file"
    fi
done

# Check if required directories exist
for dir in "${REQUIRED_DIRS[@]}"; do
    if [ ! -d "$dir" ]; then
        echo "Warning: Required directory not found: $dir"
    fi
done

# Create temporary directory for deployment
TEMP_DIR=$(mktemp -d)
echo "Created temporary directory: $TEMP_DIR"

# Function to clean up temporary directory
cleanup() {
    echo "Cleaning up temporary directory..."
    rm -rf "$TEMP_DIR"
}
trap cleanup EXIT

# Copy required files and directories
for file in "${REQUIRED_FILES[@]}"; do
    if [ -f "$file" ]; then
        cp "$file" "$TEMP_DIR/"
    fi
done

for dir in "${REQUIRED_DIRS[@]}"; do
    if [ -d "$dir" ]; then
        cp -r "$dir" "$TEMP_DIR/"
    fi
done

# Session files
if [ "$INCLUDE_SESSION_FILES" = true ]; then
    for session_file in *.session; do
        if [ -f "$session_file" ]; then
            cp "$session_file" "$TEMP_DIR/"
        fi
    done
fi

# Create systemd service file
cat > "$TEMP_DIR/selfbot.service" << EOL
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
EOL

# Create setup script
cat > "$TEMP_DIR/setup.sh" << EOL
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
EOL

# Make setup script executable
chmod +x "$TEMP_DIR/setup.sh"

# SSH options
SSH_OPTIONS="-i \"$KEY_PATH\" -o StrictHostKeyChecking=no"

# Create remote directory if it doesn't exist
echo "Creating remote directory: $REMOTE_DIR"
ssh $SSH_OPTIONS $USERNAME@$HOST_IP "mkdir -p $REMOTE_DIR"

# Transfer files
echo "Transferring files to EC2 instance..."
scp $SSH_OPTIONS -r "$TEMP_DIR/"* "$USERNAME@$HOST_IP:$REMOTE_DIR/"

# Make setup script executable (again, just to be sure)
ssh $SSH_OPTIONS $USERNAME@$HOST_IP "chmod +x $REMOTE_DIR/setup.sh"

# Run setup script
echo "Running setup script..."
ssh $SSH_OPTIONS $USERNAME@$HOST_IP "cd $REMOTE_DIR && ./setup.sh"

echo "Deployment completed successfully!"
echo "Remote directory: $REMOTE_DIR"
echo "To start the service: ssh $SSH_OPTIONS $USERNAME@$HOST_IP 'sudo systemctl start selfbot.service'"
echo "To check service status: ssh $SSH_OPTIONS $USERNAME@$HOST_IP 'sudo systemctl status selfbot.service'"
echo "To view logs: ssh $SSH_OPTIONS $USERNAME@$HOST_IP 'sudo journalctl -u selfbot.service -f'"
